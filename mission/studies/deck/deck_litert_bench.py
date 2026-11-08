#!/usr/bin/env python3
"""Deck latency client for an already-running OpenAI-compatible server (LiteRT-LM serve): same 60 cases, warm-up,
streaming TTFT and wall time as deck_bench.py (llama.cpp). usage: deck_litert_bench.py <base url> <model id> <out.jsonl> [n]"""
import json, sys, time
from urllib.request import Request, urlopen
BASE, MODEL, OUT = sys.argv[1:4]; N = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9
cases = [json.loads(l) for l in open('/home/deck/otakubench-deck/cases.jsonl')][:N]
def run(payload, stream=True):
    p = dict(payload, model=MODEL, stream=stream); p.pop('cache_prompt', None)
    req = Request(BASE + '/chat/completions', data=json.dumps(p, ensure_ascii=False).encode(), headers={'Content-Type': 'application/json'})
    t0 = time.perf_counter(); ttft = None; text = []; fin = None; usage = None
    with urlopen(req, timeout=300) as resp:
        if not stream:
            o = json.load(resp); return {'raw': o['choices'][0]['message'].get('content') or '', 'finish': o['choices'][0].get('finish_reason'),
                                         'seconds': round(time.perf_counter() - t0, 4), 'ttft_s': None, 'usage': o.get('usage')}
        for raw in resp:
            line = raw.decode('utf-8', 'replace').strip()
            if not line.startswith('data:'): continue
            d = line[5:].strip()
            if d == '[DONE]': break
            try: o = json.loads(d)
            except json.JSONDecodeError: continue
            usage = o.get('usage') or usage
            for ch in o.get('choices') or []:
                piece = (ch.get('delta') or {}).get('content')
                if piece:
                    if ttft is None: ttft = time.perf_counter() - t0
                    text.append(piece)
                fin = ch.get('finish_reason') or fin
    return {'raw': ''.join(text), 'finish': fin, 'seconds': round(time.perf_counter() - t0, 4), 'ttft_s': round(ttft, 4) if ttft else None, 'usage': usage}
stream = True
try: w = run(cases[0]['payload'])
except Exception as e: print('stream failed, falling back:', e); stream = False; w = run(cases[0]['payload'], False)
print('warm-up:', w['seconds'], 's', repr(w['raw'][:120]), flush=True)
with open(OUT, 'w') as f:
    for c in cases:
        try: r = run(c['payload'], stream); r['error'] = None
        except Exception as e: r = {'error': repr(e)}
        r.update(id=c['id'], depth=c['depth']); f.write(json.dumps(r, ensure_ascii=False) + '\n'); f.flush()
rs = [json.loads(l) for l in open(OUT)]; ok = [r for r in rs if not r.get('error')]
import statistics as st
for d in sorted({r['depth'] for r in ok}):
    s = sorted(r['seconds'] for r in ok if r['depth'] == d); print(f'depth {d}: n={len(s)} p50={st.median(s):.2f}s max={s[-1]:.2f}s')
print('all p50', round(st.median(r['seconds'] for r in ok), 3), 'errors', len(rs) - len(ok))
