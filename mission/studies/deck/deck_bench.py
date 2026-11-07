#!/usr/bin/env python3
"""Deck latency run: same payloads as the screen latency gate, timed locally (no Wi-Fi in the loop).
usage: python3 deck_bench.py <llama bin dir> <model.gguf> <out.jsonl>"""
import json, os, subprocess, sys, time
from urllib.request import Request, urlopen
B, MODEL, OUT = sys.argv[1:4]
PORT = 8125
env = dict(os.environ, LD_LIBRARY_PATH=B)
cmd = [f'{B}/llama-server', '-m', MODEL, '--host', '127.0.0.1', '--port', str(PORT), '-ngl', '99', '-c', '2048',
       '--parallel', '1', '--jinja', '--reasoning', 'off', '--alias', 'otb']
log = open(OUT + '.server.log', 'w')
proc = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
try:
    for _ in range(300):
        try:
            with urlopen(f'http://127.0.0.1:{PORT}/health', timeout=2) as r:
                if r.status == 200: break
        except Exception: time.sleep(1)
    else: raise SystemExit('server not ready')
    def run(payload):
        req = Request(f'http://127.0.0.1:{PORT}/v1/chat/completions', data=json.dumps(payload, ensure_ascii=False).encode(),
                      headers={'Content-Type': 'application/json'}, method='POST')
        t0 = time.perf_counter(); ttft = None; text = []; fin = tim = None
        with urlopen(req, timeout=120) as resp:
            for raw in resp:
                line = raw.decode('utf-8', 'replace').strip()
                if not line.startswith('data:'): continue
                d = line[5:].strip()
                if d == '[DONE]': break
                try: o = json.loads(d)
                except json.JSONDecodeError: continue
                tim = o.get('timings') or tim
                for ch in o.get('choices') or []:
                    piece = (ch.get('delta') or {}).get('content')
                    if piece:
                        if ttft is None: ttft = time.perf_counter() - t0
                        text.append(piece)
                    fin = ch.get('finish_reason') or fin
        return {'raw': ''.join(text), 'finish': fin, 'seconds': round(time.perf_counter() - t0, 4),
                'ttft_s': round(ttft, 4) if ttft else None, 'timings': tim}
    cases = [json.loads(l) for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cases.jsonl'))]
    run(cases[0]['payload'])  # warm-up (shader compile, first allocation)
    with open(OUT, 'w') as f:
        for c in cases:
            try: r = run(c['payload']); r['error'] = None
            except Exception as e: r = {'error': f'{type(e).__name__}: {e}'}
            r.update(id=c['id'], depth=c['depth']); f.write(json.dumps(r, ensure_ascii=False) + '\n'); f.flush()
finally:
    proc.terminate(); proc.wait(timeout=30)
