#!/usr/bin/env python3
"""Render active v3 priority list from manifest; no external requests."""
from collections import Counter
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
source=json.loads((ROOT/'data/otakubench50_v3.json').read_text())
rows=source['models']
new_names={x['model'] for x in json.loads((ROOT/'data/model_selection_delta_v3.json').read_text())['added']}
lines=[
 '# OtakuBench v3 — 50-model GGUF shortlist',
 '',
 '> **Priority ordering is for experiments, not measured translation ability.** None of these 50 candidates has completed a live OtakuBench run here. New GGUF filenames were individually checked against repository pages; none of the new 12 has a pinned Hugging Face API revision in this workspace. Memory suitability of any candidate is also unverified.',
 '',
 f'**50 candidates, {len(new_names)} newly admitted adaptations/specialists, 12 retired; {sum(r["deck_default_candidate"] for r in rows)} file-size-only Deck candidates (not confirmed to load).**',
 '',
 'Original training publisher and GGUF-conversion publisher are recorded separately. All files and evidence links are in `data/otakubench50.json` / `.csv`.',
 '',
 '| Priority | Model and original release | Total B | Training lane | GGUF source and exact filename | Quant | File GB† | Deck file size |',
 '|---:|---|---:|---|---|---|---:|---|',
]
for x in rows:
    name=x['model'].replace('|',r'\|')
    mark=' **NEW**' if name in new_names else ''
    file=x.get('quant_file') or x.get('listed_file_name') or 'unverified'
    if isinstance(file,list):file=', '.join(file)
    gb=x.get('quant_size_gb') or x.get('listed_size_gb')
    dims=f'{gb:.2f}' if gb is not None else '—'
    lane=x['eligibility_lane'].replace('_',' ')
    repo=x['quant_repo']
    lines.append(f'| {x["rank"]} | [{name}](https://huggingface.co/{x["original_repo"]}){mark} | {x["total_params_b"]:g} | {lane} | [{repo}](https://huggingface.co/{repo}) — `{file}` | `{x["preferred_quant"]}` | {dims} | {"size only" if x["deck_default_candidate"] else "no"} |')
lines+=['',
 '† Decimal gigabytes where a file size was reported. Not RAM/VRAM or a verified measurement. Some prior-v2 rows list a repository size or recommended quant without a fully verified exact file; run `tools/resolve_ggufs.py` to attest each candidate, and check multi-part GGUF support before evaluation.',
 '',
 '## New admission breakdown',
 '',
]
cnt=Counter(x['eligibility_lane'] for x in rows if x['model'] in new_names)
for lane,n in sorted(cnt.items()):lines.append(f'- `{lane}`: {n} model(s)')
lines+=['',
 '## Guardrails',
 '',
 '- Do not treat `deck_default_candidate=true` as confirmation the model fits a 16GB Deck. Test actual memory with KV cache, OS reserve, and chosen context.',
 '- VNTL v2 uses publisher-documented raw Llama3 `Japanese` / `English` turn headers, not generic system/user chat. Bare lines and bare multi-line scenes supported by runner; context-mode templates require qualification.',
 '- Sugoi 14B and 32B use the publisher localization system prompt and lower sampling temperature.',
 '- Swallow reasoning-on is the qualified prompt exploration starting point, not a proven winner.',
 '- Pinned Hugging Face quant metadata and matching card ancestry do not prove weights parity or translation quality.',
 '- Translator models, plus premium judges, must pass canary, semantic scoring and independent adjudication before public rankings.',
 '',
 'See `ELIGIBILITY_POLICY.md` for detailed selection rules and `README_V3.md` for repeatable commands.',
 '']
p=ROOT/'CATALOG_V3.md';p.write_text('\n'.join(lines),encoding='utf-8')
print(f'{len(rows)} entries rendered to {p}')
