# Ranking

| # | Model | Hard lines /10 | Full scenes /10 | Bad lines (≤5) | Seconds per line | VRAM GB | Most common slips |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | **Gemma 4 26B-A4B IT** | 9.73 | 9.55 | 1 | 0.28 | 16.6 | voice, who did what, idioms |
| 2 | **Qwen3.8-27B** | 9.57 | 9.29 | 3 | 1.17 | 15.1 | voice, idioms, implication |
| 3 | **Qwen3.6-35B-A3B** | 9.37 | 9.35 | 6 | 0.42 | 20.2 | voice, idioms, omissions |

Being judged: Gemma 4 31B IT (81/200 lines).

## By category

Share of the 20 eval lines in each category translated well (9 or 10 out of 10). With 20 lines per cell, differences under about 20 points are noise.

| Model | Idioms & proverbs | Wordplay & irony | Dialect & voice | Politeness (keigo) | Indirect speech | Emotional subtext | Omitted subjects | Culture & institutions | Literary style | Onomatopoeia |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gemma 4 26B-A4B IT | 75% | 75% | 95% | 100% | 100% | 100% | 95% | 95% | 100% | 90% |
| Qwen3.8-27B | 60% | 80% | 85% | 95% | 100% | 85% | 95% | 75% | 95% | 100% |
| Qwen3.6-35B-A3B | 60% | 70% | 80% | 95% | 95% | 90% | 90% | 80% | 80% | 95% |

## Output compliance

Decided mechanically, identically for every model. **Automatic zeros** are already in the scores above: no usable output, or the source returned untranslated. **Flags** are recorded only and do not change the score yet: *commentary* = an alternative, note or literal gloss appended to the translation; *format* = speaker labels rewritten as `Name:` or markdown emphasis.

| Model | Zero: no output | Zero: untranslated | Commentary | Format |
|---|---:|---:|---:|---:|
| Gemma 4 26B-A4B IT | 0 | 0 | 0 | 1 |
| Qwen3.8-27B | 0 | 0 | 0 | 0 |
| Qwen3.6-35B-A3B | 0 | 0 | 0 | 2 |

Scores are out of 10: adequacy 0–4, pragmatics and voice 0–4, fluency 0–2, judged by GPT-6.1 Sol. A line the model failed to produce scores 0. Speed is the median time to finish a line with 6 lines of history on an RTX 3090.
