"""Case-matched comparison; avoid independent per-model CI overlap fallacy."""
from __future__ import annotations
import random, statistics

def paired_delta(rows_a, rows_b, expected, excluded=frozenset(), reps=4000, seed=20261023):
    """Same cases, same judge; delta A-B, item-resampled bootstrap, two-sided tail area.

    95% intervals are exploratory (no correction for multiple comparisons or judge bias).
    """
    common=sorted((set(rows_a)&set(rows_b)&set(expected))-set(excluded))
    n=len(common)
    if n<2:return {'shared_items':n,'comparable':False,'reason':'fewer than two shared scores'}
    diffs=[rows_a[i]-rows_b[i] for i in common]
    obs=statistics.mean(diffs)
    rng=random.Random(seed)
    boot=sorted(sum(diffs[rng.randrange(n)] for _ in range(n))/n for _ in range(reps))
    ci=[round(boot[int(reps*.025)],4),round(boot[min(reps-1,int(reps*.975))],4)]
    tail_less=sum(x<=0 for x in boot)/reps
    tail_more=sum(x>=0 for x in boot)/reps
    return {'shared_items':n,'comparable':True,'mean_delta_a_minus_b':round(obs,4),
            'paired_bootstrap_95_ci':ci,'win_rate_a':round(sum(x>0 for x in diffs)/n,4),
            'tie_rate':round(sum(x==0 for x in diffs)/n,4),
            'bootstrap_probability_a_better':round(sum(x>0 for x in boot)/reps,4),
            'descriptive_two_sided_tail_fraction':round(min(1,2*min(tail_less,tail_more)),4),
            'interval_excludes_zero':ci[0]>0 or ci[1]<0,
            'statistical_warning':'Exploratory unadjusted item-bootstrap, not an independent judge reliability or expert-quality guarantee.'}
