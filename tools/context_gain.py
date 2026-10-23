#!/usr/bin/env python3
"""Compare a model's bare vs preceding-dialogue scene translations on matched IDs.

This is a SECONDARY diagnostic. A context increase is meaningful only with
valid gold and judges; with 6 dev/25 eval scenes, report wide CIs, not ranks.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from judge import GOLD,load_jsonl,sha
from paired_stats import paired_delta

def index(paths,mode,judge,split,refs,run_id=None):
    runs={}
    for path in paths:
        for r in load_jsonl(path):
            if (r.get('dataset')!='scenes' or r.get('mode')!=mode or
                r.get('model')!=judge or r.get('annotated') or 'score' not in r):continue
            if r['id'] not in refs or refs[r['id']]['split']!=split:continue
            if r.get('gold_sha256')!=sha(refs[r['id']]):continue
            arm=r.get('run_id',r.get('candidate_model'))
            if run_id and arm!=run_id:continue
            if r['score'].get('gold_uncertain'):continue
            runs.setdefault(arm,{})[r['id']]=sum(r['score'][z] for z in ('adequacy','pragmatics','fluency'))
    return runs

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bare',type=Path,action='append',required=True)
    p.add_argument('--context',type=Path,action='append',required=True)
    p.add_argument('--judge-model',default='gpt-6.1-sol')
    p.add_argument('--split',choices=['dev','eval'],default='eval')
    p.add_argument('--run-id')
    p.add_argument('--bootstrap-reps',type=int,default=4000)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    refs={r['id']:r for r in load_jsonl(GOLD/'scenes_gold.jsonl')}
    bare=index(a.bare,'bare',a.judge_model,a.split,refs,a.run_id)
    ctx=index(a.context,'context',a.judge_model,a.split,refs,a.run_id)
    shared=sorted(set(bare)&set(ctx))
    if not shared:p.error('No matching run_id/current-gold judged arms in both modes')
    expected={i for i,r in refs.items() if r['split']==a.split}
    comparisons=[]
    for run_id in shared:
        result=paired_delta(ctx[run_id],bare[run_id],expected,reps=a.bootstrap_reps)
        result.update(run_id=run_id,delta_interpretation='context minus bare; positive means context helps')
        result['coverage']=round(result['shared_items']/len(expected),4)
        result['status']='DIAGNOSTIC_ONLY_NOT_RANKABLE'
        comparisons.append(result)
    report={'benchmark':'OtakuBench v4','metric':'paired same-case context benefit /10','split':a.split,
            'judge':a.judge_model,'expected_cases':len(expected),'comparisons':comparisons,
            'warning':'25 eval and 6 dev scenes have inadequate power for definitive conclusions; positive intervals are exploratory.'}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if a.out:a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
