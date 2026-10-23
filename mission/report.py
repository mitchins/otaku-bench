#!/usr/bin/env python3
"""Summarise a screen-mission run: latency table + side-by-side skim of full-scene output.

Writes results/screen/REPORT.md and results/screen/SKIM.md. No API calls.
Quality scores come later from tools/judge.py on the per-model JSONL files.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / 'benchmark/otakubench/data/build/scenes_gold.jsonl'


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding='utf8').splitlines() if x.strip()]


def fmt(v, suffix=''):
    return '—' if v is None else f'{v}{suffix}'


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results', type=Path, default=ROOT / 'results/screen')
    p.add_argument('--skim-scenes', default='OTB-P005,OTB-P009,OTB-P013,OTB-P019,OTB-P020,OTB-P023,OTB-P024,OTB-P031')
    args = p.parse_args()

    latest = {}
    for r in load(args.results / 'summary.jsonl'):
        latest[r['run_id']] = r  # last record wins
    rows = sorted(latest.values(), key=lambda r: (r['status'] != 'COMPLETE',
                  (r.get('latency') or {}).get(str(r.get('gate_depth', 6)), {}).get('median_s') or 1e9))

    out = ['# OtakuBench screen mission — run report', '',
           'Latency is full-line wall time on the mission GPU (cold prefill, no cross-request cache reuse). '
           '`d0` = line alone, `d6` = six preceding dialogue lines (gate), `d24` = long history.', '',
           '| # | model | style | GB | VRAM MiB | status | ttft d6 | line d0 | line d6 | line d24 | tok/s | arms |',
           '|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|']
    for r in rows:
        lat = r.get('latency') or {}
        g = str(r.get('gate_depth', 6))
        arms = ' '.join(f"{k.replace('scenes_', 's_').replace('lines_bare', 'L')}={v}" for k, v in (r.get('arms') or {}).items() if v != 'n/a')
        out.append(f"| {r['rank']} | {r['model']} | {r['style']} | {r['size_gb']}{'~' if r.get('size_estimated') else ''} "
                   f"| {fmt(r.get('vram_used_mib_loaded'))} | {r['status']} "
                   f"| {fmt(lat.get(g, {}).get('median_ttft_s'), 's')} | {fmt(lat.get('0', {}).get('median_s'), 's')} "
                   f"| {fmt(lat.get(g, {}).get('median_s'), 's')} | {fmt(lat.get('24', {}).get('median_s'), 's')} "
                   f"| {fmt(lat.get(g, {}).get('median_tok_s'))} | {arms} |")
    deferred = [r for r in rows if r['status'] == 'DEFER_5090']
    if deferred:
        out += ['', '## Deferred to the 5090', ''] + [f"- {r['rank']} {r['model']} — {r.get('reason', '')}" for r in deferred]
    failed = [r for r in rows if r['status'] not in ('COMPLETE', 'DEFER_5090', 'LATENCY_FAIL', 'SKIP_TEMPLATE_UNVERIFIED')]
    if failed:
        out += ['', '## Needs a look', ''] + [f"- {r['rank']} {r['model']} — {r['status']} {r.get('reason', '')}" for r in failed]
    (args.results / 'REPORT.md').write_text('\n'.join(out) + '\n', encoding='utf8')

    gold = {g['id']: g for g in load(GOLD)}
    skim = ['# Skim — full-scene translations side by side', '']
    for sid in [s.strip() for s in args.skim_scenes.split(',') if s.strip()]:
        g = gold.get(sid)
        if not g:
            continue
        skim += [f'## {sid} · {g.get("phenomenon", "")}', '', '```', g['full_japanese'], '```', '',
                 f'Reference:', '', '```', g['full_english_reference'], '```', '']
        for r in rows:
            if r['status'] not in ('COMPLETE', 'PARTIAL'):
                continue
            mdir = args.results / f"{r['rank']:02d}_{re.sub(r'[^A-Za-z0-9._-]+', '_', r['model']).strip('_')}"
            hits = [x for x in load(mdir / 'scenes_full.jsonl') if x['id'] == sid and x.get('run_id') == r['run_id']]
            if hits:
                skim += [f"**{r['model']}** ({fmt(hits[-1].get('seconds'), 's')})", '', '```', hits[-1].get('translation') or f"[{hits[-1].get('error')}]", '```', '']
    (args.results / 'SKIM.md').write_text('\n'.join(skim) + '\n', encoding='utf8')
    print('\n'.join(out))
    print(f"\nwrote {args.results / 'REPORT.md'} and {args.results / 'SKIM.md'}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
