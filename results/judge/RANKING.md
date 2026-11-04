# Ranking (Preview)

Sorted by **Standard**. Pass % is the share of lines translated in full: meaning and intent intact, readable English, nothing added. Overview is the plain mean of Standard and Hard. Adult is reported separately: pass % among the lines the model did not refuse, with the refusal rate beside it. A dash means not judged yet.

| # | Model | Overview % | Standard % | Hard % | Adult % (not refused) | Adult refused % | Standard /10 | Full scenes /10 | Bad lines (≤5) | Seconds per line | VRAM GB | Most common slips |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | **Claude Sonnet 5.5 (cloud)** | — | 91.5 | — | 86.4 | 9.5 | 9.84 | 9.84 | 0 | — | — | ambiguity, additions, voice |
| 2 | **Gemma 4 31B IT (Q4_K_M)** | — | 91.0 | — | 81.9 | 0.0 | 9.82 | 9.23 | 1 | 1.09 | 20.0 | voice, implication, ambiguity |
| 3 | **Gemma 4 31B IT (Q5_K_M)** | — | 91.0 | — | — | — | 9.85 | 9.29 | 0 | 1.21 | 22.9 | voice, ambiguity, terms |
| 4 | **Claude Haiku 5.5 (cloud)** | — | 89.0 | — | 83.3 | 0.0 | 9.77 | 9.26 | 0 | — | — | idioms, ambiguity, additions |
| 5 | **Gemma 4 26B-A4B IT (UD-Q4_K_M)** | — | 86.5 | — | 75.0 | 0.0 | 9.73 | 9.55 | 1 | 0.28 | 16.6 | voice, who did what, idioms |
| 6 | **Gemma 4 12B IT (UD-Q4_K_XL)** | — | 85.5 | — | 75.0 | 0.0 | 9.65 | 9.45 | 2 | 0.42 | 7.8 | idioms, voice, omissions |
| 7 | **Gemma 4 26B-A4B heretic JP-pruned 120e (Q4_0)** | — | 85.5 | — | 68.1 | 0.0 | 9.64 | 9.16 | 3 | 0.27 | 13.3 | who did what, idioms, ambiguity |
| 8 | **Gemini 3.5 Flash-Lite (cloud)\*** | — | 84.5 | — | 77.8 | 0.0 | 9.72 | 9.48 | 0 | — | — | additions, ambiguity, idioms |
| 9 | **Qwen3.8-27B (UD-Q6_K_L)** | — | 83.5 | — | — | — | 9.62 | 9.19 | 2 | 1.33 | 22.0 | voice, idioms, omissions |
| 10 | **Qwen3.8-27B (UD-Q4_K_M)** | — | 81.0 | — | 75.0 | 0.0 | 9.57 | 9.29 | 3 | 1.17 | 15.1 | voice, idioms, implication |
| 11 | **Hy-MT2-30B-A3B (Q4_K_M)** | — | 76.5 | — | 72.2 | 0.0 | 9.52 | 9.29 | 2 | 0.17 | 17.4 | voice, ambiguity, idioms |
| 12 | **Ornith-1.5-35B-A3B (Q4_K_M)** | — | 76.0 | — | 73.6 | 0.0 | 9.40 | 9.29 | 6 | 0.41 | 20.2 | idioms, additions, voice |
| 13 | **Gemma 4 E4B IT (UD-Q4_K_XL)** | — | 75.5 | — | 68.1 | 0.0 | 9.30 | 9.13 | 7 | 0.17 | 3.5 | idioms, voice, who did what |
| 14 | **Qwen3.6-35B-A3B (Q4_K_M)** | — | 75.0 | — | 75.0 | 0.0 | 9.37 | 9.35 | 6 | 0.42 | 20.2 | voice, idioms, omissions |
| 15 | **Ternary-Bonsai-2-27B (PQ2_0)** | — | 72.0 | — | 58.3 | 0.0 | 9.18 | 8.87 | 8 | 0.98 | 7.1 | idioms, terms, voice |
| 16 | **TranslateGemma 27B IT (Q4_K_M)** | — | 71.0 | — | 44.4 | 0.0 | 9.33 | 9.39 | 3 | 0.57 | 16.7 | voice, idioms, omissions |
| 17 | **TranslateGemma 12B IT (Q4_K_M)** | — | 67.5 | — | 47.2 | 0.0 | 9.20 | 8.87 | 6 | 0.30 | 7.8 | voice, idioms, additions |
| 18 | **Gemma 4 26B-A4B heretic JP-pruned 72e (Q4_0)** | — | 66.5 | — | — | — | 8.97 | 7.94 | 10 | 0.26 | 8.8 | voice, idioms, additions |
| 19 | **Hy-MT2-7B (Q4_K_M)** | — | 66.5 | — | 68.1 | 0.0 | 9.21 | 8.74 | 5 | 0.16 | 5.0 | idioms, voice, terms |
| 20 | **Nemotron 3.5 Bolt 74B-A9B 24GB (IQ2_XXS)** | — | 66.5 | — | 52.8 | 0.0 | 9.00 | 9.16 | 10 | 0.94 | 20.6 | idioms, voice, modality |
| 21 | **Sugoi-14B-Ultra (Q4_K_M)** | — | 66.5 | — | 70.8 | 0.0 | 9.05 | 8.90 | 9 | 0.30 | 8.8 | voice, idioms, additions |
| 22 | **Shisa-v2.1-qwen3-8B (Q4_K_M)** | — | 65.0 | — | — | — | 9.04 | 8.16 | 12 | 0.17 | 5.0 | additions, idioms, omissions |
| 23 | **Gemma 4 E2B IT (UD-Q4_K_XL)** | — | 59.0 | — | 61.1 | 0.0 | 8.70 | 8.77 | 18 | 0.11 | 1.9 | idioms, voice, modality |
| 24 | **Qwen3-4B-Instruct-2507 (Q4_K_M)** | — | 50.5 | — | — | — | 8.26 | 7.90 | 28 | 0.12 | 3.0 | idioms, voice, who did what |
| 25 | **Hy-MT2-1.8B-JP-Manga-v5 (Q4_K_M)** | — | 49.0 | — | 59.7 | 0.0 | 8.22 | 7.26 | 28 | 0.06 | 1.5 | idioms, additions, voice |
| 26 | **Flint 40B-A2.5B (IQ4_XS, empty-think)** | — | 47.0 | — | 40.3 | 0.0 | 7.88 | 7.61 | 37 | 0.27 | 21.1 | idioms, who did what, voice |
| 27 | **gpt-oss-20b (Q4_K_M, effort-low)** | — | 47.0 | — | — | — | 7.81 | 8.26 | 38 | 0.49 | 11.0 | idioms, voice, terms |
| 28 | **LFM2.5-24B-A2B (Q4_K_M, empty-think)** | — | 46.5 | — | 45.8 | 0.0 | 8.06 | 7.45 | 28 | 0.16 | 14.7 | idioms, voice, who did what |
| 29 | **Hy-MT2-1.8B (Q4_K_M)** | — | 39.0 | — | 43.1 | 0.0 | 7.99 | 7.35 | 33 | 0.07 | 1.5 | voice, idioms, who did what |

\* Gemini: full scenes use only the first sentence of the system prompt; with the full prompt it returns some scenes untranslated.

Being judged: Gemini 3.8 Flash (cloud) (165/200 lines), Qwen3.5-4B (Q4_K_M) (131/200 lines).

## By category

Share of the 20 eval lines in each category translated well (9 or 10 out of 10). With 20 lines per cell, differences under about 20 points are noise.

| Model | Idioms & proverbs | Wordplay & irony | Dialect & voice | Politeness (keigo) | Indirect speech | Emotional subtext | Omitted subjects | Culture & institutions | Literary style | Onomatopoeia |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Claude Sonnet 5.5 (cloud) | 95% | 85% | 95% | 100% | 100% | 95% | 90% | 95% | 100% | 100% |
| Gemma 4 31B IT (Q4_K_M) | 85% | 100% | 95% | 100% | 100% | 95% | 100% | 90% | 95% | 100% |
| Gemma 4 31B IT (Q5_K_M) | 80% | 95% | 100% | 100% | 100% | 95% | 100% | 100% | 95% | 95% |
| Claude Haiku 5.5 (cloud) | 90% | 95% | 95% | 95% | 100% | 85% | 90% | 90% | 100% | 90% |
| Gemma 4 26B-A4B IT (UD-Q4_K_M) | 75% | 75% | 95% | 100% | 100% | 100% | 95% | 95% | 100% | 90% |
| Gemma 4 12B IT (UD-Q4_K_XL) | 90% | 75% | 90% | 100% | 100% | 100% | 95% | 80% | 90% | 95% |
| Gemma 4 26B-A4B heretic JP-pruned 120e (Q4_0) | 75% | 80% | 100% | 95% | 100% | 90% | 95% | 90% | 85% | 95% |
| Gemini 3.5 Flash-Lite (cloud)\* | 90% | 70% | 100% | 90% | 100% | 100% | 100% | 95% | 90% | 95% |
| Qwen3.8-27B (UD-Q6_K_L) | 65% | 80% | 85% | 95% | 100% | 85% | 95% | 75% | 95% | 100% |
| Qwen3.8-27B (UD-Q4_K_M) | 60% | 80% | 85% | 95% | 100% | 85% | 95% | 75% | 95% | 100% |
| Hy-MT2-30B-A3B (Q4_K_M) | 85% | 65% | 80% | 95% | 100% | 85% | 95% | 95% | 90% | 90% |
| Ornith-1.5-35B-A3B (Q4_K_M) | 65% | 65% | 85% | 100% | 85% | 95% | 75% | 85% | 90% | 100% |
| Gemma 4 E4B IT (UD-Q4_K_XL) | 60% | 70% | 75% | 90% | 90% | 85% | 85% | 80% | 90% | 90% |
| Qwen3.6-35B-A3B (Q4_K_M) | 60% | 70% | 80% | 95% | 95% | 90% | 90% | 80% | 80% | 95% |
| Ternary-Bonsai-2-27B (PQ2_0) | 50% | 80% | 80% | 85% | 80% | 90% | 85% | 65% | 85% | 80% |
| TranslateGemma 27B IT (Q4_K_M) | 65% | 65% | 75% | 90% | 85% | 85% | 80% | 85% | 85% | 90% |
| TranslateGemma 12B IT (Q4_K_M) | 55% | 60% | 60% | 100% | 80% | 75% | 80% | 70% | 95% | 85% |
| Gemma 4 26B-A4B heretic JP-pruned 72e (Q4_0) | 60% | 65% | 50% | 80% | 85% | 80% | 80% | 80% | 80% | 80% |
| Hy-MT2-7B (Q4_K_M) | 55% | 70% | 85% | 85% | 95% | 85% | 85% | 70% | 85% | 95% |
| Nemotron 3.5 Bolt 74B-A9B 24GB (IQ2_XXS) | 40% | 60% | 50% | 85% | 85% | 80% | 90% | 75% | 75% | 85% |
| Sugoi-14B-Ultra (Q4_K_M) | 55% | 65% | 65% | 90% | 85% | 80% | 75% | 85% | 70% | 85% |
| Shisa-v2.1-qwen3-8B (Q4_K_M) | 45% | 45% | 75% | 95% | 85% | 75% | 95% | 55% | 80% | 90% |
| Gemma 4 E2B IT (UD-Q4_K_XL) | 25% | 70% | 55% | 90% | 80% | 75% | 60% | 60% | 80% | 65% |
| Qwen3-4B-Instruct-2507 (Q4_K_M) | 20% | 50% | 55% | 65% | 60% | 55% | 70% | 70% | 75% | 70% |
| Hy-MT2-1.8B-JP-Manga-v5 (Q4_K_M) | 25% | 50% | 60% | 55% | 60% | 55% | 95% | 40% | 55% | 75% |
| Flint 40B-A2.5B (IQ4_XS, empty-think) | 20% | 35% | 55% | 60% | 55% | 55% | 70% | 40% | 55% | 60% |
| gpt-oss-20b (Q4_K_M, effort-low) | 20% | 50% | 30% | 50% | 65% | 55% | 80% | 35% | 80% | 60% |
| LFM2.5-24B-A2B (Q4_K_M, empty-think) | 15% | 45% | 55% | 60% | 60% | 60% | 70% | 35% | 70% | 75% |
| Hy-MT2-1.8B (Q4_K_M) | 15% | 35% | 55% | 60% | 50% | 65% | 70% | 40% | 60% | 70% |

## Output compliance

Decided mechanically, identically for every model. **Automatic zeros** are already in the scores above: no usable output, or the source returned untranslated. **Flags** do not change the /10 scores; *commentary* fails a line for Pass %: *commentary* = an alternative, note or literal gloss appended to the translation; *format* = speaker labels rewritten as `Name:` or markdown emphasis.

| Model | Zero: no output | Zero: untranslated | Commentary | Format |
|---|---:|---:|---:|---:|
| Claude Sonnet 5.5 (cloud) | 0 | 0 | 0 | 4 |
| Gemma 4 31B IT (Q4_K_M) | 0 | 0 | 0 | 0 |
| Gemma 4 31B IT (Q5_K_M) | 0 | 0 | 0 | 0 |
| Claude Haiku 5.5 (cloud) | 0 | 0 | 0 | 1 |
| Gemma 4 26B-A4B IT (UD-Q4_K_M) | 0 | 0 | 0 | 1 |
| Gemma 4 12B IT (UD-Q4_K_XL) | 0 | 0 | 0 | 0 |
| Gemma 4 26B-A4B heretic JP-pruned 120e (Q4_0) | 0 | 0 | 0 | 2 |
| Gemini 3.5 Flash-Lite (cloud)\* | 0 | 0 | 1 | 5 |
| Qwen3.8-27B (UD-Q6_K_L) | 0 | 0 | 0 | 0 |
| Qwen3.8-27B (UD-Q4_K_M) | 0 | 0 | 0 | 0 |
| Hy-MT2-30B-A3B (Q4_K_M) | 0 | 0 | 0 | 0 |
| Ornith-1.5-35B-A3B (Q4_K_M) | 0 | 0 | 0 | 9 |
| Gemma 4 E4B IT (UD-Q4_K_XL) | 0 | 0 | 0 | 0 |
| Qwen3.6-35B-A3B (Q4_K_M) | 0 | 0 | 0 | 2 |
| Ternary-Bonsai-2-27B (PQ2_0) | 0 | 0 | 0 | 1 |
| TranslateGemma 27B IT (Q4_K_M) | 0 | 0 | 0 | 0 |
| TranslateGemma 12B IT (Q4_K_M) | 0 | 0 | 0 | 1 |
| Gemma 4 26B-A4B heretic JP-pruned 72e (Q4_0) | 0 | 0 | 0 | 1 |
| Hy-MT2-7B (Q4_K_M) | 0 | 0 | 0 | 0 |
| Nemotron 3.5 Bolt 74B-A9B 24GB (IQ2_XXS) | 0 | 0 | 0 | 0 |
| Sugoi-14B-Ultra (Q4_K_M) | 0 | 0 | 1 | 0 |
| Shisa-v2.1-qwen3-8B (Q4_K_M) | 0 | 0 | 0 | 33 |
| Gemma 4 E2B IT (UD-Q4_K_XL) | 0 | 0 | 0 | 0 |
| Qwen3-4B-Instruct-2507 (Q4_K_M) | 0 | 0 | 0 | 0 |
| Hy-MT2-1.8B-JP-Manga-v5 (Q4_K_M) | 0 | 0 | 0 | 6 |
| Flint 40B-A2.5B (IQ4_XS, empty-think) | 2 | 0 | 1 | 0 |
| gpt-oss-20b (Q4_K_M, effort-low) | 1 | 0 | 0 | 2 |
| LFM2.5-24B-A2B (Q4_K_M, empty-think) | 1 | 0 | 0 | 2 |
| Hy-MT2-1.8B (Q4_K_M) | 0 | 0 | 0 | 0 |

Standard: 200 eval lines judged by GPT-6.1 Sol on adequacy 0–4, pragmatics and voice 0–4, fluency 0–2; a line passes at 4, 4 and at least 1 with no commentary appended. Hard and Adult: each line has named checks, and it passes when every check passes (uncertain is not a pass). A line the model failed to produce fails (scores 0 out of 10). Speed is the median time to finish a line with 6 lines of history on an RTX 3090.
