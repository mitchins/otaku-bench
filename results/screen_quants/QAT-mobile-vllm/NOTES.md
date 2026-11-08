# Gemma 4 E2B IT QAT mobile (wNa8o8), vLLM on the local RTX 3090 GPU 0: quality qualification only

`google/gemma-4-E2B-it-qat-mobile-ct` @ 594b1c7919e98f8275aefdc844c306d709e61727 (2.6 GB, Apache-2.0). Google's mobile
QAT scheme from `config.json`: 2-bit lm_head, token embeddings and MLPs of layers 15+; 4-bit attention, MLPs of layers
0-14 and per-layer embeddings; 8-bit vision tower and per-layer gates; static int8 activations; quantised KV cache.

Served 2026-11-08 by vLLM 0.32.0 (the vllm-serve env, run as a separate process on GPU 0, port 8091;
`--gpu-memory-utilization 0.5 --max-model-len 8192 --no-enable-prefix-caching --limit-mm-per-prompt
'{"image":0,"audio":0}'`; LD_LIBRARY_PATH set to the env's nvidia/cu13/lib so the wNa8o8 JIT kernels find
libnvrtc-builtins). Arms via mission/studies/remote_arm.py, 8 workers, thinking off. Timings are not comparable with
the llama.cpp gate (different engine and batching), so the row stays off the board, like W4A16-vllm.

- All arms and slices: 0 errors, 0 empty, 0 reasoning tokens.
- Context arm: 10/31 scenes return the Japanese untranslated (QAT Q4_0 llama.cpp: 3/31).
- Hard: 6/167 source echoes under the screen-output contract (QAT Q4_0: 1 echo + 2 extra lines).
- Identical to the QAT Q4_0 GGUF outputs: lines 75/250, scenes 2-8/31 per arm.
- Kernel check: vLLM vs Google's transformers reference (`google/gemma-4-E2B-it-qat-mobile-transformers` @ dd693ff4,
  transformers 5.19, greedy) on the 50 dev lines: 29/50 identical, the rest same-meaning rewordings with no
  direction. The vLLM wNa8o8 kernels implement the scheme; outputs are valid for judging.

## Prompt-wording probe (2026-11-08, DEV items and own lines only; mission/studies/e2b_prompt_probe.py)

Question (user): does E2B, like Gemini 3.5 Flash-Lite, echo the Japanese back and benefit from naming the target
language? Context items: 12 from the 6 dev scenes split by line, 49 from the 50 dev lines chained as history, 19 from
20 hand-written lines (no benchmark data). Sampled 4x per item (temperature 1.0, top-p 0.95, top-k 64), since greedy
echoes flip between runs. Source echo = the screen-output contract's `source_echo`.

| Variant | Mobile (vLLM) ctx echo | Google Q4_0 (llama.cpp) ctx echo | Lines with Japanese/meta left |
|---|---|---|---|
| shared prompt (board) | 5/320 | 24/320 | 0/200 both |
| explicit-target (user turn names "from Japanese to English") | 0/320 | 0/320 | 0/200 both |
| short-system (Flash-Lite's fix) | 2/320 | 0/320 | mobile 21/200: "Here are a few ways to translate..." |
| caps system ("FROM JAPANESE TO ENGLISH ... English only") + explicit | 0/320 | 0/320 | 0/200 |
| caps + "(Reply in English only.)" suffix | 0/320 (2 extra-line) | 0/320 (1 extra-line) | 0/200 |

Both E2B builds echo the source on some context turns with the shared prompt (Q4_0 more than mobile on this set;
the eval-arm 10/31 vs 3/31 the other way round is single greedy runs, so treat build differences as noise). Naming
the target language in the user turn removes it on both; stronger caps wording adds nothing, the suffix makes it
translate the context too, and Flash-Lite's short system prompt breaks E2B lines (the "output only" clause matters).
Greedy wording changes with explicit-target look neutral (go back -> go home, cat -> cat's paw; a pun quote dropped).
