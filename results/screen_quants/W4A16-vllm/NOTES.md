# Gemma 4 26B-A4B IT QAT W4A16 (vLLM, local RTX 3090 GPU 1): qualification only

The LAN workhorse: `reinforce20001/gemma4-26b-a4b-it-qat-w4a16-ct` @ 69fa1750, compressed-tensors W4A16, served by the
user's own vLLM (port 8000, custom tool-calling Gemma 4 chat template; thinking off renders the same empty thought
channel as the stock template). Run 2026-11-06 with remote_arm.py, 8 requests at a time at low scheduling priority
(`priority: 10`) so the server's own traffic came first. Translations are valid for judging; timings are not comparable
with the llama.cpp gate (different engine, batching, shared server), so the board shows no speed and the row stays off
the board, like NVFP4-vllm. All arms 0 errors, 0 reasoning tokens; hard slice 0 screen-contract violations.
