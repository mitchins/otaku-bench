#!/usr/bin/env python3
"""Bounded Flint adapter/sampling study (2026-10-24).

Flint 40B-A2.5B has no thinking-off switch. Under the empty-think prefill it got 250/250 lines but 82/93
scene items: 11 requests reasoned in the visible reply until the 256-token cap. This study re-runs those
11 plus 10 controls that succeeded, under these arms:

  A  empty-think prefill, greedy, cap 256         (reproduce)
  B  rendered-prompt check of the prefill          (is the workaround malformed? printed, not scored)
  C  empty-think prefill, publisher sampling ×3    (temp 1.0 / top-p 0.95 / top-k 20; is greedy the cause?)
  D  thinking on, --reasoning-budget 64 / 128      (does a short think recover completion?)
  E  empty-think prefill, greedy, cap 512          (are they just long?)
  F  thinking on, unlimited, publisher sampling    (natural behaviour, for reference)

Records success, reasoning size, wall time and finish per request. No paid judging; the latency gate still
applies to any configuration taken forward.
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'mission'))
import screen_mission as sm  # noqa: E402

OUT = ROOT / 'results/studies/flint_adapter'
FAILED = ROOT / 'results/screen_variants/empty-think/51_Flint_40B-A2.5B'
PUBLISHER = {'temperature': 1.0, 'top_p': 0.95, 'top_k': 20}
PREFILL = '<think>\n</think>\n\n'
PORT = 8131


def cases() -> list[dict]:
    """The 11 failed scene requests plus 10 successful controls (5 canary lines, 5 scene items)."""
    out, ok_scenes = [], []
    for mode in ('bare', 'context', 'full'):
        src = {c['id']: c for c in sm.load_jsonl(sm.DATA / f'scenes_{mode}.jsonl')}
        for r in sm.load_jsonl(FAILED / f'scenes_{mode}.jsonl'):
            (out if r['error'] else ok_scenes).append({**src[r['id']], '_dataset': 'scenes', '_mode': mode, '_was': 'failed' if r['error'] else 'ok'})
    controls = [c for c in ok_scenes if c['_mode'] == 'context'][:2] + [c for c in ok_scenes if c['_mode'] == 'full'][:2] + [c for c in ok_scenes if c['_mode'] == 'bare'][:1]
    lines = sm.load_jsonl(sm.DATA / 'lines_bare.jsonl')
    controls += [{**lines[i], '_dataset': 'lines', '_mode': 'bare', '_was': 'ok'} for i in sm.CANARY_INDICES]
    return out + controls


def server(gguf: str, extra: list[str]) -> subprocess.Popen:
    cmd = [os.environ.get('LLAMA_SERVER', 'llama-server'), '-m', gguf, '--host', '127.0.0.1', '--port', str(PORT),
           '-ngl', '99', '-c', '4096', '--parallel', '1', '--jinja', *extra]
    env = dict(os.environ, CUDA_DEVICE_ORDER='PCI_BUS_ID', CUDA_VISIBLE_DEVICES='0')
    log = (OUT / f"server_{'_'.join(x.strip('-') for x in extra) or 'default'}.log").open('w')
    p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
    if not sm.wait_ready(p, PORT, 300):
        sm.stop(p)
        raise SystemExit(f'server failed to start: {extra}')
    return p


def request(case: dict, prefill: bool, sampling: dict | None, max_tokens: int, seed: int) -> dict:
    sm.VARIANT.clear()
    if prefill:
        sm.VARIANT['prefill'] = PREFILL
    payload, completions = sm.build_payload(case, 'chat', case['_dataset'], case['_mode'])
    payload['max_tokens'] = max_tokens
    payload['seed'] = seed
    payload.update(sampling or {'temperature': 0})
    if not prefill:
        payload.pop('chat_template_kwargs', None)  # let the model decide; Flint ignores enable_thinking anyway
    res = sm.stream_once(f'http://127.0.0.1:{PORT}/v1', payload, completions, timeout=120)
    text = (res['raw'] or '').strip()
    return {'id': case['id'], 'mode': case['_mode'], 'was': case['_was'], 'ok': bool(text) and res['finish'] != 'length',
            'finish': res['finish'], 'seconds': res['seconds'], 'ttft_s': res['ttft_s'],
            'reasoning_chars': len(res['reasoning'] or ''), 'visible_chars': len(text),
            'tokens': (res['timings'] or {}).get('predicted_n'), 'text': text[:400]}


def render_check(cs: list[dict]) -> None:
    """Arm B: what llama-server actually renders for the prefill, versus no prefill."""
    for prefill in (False, True):
        sm.VARIANT.clear()
        if prefill:
            sm.VARIANT['prefill'] = PREFILL
        payload, _ = sm.build_payload(cs[0], 'chat', cs[0]['_dataset'], cs[0]['_mode'])
        req = Request(f'http://127.0.0.1:{PORT}/apply-template', data=json.dumps({'messages': payload['messages']}).encode(),
                      headers={'Content-Type': 'application/json'}, method='POST')
        prompt = json.load(urlopen(req, timeout=30))['prompt']
        print(f"\n--- B: rendered prompt tail, prefill={prefill} ({prompt.count('<|assistant|>')} assistant headers)\n{prompt[-160:]!r}")
        (OUT / f'render_prefill_{prefill}.txt').write_text(prompt, encoding='utf8')


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    row = next(r for r in json.loads((ROOT / 'data/attested.json').read_text())['models'] if r['rank'] == 51)
    from huggingface_hub import hf_hub_download
    gguf = hf_hub_download(row['quant_repo'], row['quant_file'], revision=row['model_repo_sha'])
    cs = cases()
    print(f'{len(cs)} cases: {sum(c["_was"] == "failed" for c in cs)} previously failed, {sum(c["_was"] == "ok" for c in cs)} controls')
    plan = [  # (arm, server flags, prefill, sampling, max_tokens, seeds)
        ('A greedy+prefill 256', ['--reasoning', 'off'], True, None, 256, [0]),
        ('C publisher+prefill 256', ['--reasoning', 'off'], True, PUBLISHER, 256, [1, 2, 3]),
        ('E greedy+prefill 512', ['--reasoning', 'off'], True, None, 512, [0]),
        ('D budget 64', ['--reasoning', 'on', '--reasoning-budget', '64'], False, PUBLISHER, 64 + 256, [1]),
        ('D budget 128', ['--reasoning', 'on', '--reasoning-budget', '128'], False, PUBLISHER, 128 + 256, [1]),
        ('F natural thinking', ['--reasoning', 'on'], False, PUBLISHER, 1536, [1]),
    ]
    results = []
    current, proc = None, None
    try:
        for arm, flags, prefill, sampling, cap, seeds in plan:
            if flags != current:
                sm.stop(proc)
                proc, current = server(gguf, flags), flags
                if arm.startswith('A'):
                    render_check(cs)
            for seed in seeds:
                for c in cs:
                    r = request(c, prefill, sampling, cap, seed)
                    r.update(arm=arm, seed=seed)
                    results.append(r)
                    sm.append_jsonl(OUT / 'results.jsonl', r)
            rs = [r for r in results if r['arm'] == arm]
            secs = [r['seconds'] for r in rs if r['ok']]
            fixed = sum(r['ok'] for r in rs if r['was'] == 'failed')
            print(f"{arm:26} failed→ok {fixed}/{sum(r['was'] == 'failed' for r in rs)}  controls ok {sum(r['ok'] for r in rs if r['was'] == 'ok')}/{sum(r['was'] == 'ok' for r in rs)}"
                  f"  median {statistics.median(secs) if secs else 0:.2f}s  p90 {sm.pct(secs, .9) or 0:.2f}s  reasoning {statistics.median(r['reasoning_chars'] for r in rs):.0f} ch", flush=True)
    finally:
        sm.stop(proc)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
