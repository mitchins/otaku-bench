#!/usr/bin/env python3
"""Read-only post-hoc OtakuBench scoring diagnostics; never changes gold or judgments.

Uses the existing GPT judge's integer adequacy (0..4), pragmatics (0..4),
and fluency (0..2) axes. All alternatives are exploratory, not the
published primary metric. Partial model runs are explicitly marked.

Usage:
    python mission/score_sensitivity.py
    python mission/score_sensitivity.py results/judge/sol/*.lines_eval.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / 'benchmark/otakubench/data/build/lines_gold.jsonl'
JUDGMENTS = ROOT / 'results/judge/sol'


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def gold_digest(gold: dict) -> str:
    """Mirror tools/judge.py's canonical gold hash."""
    payload = json.dumps(gold, ensure_ascii=False, sort_keys=True).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def axes(s: dict) -> tuple[int, int, int]:
    a, p, f = s['adequacy'], s['pragmatics'], s['fluency']
    assert type(a) is int and 0 <= a <= 4, f'invalid adequacy: {a!r}'
    assert type(p) is int and 0 <= p <= 4, f'invalid pragmatics: {p!r}'
    assert type(f) is int and 0 <= f <= 2, f'invalid fluency: {f!r}'
    return a, p, f


def raw_score(s: dict) -> float:
    return sum(axes(s))


def gated_nuance(s: dict) -> float:
    """Exploratory: adequacy gates total; nuance dominates fluency 80:20.

    a=3 caps at 7.5, a=2 caps at 5.0; no tuning to a desired model score.
    """
    a, p, f = axes(s)
    return 10.0 * (a / 4.0) * (0.8 * (p / 4.0) + 0.2 * (f / 2.0))


def records_for(path: Path, refs: dict[str, dict]) -> tuple[dict[str, dict], int, int]:
    """Last valid record for each current-gold item; reject stale IDs or hashes."""
    out = {}
    stale = 0
    errors = 0
    for row in read_jsonl(path):
        item_id = row.get('id')
        if item_id not in refs:
            stale += 1
            continue
        if row.get('gold_sha256') != gold_digest(refs[item_id]):
            stale += 1
            continue
        if row.get('dataset') != 'lines' or row.get('mode') != 'bare':
            stale += 1
            continue
        if 'score' not in row:
            errors += 1
            continue
        axes(row['score'])
        out[item_id] = row
    return out, stale, errors


def summarize(path: Path, refs: dict[str, dict]) -> dict:
    by_id, stale, errors = records_for(path, refs)
    scores = [r['score'] for r in by_id.values()]
    n = len(scores)
    expected = len(refs)
    hist = Counter(int(raw_score(s)) for s in scores)
    return {
        'model': path.name.removesuffix('.lines_eval.jsonl'),
        'status': 'COMPLETE' if n == expected else 'PARTIAL',
        'scored': n,
        'expected': expected,
        'raw': mean(raw_score(s) for s in scores) if n else None,
        'gated': mean(gated_nuance(s) for s in scores) if n else None,
        'adequacy': mean(axes(s)[0] for s in scores) if n else None,
        'pragmatics': mean(axes(s)[1] for s in scores) if n else None,
        'fluency': mean(axes(s)[2] for s in scores) if n else None,
        'perfect': hist[10],
        'nine': hist[9],
        'subnine': sum(v for k, v in hist.items() if k < 9),
        'major': sum(1 for s in scores if s['adequacy'] <= 2 or s.get('refusal') is True),
        'gold_uncertain': sum(bool(s.get('gold_uncertain')) for s in scores),
        'stale_rejected': stale,
        'judge_errors': errors,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('paths', type=Path, nargs='*', help='*.lines_eval.jsonl; defaults to results/judge/sol')
    ap.add_argument('--gold', type=Path, default=GOLD)
    ap.add_argument('--only-complete', action='store_true')
    ap.add_argument('--json', action='store_true', help='Machine-readable summary instead of table')
    args = ap.parse_args()
    refs = {g['id']: g for g in read_jsonl(args.gold) if g.get('split') == 'eval'}
    if not refs:
        ap.error('No eval gold records available (unlock encrypted data if necessary)')
    paths = args.paths or sorted(JUDGMENTS.glob('*.lines_eval.jsonl'))
    data = [summarize(p, refs) for p in paths]
    if args.only_complete:
        data = [r for r in data if r['status'] == 'COMPLETE']
    if args.json:
        print(json.dumps({'note': 'Exploratory, not calibrated or published; partial means cover observed judgments only',
                          'scores': data}, indent=2))
        return 0
    print('Scores are MEANS OVER OBSERVED JUDGMENTS; PARTIAL rows are NOT rankings.')
    print('Gated = 10*(adequacy/4)*(0.8*pragmatics/4 + 0.2*fluency/2). No raw data changed.\n')
    print(f"{'Model':37} {'State':9} {'N':>7} {'Raw':>6} {'Gated':>6} {'A/4':>5} {'P/4':>5} {'F/2':>5} {'10s':>4} {'9s':>4} {'<9':>4} {'Major':>5} {'Stale':>5}")
    for r in data:
        fmt = lambda v: f'{v:.2f}' if v is not None else '—'
        print(f"{r['model'][:37]:37} {r['status']:9} {r['scored']:>3}/{r['expected']:<3} "
              f"{fmt(r['raw']):>6} {fmt(r['gated']):>6} {fmt(r['adequacy']):>5} "
              f"{fmt(r['pragmatics']):>5} {fmt(r['fluency']):>5} "
              f"{r['perfect']:>4} {r['nine']:>4} {r['subnine']:>4} {r['major']:>5} {r['stale_rejected']:>5}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
