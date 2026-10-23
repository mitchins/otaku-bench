# OtakuBench screen mission — run report

Latency is full-line wall time on the mission GPU with a warm server: weights resident, kernels warmed by the canary, and the instruction prefix served from the prompt cache. Dialogue history is prefilled fresh on every request, as a sliding-window client would send it. `d0` = line alone (minimal-context baseline); `d6` = six preceding lines (headline latency and gate); `d24` = long history (context scaling). Append-only clients that keep history cached have not been measured yet.

| # | model | style | GB | VRAM MiB | status | ttft d6 | line d0 | line d6 | line d24 | tok/s | arms |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| 29 | CAT-Translate-0.8B | cat | 0.528 | 906 | COMPLETE | 0.008s | 0.04s | 0.04s | — | 511.251 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 45 | LFM2.5-1.2B Instruct | chat | 0.731 | 1102 | COMPLETE | 0.018s | 0.042s | 0.045s | 0.055s | 535.429 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 27 | CAT-Translate-1.4B | cat | 0.931 | 1324 | COMPLETE | 0.01s | 0.049s | 0.049s | — | 401.648 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 18 | TinySwallow-1.5B-Instruct | chat | 1.125 | 1506 | COMPLETE | 0.017s | 0.055s | 0.06s | 0.075s | 300.719 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 17 | Shisa-v2.1-lfm2-1.2B | chat | 0.731 | 1102 | COMPLETE | 0.017s | 0.079s | 0.07s | 0.103s | 543.991 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 16 | Shisa-v2.1-llama3.2-3B | chat | 2.019 | 2534 | COMPLETE | 0.037s | 0.103s | 0.089s | 0.1s | 233.138 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 28 | HY-MT1.5-1.8B | hunyuan | 1.133 | 1574 | COMPLETE | 0.025s | 0.089s | 0.091s | 0.09s | 303.291 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 42 | Gemma 4 E2B IT | chat | 3.184 | 1946 | COMPLETE | 0.04s | 0.106s | 0.111s | 0.137s | 204.537 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 34 | TranslateGemma 4B IT | translategemma_text | 2.49 | 2982 | COMPLETE | 0.032s | 0.121s | 0.121s | — | 168.714 | L=250/250 s_bare=31/31 s_full=31/31 |
| 46 | Qwen3-4B-Instruct-2507 | chat | 2.497 | 3058 | COMPLETE | 0.044s | 0.147s | 0.122s | 0.151s | 180.932 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 44 | Qwen3.5-2B | chat | 1.396 | 1674 | COMPLETE | 0.078s | 0.106s | 0.128s | 0.126s | 273.969 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 10 | CAT-Translate-7B | cat | 4.538 | 4882 | COMPLETE | 0.026s | 0.141s | 0.141s | — | 122.933 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 20 | VNTL-Llama3-8B-v2 | vntl | 5.733 | 5806 | COMPLETE | 0.028s | 0.161s | 0.161s | — | 101.378 | L=250/250 s_bare=31/31 s_full=31/31 |
| 38 | Qwen3-8B | chat | 5.028 | 5166 | COMPLETE | 0.049s | 0.189s | 0.165s | 0.203s | 116.128 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 24 | Seed-X-PPO-7B | seedx | 4.558 | 4892 | COMPLETE | 0.033s | 0.168s | 0.168s | — | 120.465 | L=250/250 s_bare=31/31 |
| 19 | LFM2.5-1.2B-JP-202606 | chat | 0.731 | 1102 | COMPLETE | 0.018s | 0.041s | 0.175s | — | 547.578 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 15 | Shisa-v2.1-qwen3-8B | chat | 5.028 | 5166 | COMPLETE | 0.052s | 0.19s | 0.175s | 0.202s | 113.588 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 41 | Gemma 4 E4B IT | chat | 5.126 | 3548 | COMPLETE | 0.062s | 0.157s | 0.175s | 0.224s | 132.029 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 37 | GLM-4.7-Flash | chat | 18.475 | 17948 | COMPLETE | 0.061s | 0.166s | 0.179s | 0.196s | 116.961 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 23 | HY-MT1.5-7B | hunyuan | 4.625 | 5094 | COMPLETE | 0.048s | 0.189s | 0.189s | 0.202s | 116.016 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 43 | Ministral 3 8B Instruct | chat | 5.288 | 5454 | COMPLETE | 0.051s | 0.201s | 0.218s | 0.236s | 107.697 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 5 | Gemma 4 26B-A4B IT | chat | 16.948 | 16954 | COMPLETE | 0.146s | 0.317s | 0.283s | 0.389s | 112.388 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 33 | TranslateGemma 12B IT | translategemma_text | 7.301 | 8008 | COMPLETE | 0.08s | 0.297s | 0.297s | — | 70.672 | L=250/250 s_bare=31/31 s_full=31/31 |
| 21 | Sugoi-14B-Ultra | sugoi | 8.988 | 8976 | COMPLETE | 0.078s | 0.309s | 0.298s | 0.343s | 62.224 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 48 | Qwen2.5-14B-Instruct | chat | 8.988 | 8976 | COMPLETE | 0.077s | 0.308s | 0.307s | 0.353s | 61.421 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 31 | Qwen3.5-4B | chat | 3.013 | 3252 | COMPLETE | 0.247s | 0.32s | 0.33s | 0.365s | 154.049 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 30 | Qwen3.5-9B | chat | 6.169 | 5622 | COMPLETE | 0.244s | 0.37s | 0.374s | 0.44s | 100.735 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 49 | Phi-4 14B | chat | 9.053 | 9218 | COMPLETE | 0.086s | 0.363s | 0.38s | 0.463s | 56.895 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 3 | Qwen3.6-35B-A3B | chat | 22.285 | 20646 | COMPLETE | 0.321s | 0.39s | 0.424s | 0.474s | 144.714 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 8 | Gemma 4 12B IT | chat | 7.366 | 7966 | COMPLETE | 0.205s | 0.474s | 0.425s | 0.59s | 69.396 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 32 | TranslateGemma 27B IT | translategemma_text | 16.547 | 17050 | COMPLETE | 0.178s | 0.566s | 0.566s | — | 36.689 | L=250/250 s_bare=31/31 s_full=31/31 |
| 22 | Sugoi-32B-Ultra | sugoi | 19.851 | 19548 | COMPLETE | 0.137s | 0.649s | 0.653s | 0.753s | 26.725 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 11 | Qwen3-Swallow-32B-RL-v0.2 | chat | 19.762 | 19450 | COMPLETE | 0.137s | 0.701s | 0.692s | 0.773s | 26.223 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 13 | NVIDIA-Nemotron-Nano-9B-v2-Japanese | chat | 6.526 | 6474 | COMPLETE | 0.598s | 0.73s | 0.744s | 0.79s | 89.9 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 14 | Shisa-v2.1-unphi4-14B | chat | 8.89 | 9064 | COMPLETE | 0.097s | 1.094s | 0.967s | 1.217s | 57.828 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 2 | Gemma 4 31B IT | chat | 19.598 | 20528 | COMPLETE | 0.51s | 1.211s | 1.089s | 1.527s | 25.074 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 1 | Qwen3.8-27B | chat | 16.464 | 15424 | COMPLETE | 0.736s | 1.086s | 1.169s | 1.308s | 31.902 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 4 | Qwen3.6-27B | chat | 17.985 | 16778 | COMPLETE | 0.748s | 1.147s | 1.195s | 1.385s | 30.223 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 25 | CAT-Translate-3.3B-beta | cat | 2.066 | 2556 | PARTIAL | 0.02s | 0.094s | 0.094s | — | 198.697 | L=249/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 50 | Llama-3.2-3B-Instruct | chat | 2.019 | 2534 | PARTIAL | 0.037s | 0.118s | 0.1s | 0.096s | 231.009 | L=249/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 47 | rinna-llama-3-youko-8b | base_completion | 4.921 | 5094 | PARTIAL | 0.021s | 0.138s | 0.138s | — | 115.986 | L=249/250 s_bare=29/31 |
| 9 | Qwen3-Swallow-30B-A3B-RL-v0.2 | chat | 18.557 | 18122 | PARTIAL | 0.064s | 0.156s | 0.149s | 0.166s | 165.269 | L=243/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 6 | LLM-jp-4.1-32B-A3B Thinking | chat | 21.522 | 20802 | LATENCY_FAIL | 1.321s | 1.351s | 1.378s | 1.499s | 179.446 |  |
| 35 | LLM-jp-4.1-8B Thinking | chat | 5.5 | 5500 | LATENCY_FAIL | 2.32s | 1.937s | 2.451s | 2.624s | 95.571 |  |
| 7 | LLM-jp-4.1-33B Thinking | chat | 20.408 | 19956 | LATENCY_FAIL | 9.533s | 7.823s | 9.967s | 7.241s | 23.188 |  |
| 26 | Qwen3-Swallow-8B-RL-v0.2 | chat | 5.028 | 5166 | CANARY_FAILED | — | — | — | — | — |  |
| 39 | gpt-oss-20b | chat | 11.673 | 11216 | CANARY_FAILED | — | — | — | — | — |  |
| 36 | LFM2.5-24B-A2B | chat | 15.352 | 15080 | CANARY_FAILED | — | — | — | — | — |  |
| 12 | GPT-OSS-Swallow-20B-RL-v0.1 | chat | 15.805 | 15156 | CANARY_FAILED | — | — | — | — | — |  |
| 40 | Nemotron 3 Nano 30B-A3B | chat | 24.656 | — | DEFER_5090 | — | — | — | — | — |  |

## Deferred to the 5090

- 40 Nemotron 3 Nano 30B-A3B — needs ~25313 MiB, GPU 0 has 24157 MiB free

## Needs a look

- 25 CAT-Translate-3.3B-beta — PARTIAL 
- 50 Llama-3.2-3B-Instruct — PARTIAL 
- 47 rinna-llama-3-youko-8b — PARTIAL 
- 9 Qwen3-Swallow-30B-A3B-RL-v0.2 — PARTIAL 
- 26 Qwen3-Swallow-8B-RL-v0.2 — CANARY_FAILED hit 256-token cap (thinking or runaway output)
- 39 gpt-oss-20b — CANARY_FAILED hit 256-token cap (thinking or runaway output)
- 36 LFM2.5-24B-A2B — CANARY_FAILED hit 256-token cap (thinking or runaway output)
- 12 GPT-OSS-Swallow-20B-RL-v0.1 — CANARY_FAILED hit 256-token cap (thinking or runaway output)
