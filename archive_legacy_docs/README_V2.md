# OtakuBench v2 — executable *draft*, not a scored leaderboard

**Status: 23 October 2026.** This patch corrects substantive problems identified in the JP-Media-250/OtakuBench review. It is an offline-built benchmark and runnable inference/judging system. **No actual local model has been run or scored. Neither GPT-6.1 Sol nor Claude Opus 5.5 has been calibrated on the dataset. Editorial references are not expert-verified ground truth.**

## What's inside

- `benchmark/otakubench/data/items/lines.jsonl`: all **250 unique** original Japanese linguistic probes, stable IDs, English draft references, alternatives, real tags, difficulty, pitfalls. All four historical media labels are **unvalidated scenario styles**; original version assigned them round-robin. Do not publish results by media on this table.
- `benchmark/otakubench/data/scenes/scenes.jsonl`: **31 additional** multi-line, independently authored passages. Each has two or more preceding Japanese utterances, actual speaker tags or narration, target line and English references. Phenomena include social address, uchi/soto keigo, names/terms, dialect, branching, hook noise, ruby, ambiguous speaker/reference, concealed intent, longer narration, violence, and adult-but-nonexplicit dialogue. These are still short pilot scenes, not representative chapters or proven hook-capture output.
- `benchmark/otakubench/data/build/`: validated JSONL / CSV and **blind** variants. Translator inputs never include editorial trap notes, reference English, or invented context hints.
- `benchmark/otakubench/data/items/corrections.json`: targeted repairs responding to the review. Alternate translations now live *on their stable-ID record*. The earlier row-index mapping is deprecated.
- `data/otakubench50.json` and `.csv`: revised **50 original-lab model weights** and exact *web-observed* quant names for most added Japanese specialists. This is an **acquisition priority**, **not translation results**. Six generic/older models were replaced in addition to four earlier substitutions (ten total). Q4 defaults are separate from Q6/Q8 sensitivity tests, and no file is called runtime-compatible based solely on file size.
- `tools/run_translations.py`: OpenAI-compatible local endpoint translator (chat, Hunyuan, CAT-Translate, raw Seed-X, experimental TranslateGemma). Accepts `--run-id` to preserve model+quant+thinking identity and never counts an unclosed `<think>` as a translation.
- `tools/run_matrix_v2.py`: **serial** `llama-server` launcher, canary test and complete run. Explicit `--jinja`, `--reasoning on|off|auto`, Deck-size heuristic, optional Q6/Q8, no downloads without `--execute`.
- `tools/audit_gold.py`: independent bilingual LLM review of **all 281 drafted references** without editorial hint notes, using Sol and Opus separately; their disputes remain flagged, not silently treated as a certified gold.
- `tools/calibrate_judge.py`: 24 known-error examples presented in both A/B orders (48 comparisons). A judge must achieve >=90% pairwise accuracy **and** >=85% correct in both orders to pass the authored sanity gate. This detects elementary errors and position bias, **not absolute literary evaluation quality**.
- `tools/judge.py`: LLM judge with adequacy 0–4, pragmatics/voice 0–4, English fluency 0–2 and specific error flags. Supports GPT-6.1 Sol and Claude Opus 5.5 APIs, resumable content-hashed JSONL, two retries, real token usage and a per-run budget ceiling. Reads draft gold but not source hints by default. **Never silently equates the reference to the only correct translation.**
- `tools/aggregate.py`: deterministic scoreboard with >=95% coverage gate, shared exclusion of flagged uncertain gold, bootstrap item intervals, error flags, run-ID matching, model timing and difficulty-1 sanity reporting separately. **It refuses to publish a rank until calibration and two independent, full-coverage AI gold audits have passed.**
- `tools/adjudicate.py` and `tools/judge_agreement.py`: select low-confidence/ambiguous/refusal cases for a bounded independent Opus pass and quantify disagreements; don't relabel automatically when the two disagree.
- `benchmark/jpmedia250/`: retained *legacy v1* for provenance. **Do not use the old runner/ctx mode or positional alternate mapping.**

## Run locally (from the extracted project root)

Requires Python 3.10+, a recent `llama-server` if running local models, and separate provider API keys for paid judging. Build/validate do not require downloads or keys.

```bash
python benchmark/otakubench/tools/build.py
python tools/curate_50.py
python -m pytest -q tests/test_otakubench_v2.py

# No downloads, no inference; inspect the exact command first.
python tools/run_matrix_v2.py --ranks 12-20 --device deck \
  --dataset lines --mode bare --quant default --reasoning off

# Actual local inference: opt in to downloading/loading model weights.
python tools/run_matrix_v2.py --ranks 12 --device deck \
  --dataset lines --mode bare --reasoning off --execute

# Separate controlled higher-precision arm. Q8 file availability is not
# implied by presence of Q4; verify repo and memory first.
python tools/run_matrix_v2.py --ranks 12 --device deck \
  --dataset lines --mode bare --quant Q8_0 --reasoning off

# For one already-running llama-server (no extra downloads):
python tools/run_translations.py --model 'My-Local-Model' --run-id 'My-Model:Q8:off' \
  --dataset scenes --mode context --output results/my-scenes.jsonl --execute
```

All default scripts are dry-run except `build.py`, `curate_50.py` and `aggregate.py`, which write only local non-paid files. The `--execute` flag is mandatory for network inference **and** for paid API judge calls. The matrix runner's `--execute` may download multi-gigabyte GGUF files to your local Hugging Face cache.

## LLM judge: choose by measured *judge* performance, not model reputation

```bash
# Each judge gets the same 48 swapped-order blind anchors.
python tools/audit_gold.py --dataset both --provider openai --model gpt-6.1-sol \
  --output results/gold_audit_sol.jsonl --budget-usd 10 --execute
python tools/audit_gold.py --dataset both --provider anthropic --model claude-opus-5-5 \
  --output results/gold_audit_opus.jsonl --budget-usd 10 --execute

python tools/calibrate_judge.py --provider openai --model gpt-6.1-sol \
  --output results/cal_sol.jsonl --execute
python tools/calibrate_judge.py --provider anthropic --model claude-opus-5-5 \
  --output results/cal_opus.jsonl --execute

# The primary judge (replace input path with one completed inference JSONL).
python tools/judge.py --responses results/v2/MODEL_all.jsonl --dataset lines --mode bare \
  --provider openai --model gpt-6.1-sol --split eval \
  --output results/judge_sol.jsonl --budget-usd 10 --execute

# Only high-risk cases are forwarded for a separate Opus judgment.
python tools/adjudicate.py --judgments results/judge_sol.jsonl \
  --inferences results/v2/MODEL_all.jsonl \
  --max-cases 100 --output results/opus_queue.jsonl
python tools/judge.py --responses results/opus_queue.jsonl --dataset lines --mode bare \
  --provider anthropic --model claude-opus-5-5 --split eval \
  --output results/judge_opus.jsonl --budget-usd 10 --execute
python tools/judge_agreement.py --primary results/judge_sol.jsonl \
  --secondary results/judge_opus.jsonl --output results/judge_disagreements.json

# Publishes numeric ranks ONLY if judge calibration and BOTH AI gold audits cover every evaluated item.
python tools/aggregate.py --dataset lines --mode bare --split eval \
  --judgments results/judge_sol.jsonl --inferences results/v2/MODEL_all.jsonl \
  --calibration results/cal_sol.jsonl \
  --gold-audits results/gold_audit_sol.jsonl \
  --gold-audits results/gold_audit_opus.jsonl --output results/leaderboard.json
```

The analyst should check the same model's sample translations in *blind* mode before giving the judge gold/reference; a supplied note that says `rejects` or `sarcastic` creates information leakage. The primary judge defaults to seeing the Japanese, the anonymous translation, one drafted reference, and acceptable variants (if available), but **no explanatory note**. Only an explicitly flagged independent second pass can show notes.

## Budget

Provider published standard API rates as of 23 Oct 2026: GPT-6.1 Sol **$2 input / $10 output** per million tokens; Claude Opus 5.5 **$4 / $20**. Batch processing can save ~50% on both, but this runner uses synchronous API calls and so **does not itself implement Batch**. Costs below are illustrative only.

25,000 judgments × 900 input tokens × $2/1M + 25,000 × 160 output tokens × $10/1M = **$85 on Sol** at standard rates, **$170 on Opus**; Batch would be approximately $42.50 or $85 at the same token counts. These are not quotes: actual paid reasoning output, caching, output length, retries, and context length change the bill. The runner reads usage and caps *observed* total, but the final request can overshoot by one call. Start with a small calibration, then a 50–100-item pilot to measure actual usage.

Using both judges on all 25,000 outputs doubles cost without establishing either is truthful. Instead: choose primary only after the paired calibration, send disputed/low-confidence examples to secondary (bounded 5–15% initially), compare substantive error flags and rank reversals. If judges disagree materially, label it **unresolved**, not adjudicated gold.

## Benchmark contract and unresolved limitations

1. **Original authored data:** no fake quotes or work attribution. The dataset is media-*style*, not a licensed set of actual VN excerpts.
2. **Gold is provisional:** even after two independent AI audits, repairs are editorial; not independently reviewed by bilingual readers or a validated external judge. Judge calibration anchors are also authored by this project. Do not claim objective Japanese translation scores yet.
3. **No line-context leakage:** the 250 old line probes have only Japanese source. Their historical scene annotations are retained only for auditing. The 31 new scenes are the *only* context-capable examples.
4. **Difficulty-1 is sanity:** the main ranked score is difficulty 2–5 (160 cases in the 200-case line eval split); level 1 (40 eval cases) is reported separately.
5. **Real VN workloads are not covered by 31 short scenes:** missing long arcs, repeated character identities across hours, independently collected hook capture, ruby and broken markup diversity, and enough hard adult/violent passages for robust refusal statistics. Expand empirically before broad claims.
6. **Context translation is not equally supported by every specialist:** Seed-X and TranslateGemma native context paths are explicitly not yet qualified. TranslateGemma's nonstandard payload may fail in `llama-server`; the matrix deliberately skips it until proven. Translation specialists may require native prompt formats and have limitations in handling metadata or context.
7. **Total parameter count <=35B**: total weights, not MoE active count. `deck_default_candidate` is based on reported GGUF *file size* <=9 GB only, **not actual Steam Deck fit** (OS, KV cache and runtime overhead matter).
8. **Q4 is the default publisher-typical arm, not assumed best:** test small models in Q6_K and Q8_0 if the quant exists, record measured throughput and quality. Keep thinking-on/off and bare/context/full separately identifiable.
9. **Licences:** PLaMo, HY-MT1.5, TranslateGemma and other model licences require independent verification before commercial use or distribution. A public GGUF and local runtime do not convey permission.
10. **Benchmark contamination and circular grading remain possible** if a candidate model or judge memorizes authored probes, or if a judge is from the candidate model's lab. Hold out unreleased scenes and publish version/hash.

## Sources checked for the specialised models

- CyberAgent CAT-Translate family and 7B native prompt: https://huggingface.co/cyberagent/CAT-Translate-7b
- Tencent's official HY-MT1.5 GGUF (7B and 1.8B): https://huggingface.co/tencent/HY-MT1.5-7B-GGUF and https://huggingface.co/tencent/HY-MT1.5-1.8B-GGUF
- Hunyuan-MT original: https://huggingface.co/tencent/Hunyuan-MT-7B
- Seed-X-PPO native raw prompt and unofficial-quant warning: https://huggingface.co/ByteDance-Seed/Seed-X-PPO-7B (quant file: https://huggingface.co/mradermacher/Seed-X-PPO-7B-GGUF/tree/main)
- Swallow 8B Japanese research: https://huggingface.co/tokyotech-llm/Qwen3-Swallow-8B-RL-v0.2
- PLaMo specialist (different license/runtime): https://huggingface.co/pfnet/plamo-2-translate
- OpenAI API rates: https://platform.openai.com/pricing/
- Anthropic API rates: https://www.anthropic.com/pricing

*The baseline catalog in `CATALOG.md` and `README.md` reflects the original 50-model shortlist and must not override this v2 document or `data/otakubench50.json`.*
