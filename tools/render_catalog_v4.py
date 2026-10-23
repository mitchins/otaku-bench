#!/usr/bin/env python3
"""Render current 50-model decision catalog from the active, versioned manifest."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/otakubench50.json').read_text(encoding='utf-8'))
assert manifest['version']=='4.0', 'Do not produce a v4 catalog from another manifest revision'
rows=manifest['models']
assert len(rows)==50 and {x['rank'] for x in rows}==set(range(1,51))
delta=json.loads((ROOT/'data/model_selection_delta_v4.json').read_text())
new=set(delta['added_v4']);removed=set(delta['removed_v4'])
lines=[
 '# OtakuBench v4 — 50 local Japanese→English translation candidates',
 '',
 '> **Provisional test priority, not translation performance.** Zero models were run or scored in this working container. Exact GGUF names and reported sizes require Hugging Face revision/byte attestation before any qualified run.',
 '',
 f'**50 total, {len(new)} v4 controls added, {len(removed)} redundant entries removed; {sum(x["deck_default_candidate"] for x in rows)} weight-size-proxy-only Deck candidates.**',
 '',
 'The four lanes: first-party laboratory models; documented Japanese/bilingual adaptations; laboratory distillations; narrowly permitted VN-specialist releases. Parent models used as experimental *controls* are not predicted winners.',
 '',
 '| # | Model (original release) | Total B | Category | Recommended GGUF / converter | Quant | Reported GB† | Deck weight proxy |',
 '|---:|---|---:|---|---|---|---:|---|',
]
for r in rows:
 name=r['model'].replace('|',r'\|')
 mark=' **v4**' if name in new else ''
 role=' **control**' if r.get('evaluation_role')=='ancestor_diagnostic_only' else ''
 q=r.get('quant_file') or r.get('listed_file_name') or 'unverified'
 if isinstance(q,list):q=', '.join(q)
 repo=r.get('quant_repo') or ''
 gb=r.get('quant_size_gb') or r.get('listed_size_gb')
 gb_text=f'{gb:.2f}' if isinstance(gb,(int,float)) else '—'
 lines.append(f'| {r["rank"]} | [{name}](https://huggingface.co/{r["original_repo"]}){mark}{role} | {r["total_params_b"]:g} | {r["eligibility_lane"]} | [{repo}](https://huggingface.co/{repo}) — `{q}` | `{r["preferred_quant"]}` | {gb_text} | {"size only" if r["deck_default_candidate"] else "no"} |')
lines += [
 '',
 '† Decimal gigabytes from repository listings, not measured physical footprint or a promise of model correctness. Verify quant names, file sizes, shard counts, immutable repo SHAs, native prompts, and actual loading with `tools/resolve_ggufs.py` and five-item canaries.',
 '',
 '## v4 candidate changes',
 '',
 '**Added:** '+', '.join(sorted(new))+'.',
 '',
 '**Removed:** '+', '.join(sorted(removed))+'.',
 '',
 '## Control comparisons',
 '',
 '| Adaptation | Base/control | Scope |',
 '|---|---|---|',
]
for child,parent in delta['required_controls'].items():
 suffix=' *diagnostic-only ancestor; non-instruction model needs separate prompting*' if child=='VNTL-Llama3-8B-v2' else ''
 lines.append(f'| {child} | {parent} | Base-vs-adaptation{suffix} |')
lines += [
 '',
 'A base-model control establishes *relative improvement* only after identical items, compatible prompting, and quant/hardware choices. Original ancestors lacking instruction tuning are **not** apples-to-apples leaderboard entries.',
 '',
 '## Runtime/policy constraints',
 '',
 '- TranslateGemma needs a native language-coded template. The ordinary llama.cpp chat adapter is not declared qualified.',
 '- VNTL v2 expects the publisher `Metadata` / `Japanese` / `English` Llama3 completion format without a literal duplicated BOS; full multiline scenes are supported as an experimental arm.',
 '- `rinna-llama-3-youko-8b` is VNTL v2’s declared Japanese continued-pretrained base, **not** ordinary Meta Llama-3-8B.',
 '- `--reasoning on/off/auto`, `--jinja` and `--alias` require a compatible recent llama-server; the matrix runner preflights them for execution.',
 '- Q6/Q8 require independent Hugging Face quant attestation, and are separate experimental arms. The Q4/default selection is not a universal best-quality quant.',
 '- 16 GB Steam Deck compatibility cannot be decided from GGUF filesize alone. A 14B 8.99 GB file is **not** qualified for the Deck without actual RAM/KV checks.',
 '- Third-party converters are provisional until provenance/quant inspection and canaries; page listings are **not** equivalent to runtime qualification.',
 '- Priority rank is a candidate order, never an inferred result or a public translation leaderboard.',
 '',
 'See [README.md](README.md), [PROTOCOL.md](PROTOCOL.md), [ELIGIBILITY_POLICY.md](ELIGIBILITY_POLICY.md).',
 '']
text='\n'.join(lines)
(ROOT/'CATALOG_V4.md').write_text(text,encoding='utf-8')
(ROOT/'CATALOG.md').write_text(text,encoding='utf-8')
print('Rendered',len(rows),'models,',Counter(r['eligibility_lane'] for r in rows))
