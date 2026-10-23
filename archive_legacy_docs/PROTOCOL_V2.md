# OtakuBench v2 evaluation protocol — provisional, adversarial, auditable

## Question the benchmark is allowed to answer

Within tested hardware and identical quant/model settings: which GGUF translates these specifically authored Japanese lines/scenes more faithfully, naturally, and promptly, with fewer refusals? Until native-language validation or independent demonstrations exist, **do not generalize to a definitive ranking of authentic copyrighted visual novels.**

### Dataset arms

| Arm | Instances | Inputs | Outputs/scoring | Intended metric |
| --- | ---: | --- | --- | --- |
| L250-bare | 250 | Japanese line only | One English translation | 0-10 semantic/pragmatic rubric, category errors |
| P31-bare | 31 | Target Japanese line only | Target translation | Baseline without history |
| P31-context | 31 | Actual preceding Japanese dialogue + target | Target translation only | Coreference, subtext, social markers |
| P31-full | 31 | Entire 3+ line scene | Full English scene with tags/line boundaries | Continuity, term/speaker preservation, completeness |

Splits are frozen: L250 = dev50/eval200, P31=dev6/eval25. The primary L250 eval score excludes 40 trivial difficulty-1 sanity items, leaving 160 potential hard-core cases; don't use dev to claim final performance. Don't mix arms, quantizations or reasoning toggles in the same leaderboard. Expose per-item outputs and raw completions, no hidden cleanup.

### Judge rubric

- Adequacy: 0–4; semantic fidelity, quantifiers, polarity, negation, temporal/aspectual scope, referents.
- Pragmatics/voice: 0–4; idioms, keigo, speech persona, indirect refusals, sarcasm, humour, deliberate ambiguity.
- Fluency/localization: 0–2; natural English, sensible dialogue and formatting. Allow intentional fragmentary English.
- Refusal or substantive censoring is an independent failure event; do not let smooth English mask it.
- Gold uncertainty: mark any dubious Japanese, perspective, or reference; exclude that item across *all* compared models before ranking (common-core policy).
- Hard audit flags: NEG / AGENT / ASPECT / MOD / IDIOM / VOICE / KEIGO / IMPL / CULT / HUMOUR / ADD / OMIT / REFUSAL / TERMINOLOGY / FORMAT / AMBIGUITY.

A reference translation is a *comparison aid*, not an unalterable exact match. Judge does not see authored trap notes on primary pass. All model identities are anonymous to the grader; inferential arms remain traceable by `run_id` for aggregation.

### Judge qualification without humans

0. Before ranking, use `audit_gold.py` with both independent bilingual judges to inspect all 281 references; any material/invalid finding is quarantined across candidates until defensible correction. AI agreement is still **not** human certification.
1. 24 authored *meaning-changing* translation errors × both A/B orders = 48 trials, simultaneously for each judge with prompts devoid of answer hints. Score consistency vs expected semantic reading; reject fewer than 90% correct and fewer than 85% both-order correctness. These thresholds are heuristics, not proof of quality.
2. Test 50–100 genuine model outputs per judge, score both models twice on 20 cases, compare paired discrepancies, direction of ranking difference, reference-favoring bias and hallucinated specificity. This is an experiment plan, **not a completed result**.
3. If pass: Sol as main / Opus as secondary *subject to measured actual cost*. On failure, don't publish leaderboard; adjust prompt/rubric and re-run calibration with version changes. Calibration failures on the same authored anchors cannot be tuned away silently—version the fixtures.
4. Secondary judge examines under ~15% of outputs: gold_uncertain, low-confidence, refusals, ambiguous/mid-range scores, high-impact errors. Judge disagreements stay visible, and rankings should be robust to worst-case disputed-score substitutions. The provided tools compute deltas; manual review is not assumed.
5. At most a **calibrated draft leaderboard**. Even two agreeing proprietary LLM judges are not equivalent to native human validation; avoid expert-grade claims.

### Model eligibility

Original lab-trained checkpoint or major **lab-published** new training/adaptation. Original 0.6–35B total parameter budget; third-party GGUF conversions fine, third-party minimal LoRA fine-tunes not eligible. Some Japanese translation specialists are lab fine-tunes trained for a new task; they are not excluded on the simplistic grounds that they share an architecture with a base model. Skip any not supported by current validated GGUF runtime or use an explicitly separate non-GGUF arm, and label why.

### Deployment scenarios

- Deck: actual installed/available shared RAM, measured KV+weights, process start time, generation time, median/p90/p99 time per target, peak RSS/VRAM. The catalog size flag is a **candidate filter only**.
- LAN: no Deck limit; local 24GB and 32GB hardware are valid. Keep scoring distinct from device-specific latency.
- At 2–9B, Q6/Q8 challenger quants as separate controlled arms. The reference policy Q4 is about common downloads, not maximizing quality.
- Thinking-on and thinking-off separate; strict fixed generation cap and record finish reason. A timeout, unclosed thought, a refusal or blank text is **not** a translation.

### Falsification criteria

- Context-aware arm offers no measurable improvement over bare *for the same 31 scenes* after a sufficient expansion: preceding dialogue may not test meaningful contextual inference.
- Judge reversal from valid Japanese alternates changes top-10 rank ordering materially: scoring is gold-reference-biased.
- Quality ordering flips between Sol and Opus on common items or many `gold_uncertain`: withhold ranking.
- Specialist template cannot return faithful multi-line translation or violates required tags: keep out of relevant arm, don't mark the whole model as low intelligence.
- Deck quant fails to load or exceeds practical RAM: cannot claim viable based on 9GB disk size.

### Planned extension before *real* VN leaderboard

At least 100 additional discourse/multi-line passages with 10+ longer paragraphs and repeated named entities; at least 30 independently captured OCR/text-hook noisy samples (with redistributable provenance); systematic contradiction/retcon/multi-route history; >20 clearly lawful non-explicit mature/violent snippets for refusal tracking; blind independent judge evaluation of these with stable item IDs. These are future gates, not falsely represented as already implemented.
