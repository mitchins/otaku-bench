# Method

## Per model, one at a time

1. **Fit check.** If file size plus 1.8 GB of headroom exceeds free VRAM, the model is deferred to a larger GPU without being downloaded.
2. **Download** the GGUF at a pinned Hugging Face revision, then start `llama-server -ngl 99 -c 2048 --reasoning off`.
3. **Canary.** Five fixed lines must each produce a visible translation.
4. **Latency gate and history sweep.** 12 scenes × 0, 3, 6, 12 and 24 lines of history. The gate is at 6 lines: median ≤ 2 s and p90 ≤ 3 s for the whole line.
5. **Quality arms.** 250 bare lines, plus the 31 scenes bare, with context, and in full.

## Prompts: each model's native format

Every model family gets the prompt format its model card documents. Building these correctly turned out to matter more than expected:

- **Dedicated translators translate everything they're given.** CAT-Translate and HY-MT originally received English instructions ("Previous dialogue (for context only)…") inside the text to translate, and translated those too. Now they get only Japanese.
- **CAT-Translate** documents no way to pass context, so it gets the target line alone.
- **HY-MT1.5**'s official contextual template is Chinese-only. With 英语 as the target, the 1.8B answered in Chinese on 12 of 31 scenes. An English version of the same instruction gives 0 of 31.
- **TranslateGemma**'s chat template takes language codes in structured content parts, which llama-server drops, so it rendered "English (en-GB) to English (en-GB)". The harness renders the template's text branch by hand for `ja` → `en` and uses raw completion.
- **Third-party GGUFs** sometimes don't mark EOS as a special token, so a literal `</s>` ends every output. The harness strips it from translations and keeps it in the raw response.

## Judge

GPT-6.1 Sol scores each translation against a reference, which is treated as *one* valid reading, not the answer:

| Axis | Range | Meaning |
|---|---|---|
| Adequacy | 0–4 | Is the meaning right? |
| Pragmatics | 0–4 | Intent, voice, politeness, implication, humour |
| Fluency | 0–2 | Natural English |

It also returns flags (`IDIOM`, `NEG`, `AGENT`, `KEIGO`, `OMIT`, `ADD`, `REFUSAL` and others) and a one-line justification. It never sees the model's name. Items a model failed to produce score 0, so dropping hard lines can't help a model's rank.

**Planned:** once the board and both unreleased slices are fully scored, GPT-6 Astra (in the same free tier) will be compared as a judge on the stored outputs. The judge only changes if that comparison favours it.

The context-scene arm is too easy for the top models (Qwen3.6-35B-A3B scored 10/10 on 28 of 31), so it is not used for ranking. The 31 full scenes are reported beside each model.

## Ranking: Pass % on three slices

Each slice is reported as a **Pass %**, the share of its lines translated in full:

| Slice | Lines | A line passes when |
|---|---|---|
| Standard | 200 eval lines | Meaning 4/4, pragmatics 4/4, fluency at least 1/2, and no commentary appended |
| Hard (unreleased) | 167 scored lines from 57 scenes | Every named check on the line passes. *Uncertain* is not a pass; a refusal fails |
| Adult (unreleased) | 72 scored lines | Every named check passes, counted only among lines the model did not refuse |

**Overview** is the plain mean of Standard and Hard, equal weight per slice, so the 200 Standard lines don't outweigh the Hard slice. A model gets an Overview only when both are fully judged; a missing slice is never averaged around.

**Adult** is shown and sortable but kept out of the Overview. A refusal there is a policy choice, not a translation error, so the slice reports two numbers rather than one: the pass rate among lines the model translated, and the refusal rate on lines that should be translated. Lines that must *not* be sexualised are checked too, and counted in each model's details.

If the judge itself declines to score a line, that line is left out of the denominator and counted, never imputed. Intervals are 95% bootstrap intervals over lines (Standard: resampled within its ten challenge categories).

## Versions

OtakuBench is in **Preview**: slices, checks and the pass rule may still change, and ranks can move when they do. **1.0** freezes the method, the slices and the judge. Later changes ship as **1.1**, **1.2** and so on; each version's results are kept so models can be compared within a version.

## Output compliance

A screen translator's output is shown to the reader as it is, so some outcomes are decided mechanically, identically for every model, before or instead of the judge (`tools/mechanical.py`). The policy was frozen on 2026-10-24 and checked for false positives against every stored output.

| Outcome | How it's detected | Treatment |
|---|---|---|
| No usable output | Error, token cap, timeout, unclosed thinking, or empty text | **0**, never sent to the judge |
| Source returned untranslated | Equal to the source after Unicode normalisation, with whitespace and speaker tags removed | **0**, never sent to the judge |
| Partly untranslated, or Japanese terms kept | Anything short of an exact echo | Judged normally |
| Commentary | An alternative, note or "literally" gloss appended to the translation | Flagged |
| Format | Speaker labels rewritten as `Name:` / `**Name:**`, or markdown emphasis | Flagged |
| Wrong meaning, lost irony, added content | The judge | Judged normally |

The automatic zeros are already in the scores, and they count toward a model being fully judged. Flags don't change the scores out of 10. For Pass %, **commentary fails the line**; formatting is recorded only. Every automatic zero and flag is saved per item under `results/judge/mechanical/`. Original translations and judgments are never modified.
