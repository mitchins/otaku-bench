#!/usr/bin/env python3
"""Auditable OtakuBench scoreboard. No ranking without passing paired judge calibration.

Compare only the same dataset/mode/split. Easy probes remain sanity checks rather
than dominating translation-quality rankings. Deduplicate by run_id, stable case ID.
"""
from __future__ import annotations
import argparse, json, math, random, statistics, re
from collections import Counter, defaultdict
from pathlib import Path
from judge import GOLD,load_jsonl
from calibrate_judge import summarize
from paired_stats import paired_delta
from judge import sha

def get_gold(dataset,split):
    name='lines_gold.jsonl' if dataset=='lines' else 'scenes_gold.jsonl'
    return {x['id']:x for x in load_jsonl(GOLD/name) if split=='all' or x['split']==split}

def ci(values,replicates=1000,seed=20261023):
    if not values:return None
    rand=random.Random(seed);n=len(values)
    if n<2:return [values[0],values[0]]
    means=sorted(sum(values[rand.randrange(n)] for _ in range(n))/n for _ in range(replicates))
    return [round(means[int(replicates*.025)],3),round(means[min(replicates-1,int(replicates*.975))],3)]

def summarize_one(rows,expected,refs,excluded,inferences,min_coverage):
    by_id={r['id']:r for r in rows if r['id'] in expected and r['id'] not in excluded}
    counted=[r for r in by_id.values() if 'score' in r and not r['score'].get('gold_uncertain')]
    n=len(counted);denom=len(expected-excluded)
    coverage=n/denom if denom else 0
    scores=[r['score']['adequacy']+r['score']['pragmatics']+r['score']['fluency'] for r in counted]
    timings=[inferences[r['id']]['seconds'] for r in counted if r['id'] in inferences and isinstance(inferences[r['id']].get('seconds'),(int,float))]
    hist=defaultdict(list)
    for r in counted:
        g=refs[r['id']];bucket=(g['primary_challenge'] if 'primary_challenge' in g else g['phenomenon'])
        hist[bucket].append(r['score']['adequacy']+r['score']['pragmatics']+r['score']['fluency'])
    cost=sum((r.get('cost') or {}).get('estimated_standard_usd_excluding_cache_write') or 0 for r in rows)
    flags=Counter(f for r in counted for f in r['score'].get('flags',[]))
    return {'n_scored':n,'n_expected':denom,'coverage':round(coverage,4),'rankable_coverage':coverage>=min_coverage,
            'mean_10':round(statistics.mean(scores),3) if scores else None,
            'bootstrap_95_ci_10':ci(scores),
            'median_seconds_per_case':round(statistics.median(timings),3) if timings else None,
            'refusals':sum(r['score'].get('refusal',False) for r in counted),
            'flags':dict(flags.most_common()),
            'challenge_mean_10':{k:round(statistics.mean(v),3) for k,v in sorted(hist.items())},
            'judge_cost_estimated_standard_usd':round(cost,4),
            'gold_uncertain_in_candidate':sum(r.get('score',{}).get('gold_uncertain',False) for r in rows)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--judgments',type=Path,action='append',required=True)
    p.add_argument('--inferences',type=Path,action='append',default=[])
    p.add_argument('--calibration',type=Path,help='Paired known-error calibration for selected judge model')
    p.add_argument('--gold-audits',type=Path,action='append',default=[],help='Gold-reference audits from two independent judges; required for publishable draft ranking')
    p.add_argument('--judge-model',default='gpt-6.1-sol')
    p.add_argument('--dataset',choices=['lines','scenes'],required=True)
    p.add_argument('--mode',choices=['bare','context','full'],default='bare')
    p.add_argument('--split',choices=['all','dev','eval'],default='eval')
    p.add_argument('--min-coverage',type=float,default=.95)
    p.add_argument('--output',type=Path)
    p.add_argument('--bootstrap-reps',type=int,default=2000,help='Paired bootstrap replicates per model pair (default 2000)')
    p.add_argument('--compare-pairs',choices=['adjacent','all'],default='adjacent',help='Default bounded paired comparisons on neighboring scored arms; --compare-pairs all computes O(models²) pairs')
    args=p.parse_args()
    if args.dataset=='lines' and args.mode!='bare':p.error('lines support bare mode only')
    if not 0<args.min_coverage<=1:p.error('min coverage must be 0..1')
    refs=get_gold(args.dataset,args.split)
    judgments=[r for path in args.judgments for r in load_jsonl(path)
               if r.get('model')==args.judge_model and r.get('dataset')==args.dataset and r.get('mode')==args.mode
               and not r.get('annotated') and r.get('id') in refs
               and r.get('gold_sha256')==sha(refs[r['id']])]
    run_rows=defaultdict(dict)
    for r in judgments:
        if 'score' not in r:continue
        run_rows[r.get('run_id',r.get('candidate_model','unknown'))][r['id']]=r
    # Gold quarantine is dataset-wide ONLY when both independent gold auditors
    # judge an item material/invalid; one arbitrary model-level gold_uncertain flag
    # must NEVER contaminate the 49 other model arms.
    expected={id_ for id_,g in refs.items() if args.dataset=='scenes' or g['difficulty']>=2}
    sanity={id_ for id_,g in refs.items() if args.dataset=='lines' and g['difficulty']==1}
    audit_rows=[r for path in args.gold_audits for r in load_jsonl(path)
                if r.get('dataset')==args.dataset and r.get('id') in refs and r.get('finding')
                and r.get('gold_sha256')==sha(refs[r['id']])]
    # A "second auditor" must be independent at the PROVIDER level, not just
    # an alternative model/configuration from the same provider. The source
    # file records provider and model; legacy/missing provider cannot count.
    audited={}
    for r in audit_rows:
        provider=r.get('provider')
        if provider in ('openai','anthropic'):
            audited[(r['id'],provider,r.get('model'))]=r['finding']
    auditors=sorted({f'{provider}/{model}' for _,provider,model in audited if model})
    providers=sorted({provider for _,provider,_ in audited})
    covered={id_:set() for id_ in expected}
    for id_,provider,_ in audited:
        if id_ in covered:covered[id_].add(provider)
    double_reviewed={id_ for id_,ms in covered.items() if len(ms)>=2}
    flagged=defaultdict(set)
    for (id_,provider,_),finding in audited.items():
        if finding.get('severity') in ('material','invalid'):flagged[id_].add(provider)
    global_bad={id_ for id_ in expected if len(flagged[id_])>=2}
    conflicts=sorted(id_ for id_ in expected if id_ not in global_bad and flagged[id_])
    gold_gate=len(providers)>=2 and all(id_ in double_reviewed for id_ in expected) and not conflicts
    gold_audit_status={'auditors':auditors,'independent_providers':providers,
                       'two_independent_audits_for':len(double_reviewed),
                       'required_items':len(expected),'gate':gold_gate,
                       'quarantined_by_two_auditors':len(global_bad),
                       'unresolved_material_conflicts':conflicts,
                       'warning':'Global exclusions require two DIFFERENT audit providers (OpenAI and Anthropic), not two models from one provider. Missing-provider audits cannot qualify. A one-provider conflict blocks publication until resolved.'}
    inferences=defaultdict(dict)
    for path in args.inferences:
        for r in load_jsonl(path):
            if r.get('dataset')==args.dataset and r.get('mode')==args.mode:
                inferences[r.get('run_id',r.get('model','unknown'))][r['id']]=r
    calibration={'gate':False,'reason':'No completed judge calibration provided'}
    if args.calibration:
        cal=[r for r in load_jsonl(args.calibration) if r.get('judge')==args.judge_model]
        calibration=summarize(cal)
    # Publication needs enough independent cases; 25 evaluation scenes are
    # diagnostics, not a real-world VN ranking, even with perfect judge coverage.
    min_publishable_items=100 if args.dataset=='lines' else 60
    groups=[]
    scoremaps={}
    for arm,by in sorted(run_rows.items()):
        result=summarize_one(list(by.values()),expected,refs,global_bad,inferences.get(arm,{}),args.min_coverage)
        scoremaps[arm]={id_:(r['score']['adequacy']+r['score']['pragmatics']+r['score']['fluency'])
                        for id_,r in by.items() if id_ in expected-global_bad and 'score' in r and not r['score'].get('gold_uncertain')}
        proof_items=[r for r in by.values() if r['id'] in expected-global_bad and 'score' in r and not r['score'].get('gold_uncertain')]
        proof_good=bool(proof_items) and all(
            r.get('quant_attested') is True and r.get('canary_passed') is True and
            isinstance(r.get('quant_repo_sha'),str) and
            re.fullmatch('[0-9a-fA-F]{40,64}',r['quant_repo_sha'])
            for r in proof_items)
        result['attested_canary_provenance']=proof_good
        if sanity:result['difficulty_1_sanity']=summarize_one(list(by.values()),sanity,refs,global_bad,inferences.get(arm,{}),0)
        result.update(run_id=arm,judge=args.judge_model,dataset=args.dataset,mode=args.mode,split=args.split)
        result['publishable_rank']=bool(gold_gate and calibration.get('gate') and result['rankable_coverage']
                                      and result['n_scored']>=min_publishable_items and result['attested_canary_provenance'] and bool(expected-global_bad))
        groups.append(result)
    eligible=sorted((x for x in groups if x['publishable_rank']),key=lambda x:-x['mean_10'])
    for idx,row in enumerate(eligible,1):row['rank']=idx
    paired=[]
    # Bound pairwise statistics by default: at 50 candidates, 1,225 all-vs-all
    # pairs × thousands of bootstrap rounds is wasteful for first-pilot triage.
    # Order arms by their observed scores, then compare only neighboring ranks;
    # full pairwise analysis remains an opt-in for finished experiments.
    sorted_arms=[x['run_id'] for x in sorted(groups,key=lambda x:(x['mean_10'] is None,-(x['mean_10'] or 0),x['run_id']))]
    if args.compare_pairs=='all':
        pair_ids=[(a,b) for i,a in enumerate(sorted_arms) for b in sorted_arms[i+1:]]
    else:
        pair_ids=list(zip(sorted_arms,sorted_arms[1:]))
    for a,b in pair_ids:
            sa,sb=scoremaps[a],scoremaps[b]
            comparison=paired_delta(sa,sb,expected,global_bad,args.bootstrap_reps)
            comparison.update(run_id_a=a,run_id_b=b)
            comparison['coverage_of_expected_valid']=round(comparison['shared_items']/max(1,len(expected-global_bad)),4)
            comparison['ranking_qualified']=bool(gold_gate and calibration.get('gate') and
              comparison['coverage_of_expected_valid']>=.90 and
              all(x['publishable_rank'] for x in groups if x['run_id'] in (a,b)))
            paired.append(comparison)
    report={'benchmark':'OtakuBench v4 editorial draft','dataset':args.dataset,'mode':args.mode,'split':args.split,
            'judge_model':args.judge_model,'judge_calibration':calibration,'gold_audit':gold_audit_status,
            'min_scored_items_for_publishable_rank':min_publishable_items,
            'global_gold_uncertain_excluded':sorted(global_bad),
            'candidate_gold_uncertain_only_affects_its_own_run':True,
            'pairwise_comparisons':paired,'compare_pairs_mode':args.compare_pairs,
            'primary_metric':'mean /10 on difficulty 2-5 for lines, all scenes otherwise; easy lines reported separately',
            'rank_status':'AI_AUDITED_CALIBRATED_DRAFT_LEADERBOARD' if eligible else 'NO_PUBLISHABLE_RANKING_PENDING_JUDGE_GOLD_OR_CASE_COUNT',
            'confidence_limits':'Paired item-bootstrap estimates same-case model differences; unadjusted for multiple testing and blind to judge bias or reference quality.',
            'results':sorted(groups,key=lambda x:(not x['publishable_rank'],-(x['mean_10'] or -1),x['run_id']))}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return 0
if __name__=='__main__':raise SystemExit(main())
