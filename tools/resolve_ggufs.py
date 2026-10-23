#!/usr/bin/env python3
"""Attest precise Q4 GGUF paths, sizes, and revision hashes using Hugging Face.

No files are downloaded. All network-dependent attestations are distinguished from
manually reviewed repo links. Failure/ambiguity is not reported as a qualified file.
"""
from __future__ import annotations
import argparse, copy, csv, json, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def quant_matches(path: str, quant: str) -> bool:
    """Match complete quant tokens; do not accidentally select a projector or draft."""
    p = path.lower()
    if not p.endswith('.gguf') or any(x in p for x in ('mmproj', 'projector', 'draft', 'mtp-', '/mtp/')):
        return False
    q = re.escape(quant.lower())
    if quant.lower() == 'q4_k_m' and 'ud-q4_k_m' in p:
        return False
    # Covers foo-Q4_K_M.gguf, foo.Q4_K_M.gguf and split foo-Q4_K_M-00001-of-00003.gguf.
    return bool(re.search(rf'(?<![a-z0-9]){q}(?:-\d{{5}}-of-\d{{5}})?\.gguf$', p))


def group_quant_files(files: list[dict], quant: str) -> list[dict] | None:
    matches = [f for f in files if quant_matches(f['path'], quant)]
    if not matches:
        return None
    split_re = re.compile(r'^(.*?)-(?P<n>\d{5})-of-(?P<total>\d{5})\.gguf$', re.I)
    groups: dict[str,list[dict]] = {}
    for f in matches:
        m = split_re.match(f['path'])
        key = (m.group(1) + '.gguf') if m else f['path']
        groups.setdefault(key, []).append(f)
    valid = []
    for key, chunk in groups.items():
        if len(chunk) == 1 and not split_re.match(chunk[0]['path']):
            valid.append(chunk)
            continue
        match = [split_re.match(x['path']) for x in chunk]
        if any(m is None for m in match):
            continue
        total = int(match[0]['total'])
        indices = [int(m['n']) for m in match]
        if (len(chunk) == total and set(indices) == set(range(1,total+1))
                and all(int(m['total']) == total for m in match)):
            valid.append(sorted(chunk, key=lambda x:x['path']))
    if len(valid) != 1:
        return None  # ambiguous or incomplete; require human inspection
    return valid[0]


def select_quant_files(files: list[dict], preferred_quant: str, allow_fallback: bool=False):
    selection = group_quant_files(files, preferred_quant)
    if selection:
        return selection, preferred_quant, False
    if allow_fallback:
        for fallback in ('Q4_K_M', 'UD-Q4_K_M', 'UD-Q4_K_XL'):
            if fallback == preferred_quant:
                continue
            selection = group_quant_files(files, fallback)
            if selection:
                return selection, fallback, True
    return None, None, False


def declared_parents(card_data):
    """Return explicitly declared HF base-model ids, if available (not authoritative proof)."""
    if not card_data:
        return []
    if hasattr(card_data, 'to_dict'):
        data=card_data.to_dict()
    elif isinstance(card_data, dict):
        data=card_data
    else:
        try: data=dict(card_data)
        except (TypeError, ValueError): return []
    obj=data.get('base_model') or []
    if isinstance(obj,str): return [obj]
    if isinstance(obj,list): return [str(x) for x in obj if isinstance(x,str)]
    return []


def attestation_for_row(row, api, allow_fallback=False):
    out = copy.deepcopy(row)
    try:
        # metadata flag returns exact sibling sizes without transferring GGUFs.
        info = api.model_info(out['quant_repo'], files_metadata=True)
        out['repo_declared_parents'] = declared_parents(getattr(info,'card_data',None))
        out['lineage_attestation'] = ('publisher_declared' if out['repo_declared_parents'] and any(
            parent.casefold() == out['original_repo'].casefold() for parent in out['repo_declared_parents'])
            else 'not_declared_or_non_matching')
        if out['repo_declared_parents'] and not any(
                parent.casefold() == out['original_repo'].casefold() for parent in out['repo_declared_parents']):
            out['lineage_attestation'] = 'upstream_ancestry_or_mismatch_requires_review'
            out['lineage_review_note'] = f"Expected training release {out['original_repo']}; GGUF card declares {out['repo_declared_parents']}. Source lineage NOT confirmed."
        files = [{'path': s.rfilename, 'size': getattr(s, 'size', None)} for s in info.siblings
                 if s.rfilename.lower().endswith('.gguf')]
        selected, selected_quant, fallback = select_quant_files(files, out['preferred_quant'], allow_fallback)
        out['model_repo_sha'] = info.sha
        out['repository_downloads_30d'] = getattr(info, 'downloads', None)
        if not selected:
            available = sorted({q for q in ('Q4_K_M','UD-Q4_K_M','UD-Q4_K_XL','MXFP4')
                                if any(quant_matches(f['path'],q) for f in files)})
            out['repro_status'] = 'HUB_VERIFIED_REPO_BUT_PREFERRED_QUANT_NOT_UNAMBIGUOUS'
            out['attestation_error'] = 'Preferred quant not exactly found / ambiguous / incomplete split files'
            out['available_quants_in_policy'] = available
            return out
        out['quant_file'] = selected[0]['path'] if len(selected)==1 else [f['path'] for f in selected]
        out['selected_quant'] = selected_quant
        out['non_default_fallback'] = fallback
        out['quant_files_count'] = len(selected)
        out['quant_size_gb'] = (round(sum(f['size'] for f in selected)/1e9,3)
                                if all(isinstance(f['size'],int) for f in selected) else None)
        out['exact_file_url'] = ('https://huggingface.co/' + out['quant_repo'] + '/blob/' + info.sha
                                 + '/' + quote(selected[0]['path'],safe='/')
                                 if len(selected)==1 else None)
        out['hf_paths'] = [f['path'] for f in selected]
        out['file_sizes_bytes'] = [f['size'] for f in selected]
        out['repro_status'] = ('HUB_QUANT_ATTESTED_FALLBACK' if fallback else 'HUB_QUANT_ATTESTED')
        if out['quant_size_gb'] is None or not out['model_repo_sha']:
            out['repro_status'] = 'HUB_QUANT_PATH_FOUND_BUT_SIZE_OR_REVISION_MISSING'
        elif out['lineage_attestation'] == 'upstream_ancestry_or_mismatch_requires_review':
            out['repro_status'] = 'HUB_QUANT_ATTESTED_PARENT_REVIEW_PENDING'
    except Exception as e:
        out['repro_status'] = 'HUB_PREFLIGHT_FAILED'
        out['attestation_error'] = f'{type(e).__name__}: {str(e)[:400]}'
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog',type=Path,default=ROOT/'data'/'otakubench50.json',help='Active v4 model manifest, not original 50 baseline')
    p.add_argument('--limit',type=int,default=50,help='Attest top N; default 50')
    p.add_argument('--workers',type=int,default=5)
    p.add_argument('--allow-fallback',action='store_true',help='Permit another Q4 scheme, explicitly flagged')
    p.add_argument('--quant',choices=['Q4_K_M','Q5_K_M','Q6_K','Q8_0','UD-Q4_K_M','UD-Q4_K_XL'],default=None,help='Attest a specific quant for every row; do not guess high-quant files')
    p.add_argument('--out',type=Path,default=ROOT/'data'/'attested.json')
    p.add_argument('--token',default=None,help='HF token (recommended via HF_TOKEN env, not CLI)')
    args=p.parse_args()
    from huggingface_hub import HfApi
    api=HfApi(token=args.token)
    data=json.loads(args.catalog.read_text(encoding='utf-8'))
    rows=copy.deepcopy(data['models'][:args.limit])
    if args.quant:
        for r in rows:r['preferred_quant']=args.quant
    results=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(attestation_for_row,r,api,args.allow_fallback):r for r in rows}
        for ft in as_completed(futures):
            r=ft.result();results.append(r)
            print(f"{r['rank']:02d} {r['repro_status']} {r['model']}",flush=True)
    results.sort(key=lambda r:r['rank'])
    updated=dict(data)
    updated['models']=results
    updated['verification']={
        'method':'huggingface_hub HfApi.model_info(files_metadata=True)',
        'scope':f'first {len(rows)} candidates from {args.catalog}; NOT an inference benchmark',
        'quant_override':args.quant,
        'attested':sum(x['repro_status']=='HUB_QUANT_ATTESTED' for x in results),
        'failed_or_ambiguous':sum(x['repro_status']!='HUB_QUANT_ATTESTED' for x in results),
        'downloaded_bytes':0,
        'human_file_review_required_for_failures':True,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n')
    with args.out.with_suffix('.csv').open('w',newline='',encoding='utf-8-sig') as f:
        fields=list(dict.fromkeys(k for r in results for k in r))
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in results:
            w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
    print(json.dumps(updated['verification'],indent=2))
    if updated['verification']['failed_or_ambiguous']:
        return 2
    return 0

if __name__=='__main__':sys.exit(main())
