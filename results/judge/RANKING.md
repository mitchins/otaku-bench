# Ranking

| # | Model | Hard lines /10 | Full scenes /10 | Bad lines (≤5) | Seconds per line | VRAM GB | Most common slips |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | **Qwen3.6-35B-A3B** | 9.37 | 9.35 | 6 | 0.42 | 20.2 | voice, idioms, omissions |

Being judged: Gemma 4 26B-A4B IT (140/200 lines).

## By category

Share of the 20 eval lines in each category translated well (9 or 10 out of 10). With 20 lines per cell, differences under about 20 points are noise.

| Model | Idioms & proverbs | Wordplay & irony | Dialect & voice | Politeness (keigo) | Indirect speech | Emotional subtext | Omitted subjects | Culture & institutions | Literary style | Onomatopoeia |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.6-35B-A3B | 60% | 70% | 80% | 95% | 95% | 90% | 90% | 80% | 80% | 95% |

Scores are out of 10: adequacy 0–4, pragmatics and voice 0–4, fluency 0–2, judged by GPT-6.1 Sol. A line the model failed to produce scores 0. Speed is the median time to finish a line with 6 lines of history on an RTX 3090.
