# OtakuBench v4 — evaluation and publication contract

**Status: editorial candidate benchmark, no empirically qualified translation rankings.** Original authored Japanese, not direct excerpts. Two AI judges are a pragmatic replacement for large-scale human review, but no agreement protocol certifies them as human-level translators.

## Testable units and splits

| Arm | Count | Output to score | Intended use | Status |
|---|---:|---|---|---|
| `lines/bare` | 250 (50 dev, 200 eval) | Single translated utterance | Ten phenomena, nuance, idiom, negation, voice | diagnostic, can provide provisional AI-audited item ranking |
| `scenes/bare` | 31 (6 dev, 25 eval) | Final target line alone | context-free same-target baseline | diagnostic only |
| `scenes/context` | 31 | Final line, actual preceding Japanese visible | discourse/context benefit against bare on identical cases | diagnostic only |
| `scenes/full` | 31 | All distinct source lines, preserving speaker labels | primary scene outcome: continuity, register, source integrity, terminology | diagnostic only |

The 250 originally labeled media categories were assigned round-robin: **never claim per-medium accuracy**. Difficulty 1 is sanity-check only; line eval has 160 eligible difficulty 2–5 items and 40 easy items. The context scenes were independently written, not extracted from a genuine VN text hook. Two marked cases contain *synthetic* duplicated UI strings and midword linebreaks; normalise those extraction artifacts, but retain *intentional* hesitation and repeats. The actual targets in P005/P025/P027 were rewritten to be more context-dependent, and full-scene scores sidestep easy-target masking. More scenes would be required for valid real-VN ranking.

## Scoring: no string-match trap

A two-part auditable review:

1. **Reference auditing:** two independently configured bilingual evaluators (e.g. Sol and Opus) examine source and reference **without editorial translation notes**; detect unnatural source Japanese, invented gender/facts, ambiguity and invalid English gold. Material/invalid in both audits => global exclusion for that item. One material flag alone => **unresolved conflict** and publication block, never a silent all-model drop. A score grader's *own* `gold_uncertain` applies only to that candidate translation; it is not a gold-audit vote. Without two fully completed independent auditors, publication is blocked.
2. **Grading:** adequacy 0–4 + pragmatics/voice 0–4 + English fluency 0–2. Explicit refusals, self-censorship, hallucinated referents, hard negation, speaker mistakes, uncorrected source hook noise are recorded independently. Accept stylistically faithful variants, omitted Japanese subjects and deliberate fragments. Standard blind pass omits editorial trap notes to avoid teaching the answer. The candidate's identity is withheld from grading prompts. Optional annotated adjudication is separate, not quietly used as the primary score.

The graders require calibration on known-error swapped A/B pairs before even an AI-audited draft ranking is allowed. The fixtures are authored and are not independent ground truth; audit drift with a second judge and require robust agreement. An external human linguist is not assumed to be available for 25,000 decisions. Do not claim one premium judge is superior based on price alone. Neither provider has been evaluated in this working container.

## Statistical correctness

- A published **draft** line ranking requires judge calibration, complete independent gold audits with no unresolved one-sided material flags, >=95% item coverage and >=100 independently scored difficulty-2–5 items, plus pinned GGUF revision and successful five-case canary metadata for every counted score. Scores based on fewer cases are diagnostic. **Scenes cannot produce any publishable rankings from this v4 corpus**: there are only 25 eval scenes and the evidence floor is 60.
- Global quarantine uses only **two-auditor, two-provider** source-gold assessment, never the union of all candidate judgments. A 2% false-positive per-candidate flag over 50 candidates would otherwise globally discard about 64% of the corpus.
- Compare models on the **same cases** with paired item-bootstrap `delta(A−B)` and 95% interval. This is more informative than overlapping independent confidence intervals. No judge-bias correction or multiple-comparisons correction is inferred. Default comparisons are neighboring scored arms to avoid >1,000 × 2,000 bootstrap samples; `--compare-pairs all` is explicit.
- Context `delta(context−bare)` compares the *same run_id*, current gold SHA, judge model and scene ID. It is a **diagnostic**, not a 25-case proof that context does/doesn't help.
- Every record is bound to immutable source/gold digests; changing the Japanese, reference, previous lines or metadata changes the digest and invalidates prior judgments. No mixed-vintage leaderboards. Regenerate from source JSONL and re-audit after gold changes.
- Report actual weights/quant, generator, tokenizer/template, reasoning state, tokens per second, latency, refusal/omission counts and observed memory. Do not confuse GGUF file size with Deck VRAM/RAM fit. Unknown or unsupported GGUF runtime → not runnable, **not** a score of zero.

## Model-selection scope

50 slots, total params >=0.6B <=35B. Distinguish training publisher from GGUF converter, publicly documented substantial Japanese adaptation from light third-party tunes, plus narrow VN translation exceptions. Only current release per family/size barring explicit original-base controls. At least Q4/Q5 recommended publisher quant first, Q6/Q8 variants optional after independent attestation. Specialist model prompts must use documented formats, including VNTL completion; translated whole-scene support has a canary gate. In `rinna-llama-3-youko-8b`, non-chat base prompting is a **control diagnostic**, not an apples-to-apples user-facing model ranking. Translation models and judges have **zero empirical results** in this package.

## Falsification and scope of claims

- If references have sustained auditor disagreements or model rankings flip with reasonable alternate translations, don't publish relative quality.
- If models fail the native-format five-case canary or generate unclosed thoughts, don't rank their incomplete output.
- If judge calibration has poor swapped-order stability, use only qualitative error examples until resolved.
- A context benefit claim requires same-case paired evaluation and expanded context-dependent targets; 25 scenes are insufficient to rule out realistic gains.
- A VN-level recommendation requires more genuine discourse, longer narration and messy source artifacts, plus memory/latency data in actual use. Avoid building additional prose fixtures **before** the first six-model pilot reveals whether the current test separates plausible contenders.

See `README.md` for commands and `CATALOG.md` for the actual model/quant list.
