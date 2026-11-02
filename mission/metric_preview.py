#!/usr/bin/env python3
"""Read-only proposal for OtakuBench's primary quality metric.

Use existing rubric axes, saved raw inferences, and frozen mechanical policy;
never regenerate translations, judge calls, scores, or ranking artifacts.

    python mission/metric_preview.py
    python mission/metric_preview.py --json

A full-fidelity pass means adequate meaning (4/4), preserved pragmatics
(4/4), and readable English (>=1/2). A screen-ready pass additionally
requires no detected commentary. Format warnings are reported separately.
Only finished 200-item eval arms are comparable; incomplete models have
no score. Rule A is the board's Standard Pass % (mission/judge_table.py, Preview);
this script adds diagnostics and paired comparisons.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import mechanical as mech  # type: ignore  # noqa: E402

GOLD = ROOT / 'benchmark/otakubench/data/build/lines_gold.jsonl'
BLIND = ROOT / 'benchmark/otakubench/data/build/lines_bare.jsonl'
JUDGE = ROOT / 'results/judge/sol'
RESPONSES = ROOT / 'results'


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]


def sha(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def response_dir(name: str, root: Path = RESPONSES) -> Path | None:
    """Same naming convention as mission/judge_table.py."""
    base, _, variant = name.partition('+')
    candidates = ([root / 'screen' / base] if not variant else
                  [root / 'screen_variants' / variant / base,
                   root / 'screen_quants' / variant / base])
    return next((p for p in candidates if p.is_dir()), None)


def axes(s: dict) -> tuple[int, int, int]:
    a, p, f = (s['adequacy'], s['pragmatics'], s['fluency'])
    if (type(a) is not int or not 0 <= a <= 4 or
        type(p) is not int or not 0 <= p <= 4 or
        type(f) is not int or not 0 <= f <= 2):
        raise ValueError(f'Invalid judge score: {a!r}, {p!r}, {f!r}')
    return a, p, f


def assess_case(gold: dict, blind: dict, response: dict | None,
                judgment: dict | None, source_hash: str | None = None) -> dict:
    """Classify one case, including pending vs. deterministic zero."""
    base = {'id': gold['id'], 'category': gold['primary_challenge'],
            'status': 'pending', 'raw': None, 'pass': False, 'polished': False, 'fidelity': False,
            'meaning_full': False, 'nuance_full_given_meaning': False,
            'minor': False, 'consequential': False, 'flags': [],
            'gold_uncertain': False, 'zero_reason': None}
    if response is None:
        base['status'] = 'not_run'
        return base
    if source_hash is not None and response.get('source_sha256') != source_hash:
        base['status'] = 'stale_inference'
        return base
    reason = mech.zero_reason(blind['japanese'], response.get('translation'), response.get('error'))
    if reason:
        base.update(status='mechanical_zero', raw=0, consequential=True,
                    zero_reason=reason)
        return base
    flags = mech.flags(blind['japanese'], response['translation'])
    base['flags'] = flags
    if judgment is None or 'score' not in judgment or judgment.get('gold_sha256') != sha(gold):
        base['status'] = 'pending_judge'
        return base
    s = judgment['score']
    a, p, f = axes(s)
    fidelity = (a == 4 and p == 4 and f >= 1)
    screen_ready = fidelity and 'commentary' not in flags
    polished = screen_ready and f == 2
    minor = (not screen_ready and 'commentary' not in flags and
             a >= 3 and p >= 3 and f >= 1)
    consequential = (a <= 2 or p <= 2 or f == 0)
    base.update(status='judged', raw=a+p+f, pass_=screen_ready, polished=polished,
                fidelity=fidelity, meaning_full=a == 4,
                nuance_full_given_meaning=a == 4 and p == 4,
                minor=minor, consequential=consequential,
                gold_uncertain=bool(s.get('gold_uncertain')))
    base['pass'] = base.pop('pass_')
    return base


def percentile_ci(xs: list[float], *, seed: int = 20261024,
                  reps: int = 3000) -> list[float] | None:
    if not xs:
        return None
    rng = random.Random(seed)
    n = len(xs)
    sims = sorted(sum(xs[rng.randrange(n)] for _ in range(n))/n
                  for _ in range(reps))
    return [round(100*sims[int(.025*reps)], 1),
            round(100*sims[min(reps-1, int(.975*reps))], 1)]


def stratified_ci(rows: list[dict], *, reps: int = 3000, seed: int = 20261024) -> list[float] | None:
    """Resample items within their fixed challenge categories, not across categories."""
    cats = defaultdict(list)
    for row in rows:
        cats[row['category']].append(float(row['pass']))
    if not cats:
        return None
    rng = random.Random(seed)
    keys = sorted(cats)
    sims = []
    for _ in range(reps):
        category_rates = [sum(values[rng.randrange(len(values))] for _ in values)/len(values)
                          for k in keys for values in [cats[k]]]
        sims.append(sum(category_rates)/len(keys))
    sims.sort()
    return [round(100*sims[int(.025*reps)], 1),
            round(100*sims[min(reps-1, int(.975*reps))], 1)]


def summarize(name: str, judgments: list[dict], responses: list[dict],
              gold: dict[str, dict], blind: dict[str, dict],
              source_hash: str | None, *, include_cases: bool = False) -> dict:
    jr = {r['id']: r for r in judgments if r.get('id') in gold and 'score' in r
          and r.get('model') == 'gpt-6.1-sol' and not r.get('annotated')}
    rr = {r['id']: r for r in responses if r.get('id') in gold}
    cases = [assess_case(g, blind[i], rr.get(i), jr.get(i), source_hash)
             for i, g in sorted(gold.items())]
    ready = [c for c in cases if c['raw'] is not None]
    complete = len(ready) == len(gold)
    raw_avg = statistics.mean(c['raw'] for c in ready) if ready else None
    flags = Counter(flag for c in cases for flag in c['flags'])
    statuses = Counter(c['status'] for c in cases)
    zeroes = Counter(c['zero_reason'] for c in cases if c['zero_reason'])
    full = sum(c['fidelity'] for c in ready)
    polished = sum(c['polished'] for c in ready)
    pass_count = sum(c['pass'] for c in ready)
    adequate = sum(c['meaning_full'] for c in ready)
    a_and_p = sum(c['nuance_full_given_meaning'] for c in ready)
    missing = len(gold)-len(ready)
    bycat = {}
    for cat in sorted({g['primary_challenge'] for g in gold.values()}):
        sub = [c for c in cases if c['category']==cat]
        bycat[cat] = {'total': len(sub), 'decided': sum(c['raw'] is not None for c in sub),
                      'screen_ready': sum(c['pass'] for c in sub),
                      'minor_or_acceptable': sum(c['minor'] for c in sub),
                      'significant_or_output_fault': sum(c['raw'] is not None and
                                                        not (c['pass'] or c['minor']) for c in sub)}
    result = {'model': name,
              'status': 'COMPLETE' if complete else 'INCOMPLETE',
              'decided': len(ready), 'total': len(gold),
              'pending': missing, 'statuses': dict(statuses),
              'raw_mean_10': round(raw_avg, 3) if raw_avg is not None else None,
              'loss_points_per_100': round(100*(10-raw_avg), 1) if raw_avg is not None else None,
              'fidelity_pass_count': full, 'screen_ready_pass_count': pass_count,
              'polished_screen_ready_count': polished,
              'polished_screen_ready_pct': round(100*polished/len(gold), 1) if complete else None,
              'screen_ready_pct': round(100*pass_count/len(gold), 1) if complete else None,
              'screen_ready_95_ci': stratified_ci(ready) if complete else None,
              'meaning_4_of_4_pct': round(100*adequate/len(gold), 1) if complete else None,
              'nuance_4_of_4_given_meaning_pct': round(100*a_and_p/adequate, 1) if adequate else None,
              'consequential_cases': sum(c['consequential'] for c in ready),
              'output_fault_cases': zeroes.total()+flags['commentary'],
              'mechanical_zeros': dict(zeroes), 'flags': dict(flags),
              'gold_uncertain_cases': sum(c['gold_uncertain'] for c in ready),
              'categories': bycat}
    if include_cases:
        result["_private_cases"] = {c["id"]: c for c in cases}
    return result


def paired_pass_delta(a: dict, b: dict, *, reps: int = 3000, seed: int = 20261024) -> dict:
    """Matched-item bootstrap; ties stay ties. Not an LLM preference judgment."""
    ca, cb = a["_private_cases"], b["_private_cases"]
    shared = sorted(set(ca) & set(cb))
    deltas_by_cat = defaultdict(list)
    for item_id in shared:
        left, right = ca[item_id], cb[item_id]
        if left["raw"] is not None and right["raw"] is not None:
            deltas_by_cat[left["category"]].append(int(left["pass"]) - int(right["pass"]))
    vals = [v for cat in deltas_by_cat.values() for v in cat]
    if not vals:
        return {"a":a["model"], "b":b["model"], "n":0, "delta_pp":None, "ci_95_pp":None}
    wins, losses, ties = vals.count(1), vals.count(-1), vals.count(0)
    rng = random.Random(seed)
    sims = []
    for _ in range(reps):
        percat = [sum(arr[rng.randrange(len(arr))] for _ in arr)/len(arr)
                  for cat in sorted(deltas_by_cat) for arr in [deltas_by_cat[cat]]]
        sims.append(100 * sum(percat)/len(percat))
    sims.sort()
    return {"a":a["model"], "b":b["model"], "n":len(vals),
            "a_only_passes":wins, "b_only_passes":losses, "ties":ties,
            "delta_pp":round(100*sum(vals)/len(vals), 1),
            "ci_95_pp":[round(sims[int(.025*reps)],1), round(sims[min(reps-1,int(.975*reps))],1)]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--json', action='store_true')
    p.add_argument('--paired-top', type=int, default=5,
                   help='Compare the top N COMPLETE models on identical line IDs (0 disables)')
    p.add_argument('--include-partial', action='store_true',
                   help='Show diagnostic progress without providing incomplete-model scores')
    p.add_argument('--judge-dir', type=Path, default=JUDGE)
    p.add_argument('--response-root', type=Path, default=RESPONSES)
    p.add_argument('--gold', type=Path, default=GOLD)
    p.add_argument('--blind', type=Path, default=BLIND)
    args = p.parse_args()
    gold = {g['id']:g for g in read_jsonl(args.gold) if g.get('split')=='eval'}
    blind = {r['id']:r for r in read_jsonl(args.blind)}
    if not gold or any(i not in blind for i in gold):
        p.error('Need valid unlocked 200-line eval gold and matching blind source')
    source_hash = hashlib.sha256(args.blind.read_bytes()).hexdigest()
    results = []
    for f in sorted(args.judge_dir.glob('*.lines_eval.jsonl')):
        name = f.name.removesuffix('.lines_eval.jsonl')
        d = response_dir(name, args.response_root)
        results.append(summarize(name, read_jsonl(f),
                                 read_jsonl(d/'lines_bare.jsonl') if d else [],
                                 gold, blind, source_hash, include_cases=True))
    if not args.include_partial:
        results = [r for r in results if r['status']=='COMPLETE']
    results.sort(key=lambda r: (r['status']!='COMPLETE',
                                -(r['screen_ready_pct'] or 0), r['model']))
    eligible = [r for r in results if r['status']=='COMPLETE'][:max(0,args.paired_top)]
    pairs = [paired_pass_delta(a,b) for i,a in enumerate(eligible) for b in eligible[i+1:]]
    for row in results:
        row.pop('_private_cases', None)
    if args.json:
        print(json.dumps({'status': 'PROPOSED_METRIC_NOT_PUBLISHED',
                          'criterion': 'A=4 AND P=4 AND F>=1 AND no detected commentary; polished requires F=2',
                          'note':'Unchanged 0-10 rubric. Complete arms only have rates.',
                          'models': results, 'paired_pass_deltas': pairs}, ensure_ascii=False, indent=2))
        return 0
    print('OtakuBench Standard Pass % diagnostics (the board uses rule A below)')
    print('Full-fidelity screen-ready = meaning 4/4 AND nuance 4/4 AND fluency >=1/2 AND no commentary.')
    print('Flags never modify the underlying GPT-6.1 Sol judgment. Missing judgments are NOT automatic zeros.\n')
    print(f"{'Model':35} {'Cases':>8} {'Raw':>6} {'Ready %':>8} {'CI 95%':>15} {'Loss/100':>9} {'Major':>6} {'Output':>7}")
    for r in results:
        rdy = f"{r['screen_ready_pct']:.1f}" if r['screen_ready_pct'] is not None else 'pending'
        ci = ','.join(map(str,r['screen_ready_95_ci'])) if r['screen_ready_95_ci'] else '—'
        print(f"{r['model'][:35]:35} {r['decided']:>3}/{r['total']:<3} {r['raw_mean_10']:>6.2f} {rdy:>8} {ci:>15} "
              f"{r['loss_points_per_100']:>9.1f} {r['consequential_cases']:>6} {r['output_fault_cases']:>7}")
    if pairs:
        print('\nMatched-case full-fidelity pass differences (pp, bootstrap 95% CI).')
        for pair in pairs:
            print(f"{pair['a']} vs {pair['b']}: {pair['delta_pp']:+.1f} pp "
                  f"CI {pair['ci_95_pp']}, "
                  f"exclusive passes {pair['a_only_passes']}:{pair['b_only_passes']}, "
                  f"ties {pair['ties']}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
