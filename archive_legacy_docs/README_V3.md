# OtakuBench v3 — Japanese adaptation eligibility and 50 GGUF candidates

This project is a reproducible **candidate selection and evaluation harness**, not a set of claimed model-quality results.

## What changed after Claude's policy review

- Replaced the blanket third-party-fine-tune exclusion with three bounded paths: original lab releases, substantial documented Japanese/bilingual training and/or laboratory distillation, and a **narrow VN translation specialist exception**.
- 12 candidates added, 12 removed, total remains 50. The old v2 matrix is frozen at `data/otakubench50_v2.json` for traceability.
- Admitted **Qwen3 Swallow 32B, GPT-OSS Swallow 20B, NVIDIA Nemotron Nano Japanese 9B, four Shisa V2.1 variants, TinySwallow 1.5B, Liquid's LFM2.5 JP 1.2B, VNTL 8B v2, Sugoi 14B and Sugoi 32B**.
- Kept useful original-base controls (Qwen3-8B, gpt-oss-20b, Liquid 1.2B Instruct) so adaptation gains can be measured instead of assumed.
- Added published GGUF *file* names and conversion publishers to every newly added row. Filesystem paths/revisions must still be pinned by the HF API resolver before an attested trial.
- Added native VNTL raw `Japanese`→`English` turn formatting and Sugoi translation system prompt/sampling to the new evaluation runner.
- Enabled bare multiline scene translation for VNTL. It does not currently support historical-context mode until native-format behavior is validated by canaries.
- `run_matrix_v2.py` now reads the v3 catalog by default and refuses `--execute` without successful upstream SHA/file attestation. `--allow-unattested` is explicitly exploratory and **not qualified**.

## Data & scope

- `data/otakubench50.json` / `.csv` — active 50-model selection with training origins, quant files, conversion publishers, approximate GGUF sizes, device filtering flags and prompt style.
- `data/otakubench50_v2.json` — previous frozen selection.
- `data/model_selection_delta_v3.json` — 12 in / 12 out with source evidence.
- `CATALOG_V3.md` — human-readable 50-model shortlist.
- `ELIGIBILITY_POLICY.md` — binding entry/exception policy.
- `benchmark/otakubench/` — **250 isolated probes plus 31 contextual scenes**, separated blind tests/gold, and build metadata.
- `tools/resolve_ggufs.py` — Hugging Face repository metadata attestation (no model download).
- `tools/run_matrix_v2.py` and `tools/run_translations.py` — serial `llama-server` canary → 250/31 inference, with separate prompt/quant/reasoning arms.
- `tools/audit_gold.py`, `judge.py`, `calibrate_judge.py`, `aggregate.py`, `adjudicate.py` — reference audit, LLM grading, calibration and controlled leaderboard. See `PROTOCOL_V2.md` for validity limitations.
- `tools/curate_50_v3.py`, `tools/render_catalog_v3.py` — deterministic regeneration from frozen prior selection.

## Commands

From inside this folder, Python 3.11+ and `pytest` for tests:

```bash
python tools/curate_50_v3.py
python tools/render_catalog_v3.py
python -m pytest -q tests/test_otakubench_v2.py tests/test_selection_and_runner.py tests/test_selection_v3.py
```

Verify the **exact quant paths, byte sizes and immutable repository SHA** using Hugging Face metadata (requires network, `pip install huggingface_hub`):

```bash
python tools/resolve_ggufs.py --catalog data/otakubench50.json --out data/attested.json
# Explicit high-precision files are separate experiments, never implicit fallbacks:
python tools/resolve_ggufs.py --catalog data/otakubench50.json --quant Q8_0 --out data/attested_q8.json
```

A nonzero resolver exit is **expected** if an exact quant or metadata is missing; inspect `data/attested.json` for each row's `repro_status`. A pinned file path is not proof of train-publisher ancestry or correct inference support.

Preview four highly relevant Deck-size candidates (no download or launch):

```bash
python tools/run_matrix_v2.py --ranks 18-21 --device deck --dataset lines --mode bare --reasoning off
```

To run VNTL v2 on **bare multi-line scenes** after the quant and source have been attested:

```bash
python tools/run_matrix_v2.py --catalog data/attested.json --ranks 20 \
  --dataset scenes --mode bare --reasoning off --execute
```

To run a 250-line serial inference trial:

```bash
python tools/run_matrix_v2.py --catalog data/attested.json --ranks 15 \
  --dataset lines --mode bare --reasoning off --execute
```

These commands need a current `llama-server` with compatible GGUF/chat templates and adequate memory. The execution runner explicitly blocks missing metadata or unreviewed reported ancestry by default. Use `--allow-unattested` **only for non-ranking exploratory canaries**; its use will emit `EXPLORATORY_UNATTESTED` and cannot be used for a trusted leaderboard.

Note: the Q6/Q8 GGUF variants require their own attestation manifest. For quantitative comparisons, fix inference hardware, context size, sampler, prompt style and use a pinned SHA per variant.

## Important boundaries

**This release contains no measured translation-quality rankings or device memory validation.** Web-checked file listings are not live HF API evidence, source lineage is not numerically checked against FP16 tensors, and the native templates for several specialist families still need actual canary runs.

The original 250 strings remain diagnostic language probes. For decisions about real VN translation, weight the contextual scenes, character consistency, forbidden hallucinated details, refusal/softening, source-accurate emotion, term consistency, and runtime latency more heavily. Neither premium judge should be considered calibrated merely because its JSON parser works. The existing judge fixture and coverage gates need empirical validation.

**Steam Deck filtering** is only a file-size proxy (`<=9.0 GB` of GGUF weight files) and in particular does not imply a 14B Q4 will run acceptably in 16GB shared RAM. Test actual process memory, context KV, OS consumption, throughput and thermal behavior.

**Security and source trust**: GGUF converters can differ from model trainers; treat non-lab quants as untrusted until repository ownership, immutable revisions, hashes, and conversion ancestry are reviewed. The v3 manifest names converter organisations explicitly. Review source licensing before redistribution/use of the models or any proprietary text. The benchmark itself uses independently authored text, not copied VN dialogue.
