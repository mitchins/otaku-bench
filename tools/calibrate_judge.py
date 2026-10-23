#!/usr/bin/env python3
"""Blind paired judge-calibration with 24 hand-authored known-error translations.

Tests contrast sensitivity and swapped-order stability; not an independent gold standard.
Use same fixture for both candidate judges before choosing one.
"""
from __future__ import annotations
import argparse,json,sys,time,hashlib
from pathlib import Path
from judge import GOLD,api_request,load_jsonl
ROOT=Path(__file__).resolve().parents[1]
# ID : deliberately wrong but plausible English rendering. The positive arm is editorial gold.
FLAWS={
'JMB-036':'The department head has graciously come back to see you.',
'JMB-047':'If you knew, why did you tell everyone?',
'JMB-053':"That kid is terrible at keeping secrets.",
'JMB-060':"I can't raise my head because the person injured my neck.",
'JMB-066':'That house has such a high doorstep that I cannot get inside.',
'JMB-076':"Today sounds like a very short day.",
'JMB-091':"Let’s wait until every single person arrives before starting.",
'JMB-096':"An excellent plan, and you've already inspected every detail on the ground.",
'JMB-111':"That’s your problem to handle, not mine.",
'JMB-137':"Shouting 'read the room' is a perfect example of reading the room.",
'JMB-141':"It's not that you won't; you physically can't do it.",
'JMB-146':"They announced clear skies tomorrow, and I'd rather believe it will rain.",
'JMB-171':"The arrow pierced his cheek and pinned him to the wall.",
'JMB-172':"His genuine smile immediately put all my doubts to rest.",
'JMB-196':"Whenever someone tells me not to disturb the peace, I agree completely.",
'JMB-199':"The community mailed that house an invitation and everyone agreed it was an accidental omission.",
'JMB-210':"Their voice was steady as they said, 'I hate you.'",
'JMB-224':"I heard the order, and I clearly promised to obey it.",
'JMB-225':"You spoke the words aloud, and I heard them all.",
'JMB-248':"She must have lied to us about every detail.",
'OTB-P006':'【Radio Operator】 "Okay. I’ll tell the Whitefeather Unit to advance."',
'OTB-P020':"【Trooper】 \"I'll shoot him, orders or not.\"",
'OTB-P022':"【Haru】 \"Absolutely. I remember every detail perfectly.\"",
'OTB-P025':'【System】 "Connection restored. All systems operational."',
}
SYS='''Compare two anonymous English translations of Japanese fiction or game text. One is an intentionally flawed translation, one is a baseline translation; the order is hidden. Choose which preserves Japanese meaning, pragmatic force, polarity, speaker identity and style better. A natural nonliteral localization may beat a wooden literal rendering. Return one JSON object {"winner":"A"|"B"|"TIE","confidence":0..1,"explanation":"specific concise difference"}; no markdown, no extra fields. Do not guess based on length or polish alone.'''

def fixtures():
 gs={r['id']:r for r in load_jsonl(GOLD/'lines_gold.jsonl')};gs.update({r['id']:r for r in load_jsonl(GOLD/'scenes_gold.jsonl')})
 tests=[]
 for id_,bad in FLAWS.items():
  g=gs[id_];is_scene=id_.startswith('OTB')
  tests.append({'id':id_,'source':g['target_japanese'] if is_scene else g['japanese'],
      'preceding':g['context_lines'] if is_scene else [],
      'good':g['english_reference'],'bad':bad,'flaw_type':'deliberately wrong translation',
      'source_kind':'scene_target' if is_scene else 'line'})
 return tests

def make_case(row,order):
 # A=good / B=bad on even order; reversed on odd; each pair seen twice
 a,b=(row['good'],row['bad']) if order==0 else (row['bad'],row['good'])
 return {'japanese':row['source'],'preceding_japanese':row['preceding'],
         'translation_A':a,'translation_B':b},('A' if order==0 else 'B')

def parse(txt):
 t=txt.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
 r=json.loads(t)
 if r.get('winner') not in ('A','B','TIE') or not isinstance(r.get('confidence'),(float,int)) or not 0<=r['confidence']<=1:raise ValueError('invalid winner/confidence')
 if not r.get('explanation'):raise ValueError('missing explanation')
 return r

def summarize(rows):
 by={}
 for r in rows:
  if 'response' not in r:continue
  by.setdefault(r['id'],[]).append(r)
 trials=[r for rs in by.values() for r in rs]
 correct=sum(r['response']['winner']==r['expected'] for r in trials)
 both=sum(len(rs)==2 and all(r['response']['winner']==r['expected'] for r in rs) for rs in by.values())
 covered=sum(len(rs)==2 for rs in by.values())
 return {'trials':len(trials),'correct':correct,'accuracy':round(correct/len(trials),4) if trials else None,
         'both_orders_correct':both,'both_orders_seen':covered,'order_stability_rate':round(both/covered,4) if covered else None,
         'gate':(len(trials)==2*len(FLAWS) and correct/len(trials)>=0.90 and both/len(FLAWS)>=0.85) if trials else False}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--provider',choices=['openai','anthropic'],default='openai')
 p.add_argument('--model',default='gpt-6.1-sol')
 p.add_argument('--effort',choices=['low','medium','high'],default='medium')
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--max-output-tokens',type=int,default=1536)
 p.add_argument('--limit',type=int,default=0)
 p.add_argument('--execute',action='store_true')
 args=p.parse_args()
 rows=fixtures();work=[]
 for row in rows:
  for order in (0,1):
   q,expected=make_case(row,order)
   work.append((row['id'],order,q,expected))
 if args.limit:work=work[:args.limit]
 done={}
 if args.output.exists():
  for r in load_jsonl(args.output):
   if r.get('judge')==args.model and 'response' in r:done[(r['id'],r['order'])]=r
 todo=[q for q in work if (q[0],q[1]) not in done]
 print(json.dumps({'model':args.model,'pairs':len(rows),'swapped_trials':len(work),'pending':len(todo),'execute':args.execute},indent=2))
 if not args.execute:
  print(json.dumps(todo[0][2],ensure_ascii=False,indent=2) if todo else 'Completed');return 0
 args.output.parent.mkdir(parents=True,exist_ok=True)
 with args.output.open('a',encoding='utf8') as f:
  for id_,order,q,expected in todo:
   result={'id':id_,'order':order,'expected':expected,'judge':args.model,'provider':args.provider,'v':'blind_calibration_v1'}
   try:
    text,usage,cost,finish=api_request(args.provider,args.model,SYS,q,args.max_output_tokens,args.effort,120)
    result.update(response=parse(text),usage=usage,cost=cost)
   except Exception as e:result['error']=f'{type(e).__name__}: {str(e)[:200]}'
   f.write(json.dumps(result,ensure_ascii=False)+'\n');f.flush()
   print(id_,order,'OK' if 'response' in result else result['error'])
 report=summarize([r for r in load_jsonl(args.output) if r.get('judge')==args.model])
 print(json.dumps(report,indent=2))
 return 0 if report['gate'] else 2
if __name__=='__main__':raise SystemExit(main())
