#!/usr/bin/env python3
"""Bilingual AI audit of provisional references, not a human-reviewed gold certification.

Run with two independent judge providers; do not use authored trap notes as clues.
"""
from __future__ import annotations
import argparse,hashlib,json,sys,time
from pathlib import Path
from judge import GOLD,RUBRIC_VERSION,api_request,load_jsonl,sha

SYSTEM='''You are a critical bilingual Japanese-English literary localization editor, auditing a draft benchmark.
Check JAPANESE first: naturalness, uchi/soto and honorific consistency, ambiguous grammar, omitted subjects, plausible character voice. Check the given reference: accuracy, no invented gender/referents, retained nuance, no misplaced sentiment, no stylistic flattening that invalidates the item's intended test. Do not assume draft reference is correct. For lines with no actual prior utterances, missing context must be treated as missing; do not take author notes as source context. For scenes, use only source preceding dialogue. Distinguish firm error, ambiguous reading and subjective preference. Reply with one JSON object containing EXACTLY keys:
{"japanese_natural":true,"reference_acceptable":true,"source_ambiguity":false,"severity":"none|minor|material|invalid","issues":["concrete, checkable issues"],"suggested_english":"English alternative if change needed, else empty string","confidence":0.8,"rationale":"concise explanation tied to Japanese grammar and social context"}
Return pure valid JSON, no Markdown.'''

def parse(txt):
 s=txt.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip();x=json.loads(s)
 if set(x)!={'japanese_natural','reference_acceptable','source_ambiguity','severity','issues','suggested_english','confidence','rationale'}:raise ValueError('invalid keys')
 if any(type(x[z])!=bool for z in ('japanese_natural','reference_acceptable','source_ambiguity')):raise ValueError('invalid bools')
 if x['severity'] not in ('none','minor','material','invalid'):raise ValueError('invalid severity')
 if not isinstance(x['issues'],list) or not isinstance(x['suggested_english'],str):raise ValueError('invalid issues/reference')
 if not isinstance(x['confidence'],(int,float)) or not 0<=x['confidence']<=1:raise ValueError('invalid confidence')
 if not isinstance(x['rationale'],str) or not x['rationale']:raise ValueError('missing rationale')
 return x

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--dataset',choices=['lines','scenes','both'],default='both')
 p.add_argument('--provider',choices=['openai','anthropic'],default='openai')
 p.add_argument('--model',default='gpt-6.1-sol')
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--budget-usd',type=float,default=10.)
 p.add_argument('--limit',type=int,default=0)
 p.add_argument('--effort',choices=['low','medium','high'],default='medium')
 p.add_argument('--max-output-tokens',type=int,default=4096)
 p.add_argument('--execute',action='store_true')
 args=p.parse_args()
 ds=['lines','scenes'] if args.dataset=='both' else [args.dataset]
 tasks=[]
 for dataset in ds:
  for r in load_jsonl(GOLD/('lines_gold.jsonl' if dataset=='lines' else 'scenes_gold.jsonl')):
   d={'source_japanese':r['japanese'] if dataset=='lines' else r['full_japanese'],
      'draft_reference_english':r['english_reference'] if dataset=='lines' else r['full_english_reference']}
   if dataset=='lines':d['alternate_references']=r.get('alternate_references',[])
   elif r.get('hook_artifacts'):d['source_extraction_policy']='Duplicate UI line(s) and midword wraps are deliberate hook artifacts; judge normalized reference, preserve intentional stammers.'
   tasks.append((dataset,r['id'],d))
 if args.limit:tasks=tasks[:args.limit]
 prior={}
 if args.output.exists():
  for rec in load_jsonl(args.output):
   if rec.get('model')==args.model and 'finding' in rec:prior[rec.get('key')]=rec
 to_run=[]
 for dataset,id_,d in tasks:
  key=sha({'v':'gold_audit_v1','id':id_,'data':d,'judge':args.model,'effort':args.effort})
  if key not in prior:to_run.append((dataset,id_,d,key))
 print(json.dumps({'model':args.model,'total':len(tasks),'remaining':len(to_run),'execute':args.execute,'budget_usd':args.budget_usd}))
 if not args.execute:
  print(json.dumps(to_run[0][2],ensure_ascii=False) if to_run else '(none)');return 0
 args.output.parent.mkdir(exist_ok=True,parents=True)
 spent=0
 with args.output.open('a',encoding='utf8') as f:
  for dataset,id_,d,key in to_run:
   if spent>=args.budget_usd:
    print('budget exhausted',file=sys.stderr);break
   rec={'key':key,'gold_sha256':sha(next(x for x in load_jsonl(GOLD/('lines_gold.jsonl' if dataset=='lines' else 'scenes_gold.jsonl')) if x['id']==id_)),'dataset':dataset,'id':id_,'model':args.model,'provider':args.provider}
   for attempt in range(2):
    try:
     raw,usage,cost,finish=api_request(args.provider,args.model,SYSTEM,d,args.max_output_tokens,args.effort,180)
     rec.update(finding=parse(raw),usage=usage,cost=cost)
     spent+=cost.get('estimated_standard_usd_excluding_cache_write') or 0
     break
    except Exception as e:
     rec['error']=str(e)[:220]
     if attempt==0:time.sleep(1)
   f.write(json.dumps(rec,ensure_ascii=False)+'\n');f.flush()
   print(dataset,id_,'OK' if 'finding' in rec else 'ERROR',round(spent,4),flush=True)
 print('Neither model certifies gold as fact. Compare both independent findings and retain disputed references as invalid pending resolution.')
 return 0
if __name__=='__main__':raise SystemExit(main())
