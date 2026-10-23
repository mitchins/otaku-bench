#!/usr/bin/env python3
"""Prepare a bounded, reproducible second-judge disagreement/uncertainty queue.

The output uses the SAME inference records as judge.py. All source gold is loaded by
stable ID; no human review required. A secondary judge is not absolute ground truth.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from judge import load_jsonl

def priority(score):
    flags=set(score.get('flags',[]))
    points=(5 if score.get('gold_uncertain') else 0)+(4 if score.get('refusal') else 0)
    points+=(3 if score.get('confidence',1)<.65 else 2 if score.get('confidence',1)<.8 else 0)
    points+=min(2,len(flags & {'AMBIGUITY','KEIGO','VOICE','IMPL','AGENT','NEG','IDIOM','CULT'}))
    points+=(2 if 4<=score.get('adequacy',0)+score.get('pragmatics',0)+score.get('fluency',0)<=8 else 0)
    return points

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--judgments',type=Path,required=True)
    p.add_argument('--inferences',type=Path,required=True)
    p.add_argument('--judge-model',default='gpt-6.1-sol')
    p.add_argument('--max-cases',type=int,default=250)
    p.add_argument('--min-priority',type=int,default=3)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.max_cases<1:p.error('max-cases must be >=1')
    scores={(r.get('run_id',r.get('candidate_model')),r.get('id')):r['score'] for r in load_jsonl(args.judgments)
             if r.get('model')==args.judge_model and 'score' in r and not r.get('annotated')}
    candidates=[]
    for r in load_jsonl(args.inferences):
        key=r.get('run_id',r.get('model')),r.get('id')
        score=scores.get(key)
        if score and r.get('translation') and not r.get('error'):
            pts=priority(score)
            if pts>=args.min_priority:candidates.append((pts,key,r))
    candidates.sort(key=lambda x:(-x[0],x[1]))
    dedup={}
    for pts,key,row in candidates:
        dedup.setdefault(key,row)
    rows=list(dedup.values())[:args.max_cases]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf8')
    print(json.dumps({'selected':len(rows),'input_judgments':len(scores),
                     'next':'judge.py --provider anthropic --model claude-opus-5-5 --responses '+str(args.output)+' [matching dataset/mode] --output secondary.jsonl --execute'}))
    return 0
if __name__=='__main__':raise SystemExit(main())
