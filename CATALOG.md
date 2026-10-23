# OtakuBench v4 — 50 local Japanese→English translation candidates

> **Provisional test priority, not translation performance.** Zero models were run or scored in this working container. Exact GGUF names and reported sizes require Hugging Face revision/byte attestation before any qualified run.

**50 total, 5 v4 controls added, 5 redundant entries removed; 23 weight-size-proxy-only Deck candidates.**

The four lanes: first-party laboratory models; documented Japanese/bilingual adaptations; laboratory distillations; narrowly permitted VN-specialist releases. Parent models used as experimental *controls* are not predicted winners.

| # | Model (original release) | Total B | Category | Recommended GGUF / converter | Quant | Reported GB† | Deck weight proxy |
|---:|---|---:|---|---|---|---:|---|
| 1 | [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | 27 | lab_original_or_existing_v2_specialist | [unsloth/Qwen3.8-27B-GGUF](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF) — `Qwen3.8-27B-UD-Q4_K_M.gguf` | `UD-Q4_K_M` | 16.50 | no |
| 2 | [Gemma 4 31B IT](https://huggingface.co/google/gemma-4-31b-it) | 31 | lab_original_or_existing_v2_specialist | [bartowski/google_gemma-4-31B-it-GGUF](https://huggingface.co/bartowski/google_gemma-4-31B-it-GGUF) — `google_gemma-4-31B-it-Q4_K_M.gguf` | `Q4_K_M` | 19.60 | no |
| 3 | [Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) | 35 | lab_original_or_existing_v2_specialist | [bartowski/Qwen_Qwen3.6-35B-A3B-GGUF](https://huggingface.co/bartowski/Qwen_Qwen3.6-35B-A3B-GGUF) — `Qwen_Qwen3.6-35B-A3B-Q4_K_M.gguf` | `Q4_K_M` | 22.29 | no |
| 4 | [Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B) | 27 | lab_original_or_existing_v2_specialist | [bartowski/Qwen_Qwen3.6-27B-GGUF](https://huggingface.co/bartowski/Qwen_Qwen3.6-27B-GGUF) — `unverified` | `Q4_K_M` | — | no |
| 5 | [Gemma 4 26B-A4B IT](https://huggingface.co/google/gemma-4-26B-A4B-it) | 26 | lab_original_or_existing_v2_specialist | [unsloth/gemma-4-26B-A4B-it-GGUF](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF) — `gemma-4-26B-A4B-it-UD-Q4_K_M.gguf` | `UD-Q4_K_M` | 16.90 | no |
| 6 | [LLM-jp-4.1-32B-A3B Thinking](https://huggingface.co/llm-jp/llm-jp-4.1-32b-a3b-thinking) | 32.139 | lab_original_or_existing_v2_specialist | [llm-jp/llm-jp-4.1-32b-a3b-thinking-gguf](https://huggingface.co/llm-jp/llm-jp-4.1-32b-a3b-thinking-gguf) — `llm-jp-4.1-32b-a3b-thinking-Q4_K_M.gguf` | `Q4_K_M` | 21.50 | no |
| 7 | [LLM-jp-4.1-33B Thinking](https://huggingface.co/llm-jp/llm-jp-4.1-33b-thinking) | 33.22 | lab_original_or_existing_v2_specialist | [llm-jp/llm-jp-4.1-33b-thinking-gguf](https://huggingface.co/llm-jp/llm-jp-4.1-33b-thinking-gguf) — `llm-jp-4.1-33b-thinking-Q4_K_M.gguf` | `Q4_K_M` | 20.40 | no |
| 8 | [Gemma 4 12B IT](https://huggingface.co/google/gemma-4-12b-it) | 12 | lab_original_or_existing_v2_specialist | [unsloth/gemma-4-12b-it-GGUF](https://huggingface.co/unsloth/gemma-4-12b-it-GGUF) — `unverified` | `UD-Q4_K_XL` | — | no |
| 9 | [Qwen3-Swallow-30B-A3B-RL-v0.2](https://huggingface.co/tokyotech-llm/Qwen3-Swallow-30B-A3B-RL-v0.2) | 31 | lab_original_or_existing_v2_specialist | [yuseiito/Qwen3-Swallow-30B-A3B-RL-v0.2-GGUF](https://huggingface.co/yuseiito/Qwen3-Swallow-30B-A3B-RL-v0.2-GGUF) — `Qwen3-Swallow-30B-A3B-RL-v0.2-Q4_K_M.gguf` | `Q4_K_M` | 18.60 | no |
| 10 | [CAT-Translate-7B](https://huggingface.co/cyberagent/CAT-Translate-7b) | 7 | lab_original_or_existing_v2_specialist | [mradermacher/CAT-Translate-7b-GGUF](https://huggingface.co/mradermacher/CAT-Translate-7b-GGUF) — `CAT-Translate-7b.Q4_K_M.gguf` | `Q4_K_M` | 4.54 | size only |
| 11 | [Qwen3-Swallow-32B-RL-v0.2](https://huggingface.co/tokyotech-llm/Qwen3-Swallow-32B-RL-v0.2) | 32.5 | heavy_adaptation | [ultimatechris/Qwen3-Swallow-32B-RL-v0.2-GGUF](https://huggingface.co/ultimatechris/Qwen3-Swallow-32B-RL-v0.2-GGUF) — `Qwen3-Swallow-32B-RL-v0.2-Q4_K_M.gguf` | `Q4_K_M` | 19.80 | no |
| 12 | [GPT-OSS-Swallow-20B-RL-v0.1](https://huggingface.co/tokyotech-llm/GPT-OSS-Swallow-20B-RL-v0.1) | 21 | heavy_adaptation | [mradermacher/GPT-OSS-Swallow-20B-RL-v0.1-GGUF](https://huggingface.co/mradermacher/GPT-OSS-Swallow-20B-RL-v0.1-GGUF) — `GPT-OSS-Swallow-20B-RL-v0.1.Q4_K_M.gguf` | `Q4_K_M` | 15.80 | no |
| 13 | [NVIDIA-Nemotron-Nano-9B-v2-Japanese](https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese) | 9 | first_party_japanese | [mmnga-o/NVIDIA-Nemotron-Nano-9B-v2-Japanese-gguf](https://huggingface.co/mmnga-o/NVIDIA-Nemotron-Nano-9B-v2-Japanese-gguf) — `NVIDIA-Nemotron-Nano-9B-v2-Japanese-Q4_K_M.gguf` | `Q4_K_M` | 6.53 | size only |
| 14 | [Shisa-v2.1-unphi4-14B](https://huggingface.co/shisa-ai/shisa-v2.1-unphi4-14b) | 14 | large_sft_rl | [XpressAI/shisa-v2.1-unphi4-14b-GGUF](https://huggingface.co/XpressAI/shisa-v2.1-unphi4-14b-GGUF) — `shisa-v2.1-unphi4-14b-Q4_K_M.gguf` | `Q4_K_M` | 8.89 | size only |
| 15 | [Shisa-v2.1-qwen3-8B](https://huggingface.co/shisa-ai/shisa-v2.1-qwen3-8b) | 8 | large_sft_rl | [XpressAI/shisa-v2.1-qwen3-8b-GGUF](https://huggingface.co/XpressAI/shisa-v2.1-qwen3-8b-GGUF) — `shisa-v2.1-qwen3-8b-Q4_K_M.gguf` | `Q4_K_M` | 5.03 | size only |
| 16 | [Shisa-v2.1-llama3.2-3B](https://huggingface.co/shisa-ai/shisa-v2.1-llama3.2-3b) | 3 | large_sft_rl | [XpressAI/shisa-v2.1-llama3.2-3b-GGUF](https://huggingface.co/XpressAI/shisa-v2.1-llama3.2-3b-GGUF) — `shisa-v2.1-llama3.2-3b-Q4_K_M.gguf` | `Q4_K_M` | 2.02 | size only |
| 17 | [Shisa-v2.1-lfm2-1.2B](https://huggingface.co/shisa-ai/shisa-v2.1-lfm2-1.2b) | 1.2 | large_sft_rl | [XpressAI/shisa-v2.1-lfm2-1.2b-GGUF](https://huggingface.co/XpressAI/shisa-v2.1-lfm2-1.2b-GGUF) — `shisa-v2.1-lfm2-1.2b-Q4_K_M.gguf` | `Q4_K_M` | 0.73 | size only |
| 18 | [TinySwallow-1.5B-Instruct](https://huggingface.co/SakanaAI/TinySwallow-1.5B-Instruct) | 1.5 | lab_distillation | [SakanaAI/TinySwallow-1.5B-Instruct-GGUF](https://huggingface.co/SakanaAI/TinySwallow-1.5B-Instruct-GGUF) — `tinyswallow-1.5b-instruct-q5_k_m.gguf` | `Q5_K_M` | 1.13 | size only |
| 19 | [LFM2.5-1.2B-JP-202606](https://huggingface.co/LiquidAI/LFM2.5-1.2B-JP-202606) | 1.17 | first_party_japanese | [LiquidAI/LFM2.5-1.2B-JP-202606-GGUF](https://huggingface.co/LiquidAI/LFM2.5-1.2B-JP-202606-GGUF) — `LFM2.5-1.2B-JP-202606-Q4_K_M.gguf` | `Q4_K_M` | 0.73 | size only |
| 20 | [VNTL-Llama3-8B-v2](https://huggingface.co/lmg-anon/vntl-llama3-8b-v2-hf) | 8 | domain_exception | [lmg-anon/vntl-llama3-8b-v2-gguf](https://huggingface.co/lmg-anon/vntl-llama3-8b-v2-gguf) — `vntl-llama3-8b-v2-hf-q5_k_m.gguf` | `Q5_K_M` | 5.73 | size only |
| 21 | [Sugoi-14B-Ultra](https://huggingface.co/sugoitoolkit/Sugoi-14B-Ultra-HF) | 14.7 | domain_exception | [sugoitoolkit/Sugoi-14B-Ultra-GGUF](https://huggingface.co/sugoitoolkit/Sugoi-14B-Ultra-GGUF) — `Sugoi-14B-Ultra-Q4_K_M.gguf` | `Q4_K_M` | 8.99 | size only |
| 22 | [Sugoi-32B-Ultra](https://huggingface.co/sugoitoolkit/Sugoi-32B-Ultra-GGUF) | 32.5 | domain_exception | [sugoitoolkit/Sugoi-32B-Ultra-GGUF](https://huggingface.co/sugoitoolkit/Sugoi-32B-Ultra-GGUF) — `Sugoi-32B-Ultra-Q4_K_M.gguf` | `Q4_K_M` | 19.90 | no |
| 23 | [HY-MT1.5-7B](https://huggingface.co/tencent/HY-MT1.5-7B) | 8 | lab_original_or_existing_v2_specialist | [tencent/HY-MT1.5-7B-GGUF](https://huggingface.co/tencent/HY-MT1.5-7B-GGUF) — `HY-MT1.5-7B-Q4_K_M.gguf` | `Q4_K_M` | 4.62 | size only |
| 24 | [Seed-X-PPO-7B](https://huggingface.co/ByteDance-Seed/Seed-X-PPO-7B) | 8 | lab_original_or_existing_v2_specialist | [mradermacher/Seed-X-PPO-7B-GGUF](https://huggingface.co/mradermacher/Seed-X-PPO-7B-GGUF) — `Seed-X-PPO-7B.Q4_K_M.gguf` | `Q4_K_M` | 4.56 | size only |
| 25 | [CAT-Translate-3.3B-beta](https://huggingface.co/cyberagent/CAT-Translate-3.3b-beta) | 3.3 | lab_original_or_existing_v2_specialist | [mradermacher/CAT-Translate-3.3b-beta-GGUF](https://huggingface.co/mradermacher/CAT-Translate-3.3b-beta-GGUF) — `CAT-Translate-3.3b-beta.Q4_K_M.gguf` | `Q4_K_M` | 2.07 | size only |
| 26 | [Qwen3-Swallow-8B-RL-v0.2](https://huggingface.co/tokyotech-llm/Qwen3-Swallow-8B-RL-v0.2) | 8 | lab_original_or_existing_v2_specialist | [mmnga-o/Qwen3-Swallow-8B-RL-v0.2-gguf](https://huggingface.co/mmnga-o/Qwen3-Swallow-8B-RL-v0.2-gguf) — `Qwen3-Swallow-8B-RL-v0.2-Q4_K_M.gguf` | `Q4_K_M` | 5.03 | size only |
| 27 | [CAT-Translate-1.4B](https://huggingface.co/cyberagent/CAT-Translate-1.4b) | 1.4 | lab_original_or_existing_v2_specialist | [mradermacher/CAT-Translate-1.4b-GGUF](https://huggingface.co/mradermacher/CAT-Translate-1.4b-GGUF) — `CAT-Translate-1.4b.Q4_K_M.gguf` | `Q4_K_M` | 0.93 | size only |
| 28 | [HY-MT1.5-1.8B](https://huggingface.co/tencent/HY-MT1.5-1.8B) | 1.8 | lab_original_or_existing_v2_specialist | [tencent/HY-MT1.5-1.8B-GGUF](https://huggingface.co/tencent/HY-MT1.5-1.8B-GGUF) — `HY-MT1.5-1.8B-Q4_K_M.gguf` | `Q4_K_M` | 1.13 | size only |
| 29 | [CAT-Translate-0.8B](https://huggingface.co/cyberagent/CAT-Translate-0.8b) | 0.8 | lab_original_or_existing_v2_specialist | [mradermacher/CAT-Translate-0.8b-GGUF](https://huggingface.co/mradermacher/CAT-Translate-0.8b-GGUF) — `CAT-Translate-0.8b.Q4_K_M.gguf` | `Q4_K_M` | 0.53 | size only |
| 30 | [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) | 9 | lab_original_or_existing_v2_specialist | [bartowski/Qwen_Qwen3.5-9B-GGUF](https://huggingface.co/bartowski/Qwen_Qwen3.5-9B-GGUF) — `unverified` | `Q4_K_M` | — | no |
| 31 | [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) | 4 | lab_original_or_existing_v2_specialist | [bartowski/Qwen_Qwen3.5-4B-GGUF](https://huggingface.co/bartowski/Qwen_Qwen3.5-4B-GGUF) — `Qwen_Qwen3.5-4B-Q4_K_M.gguf` | `Q4_K_M` | 3.01 | size only |
| 32 | [TranslateGemma 27B IT](https://huggingface.co/google/translategemma-27b-it) | 27 | lab_original_or_existing_v2_specialist | [mradermacher/translategemma-27b-it-GGUF](https://huggingface.co/mradermacher/translategemma-27b-it-GGUF) — `unverified` | `Q4_K_M` | — | no |
| 33 | [TranslateGemma 12B IT](https://huggingface.co/google/translategemma-12b-it) | 12 | lab_original_or_existing_v2_specialist | [mradermacher/translategemma-12b-it-GGUF](https://huggingface.co/mradermacher/translategemma-12b-it-GGUF) — `translategemma-12b-it.Q4_K_M.gguf` | `Q4_K_M` | 7.30 | size only |
| 34 | [TranslateGemma 4B IT](https://huggingface.co/google/translategemma-4b-it) | 4 | lab_original_or_existing_v2_specialist | [mradermacher/translategemma-4b-it-GGUF](https://huggingface.co/mradermacher/translategemma-4b-it-GGUF) — `unverified` | `Q4_K_M` | — | no |
| 35 | [LLM-jp-4.1-8B Thinking](https://huggingface.co/llm-jp/llm-jp-4.1-8b-thinking) | 8.59 | lab_original_or_existing_v2_specialist | [llm-jp/llm-jp-4.1-8b-thinking-gguf](https://huggingface.co/llm-jp/llm-jp-4.1-8b-thinking-gguf) — `unverified` | `Q4_K_M` | — | no |
| 36 | [LFM2.5-24B-A2B](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B) | 24 | lab_original_or_existing_v2_specialist | [bartowski/LiquidAI_LFM2.5-24B-A2B-GGUF](https://huggingface.co/bartowski/LiquidAI_LFM2.5-24B-A2B-GGUF) — `LiquidAI_LFM2.5-24B-A2B-Q4_K_M.gguf` | `Q4_K_M` | 15.35 | no |
| 37 | [GLM-4.7-Flash](https://huggingface.co/zai-org/GLM-4.7-Flash) | 30 | lab_original_or_existing_v2_specialist | [bartowski/zai-org_GLM-4.7-Flash-GGUF](https://huggingface.co/bartowski/zai-org_GLM-4.7-Flash-GGUF) — `unverified` | `Q4_K_M` | — | no |
| 38 | [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) | 8 | lab_original_or_existing_v2_specialist | [bartowski/Qwen_Qwen3-8B-GGUF](https://huggingface.co/bartowski/Qwen_Qwen3-8B-GGUF) — `unverified` | `Q4_K_M` | — | no |
| 39 | [gpt-oss-20b](https://huggingface.co/openai/gpt-oss-20b) | 21 | lab_original_or_existing_v2_specialist | [bartowski/openai_gpt-oss-20b-GGUF](https://huggingface.co/bartowski/openai_gpt-oss-20b-GGUF) — `openai_gpt-oss-20b-Q4_K_M.gguf` | `Q4_K_M` | 11.67 | no |
| 40 | [Nemotron 3 Nano 30B-A3B](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16) | 32 | lab_original_or_existing_v2_specialist | [bartowski/nvidia_Nemotron-3-Nano-30B-A3B-GGUF](https://huggingface.co/bartowski/nvidia_Nemotron-3-Nano-30B-A3B-GGUF) — `unverified` | `Q4_K_M` | — | no |
| 41 | [Gemma 4 E4B IT](https://huggingface.co/google/gemma-4-E4B-it) | 8 | lab_original_or_existing_v2_specialist | [unsloth/gemma-4-E4B-it-GGUF](https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF) — `unverified` | `UD-Q4_K_XL` | — | no |
| 42 | [Gemma 4 E2B IT](https://huggingface.co/google/gemma-4-E2B-it) | 5.1 | lab_original_or_existing_v2_specialist | [unsloth/gemma-4-E2B-it-GGUF](https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF) — `unverified` | `UD-Q4_K_XL` | — | no |
| 43 | [Ministral 3 8B Instruct](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512) | 8 | lab_original_or_existing_v2_specialist | [unsloth/Ministral-3-8B-Instruct-2512-GGUF](https://huggingface.co/unsloth/Ministral-3-8B-Instruct-2512-GGUF) — `unverified` | `UD-Q4_K_XL` | — | no |
| 44 | [Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) | 2 | lab_original_or_existing_v2_specialist | [bartowski/Qwen_Qwen3.5-2B-GGUF](https://huggingface.co/bartowski/Qwen_Qwen3.5-2B-GGUF) — `unverified` | `Q4_K_M` | — | no |
| 45 | [LFM2.5-1.2B Instruct](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct) | 1.2 | lab_original_or_existing_v2_specialist | [LiquidAI/LFM2.5-1.2B-Instruct-GGUF](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF) — `unverified` | `Q4_K_M` | — | no |
| 46 | [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) **v4** | 4 | lab_original_or_existing_v2_specialist | [bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF](https://huggingface.co/bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF) — `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` | `Q4_K_M` | 2.50 | size only |
| 47 | [rinna-llama-3-youko-8b](https://huggingface.co/rinna/llama-3-youko-8b) **v4** **control** | 8 | lab_original_or_existing_v2_specialist | [mmnga/rinna-llama-3-youko-8b-gguf](https://huggingface.co/mmnga/rinna-llama-3-youko-8b-gguf) — `rinna-llama-3-youko-8b-Q4_K_M.gguf` | `Q4_K_M` | 4.92 | size only |
| 48 | [Qwen2.5-14B-Instruct](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct) **v4** | 14.7 | lab_original_or_existing_v2_specialist | [bartowski/Qwen2.5-14B-Instruct-GGUF](https://huggingface.co/bartowski/Qwen2.5-14B-Instruct-GGUF) — `Qwen2.5-14B-Instruct-Q4_K_M.gguf` | `Q4_K_M` | 8.99 | size only |
| 49 | [Phi-4 14B](https://huggingface.co/microsoft/phi-4) **v4** | 14.7 | lab_original_or_existing_v2_specialist | [bartowski/phi-4-GGUF](https://huggingface.co/bartowski/phi-4-GGUF) — `phi-4-Q4_K_M.gguf` | `Q4_K_M` | 9.05 | no |
| 50 | [Llama-3.2-3B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) **v4** | 3 | lab_original_or_existing_v2_specialist | [bartowski/Llama-3.2-3B-Instruct-GGUF](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF) — `Llama-3.2-3B-Instruct-Q4_K_M.gguf` | `Q4_K_M` | 2.02 | size only |

† Decimal gigabytes from repository listings, not measured physical footprint or a promise of model correctness. Verify quant names, file sizes, shard counts, immutable repo SHAs, native prompts, and actual loading with `tools/resolve_ggufs.py` and five-item canaries.

## v4 candidate changes

**Added:** Llama-3.2-3B-Instruct, Phi-4 14B, Qwen2.5-14B-Instruct, Qwen3-4B-Instruct-2507, rinna-llama-3-youko-8b.

**Removed:** Aya Expanse 8B, Hunyuan-MT-7B, LFM2.5-2.6B, Qwen2.5-7B Instruct, RakutenAI-7B-instruct.

## Control comparisons

| Adaptation | Base/control | Scope |
|---|---|---|
| VNTL-Llama3-8B-v2 | rinna-llama-3-youko-8b | Base-vs-adaptation *diagnostic-only ancestor; non-instruction model needs separate prompting* |
| Sugoi-14B-Ultra | Qwen2.5-14B-Instruct | Base-vs-adaptation |
| Shisa-v2.1-unphi4-14B | Phi-4 14B | Base-vs-adaptation |
| Shisa-v2.1-llama3.2-3B | Llama-3.2-3B-Instruct | Base-vs-adaptation |
| Shisa-v2.1-qwen3-8B | Qwen3-8B | Base-vs-adaptation |
| GPT-OSS-Swallow-20B-RL-v0.1 | gpt-oss-20b | Base-vs-adaptation |

A base-model control establishes *relative improvement* only after identical items, compatible prompting, and quant/hardware choices. Original ancestors lacking instruction tuning are **not** apples-to-apples leaderboard entries.

## Runtime/policy constraints

- TranslateGemma needs a native language-coded template. The ordinary llama.cpp chat adapter is not declared qualified.
- VNTL v2 expects the publisher `Metadata` / `Japanese` / `English` Llama3 completion format without a literal duplicated BOS; full multiline scenes are supported as an experimental arm.
- `rinna-llama-3-youko-8b` is VNTL v2’s declared Japanese continued-pretrained base, **not** ordinary Meta Llama-3-8B.
- `--reasoning on/off/auto`, `--jinja` and `--alias` require a compatible recent llama-server; the matrix runner preflights them for execution.
- Q6/Q8 require independent Hugging Face quant attestation, and are separate experimental arms. The Q4/default selection is not a universal best-quality quant.
- 16 GB Steam Deck compatibility cannot be decided from GGUF filesize alone. A 14B 8.99 GB file is **not** qualified for the Deck without actual RAM/KV checks.
- Third-party converters are provisional until provenance/quant inspection and canaries; page listings are **not** equivalent to runtime qualification.
- Priority rank is a candidate order, never an inferred result or a public translation leaderboard.

See [README.md](README.md), [PROTOCOL.md](PROTOCOL.md), [ELIGIBILITY_POLICY.md](ELIGIBILITY_POLICY.md).
