#!/usr/bin/env python3
"""Same 60 cases through the LiteRT-LM Python API with one engine kept loaded (how a Decky plugin would embed it).
usage: deck_litert_api.py <model.litertlm> <gpu|cpu> <spec on|off> <out.jsonl>"""
import json, sys, time, statistics as st
import litert_lm as L
MODEL, BACK, SPEC, OUT = sys.argv[1:5]
cases = [json.loads(l) for l in open('/home/deck/otakubench-deck/cases.jsonl')]
t0 = time.perf_counter()
eng = L.Engine(MODEL, backend=L.Backend.GPU() if BACK == 'gpu' else L.Backend.CPU(), max_num_tokens=4096,
               cache_dir='/home/deck/e2b-deck/cache')
print('engine init', round(time.perf_counter() - t0, 2), 's', flush=True)
def text_of(m):
    if isinstance(m, dict):
        c = m.get('content')
        if isinstance(c, str): return c
        if isinstance(c, list): return ''.join(x.get('text', '') for x in c if isinstance(x, dict))
    return str(m)
def run(payload):
    msgs = payload['messages']; sysm = next((m['content'] for m in msgs if m['role'] == 'system'), None)
    t = time.perf_counter()
    conv = eng.create_conversation(system_message=sysm, max_output_tokens=256, enable_speculative_decoding=(SPEC == 'on'))
    t_conv = time.perf_counter() - t; ttft = None; out = []
    for chunk in conv.send_message_async(msgs[-1]['content']):
        s = text_of(chunk)
        if s and ttft is None: ttft = time.perf_counter() - t
        out.append(s)
    total = time.perf_counter() - t; conv.close()
    return {'raw': ''.join(out), 'seconds': round(total, 4), 'ttft_s': round(ttft, 4) if ttft else None, 'conv_create_s': round(t_conv, 4)}
import resource, glob
def gpumem():
    out = {}
    for k in ('mem_info_vram_used', 'mem_info_gtt_used'):
        for p in glob.glob('/sys/class/drm/card*/device/' + k):
            try: out[k] = round(int(open(p).read()) / 1e9, 2)
            except Exception: pass
    return out
print('gpu mem before warm-up', gpumem(), flush=True)
w = run(cases[0]['payload']); print('warm-up', w, flush=True); print('gpu mem after warm-up', gpumem(), flush=True)
with open(OUT, 'w') as f:
    for c in cases:
        r = run(c['payload']); r.update(id=c['id'], depth=c['depth']); f.write(json.dumps(r, ensure_ascii=False) + '\n')
R = [json.loads(l) for l in open(OUT)]
for d in sorted({r['depth'] for r in R}):
    s = [r['seconds'] for r in R if r['depth'] == d]; t = [r['ttft_s'] for r in R if r['depth'] == d and r['ttft_s']]
    print(f'depth {d}: p50 {st.median(s):.2f}s ttft {st.median(t):.2f}s')
print('max RSS GB', round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2)); print('all p50', round(st.median(r['seconds'] for r in R), 3), 'conv create p50', round(st.median(r['conv_create_s'] for r in R), 3))
