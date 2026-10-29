#!/usr/bin/env python3
"""Run the screen profile's quality arms against an already-running remote OpenAI-compatible server (e.g. vLLM).

Same payloads, prompt style, thinking-off kwargs, token cap and record fields as screen_mission.py, so the output is
judge.py-compatible and content-key reuse applies. No server management, no VRAM/fit check, and no latency gate:
timings from other hardware or engines are recorded but are not comparable with the 3090 llama.cpp numbers.

  python mission/studies/remote_arm.py --base http://192.168.2.14:8000/v1 --served-model LilaRest/gemma-4-31B-it-NVFP4-turbo \
      --label 'Gemma 4 31B IT' --run-tag NVFP4-vllm --revision <hf sha> --out results/screen_quants/NVFP4-vllm/02_Gemma_4_31B_IT
"""
from __future__ import annotations
import argparse, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import screen_mission as sm
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import mechanical as mech


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--base', required=True)
    p.add_argument('--served-model', required=True, help='model id the server expects')
    p.add_argument('--label', required=True, help='model name recorded in results (matches the catalog family entry)')
    p.add_argument('--run-tag', required=True, help='quant/engine tag, e.g. NVFP4-vllm')
    p.add_argument('--revision', required=True, help='HF revision of the served weights')
    p.add_argument('--style', default='chat')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--workers', type=int, default=8)
    p.add_argument('--timeout', type=float, default=120)
    p.add_argument('--retries', type=int, default=6, help='retries on HTTP 429, each after --backoff seconds')
    p.add_argument('--backoff', type=float, default=20)
    p.add_argument('--retry-echo', type=int, default=0,
                   help='re-request up to N times when the reply is the source returned untranslated (flaky cloud endpoints); '
                        'existing echoed records are redone and each record keeps echo_retries for the footnote')
    p.add_argument('--interval', type=float, default=0, help='minimum seconds between request starts (rate-limited APIs)')
    args = p.parse_args()

    build = sm.build_payload
    def build_named(*a, **k):
        payload, comp = build(*a, **k)
        payload['model'] = args.served_model
        return payload, comp
    sm.build_payload = build_named

    run_id = f'{args.label}:{args.run_tag}:off:{args.revision[:12]}:{sm.PROFILE}'
    common = {'model': args.label, 'run_id': run_id, 'quant_repo_sha': args.revision, 'quant_attested': False,
              'prompt_style': args.style, 'profile': sm.PROFILE, 'engine': args.run_tag, 'served_model': args.served_model}
    args.out.mkdir(parents=True, exist_ok=True)
    gate, next_start = threading.Lock(), [0.0]
    def pace():
        with gate:
            wait = next_start[0] - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            next_start[0] = time.monotonic() + args.interval
    for dataset, mode in sm.ARM_ORDER:
        if (dataset, mode) not in sm.STYLE_ARMS[args.style]:
            continue
        src = sm.DATA / ('lines_bare.jsonl' if dataset == 'lines' else f'scenes_{mode}.jsonl')
        src_sha = sm.sha_file(src)
        path = args.out / f'{dataset}_{mode}.jsonl'
        source = sm.load_jsonl(src)
        jp = {c['id']: c['japanese'] for c in source}
        echoed = lambda r: mech.zero_reason(jp.get(r['id'], ''), r['translation'], None) == 'exact_echo'
        done = {r['id'] for r in sm.load_jsonl(path)
                if r.get('translation') and not r.get('error') and r.get('run_id') == run_id and r.get('source_sha256') == src_sha
                and not (args.retry_echo and echoed(r))}
        cases = [c for c in source if c['id'] not in done]
        if args.retry_echo and cases and path.exists():  # drop the echoed rows being redone, so each id keeps one record
            keep = [r for r in sm.load_jsonl(path) if r['id'] in done]
            path.write_text(''.join(sm.json.dumps(r, ensure_ascii=False) + '\n' for r in keep), encoding='utf-8')

        def one(c):
            limited = echoes = 0
            while True:  # 429s wait and retry (bounded by --retries); echoes re-ask (bounded by --retry-echo)
                pace()
                rec = sm.translate(args.base, c, args.style, dataset, mode, args.timeout)
                if '429' in (rec['error'] or '') and limited < args.retries:
                    limited += 1
                    time.sleep(args.backoff)
                elif args.retry_echo and rec['translation'] and echoed(dict(rec, id=c['id'])) and echoes < args.retry_echo:
                    echoes += 1
                else:
                    break
            if args.retry_echo:
                rec['echo_retries'] = echoes
            rec.update(id=c['id'], dataset=dataset, mode=mode, source_sha256=src_sha, split=c.get('split'), **common)
            return rec
        with ThreadPoolExecutor(args.workers) as ex:
            recs = list(ex.map(one, cases))
        for rec in recs:  # written in source order after the arm, so a file never interleaves arms mid-write
            sm.append_jsonl(path, rec)
        ok = sum(bool(r['translation'] and not r['error']) for r in recs) + len(done)
        sm.log(f'📝 {dataset}/{mode}: {ok}/{ok + sum(bool(r["error"]) for r in recs)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
