#!/usr/bin/env python3
"""Render curated 50 candidate manifest into a human-readable research catalog."""
import json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data'/'candidates.json').read_text())
rows=data['models']
lines=['# JP-Media-250 — 50 original-lab model candidates',
'', '**Date:** 2026-10-23  |  **Status:** metadata shortlisting only, no measured JP-to-English scores',
'', 'The rank is **priority for acquisition and benchmarking**, not a translation-quality score.',
'GGUF conversions are from Bartowski/Unsloth whenever possible. Original weights are',
'released by the model lab. mradermacher is used only where a closer quant is not in the',
'curated list; LLM-jp/LiquidAI publish their own GGUFs.',
'', '## All 50 selected models',
'', '| # | Original model | Total B | Active B | Chosen GGUF | Quant | Web-listed exact file | Web-listed size | Tier |',
'|---:|---|---:|---:|---|---|---|---:|:---:|']
for r in rows:
    quant=r['preferred_quant']
    link=f"[GGUF repo]({r['gguf_repo_url']})"
    if r['web_spotchecked']:
        direct='https://huggingface.co/'+r['quant_repo']+'/blob/main/'+r['listed_file_name']
        listed=f"[File]({direct})"
        size=f"{r['listed_size_gb']:.2f} GB"
    else:
        listed='— (API pending)'
        size='—'
    lines.append(f"| {r['rank']:02d} | [{r['model']}]({r['original_url']}) | {r['total_params_b']:g} | {r['active_params_b'] or '—'} | {link} | `{quant}` | {listed} | {size} | {r['tier']} |")
lines.extend(['','## Quantification and provenance','','Candidate parameters denote **total** parameters, NOT active MoE parameters.',
'Gemma 4 E2B: 5.1B total (2.3B effective); E4B: 8.0B total (4.5B effective).',
'The eight displayed file sizes above are public card/listing values, NOT downloaded or SHA-attested.',
'The Hugging Face verifier must resolve actual filename, size and revision before a model becomes quant-attested.',
'An exact file link in this catalog is a public source observation; its status is **web listed**, not runtime passed.',
'', '## Model-family breakdown', ''])
counts=collections.Counter(r['family'] for r in rows)
for family,n in sorted(counts.items(),key=lambda it:(-it[1],it[0])): lines.append(f'- {family}: {n}')
lines.extend(['','## Special models','',
'- **TranslateGemma 4/12/27B**: Google-trained translation specialist; Google reports 4.3B supervised fine-tuning tokens. Use its language-coded native user-message template for bare tests; a separate external context block is not part of the native protocol.',
'- **LLM-jp 4.1 (8B, 32B-A3B, 33B)**: Japanese-first native model; upstream `llama.cpp` v0.6.0 or later supports Harmony parsing. Old fork-only guidance is outdated.',
'- **gpt-oss-20b**: 21B total, 3.6B active; Bartowski recommended Q4_K_M GGUF retains native MXFP4_MOE experts. It is NOT a hypothetical MXFP4-named file.',
'- **Gemma 4 E2B/E4B**: effective sizes understate total stored parameters; total includes PLE embeddings.',
'- **Mistral, Gemma 3, Phi, Llama, Aya, LiquidAI**: ensure latest compatible llama.cpp, license and runtime conformance. Model family counts reflect deliberately balanced baselines, not empirical JP rankings.',
'', '## Decision status','',
'`selected_for_evaluation` → `HF quant/revision attested` → `canary passed` → `250 inference records complete` → `human reviewed` → `published translation rank`.',
'', '**Currently only the first stage is complete across 50.** See `README.md` for end-to-end commands, pitfalls and benchmark policy.',
''])
(ROOT/'CATALOG.md').write_text('\n'.join(lines),encoding='utf-8')
print('Rendered catalog with',len(rows),'rows')
if __name__=='__main__':pass
