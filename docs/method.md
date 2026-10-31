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

The context-scene arm is too easy for the top models (Qwen3.6-35B-A3B scored 10/10 on 28 of 31), so ranking uses the **200 eval lines** and the **31 full scenes**.

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

The automatic zeros are already in the scores, and they count toward a model being fully judged. Flags are recorded in the Full table but **don't change any score yet**: a separate screen-ready score is planned, with a hard failure for commentary and a small fixed penalty for formatting. Every automatic zero and flag is saved per item under `results/judge/mechanical/`. Original translations and judgments are never modified.
