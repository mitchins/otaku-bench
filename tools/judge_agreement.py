#!/usr/bin/env python3
"""Judge-vs-judge disagreements for same model arm/case (independent of ranking)."""
from __future__ import annotations
import argparse,json,statistics
from pathlib import Path
from judge import load_jsonl

def index(path):
 return {(x.get('run_id',x.get('candidate_model')),x['id'],x.get('dataset'),x.get('mode')):x for x in load_jsonl(path)
         if x.get('score') and not x.get('annotated')}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--primary',type=Path,required=True);p.add_argument('--secondary',type=Path,required=True)
 p.add_argument('--output',type=Path);p.add_argument('--min-score-delta',type=int,default=3)
 args=p.parse_args();a=index(args.primary);b=index(args.secondary);both=sorted(a.keys()&b.keys())
 differences=[];deltas=[];by_flag={}
 for key in both:
  x=a[key]['score'];y=b[key]['score']
  xscore=sum(x[k] for k in ('adequacy','pragmatics','fluency'))
  yscore=sum(y[k] for k in ('adequacy','pragmatics','fluency'))
  delta=abs(xscore-yscore);deltas.append(delta)
  if delta>=args.min_score_delta or x['gold_uncertain']!=y['gold_uncertain'] or x['refusal']!=y['refusal']:
   differences.append({'run_id':key[0],'id':key[1],'dataset':key[2],'mode':key[3],
           'primary_score':xscore,'secondary_score':yscore,'delta':delta,
           'primary_gold_uncertain':x['gold_uncertain'],'secondary_gold_uncertain':y['gold_uncertain'],
           'primary_reason':x['evidence'],'secondary_reason':y['evidence']})
 report={'paired':len(both),'mean_absolute_score_delta':round(statistics.mean(deltas),3) if deltas else None,
         'within_1_score_point':round(sum(z<=1 for z in deltas)/len(deltas),4) if deltas else None,
         'major_disagreements':len(differences),'cases':differences,
         'interpretation':'Disagreements expose judge uncertainty; neither judge becomes the truth automatically.'}
 print(json.dumps(report,ensure_ascii=False,indent=2))
 if args.output:args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main()
