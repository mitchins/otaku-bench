# OtakuBench v4 — bounded, reproducible Japanese→English local-model benchmark

**Status: development infrastructure passed offline tests; no model has actually been run or judged in this workspace.** This is a *screened candidate set* and an *editorial benchmark*, not a translation-quality leaderboard. Supersedes v2/v3. The original Japanese is independently authored, genre-inspired text, **not sourced dialogue** from copyrighted titles.

## Purpose, limits and what changed

- **250 single-line diagnostic probes:** fixed `JMB-001..250`, 10 phenomenon categories, five difficulty levels, 50 development/200 evaluation. They are **bare Japanese-only**. The legacy media buckets were assigned cyclically and must NOT be reported as real VN/anime/game/light-novel quality categories.
- **31 original Japanese discourse scenes:** `OTB-P001..031`, six development/25 evaluation; target-only without context, target with *actual preceding Japanese*, and complete-scene translation. **Whole-scene translation is now the primary scene diagnostic**; some target-only cases remain simple. These 25 eval scenes are too few for a publishable ranking and are explicitly gated as diagnostic-only.
- **Real adversarial features:** target-line ambiguity, in-scene referents, period-appropriate honorifics, character speech, body-language subtext, explicit but consensual adult sexual vocabulary, fictional graphic violence, heavy profanity, actual extraction duplicate lines and intra-word wraps. These should detect model refusal, euphemism and hook artefact confusion. `OTB-P009`/`OTB-P025` score against normalized English while retaining intentional stammers.
- **Proofing:** correction to `JMB-047`, alternative readings for `JMB-093`, replacement of thematic duplication at `JMB-199`, and inclusion of `風の便り` at `JMB-073` (hearsay, *not* wind chime). All metadata/alternate translations attach by stable IDs, never positional row numbers. Native gold is **NOT externally approved** and still requires AI audit.
- **Candidate model selection:** exactly 50 laboratory/provenance-qualified models and domain exceptions, total parameters 0.6–35B. v4 removes five duplicates/less useful baselines and adds the original parent controls for VNTL, Sugoi and Shisa, plus Qwen3-4B-Instruct-2507. See `CATALOG.md` and `ELIGIBILITY_POLICY.md`. Priority `rank` is NOT measured quality.
- **Runners:** default publisher recommended GGUF Q4/Q5, optional separately attested Q6/Q8, reasoning on/off, serial five-case canary and full run. Native VNTL `Metadata→Japanese→English` completions format, avoiding an explicit BOS; raw rinna parent uses separate two-shot completion format and is **diagnostic-only, not a fair leaderboard rival**. The launcher preflights upstream `llama-server --help` for flags.
- **Judges and statistics:** GPT-6.1 Sol or Opus 5.5 (configured via API, neither executed), two independent gold-reference audits and a 48-trial swapped-order calibration. Candidate-specific `gold_uncertain` never quarantines items globally; common exclusions require two separate gold auditors. Judge scores and translations are source/gold-SHA bound. Same-case paired bootstrap compares model differences; default is bounded adjacent comparisons, `--compare-pairs all` is opt-in.

## Environment

Python >=3.11; tests use `pytest`. `pip install huggingface_hub` for Hugging Face metadata; current `llama-server` in PATH for local GPU/CPU runs. The only paid features are `tools/audit_gold.py`, `tools/calibrate_judge.py`, and `tools/judge.py` when explicitly invoked with `--execute` and matching API keys. Merely unpacking, testing or previewing **does not call paid APIs or download weights**.

```bash
cd otakubench_v4
python -m pytest -q
python benchmark/otakubench/tools/build.py
python tools/render_catalog_v4.py
```

The corpus source-of-truth is `benchmark/otakubench/data/items/lines.jsonl` and `data/scenes/scenes.jsonl`. Generated blind and gold files are under `benchmark/otakubench/data/build/`. `tools/patch_corpus_v4.py` records reproducible corrections; `tools/reconcile_catalog_v4.py` is idempotent and builds the active catalog from frozen `data/otakubench50_v3.json`.

## Minimal real-world pilot — stop polishing here

**Start with up to six Deck-class candidate hypotheses**, not 50 downloads. A useful diverse initial set is ranks `15,18,19,20,31,46` (Shisa Qwen3 8B, TinySwallow, Liquid Japanese 1.2B, VNTL, Qwen3.5 4B, Qwen3-4B-Instruct-2507). These are hypotheses, not performance estimates; `deck_default_candidate` is only a <=9GB *file-size* proxy, not proven runtime fit. To test a base/adaptation effect, add an exact-matched base control separately.

**1. Attest model artifacts, without downloading weights:**

```bash
python tools/resolve_ggufs.py --catalog data/otakubench50.json --out data/attested.json
# Review any statuses other than HUB_QUANT_ATTESTED before committing to the weights.
# The resolver may exit nonzero if even one of 50 models lacks the exact recommended file.
```

**2. Preview commands without weight downloads:**

```bash
python tools/run_matrix_v2.py --catalog data/attested.json \
  --ranks 15,18,19,20,31,46 --device deck --dataset lines --mode bare \
  --reasoning off
```

**3. Run one model on the entire diagnostic corpus, then the entire short-scene arm:**

```bash
python tools/run_matrix_v2.py --catalog data/attested.json \
  --ranks 20 --dataset lines --mode bare --reasoning off --execute
python tools/run_matrix_v2.py --catalog data/attested.json \
  --ranks 20 --dataset scenes --mode full --reasoning off --execute
```

Unattested exact GGUF files are blocked by default. `--allow-unattested` is exploratory only and **never counts as a qualified rank**. No inference should be submitted to a judge until its `source_sha256` is current and all expected cases have completed. Model server logs and JSONL responses are in `results/v4/`.

**4. If Q8 is warranted, attest it as a separate arm and use both switches together:**

```bash
python tools/resolve_ggufs.py --catalog data/otakubench50.json \
  --quant Q8_0 --out data/attested_q8.json
python tools/run_matrix_v2.py --catalog data/attested_q8.json \
  --ranks 18 --quant Q8_0 --dataset lines --mode bare --reasoning off --execute
```

A Q8 file existing on Hugging Face is not proof of sufficient Deck memory. **TranslateGemma native template, third-party quant ancestry, and assorted GGUF tokenizers require independent canary verification.** Missing or unsafe runtime support is a `SKIP`/`BLOCKED`, not a score of zero or a fabricated quality rank.

## AI gold audit and evaluation: opt-in / metered

The 250 + 31 editable English references are draft gold, not bilingual-human certified. The reasonable no-human-review substitute is two independent bilingual audits and calibration, with complete disagreement records and no claimed expert guarantee. First do free **dry runs**:

```bash
python tools/audit_gold.py --dataset lines --model gpt-6.1-sol --output results/v4/gold_sol.jsonl --limit 5
python tools/calibrate_judge.py --model gpt-6.1-sol --output results/v4/cal_sol.jsonl --limit 4
# An example scored translation requires an actual inference file:
python tools/judge.py --responses results/v4/20_VNTL_Q5_K_M_lines_bare_off_all.jsonl \
  --dataset lines --mode bare --split dev --model gpt-6.1-sol \
  --output results/v4/judge_sol.jsonl
```

Review the output/input preview and budget before explicitly adding `--execute`. For Opus, pass `--provider anthropic --model claude-opus-5-5` and configure `ANTHROPIC_API_KEY`. Paid calls are disabled by default and record measured token/cost estimates. For a dev pilot score, judge only the development split first and do **not** publish a rank based on those 50 lines or six scenes.

After the model has run and the judge has been calibrated and two auditors have audited the relevant gold items:

```bash
python tools/aggregate.py --judgments results/v4/judge_sol.jsonl \
  --inferences results/v4/20_VNTL_Q5_K_M_lines_bare_off_all.jsonl \
  --calibration results/v4/cal_sol.jsonl \
  --gold-audits results/v4/gold_sol.jsonl \
  --gold-audits results/v4/gold_opus.jsonl \
  --dataset lines --mode bare --split eval \
  --output results/v4/line_scores.json
```

`--gold-audits` is only useful for fully completed, independent same-revision audits. With zero audits, the tool still computes **diagnostic** numbers but marks them unqualified. It will **not** publish a real scene ranking until at least 60 evaluated scenes exist; this v4 archive has only 25 eval scenes. Context benefit is separately computed with `tools/context_gain.py` using the *same model, judge, gold and item IDs*; expect broad confidence intervals at this sample size.

## Audit rules, source linking and interpretation

- Do **not** mix different quant/reasoning/prompt/hardware arms into a single inference `run_id` or report context-gain from different models.
- A single candidate judge `gold_uncertain=true` removes that judgment from **its own arm only**; it does **not** alter everyone else's denominator. Global quarantine requires agreement from two independent gold-audit models; auditor disagreement blocks a published ranking.
- Results from older gold or blind-source revisions are **rejected** rather than silently appended. The SHA is part of every valid inference/judgment.
- The paired bootstrap is exploratory; adjacent rankings and uncorrected intervals are *not* proof of statistically distinguishable top 50, and the judge may share biases with the corpus authors.
- The original text is copyrighted by its authors, not a reproduction of named VN source passages. No sourced-media provenance claims are made.
- No judge model, local model, nor target GGUF has actually been executed in this workspace. The offline tests validate software behaviours and synthetic fixtures **only**.

See `PROTOCOL.md` for the evaluation contract and `CHANGELOG_V4.md` for Claude-review fixes.
