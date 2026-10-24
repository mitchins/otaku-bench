#!/usr/bin/env python3
"""v4.0.1: drop alternate references that were attached to the wrong line (positional-attachment bug).

Idempotent; edits the source items only. Run benchmark/otakubench/tools/build.py afterwards.
Judgments of these items carry the old gold_sha256, so they read as pending until re-judged.
"""
import json
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / 'benchmark/otakubench/data/items/lines.jsonl'
MISATTACHED = ['JMB-041', 'JMB-048', 'JMB-069', 'JMB-241']  # each carried another line's translation

rows = [json.loads(x) for x in SRC.read_text(encoding='utf8').splitlines() if x.strip()]
n = 0
for r in rows:
    if r['id'] in MISATTACHED and r['alternate_references']:
        r['alternate_references'] = []
        r['benchmark_version'] = '4.0.1-editorial-draft'
        n += 1
SRC.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf8')
print(f'cleared misattached alternates on {n} item(s)')
