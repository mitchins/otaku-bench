#!/usr/bin/env python3
"""Comparison table of judged models -> results/judge/RANKING.md.

Means are over the whole arm: items the model failed to produce (cap hit, errors) score 0, so a model
can't rank higher by dropping hard lines. Latency/VRAM come from the mission summaries.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'results'
JUDGE = RES / 'judge/sol'
GOLD = ROOT / 'benchmark/otakubench/data/build'
ARMS = {'scenes_full': ('scenes_gold.jsonl', None), 'lines_eval': ('lines_gold.jsonl', 'eval')}


def load(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()] if p.exists() else []


def arm_ids(gold_file: str, split: str | None) -> set[str]:
    return {g['id'] for g in load(GOLD / gold_file) if split is None or g['split'] == split}


def summaries() -> dict[str, dict]:
    out = {}
    for p in [RES / 'screen/summary.jsonl', *RES.glob('screen_variants/*/summary.jsonl')]:
        variant = p.parent.name if p.parent.parent.name == 'screen_variants' else ''
        for r in load(p):
            out[f"{r['rank']:02d}" + (f'+{variant}' if variant else '')] = r
    return out


def main() -> int:
    summ = summaries()
    rows = []
    names = sorted({p.name[:-len('.jsonl')].rsplit('.', 1)[0] for p in JUDGE.glob('*.jsonl')})  # model names contain dots
    for name in names:
        row = {'name': name}
        flags = Counter()
        for arm, (gf, split) in ARMS.items():
            want = arm_ids(gf, split)
            scored = {j['id']: j['score'] for j in load(JUDGE / f'{name}.{arm}.jsonl') if 'score' in j}
            if not scored:
                row[arm] = None
                continue
            total = sum(s['adequacy'] + s['pragmatics'] + s['fluency'] for i, s in scored.items() if i in want)
            row[arm] = (total / len(want), len(scored.keys() & want), len(want))
            row[arm + '_low'] = sum(1 for i, s in scored.items() if i in want and s['adequacy'] + s['pragmatics'] + s['fluency'] <= 5)
            flags.update(f for s in scored.values() for f in s['flags'])
        variant = name.partition('+')[2]
        s = summ.get(name.partition('_')[0] + (f'+{variant}' if variant else ''), {})
        row['lat'] = ((s.get('latency') or {}).get(str(s.get('gate_depth', 6))) or {}).get('median_s')
        row['vram'] = s.get('vram_used_mib_loaded')
        row['flags'] = ', '.join(f'{f}×{n}' for f, n in flags.most_common(3))
        rows.append(row)

    def key(r):  # complete lines arm first, then lines mean
        la = r.get('lines_eval')
        return (-(la[1] == la[2]) if la else 1, -(la[0] if la else 0))

    rows.sort(key=key)
    fmt = lambda a: '—' if not a else (f'{a[0]:.2f}' + ('' if a[1] == a[2] else f' ({a[1]}/{a[2]} judged)'))
    out = ['# OtakuBench screen ranking (gpt-6.1-sol judge)', '',
           'Score /10 = adequacy 0–4 + pragmatics 0–4 + fluency 0–2. Missing items count as 0. '
           'Latency = median full line at 6 lines of history, RTX 3090. Partially judged rows are still in the queue.', '',
           '| model | lines (200 eval) | ≤5 | full scenes (31) | ≤5 | line s | VRAM MiB | top flags |',
           '|---|---:|---:|---:|---:|---:|---:|---|']
    for r in rows:
        out.append(f"| {r['name']} | {fmt(r.get('lines_eval'))} | {r.get('lines_eval_low', '—')} | {fmt(r.get('scenes_full'))} "
                   f"| {r.get('scenes_full_low', '—')} | {r['lat'] or '—'} | {r['vram'] or '—'} | {r['flags']} |")
    (RES / 'judge/RANKING.md').write_text('\n'.join(out) + '\n', encoding='utf8')
    print('\n'.join(out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
