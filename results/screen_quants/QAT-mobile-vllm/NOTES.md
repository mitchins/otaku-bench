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
