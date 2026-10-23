#!/usr/bin/env python3
"""Run JP-Media-250 through an OpenAI-compatible chat-completions API.

Works with a local server (LM Studio, llama.cpp, vLLM, etc.) exposing /v1/chat/completions.
No third-party dependencies. Results are append-only JSONL and can be resumed.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = (
    "You are a professional Japanese-to-English translator. "
    "Translate the Japanese text into natural, faithful English. "
    "Preserve uncertainty, emotional tone, implied social relationships and ambiguity. "
    "Do not explain your translation. Output only the English translation."
)


def api_call(url, key, payload, timeout, retries):
    raw = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    for attempt in range(retries + 1):
        try:
            req = Request(url, data=raw, headers={
                "Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                method="POST")
            with urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode('utf-8'))
        except (HTTPError, URLError, TimeoutError) as e:
            if attempt == retries:
                raise
            time.sleep(min(2 ** attempt, 5))


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(part.get('text', '') for part in content
                         if isinstance(part, dict) and part.get('type') == 'text')
    return ""


def clean(text):
    # Some reasoning-tuned local models emit visible <think> blocks.
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.S | re.I).strip()
    if text.startswith('"') and text.endswith('"') and text.count('"') == 2:
        text = text[1:-1]
    return text.strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-url', default='http://127.0.0.1:1234/v1')
    p.add_argument('--model', required=True)
    p.add_argument('--api-key', default=os.getenv('OPENAI_API_KEY', 'local'))
    p.add_argument('--mode', choices=['bare', 'context'], default='context')
    p.add_argument('--split', choices=['dev', 'eval', 'all'], default='all')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--limit', type=int, default=0, help='0 for all eligible entries')
    p.add_argument('--temperature', type=float, default=0)
    p.add_argument('--max-tokens', type=int, default=200)
    p.add_argument('--timeout', type=int, default=180)
    p.add_argument('--retries', type=int, default=1)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    filename = 'jpmedia250_blind_with_context.jsonl' if args.mode == 'context' else 'jpmedia250_blind_japanese_only.jsonl'
    path = ROOT / 'data' / 'build' / filename
    cases = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]
    cases = [r for r in cases if args.split == 'all' or r['split'] == args.split]
    if args.limit > 0:
        cases = cases[:args.limit]
    if args.dry_run:
        print(json.dumps({'url': args.base_url.rstrip('/') + '/chat/completions',
                          'model': args.model, 'mode': args.mode,
                          'examples': len(cases), 'sample': cases[0] if cases else None},
                         ensure_ascii=False, indent=2))
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed = set()
    if args.output.exists():
        for line in args.output.read_text(encoding='utf-8').splitlines():
            try:
                row = json.loads(line)
                if row.get('model') == args.model and row.get('mode') == args.mode and row.get('translation'):
                    completed.add(row['id'])
            except json.JSONDecodeError:
                pass
    url = args.base_url.rstrip('/') + '/chat/completions'
    with args.output.open('a', encoding='utf-8') as f:
        for idx, r in enumerate(cases, 1):
            if r['id'] in completed:
                continue
            user = r['japanese']
            if args.mode == 'context':
                user = ('Scene context (for disambiguation, not text to translate): '\
                    + r['scene_context'] + '\n\nJapanese text:\n' + r['japanese'])
            payload = {
                'model': args.model,
                'messages': [{'role':'system','content':SYSTEM}, {'role':'user','content':user}],
                'temperature': args.temperature, 'max_tokens': args.max_tokens,
                'stream': False,
            }
            start = time.perf_counter()
            result = {'id': r['id'], 'model': args.model, 'mode': args.mode,
                      'split': r['split'], 'japanese': r['japanese']}
            try:
                response = api_call(url, args.api_key, payload, args.timeout, args.retries)
                msg = response['choices'][0]['message']
                result['raw_response'] = text_of(msg.get('content'))
                result['translation'] = clean(result['raw_response'])
                result['usage'] = response.get('usage', {})
                if not result['translation']:
                    result['error'] = 'Model returned no visible translation'
            except Exception as e:
                result['error'] = f'{type(e).__name__}: {str(e)}'
            result['seconds'] = round(time.perf_counter() - start, 3)
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
            f.flush()
            print(f"[{idx}/{len(cases)}] {r['id']} {result['seconds']:.2f}s "
                  f"{'ERROR' if result.get('error') else 'OK'}", flush=True)


if __name__ == '__main__':
    main()
