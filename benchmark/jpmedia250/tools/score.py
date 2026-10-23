#!/usr/bin/env python3
"""Report reference-based character n-gram overlap as a weak diagnostic, not semantic accuracy.

Produces an editable expert review CSV. For idioms, variants, omissions and pragmatics,
use the manual rubric in RUBRIC.md; overlap is NOT a credible overall proficiency score.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalized(s):
    return ''.join(ch for ch in unicodedata.normalize('NFKC', s).casefold()
                   if ch.isalnum() or ch.isspace()).split()


def ngrams(s, n):
    chars = ' '.join(normalized(s))
    return Counter(chars[i:i+n] for i in range(max(len(chars)-n+1, 0)))


def chrf_lite(hyp, ref):
    """Unweighted F2 mean across character n-grams 1..6, NOT official sacreBLEU chrF."""
    scores = []
    for n in range(1, 7):
        h, r = ngrams(hyp, n), ngrams(ref, n)
        overlap = sum((h & r).values())
        precision = overlap/sum(h.values()) if h else 0
        recall = overlap/sum(r.values()) if r else 0
        scores.append(5 * precision*recall/(4*precision+recall) if precision+recall else 0)
    return 100 * sum(scores) / len(scores)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('responses', type=Path, help='JSONL from run_api.py')
    p.add_argument('--out', type=Path, default=Path('review_queue.csv'))
    args = p.parse_args()
    gold = {r['id']:r for r in (json.loads(l) for l in
            (ROOT/'data/build/jpmedia250_gold.jsonl').read_text(encoding='utf-8').splitlines())}
    observations = {}
    for line in args.responses.read_text(encoding='utf-8').splitlines():
        r = json.loads(line)
        if r.get('id') in gold and r.get('translation'):
            observations[r['id']] = r # most recent completed attempt for each id
    rows = []
    for id_, result in observations.items():
        ref = gold[id_]
        alt = [ref['english_reference'], *ref['alternate_references']]
        score = max(chrf_lite(result['translation'], a) for a in alt)
        rows.append({
            'id': id_, 'medium': ref['medium'], 'difficulty':ref['difficulty'],
            'challenge':ref['primary_challenge'], 'japanese':ref['japanese'],
            'context':ref['scene_context'], 'reference':ref['english_reference'],
            'alternatives':' || '.join(ref['alternate_references']),
            'candidate':result['translation'], 'chrf_lite_0_100':round(score, 2),
            'accuracy_0_4':'', 'pragmatics_0_4':'', 'fluency_0_2':'',
            'critical_error_flags':'', 'reviewer_notes':'',
            'translation_note':ref['translation_note']})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fields = ['id','medium','difficulty','challenge','japanese','context','reference',
              'alternatives','candidate','chrf_lite_0_100','accuracy_0_4',
              'pragmatics_0_4','fluency_0_2','critical_error_flags','reviewer_notes',
              'translation_note']
    with args.out.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r:r['id']))
    print(f"Scored {len(rows)}/{len(gold)} cases; wrote {args.out}")
    if not rows:
        return
    print(f"Mean chrF-lite: {sum(r['chrf_lite_0_100'] for r in rows)/len(rows):.2f} "
          "(lexical overlap ONLY; do not call this translation quality)")
    for key in ['difficulty','medium','challenge']:
        groups = defaultdict(list)
        for row in rows:
            groups[row[key]].append(row['chrf_lite_0_100'])
        print(key + ': ' + ', '.join(f'{k}: {sum(v)/len(v):.1f} (n={len(v)})' for k,v in sorted(groups.items())))


if __name__=='__main__':
    main()
