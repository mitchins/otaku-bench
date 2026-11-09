#!/usr/bin/env python3
"""Hard v0.5 pilot: does it spread the field? Compares hard05 with the board's hard (v0.4) on the same models.
Pass = every check on the turn passes and the screen-output contract holds (as the board's hard). Paired bootstrap
between neighbours on the same turns. usage: python mission/studies/hard05_spread.py"""
import io, contextlib, json, random, sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'mission')); sys.path.insert(0, str(ROOT / 'tools'))
import judge_table as jt, judge_slice as js, mechanical as mech
MODELS = ['C04_Gemini-3.8-Flash', 'C03_Claude-Sonnet-5.5', '02_Gemma_4_31B_IT', '05_Gemma_4_26B-A4B_IT', '01_Qwen3.8-27B',
          '08_Gemma_4_12B_IT', '41_Gemma_4_E4B_IT', '42_Gemma_4_E2B_IT', '65_Hy-MT2-1.8B']
def per_turn(slice_, name):
    """id -> (pass, checks dict) for turns judged against the current gold and response; None if incomplete."""
    base, _, tag = name.partition('+')
    resp = ROOT / 'results/screen_slices' / (f'{tag}/' if tag else '') / base / f'{slice_}_turns.jsonl'
    gold = {g['id']: g for g in jt.load(js.SLICES[slice_]['gold']) if g['is_scored_target']}
    if not resp.is_file(): return None
    chosen = js.pick_responses(jt.load(resp), gold)
    out = {}
    for x in jt.load(ROOT / 'results/judge/slices' / slice_ / f'{name}.jsonl'):
        g, r = gold.get(x['id']), chosen.get(x['id'])
        if g and r and x.get('outcome') not in (None, 'judge_error') and x.get('run_id') == r.get('run_id') \
                and x.get('turn_sha256') == g['turn_sha256'] and x.get('gold_sha256') == js.sha(js.make_input(slice_, g)):
            ok = x['outcome'] == 'judged' and not x.get('judge_flagged_refusal') and all(v == 'pass' for v in (x.get('checks') or {}).values())
            ok = ok and not mech.contract_violation(g['current_japanese'], r.get('translation') or '')
            out[x['id']] = (ok, x.get('checks') or {}, g)
    return out if len(out) == len(gold) else None
def boot(a, b, ids, reps=4000, seed=7):
    rnd = random.Random(seed); ids = list(ids); d = []
    for _ in range(reps):
        s = [rnd.choice(ids) for _ in ids]; d.append(sum(a[i][0] - b[i][0] for i in s) / len(s) * 100)
    d.sort(); return round(d[int(.025 * reps)], 1), round(d[int(.975 * reps)], 1)
res = {}
for m in MODELS:
    v5 = per_turn('hard05', m); v4 = per_turn('hard', m)
    res[m] = (v5, v4)
print(f"{'model':38s}{'v0.5 pass':>10}{'checks':>8}{'v0.4 pass':>10}")
for m, (v5, v4) in res.items():
    p5 = f"{100 * sum(t[0] for t in v5.values()) / len(v5):.1f}" if v5 else 'pending'
    ck = (f"{100 * sum(v == 'pass' for t in v5.values() for v in t[1].values()) / sum(len(t[1]) for t in v5.values()):.1f}" if v5 else '')
    p4 = f"{100 * sum(t[0] for t in v4.values()) / len(v4):.1f}" if v4 else '—'
    print(f"{m:38s}{p5:>10}{ck:>8}{p4:>10}")
done = [m for m in MODELS if res[m][0]]
done.sort(key=lambda m: -sum(t[0] for t in res[m][0].values()))
print('\nneighbours on v0.5 (paired 95% CI of the pass-rate gap, points):')
for a, b in zip(done, done[1:]):
    A, B = res[a][0], res[b][0]; print(f"  {a} - {b}: {boot(A, B, A)}")
    if res[a][1] and res[b][1]: print(f"      same pair on v0.4: {boot(res[a][1], res[b][1], res[a][1])}")
if done:
    ids = list(res[done[0]][0])
    allp = sum(all(res[m][0][i][0] for m in done) for i in ids); nonep = sum(not any(res[m][0][i][0] for m in done) for i in ids)
    print(f"\nturns all {len(done)} models pass: {allp}/{len(ids)}; none pass: {nonep}; discriminating: {len(ids) - allp - nonep}")
    part = defaultdict(lambda: [0, 0])
    for m in done:
        for i, t in res[m][0].items():
            k = t[2]['selection']; part[(m, k)][0] += t[0]; part[(m, k)][1] += 1
    print('by part (retained / new):')
    for m in done: print(f"  {m:38s} retained {part[(m, 'v05_retained')][0]}/{part[(m, 'v05_retained')][1]}  new {part[(m, 'v05_new')][0]}/{part[(m, 'v05_new')][1]}")
    hyp = defaultdict(lambda: [0, 0])
    for m in done:
        for i, t in res[m][0].items(): hyp[t[2]['hypothesis']][0] += t[0]; hyp[t[2]['hypothesis']][1] += 1
    print('by hypothesis (all judged models pooled):', {h: f"{100 * a / b:.0f}%" for h, (a, b) in sorted(hyp.items(), key=lambda x: int(x[0][1:]))})
