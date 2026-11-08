#!/usr/bin/env python3
"""Deployment prompt probe on DEV items only (lockbox): does stronger target-language wording stop echoes?"""
import json, re, sys, copy, collections
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
B = '/home/mitch/otakubench'
sys.path.insert(0, B + '/tools'); sys.path.insert(0, B + '/mission')
import run_translations as rt, mechanical as mech
import screen_mission as sm
BASE, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
D = B + '/benchmark/otakubench/data/build/'
full = [r for r in map(json.loads, open(D + 'scenes_full.jsonl')) if r['split'] == 'dev']
lines = [r for r in map(json.loads, open(D + 'lines_bare.jsonl')) if r['split'] == 'dev']
ctx = []
for s in full:
    ls = [l for l in s['japanese'].split('\n') if l.strip()]
    for k in range(1, len(ls)):
        ctx.append({'id': f"{s['id']}#{k}", 'japanese': ls[k], 'preceding_lines': ls[max(0, k - 6):k], 'split': 'dev'})
sys.path.insert(0, '/home/mitch/e2b-deck/research/vision-probes/synth'); from lines import LINES  # 20 hand-written lines, no benchmark data
def chain(items, tag):
    out = []
    for k in range(1, len(items)):
        out.append({'id': f'{tag}#{k}', 'japanese': items[k], 'preceding_lines': items[max(0, k - 6):k], 'split': 'dev'})
    return out
ctx += chain([r['japanese'] for r in lines], 'devlines') + chain([f'【{n}】{l}' for n, l, *_ in LINES], 'own')
SYS0 = rt.SYSTEM
EXPL = sm.VARIANTS['explicit-target']['user_rewrite']
STRONG = 'Translate FROM JAPANESE TO ENGLISH. Your reply must be in English only; never repeat the Japanese.'
VARS = {
  'base': {},
  'explicit-target': {'rw': EXPL},
  'short-system': {'rw': EXPL, 'sys': 'Translate the supplied Japanese into faithful, natural English.'},
  'caps-system': {'rw': EXPL, 'sys': STRONG + ' ' + SYS0},
  'caps-system+user-suffix': {'rw': EXPL, 'sys': STRONG + ' ' + SYS0, 'suffix': '\n\n(Reply in English only.)'},
}
def payload(rec, ds, mode, v):
    ns = SimpleNamespace(prompt_style='chat', model=MODEL, dataset=ds, mode=mode, max_tokens=768)
    m = copy.deepcopy(rt.make_payload(rec, ns)['messages'])
    if 'sys' in v: m[0]['content'] = v['sys']
    for a, b in v.get('rw', ()): m[-1]['content'] = m[-1]['content'].replace(a, b)
    m[-1]['content'] += v.get('suffix', '')
    return m
N = int(__import__('os').environ.get('SAMPLES', '1'))
def chat(m):
    if __import__('os').environ.get('LLAMA'):
        res = []
        for i in range(N):
            pl = {'model': MODEL, 'temperature': 1.0 if N > 1 else 0, 'top_p': 0.95, 'top_k': 64, 'seed': 1000 + i, 'max_tokens': 768,
                  'chat_template_kwargs': {'enable_thinking': False}, 'messages': m}
            with urlopen(Request(BASE + '/chat/completions', data=json.dumps(pl).encode(), headers={'Content-Type': 'application/json'}), timeout=300) as r:
                res.append((json.load(r)['choices'][0]['message'].get('content') or '').strip())
        return res
    pl = {'model': MODEL, 'temperature': 1.0 if N > 1 else 0, 'top_p': 0.95, 'top_k': 64, 'n': N, 'max_tokens': 768, 'chat_template_kwargs': {'enable_thinking': False}, 'messages': m}
    with urlopen(Request(BASE + '/chat/completions', data=json.dumps(pl).encode(), headers={'Content-Type': 'application/json'}), timeout=300) as r:
        return [(c['message'].get('content') or '').strip() for c in json.load(r)['choices']]
KANA = re.compile(r'[぀-ヿ]')
def body_kana(t):  # kana outside 【name】 tags and quoted single words
    t = re.sub(r'【[^】]*】', '', t); t = re.sub(r'"[^"]{1,8}"|「[^」]{1,8}」', '', t)
    return bool(KANA.search(t))
jobs = []
for vn, v in VARS.items():
    for r in ctx: jobs.append((vn, 'ctx', r, payload(r, 'scenes', 'context', v)))
    for r in lines: jobs.append((vn, 'line', r, payload(r, 'lines', 'bare', v)))
    for r in full: jobs.append((vn, 'full', r, payload(r, 'scenes', 'full', v)))
with ThreadPoolExecutor(8) as ex: outs = list(ex.map(lambda j: chat(j[3]), jobs))
recs = [{'variant': vn, 'kind': k, 'id': r['id'], 'src': r['japanese'], 'out': o, 's': i} for (vn, k, r, _), os_ in zip(jobs, outs) for i, o in enumerate(os_)]
json.dump(recs, open(OUT, 'w'), ensure_ascii=False, indent=0)
base = {(x['kind'], x['id'], x['s']): x['out'] for x in recs if x['variant'] == 'base'}
print(f"{'variant':26s}{'ctx echo':>10}{'ctx contract':>14}{'ctx kana':>10}{'lines kana':>12}{'full kana':>11}{'= base (lines)':>16}")
for vn in VARS:
    R = [x for x in recs if x['variant'] == vn]
    c = [x for x in R if x['kind'] == 'ctx']; li = [x for x in R if x['kind'] == 'line']; fu = [x for x in R if x['kind'] == 'full']
    cv = collections.Counter(mech.contract_violation(x['src'], x['out']) for x in c)
    print(f"{vn:26s}{cv['source_echo']:>6}/{len(c)}{sum(v for k, v in cv.items() if k):>10}/{len(c)}{sum(body_kana(x['out']) for x in c):>6}/{len(c)}"
          f"{sum(body_kana(x['out']) for x in li):>8}/{len(li)}{sum(body_kana(x['out']) for x in fu):>7}/{len(fu)}{sum(x['out'] == base[(x['kind'], x['id'], x['s'])] for x in li):>12}/{len(li)}")
