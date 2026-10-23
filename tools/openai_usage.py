#!/usr/bin/env python3
"""Today's (UTC) usage of the shared data-sharing token pool, from the OpenAI organisation Usage API.

Only this script reads OPENAI_ADMIN_API_KEY; the judge never sees it.

  python tools/openai_usage.py            # report
  python tools/openai_usage.py --remaining   # print only the tokens OtakuBench may still spend today

remaining = pool - margin - ours - max(reserve, others)
  ours   = pool-model usage on OtakuBench's key (OTB_OPENAI_KEY_ID)
  others = pool-model usage on every other key; the reserve keeps room for them even when they're idle,
           because the judge queue runs at 00:20 UTC, before other tools have used anything.
A request that crosses the allowance is billed in full, hence the margin.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
# models that draw on the Build plan's 250K/day data-sharing group (prefix match); gpt-6-luna has its own pool
POOL_MODELS = ('gpt-6.1-sol', 'gpt-5.5')


def load_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return dict(l.strip().split('=', 1) for l in path.read_text().splitlines() if '=' in l and not l.lstrip().startswith('#'))


def usage_today(admin_key: str) -> list[dict]:
    day0 = int(time.time()) // 86400 * 86400
    url = (f'https://api.openai.com/v1/organization/usage/completions?start_time={day0}'
           '&bucket_width=1d&group_by=api_key_id,model&limit=1')
    req = Request(url, headers={'Authorization': 'Bearer ' + admin_key})
    with urlopen(req, timeout=30) as r:
        data = json.load(r)['data']
    return [x for b in data for x in b['results']]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--pool', type=int, default=250_000)
    p.add_argument('--margin', type=int, default=5_000)
    p.add_argument('--reserve', type=int, default=20_000, help='room kept for other keys (EasyDict etc.)')
    p.add_argument('--remaining', action='store_true', help='print only the number OtakuBench may still spend')
    args = p.parse_args()

    env = {**load_env(ROOT / '.env'), **os.environ}
    admin, ours_id = env.get('OPENAI_ADMIN_API_KEY'), env.get('OTB_OPENAI_KEY_ID')
    if not admin or not ours_id:
        print('OPENAI_ADMIN_API_KEY and OTB_OPENAI_KEY_ID must be set in .env', file=sys.stderr)
        return 2
    ours = others = 0
    for r in usage_today(admin):
        if not r['model'].startswith(POOL_MODELS):
            continue
        tok = r['input_tokens'] + r['output_tokens']
        if r['api_key_id'] == ours_id:
            ours += tok
        else:
            others += tok
    remaining = max(0, args.pool - args.margin - ours - max(args.reserve, others))
    if args.remaining:
        print(remaining)
        return 0
    reset = 86400 - int(time.time()) % 86400
    print(f"""OtakuBench — data-sharing pool ({', '.join(POOL_MODELS)})
─────────────────────────────────
Daily pool:      {args.pool:>10,}
OtakuBench:      {ours:>10,}
Other keys:      {others:>10,}   (reserved {max(args.reserve, others):,})
Margin:          {args.margin:>10,}
─────────────────────────────────
Safe remaining:  {remaining:>10,}
Reset in:        {reset // 3600}h {reset % 3600 // 60}m (00:00 UTC)""")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
