#!/usr/bin/env python3
"""Export the public dev split (50 lines, 6 scenes) with gold from the git-crypted build files.

The eval split never leaves the encrypted files. Output: benchmark/otakubench/data/public/.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'benchmark/otakubench/data/build'
OUT = ROOT / 'benchmark/otakubench/data/public'
DROP = {'translation_note'}  # trap notes stay private even for dev: they are the judge's second-pass hints


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ('lines_gold', 'scenes_gold'):
        src = BUILD / f'{name}.jsonl'
        head = src.read_bytes()[:10]
        if head.startswith(b'\x00GITCRYPT'):
            raise SystemExit(f'{src} is still encrypted: run `git-crypt unlock <key>` first')
        rows = [json.loads(x) for x in src.read_text(encoding='utf8').splitlines() if x.strip()]
        dev = [{k: v for k, v in r.items() if k not in DROP} for r in rows if r['split'] == 'dev']
        (OUT / f'{name}_dev.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in dev), encoding='utf8')
        print(f'{name}: {len(dev)} dev rows')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
