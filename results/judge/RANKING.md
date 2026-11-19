# Ranking (Preview)

Sorted by **Overview**. Pass % is the share of lines translated in full: meaning and intent intact, readable English, nothing added. Overview is the plain mean of Standard and Hard. Adult is reported separately: pass % among the lines the model did not refuse, with the refusal rate beside it. A dash means not judged yet. One row per model: where several quants or variants were tested, the row shows the best-scoring build, and [All builds](#all-builds) lists the rest.

| # | Model | Overview % | Standard % | Hard % | Adult % (not refused) | Adult refused % | Standard /10 | Full scenes /10 | Bad lines (≤5) | Seconds per line | VRAM GB | Most common slips |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | **Gemini 3.8 Flash (cloud)** | 89.3 | 93.0 | 85.6 | 90.3 | 0.0 | 9.86 | 9.77 | 1 | — | — | voice, ambiguity, idioms |
| 2 | **Claude Sonnet 5.5 (cloud)** | 87.7 | 91.5 | 83.8 | 86.4 | 9.5 | 9.84 | 9.84 | 0 | — | — | ambiguity, additions, voice |
| 3 | **Gemma 4 31B IT** (QAT-Q4_0; best of 4 builds) | 86.6 | 90.0 | 83.2 | 79.2 | 0.0 | 9.78 | 9.55 | 2 | 0.91 | 18.2 | implication, wordplay, additions |
| 4 | **Claude Haiku 5.5 (cloud)** | 86.1 | 89.0 | 83.2 | 83.3 | 0.0 | 9.77 | 9.26 | 0 | — | — | idioms, ambiguity, additions |
| 5 | **Gemma 4 26B-A4B IT** (UD-Q4_K_M; best of 2 builds) | 84.0 | 86.5 | 81.4 | 75.0 | 0.0 | 9.73 | 9.55 | 1 | 0.28 | 16.6 | voice, who did what, idioms |
| 6 | **Gemma 4 12B IT** (UD-Q4_K_XL; best of 4 builds) | 81.7 | 85.5 | 77.8 | 75.0 | 0.0 | 9.65 | 9.45 | 2 | 0.42 | 7.8 | idioms, voice, omissions |
| 7 | **Qwen3.8-27B** (UD-Q6_K_L; best of 2 builds) | 81.0 | 83.5 | 78.4 | 75.0 | 0.0 | 9.62 | 9.19 | 2 | 1.33 | 22.0 | voice, idioms, omissions |
| 8 | **Gemini 3.5 Flash-Lite (cloud)\*** | 78.8 | 84.5 | 73.1 | 77.8 | 0.0 | 9.72 | 9.48 | 0 | — | — | additions, ambiguity, idioms |
| 9 | **Hy-MT2-30B-A3B** (Q4_K_M) | 76.2 | 76.5 | 76.0 | 72.2 | 0.0 | 9.52 | 9.29 | 2 | 0.17 | 17.4 | voice, ambiguity, idioms |
| 10 | **Qwen3.6-35B-A3B** (Q4_K_M) | 74.3 | 75.0 | 73.7 | 75.0 | 0.0 | 9.37 | 9.35 | 6 | 0.42 | 20.2 | voice, idioms, omissions |
| 11 | **Ornith-1.5-35B-A3B** (Q4_K_M) | 74.2 | 76.0 | 72.5 | 73.6 | 0.0 | 9.40 | 9.29 | 6 | 0.41 | 20.2 | idioms, additions, voice |
| 12 | **Gemma 4 E4B IT** (UD-Q4_K_XL; best of 3 builds) | 72.2 | 75.5 | 68.9 | 68.1 | 0.0 | 9.30 | 9.13 | 7 | 0.17 | 3.5 | idioms, voice, who did what |
| 13 | **Sugoi-14B-Ultra** (Q4_K_M) | 67.1 | 66.5 | 67.7 | 70.8 | 0.0 | 9.05 | 8.90 | 9 | 0.30 | 8.8 | voice, idioms, additions |
| 14 | **TranslateGemma 27B IT** (Q4_K_M) | 65.5 | 71.0 | 59.9 | 44.4 | 0.0 | 9.33 | 9.39 | 3 | 0.57 | 16.7 | voice, idioms, omissions |
| 15 | **TranslateGemma 12B IT** (Q4_K_M) | 64.6 | 67.5 | 61.7 | 47.2 | 0.0 | 9.20 | 8.87 | 6 | 0.30 | 7.8 | voice, idioms, additions |
| 16 | **Gemma 4 E2B IT** (UD-Q4_K_XL; best of 4 builds) | 60.6 | 59.0 | 62.3 | 61.1 | 0.0 | 8.70 | 8.77 | 18 | 0.11 | 1.9 | idioms, voice, modality |
| 17 | **LFM2.5-24B-A2B** (Q4_K_M, empty-think) | 47.8 | 46.5 | 49.1 | 45.8 | 0.0 | 8.06 | 7.45 | 28 | 0.16 | 14.7 | idioms, voice, who did what |
| 18 | **Flint 40B-A2.5B** (IQ4_XS, empty-think) | 42.6 | 47.0 | 38.3 | 40.3 | 0.0 | 7.88 | 7.61 | 37 | 0.27 | 21.1 | idioms, who did what, voice |
| 19 | **Hy-MT2-1.8B** (Q4_K_M) | 40.1 | 39.0 | 41.3 | 43.1 | 0.0 | 7.99 | 7.35 | 33 | 0.07 | 1.5 | voice, idioms, who did what |
| · | **Gemma 4 26B-A4B heretic JP-pruned 120e** (Q4_0) | — | 85.5 | — | 68.1 | 0.0 | 9.64 | 9.16 | 3 | 0.27 | 13.3 | who did what, idioms, ambiguity |
| · | **Qwen3.6-27B** (Q4_K_M) | — | 77.5 | — | — | — | 9.46 | 9.32 | 7 | 1.20 | 16.4 | voice, idioms, additions |
| · | **VNTL-Llama3-8B-v2** (Q5_K_M) | — | 74.5 | — | — | — | 9.36 | 8.87 | 5 | 0.16 | 5.7 | idioms, voice, omissions |
| · | **Ternary-Bonsai-2-27B** (PQ2_0) | — | 72.0 | — | 58.3 | 0.0 | 9.18 | 8.87 | 8 | 0.98 | 7.1 | idioms, terms, voice |
| · | **Sugoi-32B-Ultra** (Q4_K_M) | — | 71.5 | — | — | — | 9.27 | 9.03 | 7 | 0.65 | 19.1 | idioms, voice, additions |
| · | **GLM-4.7-Flash** (Q4_K_M) | — | 70.0 | — | — | — | 9.05 | 8.90 | 9 | 0.18 | 17.5 | idioms, voice, ambiguity |
| · | **Qwen3-Swallow-32B-RL-v0.2** (Q4_K_M) | — | 68.0 | — | — | — | 9.10 | 9.06 | 11 | 0.69 | 19.0 | idioms, voice, ambiguity |
| · | **Qwen3.5-9B** (Q4_K_M) | — | 67.5 | — | — | — | 8.84 | 9.06 | 19 | 0.37 | 5.5 | idioms, voice, who did what |
| · | **Gemma 4 26B-A4B heretic JP-pruned 72e** (Q4_0) | — | 66.5 | — | 59.7 | 0.0 | 8.97 | 7.94 | 10 | 0.26 | 8.8 | voice, idioms, additions |
| · | **Hy-MT2-7B** (Q4_K_M) | — | 66.5 | — | 68.1 | 0.0 | 9.21 | 8.74 | 5 | 0.16 | 5.0 | idioms, voice, terms |
| · | **Nemotron 3.5 Bolt 74B-A9B 24GB** (IQ2_XXS) | — | 66.5 | — | 52.8 | 0.0 | 9.00 | 9.16 | 10 | 0.94 | 20.6 | idioms, voice, modality |
| · | **CAT-Translate-7B** (Q4_K_M) | — | 65.5 | — | — | — | 9.00 | 8.87 | 9 | 0.14 | 4.8 | idioms, voice, who did what |
| · | **Shisa-v2.1-qwen3-8B** (Q4_K_M) | — | 65.0 | — | 50.0 | 0.0 | 9.04 | 8.16 | 12 | 0.17 | 5.0 | additions, idioms, omissions |
| · | **HY-MT1.5-7B** (Q4_K_M) | — | 60.0 | — | — | — | 8.95 | 8.74 | 7 | 0.19 | 5.0 | voice, idioms, terms |
| · | **NVIDIA-Nemotron-Nano-9B-v2-Japanese** (Q4_K_M) | — | 60.0 | — | — | — | 8.75 | 8.65 | 12 | 0.74 | 6.3 | idioms, voice, who did what |
| · | **Qwen3.5-4B** (Q4_K_M) | — | 60.0 | — | 54.2 | 0.0 | 8.62 | 8.39 | 22 | 0.33 | 3.2 | idioms, voice, omissions |
| · | **Qwen3-8B** (Q4_K_M) | — | 52.0 | — | — | — | 8.27 | 5.23 | 25 | 0.17 | 5.0 | idioms, voice, modality |
| · | **Qwen3-4B-Instruct-2507** (Q4_K_M) | — | 50.5 | — | 55.6 | 0.0 | 8.26 | 7.90 | 28 | 0.12 | 3.0 | idioms, voice, who did what |
| · | **Hy-MT2-1.8B-JP-Manga-v5** (Q4_K_M) | — | 49.0 | — | 59.7 | 0.0 | 8.22 | 7.26 | 28 | 0.06 | 1.5 | idioms, additions, voice |
| · | **gpt-oss-20b** (Q4_K_M, effort-low) | — | 47.0 | — | 53.5 | 1.6 | 7.81 | 8.26 | 38 | 0.49 | 11.0 | idioms, voice, terms |
| · | **Ling-3.0-tiny** (Q4_K_M) | — | 34.5 | — | 38.9 | 0.0 | 7.42 | 6.52 | 52 | 0.16 | 4.9 | idioms, voice, modality |
| · | **Qwen3.5-2B** (Q4_K_M) | — | 32.5 | — | 40.3 | 0.0 | 7.24 | 6.77 | 51 | 0.13 | 1.6 | idioms, voice, who did what |
| · | **LFM2.5-2.6B** (Q4_K_M, empty-think) | — | 26.5 | — | 36.1 | 0.0 | 6.76 | 2.65 | 67 | 0.14 | 2.0 | idioms, voice, additions |
| · | **LFM2.5-VL-3B** (Q4_K_M) | — | 24.5 | — | 29.2 | 0.0 | 6.71 | 6.19 | 70 | 0.15 | 2.0 | idioms, voice, omissions |
| · | **LFM3-Omni-2B** (Q4_K_M, respond-in-text) | — | 23.5 | — | 36.1 | 0.0 | 6.45 | 6.32 | 76 | 0.08 | 1.4 | idioms, voice, who did what |
| · | **LFM2.5-1.2B-JP-202606** (Q4_K_M) | — | 23.0 | — | — | — | 6.58 | 5.97 | 77 | 0.17 | 1.1 | idioms, voice, who did what |
| · | **LFM3-VL-2B** (Q4_K_M) | — | 21.5 | — | 34.7 | 0.0 | 6.22 | 5.32 | 82 | 0.08 | 1.4 | idioms, voice, who did what |
| · | **LFM3-1.7B** (Q4_K_M) | — | 20.0 | — | 34.7 | 0.0 | 5.95 | 4.84 | 98 | 0.08 | 1.4 | idioms, voice, who did what |
| · | **LFM2.5-1.2B Instruct** (Q4_K_M) | — | 18.0 | — | — | — | 5.88 | 5.52 | 100 | 0.04 | 1.1 | idioms, voice, who did what |
| · | **Shisa-v2.1-unphi4-14B** (Q4_K_M) | — | 6.5 | — | — | — | 8.63 | 8.06 | 7 | 0.97 | 8.9 | additions, formatting, idioms |

\* Gemini: full scenes use only the first sentence of the system prompt; with the full prompt it returns some scenes untranslated.

## All builds

Every build of the models above with more than one, best first. Gap is Overview points behind the best build, ± its 95% margin from comparing the two builds line by line on the same lines; *within noise* means the gap is inside that margin, so this test cannot tell the builds apart.

| Model | Build | Overview % | Gap | Standard % | Hard % | Adult % (not refused) | Seconds per line | VRAM GB |
|---|---|---:|---|---:|---:|---:|---:|---:|
| Gemma 4 31B IT | QAT-Q4_0 | 86.6 | best | 90.0 | 83.2 | 79.2 | 0.91 | 18.2 |
|  | Q5_K_M | 86.2 | -0.4 ±2.1 (within noise) | 91.0 | 81.4 | 79.2 | 1.21 | 22.9 |
|  | Q4_K_M | 85.9 | -0.7 ±2.3 (within noise) | 91.0 | 80.8 | 81.9 | 1.09 | 20.0 |
|  | Q4_K_L | — | not ranked yet | 91.0 | — | 81.9 | 1.07 | 20.4 |
| Gemma 4 26B-A4B IT | UD-Q4_K_M | 84.0 | best | 86.5 | 81.4 | 75.0 | 0.28 | 16.6 |
|  | QAT-Q4_0 | 83.7 | -0.3 ±3.0 (within noise) | 86.0 | 81.4 | 69.4 | 0.26 | 14.2 |
| Gemma 4 12B IT | UD-Q4_K_XL | 81.7 | best | 85.5 | 77.8 | 75.0 | 0.42 | 7.8 |
|  | QAT-Q4_0 | 81.0 | -0.7 ±2.7 (within noise) | 83.0 | 79.0 | 70.8 | 0.38 | 7.4 |
|  | QAT-i1-IQ3_M | 79.5 | -2.2 ±3.4 (within noise) | 80.5 | 78.4 | 72.2 | 0.42 | 6.3 |
|  | QAT-i1-Q2_K | 66.3 | -15.4 ±4.3 | 62.5 | 70.1 | 63.9 | 0.38 | 5.4 |
| Qwen3.8-27B | UD-Q6_K_L | 81.0 | best | 83.5 | 78.4 | 75.0 | 1.33 | 22.0 |
|  | UD-Q4_K_M | 80.6 | -0.4 ±2.1 (within noise) | 81.0 | 80.2 | 75.0 | 1.17 | 15.1 |
| Gemma 4 E4B IT | UD-Q4_K_XL | 72.2 | best | 75.5 | 68.9 | 68.1 | 0.17 | 3.5 |
|  | QAT-Q4_0 | 70.8 | -1.4 ±3.4 (within noise) | 74.5 | 67.1 | 68.1 | 0.16 | 3.1 |
|  | QAT-UD-Q2_K_XL | 47.2 | -25.0 ±5.1 | 43.5 | 50.9 | 52.8 | 0.25 | 2.7 |
| Gemma 4 E2B IT | UD-Q4_K_XL | 60.6 | best | 59.0 | 62.3 | 61.1 | 0.11 | 1.9 |
|  | QAT-Q4_0 | 59.5 | -1.1 ±3.8 (within noise) | 61.5 | 57.5 | 65.3 | 0.11 | 1.8 |
|  | QAT-UD-Q4_K_XL | 55.1 | -5.5 ±4.5 | 60.5 | 49.7 | 51.4 | 0.10 | 1.6 |
|  | QAT-UD-Q2_K_XL | 14.9 | -45.7 ±5.4 | 13.0 | 16.8 | 15.3 | 0.68 | 0.8 |

Being judged: Phi-4 14B (Q4_K_M) (109/200 lines), Qwen2.5-14B-Instruct (Q4_K_M) (79/200 lines), TinySwallow-1.5B-Instruct (Q5_K_M) (49/200 lines), TranslateGemma 4B IT (Q4_K_M) (49/200 lines), Ministral 3 8B Instruct (UD-Q4_K_XL) (49/200 lines), CAT-Translate-0.8B (Q4_K_M) (48/200 lines), HY-MT1.5-1.8B (Q4_K_M) (37/200 lines), CAT-Translate-1.4B (Q4_K_M) (32/200 lines), Shisa-v2.1-llama3.2-3B (Q4_K_M) (22/200 lines), Shisa-v2.1-lfm2-1.2B (Q4_K_M) (0/200 lines).

## By category

Share of the 20 eval lines in each category translated well (9 or 10 out of 10). With 20 lines per cell, differences under about 20 points are noise.

| Model | Idioms & proverbs | Wordplay & irony | Dialect & voice | Politeness (keigo) | Indirect speech | Emotional subtext | Omitted subjects | Culture & institutions | Literary style | Onomatopoeia |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gemini 3.8 Flash (cloud) | 85% | 90% | 100% | 95% | 100% | 100% | 90% | 100% | 100% | 100% |
| Claude Sonnet 5.5 (cloud) | 95% | 85% | 95% | 100% | 100% | 95% | 90% | 95% | 100% | 100% |
| Gemma 4 31B IT (QAT-Q4_0) | 80% | 90% | 95% | 100% | 100% | 95% | 100% | 100% | 90% | 95% |
| Claude Haiku 5.5 (cloud) | 90% | 95% | 95% | 95% | 100% | 85% | 90% | 90% | 100% | 90% |
| Gemma 4 26B-A4B IT (UD-Q4_K_M) | 75% | 75% | 95% | 100% | 100% | 100% | 95% | 95% | 100% | 90% |
| Gemma 4 12B IT (UD-Q4_K_XL) | 90% | 75% | 90% | 100% | 100% | 100% | 95% | 80% | 90% | 95% |
| Qwen3.8-27B (UD-Q6_K_L) | 65% | 80% | 85% | 95% | 100% | 85% | 95% | 75% | 95% | 100% |
| Gemini 3.5 Flash-Lite (cloud)\* | 90% | 70% | 100% | 90% | 100% | 100% | 100% | 95% | 90% | 95% |
| Hy-MT2-30B-A3B (Q4_K_M) | 85% | 65% | 80% | 95% | 100% | 85% | 95% | 95% | 90% | 90% |
| Qwen3.6-35B-A3B (Q4_K_M) | 60% | 70% | 80% | 95% | 95% | 90% | 90% | 80% | 80% | 95% |
| Ornith-1.5-35B-A3B (Q4_K_M) | 65% | 65% | 85% | 100% | 85% | 95% | 75% | 85% | 90% | 100% |
| Gemma 4 E4B IT (UD-Q4_K_XL) | 60% | 70% | 75% | 90% | 90% | 85% | 85% | 80% | 90% | 90% |
| Sugoi-14B-Ultra (Q4_K_M) | 55% | 65% | 65% | 90% | 85% | 80% | 75% | 85% | 70% | 85% |
| TranslateGemma 27B IT (Q4_K_M) | 65% | 65% | 75% | 90% | 85% | 85% | 80% | 85% | 85% | 90% |
| TranslateGemma 12B IT (Q4_K_M) | 55% | 60% | 60% | 100% | 80% | 75% | 80% | 70% | 95% | 85% |
| Gemma 4 E2B IT (UD-Q4_K_XL) | 25% | 70% | 55% | 90% | 80% | 75% | 60% | 60% | 80% | 65% |
| LFM2.5-24B-A2B (Q4_K_M, empty-think) | 15% | 45% | 55% | 60% | 60% | 60% | 70% | 35% | 70% | 75% |
| Flint 40B-A2.5B (IQ4_XS, empty-think) | 20% | 35% | 55% | 60% | 55% | 55% | 70% | 40% | 55% | 60% |
| Hy-MT2-1.8B (Q4_K_M) | 15% | 35% | 55% | 60% | 50% | 65% | 70% | 40% | 60% | 70% |
| Gemma 4 26B-A4B heretic JP-pruned 120e (Q4_0) | 75% | 80% | 100% | 95% | 100% | 90% | 95% | 90% | 85% | 95% |
| Qwen3.6-27B (Q4_K_M) | 70% | 90% | 70% | 90% | 95% | 85% | 85% | 85% | 95% | 95% |
| VNTL-Llama3-8B-v2 (Q5_K_M) | 60% | 60% | 85% | 90% | 90% | 85% | 85% | 80% | 90% | 90% |
| Ternary-Bonsai-2-27B (PQ2_0) | 50% | 80% | 80% | 85% | 80% | 90% | 85% | 65% | 85% | 80% |
| Sugoi-32B-Ultra (Q4_K_M) | 40% | 75% | 85% | 80% | 100% | 85% | 85% | 75% | 80% | 90% |
| GLM-4.7-Flash (Q4_K_M) | 50% | 65% | 80% | 90% | 75% | 85% | 95% | 60% | 80% | 85% |
| Qwen3-Swallow-32B-RL-v0.2 (Q4_K_M) | 50% | 70% | 70% | 85% | 85% | 85% | 80% | 55% | 85% | 85% |
| Qwen3.5-9B (Q4_K_M) | 50% | 65% | 55% | 80% | 90% | 75% | 75% | 60% | 85% | 85% |
| Gemma 4 26B-A4B heretic JP-pruned 72e (Q4_0) | 60% | 65% | 50% | 80% | 85% | 80% | 80% | 80% | 80% | 80% |
| Hy-MT2-7B (Q4_K_M) | 55% | 70% | 85% | 85% | 95% | 85% | 85% | 70% | 85% | 95% |
| Nemotron 3.5 Bolt 74B-A9B 24GB (IQ2_XXS) | 40% | 60% | 50% | 85% | 85% | 80% | 90% | 75% | 75% | 85% |
| CAT-Translate-7B (Q4_K_M) | 50% | 70% | 65% | 80% | 80% | 90% | 75% | 60% | 80% | 75% |
| Shisa-v2.1-qwen3-8B (Q4_K_M) | 45% | 45% | 75% | 95% | 85% | 75% | 95% | 55% | 80% | 90% |
| HY-MT1.5-7B (Q4_K_M) | 35% | 50% | 70% | 80% | 80% | 95% | 85% | 35% | 80% | 90% |
| NVIDIA-Nemotron-Nano-9B-v2-Japanese (Q4_K_M) | 25% | 50% | 65% | 70% | 90% | 80% | 65% | 75% | 75% | 80% |
| Qwen3.5-4B (Q4_K_M) | 20% | 65% | 55% | 70% | 80% | 70% | 85% | 70% | 85% | 60% |
| Qwen3-8B (Q4_K_M) | 30% | 35% | 55% | 85% | 60% | 65% | 50% | 50% | 50% | 95% |
| Qwen3-4B-Instruct-2507 (Q4_K_M) | 20% | 50% | 55% | 65% | 60% | 55% | 70% | 70% | 75% | 70% |
| Hy-MT2-1.8B-JP-Manga-v5 (Q4_K_M) | 25% | 50% | 60% | 55% | 60% | 55% | 95% | 40% | 55% | 75% |
| gpt-oss-20b (Q4_K_M, effort-low) | 20% | 50% | 30% | 50% | 65% | 55% | 80% | 35% | 80% | 60% |
| Ling-3.0-tiny (Q4_K_M) | 10% | 30% | 30% | 60% | 50% | 40% | 55% | 30% | 50% | 70% |
| Qwen3.5-2B (Q4_K_M) | 5% | 15% | 40% | 60% | 30% | 40% | 55% | 30% | 55% | 60% |
| LFM2.5-2.6B (Q4_K_M, empty-think) | 5% | 30% | 20% | 45% | 55% | 25% | 40% | 15% | 55% | 30% |
| LFM2.5-VL-3B (Q4_K_M) | 15% | 35% | 25% | 30% | 10% | 50% | 40% | 10% | 55% | 35% |
| LFM3-Omni-2B (Q4_K_M, respond-in-text) | 0% | 10% | 10% | 40% | 35% | 25% | 45% | 15% | 55% | 30% |
| LFM2.5-1.2B-JP-202606 (Q4_K_M) | 5% | 20% | 25% | 50% | 35% | 25% | 60% | 10% | 50% | 35% |
| LFM3-VL-2B (Q4_K_M) | 5% | 20% | 20% | 35% | 15% | 35% | 30% | 15% | 45% | 30% |
| LFM3-1.7B (Q4_K_M) | 5% | 45% | 10% | 30% | 15% | 30% | 40% | 5% | 45% | 35% |
| LFM2.5-1.2B Instruct (Q4_K_M) | 5% | 0% | 10% | 25% | 20% | 20% | 35% | 5% | 40% | 45% |
| Shisa-v2.1-unphi4-14B (Q4_K_M) | 40% | 50% | 65% | 90% | 90% | 65% | 65% | 60% | 70% | 70% |

## Output compliance

Decided mechanically, identically for every model. **Automatic zeros** are already in the scores above: no usable output, or the source returned untranslated. **Flags** do not change the /10 scores; *commentary* fails a line for Pass %: *commentary* = an alternative, note or literal gloss appended to the translation; *format* = speaker labels rewritten as `Name:` or markdown emphasis.

| Model | Zero: no output | Zero: untranslated | Commentary | Format |
|---|---:|---:|---:|---:|
| Gemini 3.8 Flash (cloud) | 0 | 0 | 0 | 2 |
| Claude Sonnet 5.5 (cloud) | 0 | 0 | 0 | 4 |
| Gemma 4 31B IT (QAT-Q4_0) | 0 | 0 | 0 | 0 |
| Claude Haiku 5.5 (cloud) | 0 | 0 | 0 | 1 |
| Gemma 4 26B-A4B IT (UD-Q4_K_M) | 0 | 0 | 0 | 1 |
| Gemma 4 12B IT (UD-Q4_K_XL) | 0 | 0 | 0 | 0 |
| Qwen3.8-27B (UD-Q6_K_L) | 0 | 0 | 0 | 0 |
| Gemini 3.5 Flash-Lite (cloud)\* | 0 | 0 | 1 | 5 |
| Hy-MT2-30B-A3B (Q4_K_M) | 0 | 0 | 0 | 0 |
| Qwen3.6-35B-A3B (Q4_K_M) | 0 | 0 | 0 | 2 |
| Ornith-1.5-35B-A3B (Q4_K_M) | 0 | 0 | 0 | 9 |
| Gemma 4 E4B IT (UD-Q4_K_XL) | 0 | 0 | 0 | 0 |
| Sugoi-14B-Ultra (Q4_K_M) | 0 | 0 | 1 | 0 |
| TranslateGemma 27B IT (Q4_K_M) | 0 | 0 | 0 | 0 |
| TranslateGemma 12B IT (Q4_K_M) | 0 | 0 | 0 | 1 |
| Gemma 4 E2B IT (UD-Q4_K_XL) | 0 | 0 | 0 | 0 |
| LFM2.5-24B-A2B (Q4_K_M, empty-think) | 1 | 0 | 0 | 2 |
| Flint 40B-A2.5B (IQ4_XS, empty-think) | 2 | 0 | 1 | 0 |
| Hy-MT2-1.8B (Q4_K_M) | 0 | 0 | 0 | 0 |
| Gemma 4 26B-A4B heretic JP-pruned 120e (Q4_0) | 0 | 0 | 0 | 2 |
| Qwen3.6-27B (Q4_K_M) | 0 | 0 | 0 | 0 |
| VNTL-Llama3-8B-v2 (Q5_K_M) | 0 | 0 | 0 | 0 |
| Ternary-Bonsai-2-27B (PQ2_0) | 0 | 0 | 0 | 1 |
| Sugoi-32B-Ultra (Q4_K_M) | 0 | 0 | 0 | 1 |
| GLM-4.7-Flash (Q4_K_M) | 0 | 0 | 0 | 3 |
| Qwen3-Swallow-32B-RL-v0.2 (Q4_K_M) | 0 | 0 | 0 | 0 |
| Qwen3.5-9B (Q4_K_M) | 0 | 0 | 0 | 0 |
| Gemma 4 26B-A4B heretic JP-pruned 72e (Q4_0) | 0 | 0 | 0 | 1 |
| Hy-MT2-7B (Q4_K_M) | 0 | 0 | 0 | 0 |
| Nemotron 3.5 Bolt 74B-A9B 24GB (IQ2_XXS) | 0 | 0 | 0 | 0 |
| CAT-Translate-7B (Q4_K_M) | 0 | 0 | 0 | 1 |
| Shisa-v2.1-qwen3-8B (Q4_K_M) | 0 | 0 | 0 | 33 |
| HY-MT1.5-7B (Q4_K_M) | 0 | 0 | 0 | 0 |
| NVIDIA-Nemotron-Nano-9B-v2-Japanese (Q4_K_M) | 0 | 0 | 0 | 11 |
| Qwen3.5-4B (Q4_K_M) | 0 | 0 | 0 | 0 |
| Qwen3-8B (Q4_K_M) | 0 | 12 | 0 | 0 |
| Qwen3-4B-Instruct-2507 (Q4_K_M) | 0 | 0 | 0 | 0 |
| Hy-MT2-1.8B-JP-Manga-v5 (Q4_K_M) | 0 | 0 | 0 | 6 |
| gpt-oss-20b (Q4_K_M, effort-low) | 1 | 0 | 0 | 2 |
| Ling-3.0-tiny (Q4_K_M) | 0 | 1 | 0 | 2 |
| Qwen3.5-2B (Q4_K_M) | 0 | 0 | 0 | 1 |
| LFM2.5-2.6B (Q4_K_M, empty-think) | 4 | 19 | 0 | 1 |
| LFM2.5-VL-3B (Q4_K_M) | 0 | 0 | 0 | 0 |
| LFM3-Omni-2B (Q4_K_M, respond-in-text) | 0 | 3 | 0 | 0 |
| LFM2.5-1.2B-JP-202606 (Q4_K_M) | 0 | 0 | 0 | 6 |
| LFM3-VL-2B (Q4_K_M) | 0 | 0 | 0 | 8 |
| LFM3-1.7B (Q4_K_M) | 4 | 6 | 3 | 0 |
| LFM2.5-1.2B Instruct (Q4_K_M) | 0 | 0 | 0 | 0 |
| Shisa-v2.1-unphi4-14B (Q4_K_M) | 0 | 0 | 172 | 228 |

Standard: 200 eval lines judged by GPT-6.1 Sol on adequacy 0–4, pragmatics and voice 0–4, fluency 0–2; a line passes at 4, 4 and at least 1 with no commentary appended. Hard and Adult: each line has named checks, and it passes when every check passes (uncertain is not a pass); a Hard line also fails if the reply carries leaked prompt headers, the Japanese echoed back or extra dialogue turns. A line the model failed to produce fails (scores 0 out of 10). Speed is the median time to finish a line with 6 lines of history on an RTX 3090.
