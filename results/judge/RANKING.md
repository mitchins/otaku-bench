# Ranking

| # | Model | Hard lines /10 | Full scenes /10 | Bad lines (≤5) | Seconds per line | VRAM GB | Most common slips |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | **Gemma 4 31B IT (Q5_K_M)** | 9.85 | 9.29 | 0 | 1.21 | 22.9 | voice, ambiguity, terms |
| 2 | **Gemma 4 31B IT** | 9.82 | 9.23 | 1 | 1.09 | 20.0 | voice, implication, ambiguity |
| 3 | **Gemma 4 26B-A4B IT** | 9.73 | 9.55 | 1 | 0.28 | 16.6 | voice, who did what, idioms |
| 4 | **Gemini 3.5 Flash-Lite (cloud)\*** | 9.72 | 9.48 | 0 | — | — | additions, ambiguity, idioms |
| 5 | **Gemma 4 12B IT** | 9.65 | 9.45 | 2 | 0.42 | 7.8 | idioms, voice, omissions |
| 6 | **Qwen3.8-27B (UD-Q6_K_L)** | 9.62 | 9.19 | 2 | 1.33 | 22.0 | voice, idioms, omissions |
| 7 | **Qwen3.8-27B** | 9.57 | 9.29 | 3 | 1.17 | 15.1 | voice, idioms, implication |
| 8 | **Hy-MT2-30B-A3B** | 9.52 | 9.29 | 2 | 0.17 | 17.4 | voice, ambiguity, idioms |
| 9 | **Ornith-1.5-35B-A3B** | 9.40 | 9.29 | 6 | 0.41 | 20.2 | idioms, additions, voice |
| 10 | **Qwen3.6-35B-A3B** | 9.37 | 9.35 | 6 | 0.42 | 20.2 | voice, idioms, omissions |
| 11 | **TranslateGemma 27B IT** | 9.33 | 9.39 | 3 | 0.57 | 16.7 | voice, idioms, omissions |
| 12 | **Gemma 4 E4B IT** | 9.30 | 9.13 | 7 | 0.17 | 3.5 | idioms, voice, who did what |
| 13 | **Hy-MT2-7B** | 9.21 | 8.74 | 5 | 0.16 | 5.0 | idioms, voice, terms |
| 14 | **TranslateGemma 12B IT** | 9.20 | 8.87 | 6 | 0.30 | 7.8 | voice, idioms, additions |
| 15 | **Sugoi-14B-Ultra** | 9.05 | 8.90 | 9 | 0.30 | 8.8 | voice, idioms, additions |
| 16 | **Gemma 4 E2B IT** | 8.70 | 8.77 | 18 | 0.11 | 1.9 | idioms, voice, modality |
| 17 | **LFM2.5-24B-A2B (empty-think)** | 8.06 | 7.45 | 28 | 0.16 | 14.7 | idioms, voice, who did what |
| 18 | **Flint 40B-A2.5B (empty-think)** | 7.88 | 7.61 | 37 | 0.27 | 21.1 | idioms, who did what, voice |

\* Gemini: full scenes use only the first sentence of the system prompt; with the full prompt it returns some scenes untranslated.

Being judged: Hy-MT2-1.8B (0/200 lines).

## By category

Share of the 20 eval lines in each category translated well (9 or 10 out of 10). With 20 lines per cell, differences under about 20 points are noise.

| Model | Idioms & proverbs | Wordplay & irony | Dialect & voice | Politeness (keigo) | Indirect speech | Emotional subtext | Omitted subjects | Culture & institutions | Literary style | Onomatopoeia |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gemma 4 31B IT (Q5_K_M) | 80% | 95% | 100% | 100% | 100% | 95% | 100% | 100% | 95% | 95% |
| Gemma 4 31B IT | 85% | 100% | 95% | 100% | 100% | 95% | 100% | 90% | 95% | 100% |
| Gemma 4 26B-A4B IT | 75% | 75% | 95% | 100% | 100% | 100% | 95% | 95% | 100% | 90% |
| Gemini 3.5 Flash-Lite (cloud)\* | 90% | 70% | 100% | 90% | 100% | 100% | 100% | 95% | 90% | 95% |
| Gemma 4 12B IT | 90% | 75% | 90% | 100% | 100% | 100% | 95% | 80% | 90% | 95% |
| Qwen3.8-27B (UD-Q6_K_L) | 65% | 80% | 85% | 95% | 100% | 85% | 95% | 75% | 95% | 100% |
| Qwen3.8-27B | 60% | 80% | 85% | 95% | 100% | 85% | 95% | 75% | 95% | 100% |
| Hy-MT2-30B-A3B | 85% | 65% | 80% | 95% | 100% | 85% | 95% | 95% | 90% | 90% |
| Ornith-1.5-35B-A3B | 65% | 65% | 85% | 100% | 85% | 95% | 75% | 85% | 90% | 100% |
| Qwen3.6-35B-A3B | 60% | 70% | 80% | 95% | 95% | 90% | 90% | 80% | 80% | 95% |
| TranslateGemma 27B IT | 65% | 65% | 75% | 90% | 85% | 85% | 80% | 85% | 85% | 90% |
| Gemma 4 E4B IT | 60% | 70% | 75% | 90% | 90% | 85% | 85% | 80% | 90% | 90% |
| Hy-MT2-7B | 55% | 70% | 85% | 85% | 95% | 85% | 85% | 70% | 85% | 95% |
| TranslateGemma 12B IT | 55% | 60% | 60% | 100% | 80% | 75% | 80% | 70% | 95% | 85% |
| Sugoi-14B-Ultra | 55% | 65% | 65% | 90% | 85% | 80% | 75% | 85% | 70% | 85% |
| Gemma 4 E2B IT | 25% | 70% | 55% | 90% | 80% | 75% | 60% | 60% | 80% | 65% |
| LFM2.5-24B-A2B (empty-think) | 15% | 45% | 55% | 60% | 60% | 60% | 70% | 35% | 70% | 75% |
| Flint 40B-A2.5B (empty-think) | 20% | 35% | 55% | 60% | 55% | 55% | 70% | 40% | 55% | 60% |

## Output compliance

Decided mechanically, identically for every model. **Automatic zeros** are already in the scores above: no usable output, or the source returned untranslated. **Flags** are recorded only and do not change the score yet: *commentary* = an alternative, note or literal gloss appended to the translation; *format* = speaker labels rewritten as `Name:` or markdown emphasis.

| Model | Zero: no output | Zero: untranslated | Commentary | Format |
|---|---:|---:|---:|---:|
| Gemma 4 31B IT (Q5_K_M) | 0 | 0 | 0 | 0 |
| Gemma 4 31B IT | 0 | 0 | 0 | 0 |
| Gemma 4 26B-A4B IT | 0 | 0 | 0 | 1 |
| Gemini 3.5 Flash-Lite (cloud)\* | 0 | 0 | 1 | 5 |
| Gemma 4 12B IT | 0 | 0 | 0 | 0 |
| Qwen3.8-27B (UD-Q6_K_L) | 0 | 0 | 0 | 0 |
| Qwen3.8-27B | 0 | 0 | 0 | 0 |
| Hy-MT2-30B-A3B | 0 | 0 | 0 | 0 |
| Ornith-1.5-35B-A3B | 0 | 0 | 0 | 9 |
| Qwen3.6-35B-A3B | 0 | 0 | 0 | 2 |
| TranslateGemma 27B IT | 0 | 0 | 0 | 0 |
| Gemma 4 E4B IT | 0 | 0 | 0 | 0 |
| Hy-MT2-7B | 0 | 0 | 0 | 0 |
| TranslateGemma 12B IT | 0 | 0 | 0 | 1 |
| Sugoi-14B-Ultra | 0 | 0 | 1 | 0 |
| Gemma 4 E2B IT | 0 | 0 | 0 | 0 |
| LFM2.5-24B-A2B (empty-think) | 1 | 0 | 0 | 2 |
| Flint 40B-A2.5B (empty-think) | 2 | 0 | 1 | 0 |

Scores are out of 10: adequacy 0–4, pragmatics and voice 0–4, fluency 0–2, judged by GPT-6.1 Sol. A line the model failed to produce scores 0. Speed is the median time to finish a line with 6 lines of history on an RTX 3090.
