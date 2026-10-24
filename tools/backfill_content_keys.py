#!/usr/bin/env python3
"""Add content_key to judgments made before judge.py stored it, so later models can reuse them.

A judgment's key already fingerprints exactly what the judge saw (judge settings, rubric, the item
and the translation) plus which model produced it. This recomputes that key from the current
response file and gold; only where it matches the stored key is the matching content_key written.
Anything that doesn't match (gold edited since, response replaced) is left alone and stays unreusable.
Usage: backfill_content_keys.py [--write]   (dry run by default)
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import judge as J

def response_file(judgment:Path,results:Path)->Path:
 name,arm=judgment.stem.rsplit('.',1)
 dataset,suffix=arm.split('_',1)
 base,_,tag=name.partition('+')
 root=next((results/d/tag for d in ('screen_variants','screen_quants') if tag and (results/d/tag).exists()),results/'screen')
 return root/base/('lines_bare.jsonl' if dataset=='lines' else f'scenes_{suffix}.jsonl')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--dir',type=Path,default=ROOT/'results/judge/sol')
 p.add_argument('--results',type=Path,default=ROOT/'results')
 p.add_argument('--write',action='store_true')
 args=p.parse_args()
 refs={ds:J.gold(ds) for ds in ('lines','scenes')}
 for f in sorted(args.dir.glob('*.jsonl')):
  rows=J.load_jsonl(f);rf=response_file(f,args.results)
  if not rf.exists():print(f'{f.name}: no response file {rf}, skipped');continue
  resp={(r['id'],r.get('run_id',r.get('model'))):r for r in J.load_jsonl(rf) if r.get('translation') and not r.get('error')}
  added=mismatch=0
  for x in rows:
   if 'content_key' in x or 'score' not in x:continue
   r=resp.get((x['id'],x.get('run_id'))); g=refs[x['dataset']].get(x['id'])
   if not r or not g:mismatch+=1;continue
   d=J.make_input(g,r['translation'],x['dataset'],x['mode'],x.get('annotated',False))
   common={'judge':x['model'],'provider':x['provider'],'effort':x.get('effort','medium'),'rubric':x['rubric_version'],'data':d,'mode':x['mode']}
   if J.sha({**common,'source_model':r.get('model'),'run_id':r.get('run_id',r.get('model'))})!=x['key']:mismatch+=1;continue
   x['content_key']=J.sha(common);added+=1
  print(f'{f.name}: {added} keyed, {mismatch} not verifiable')
  if args.write and added:f.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf8')
 if not args.write:print('Dry run; pass --write to save.')

if __name__=='__main__':main()
