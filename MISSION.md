# OtakuBench — screen-translator mission

**Question:** which local GGUF translates the line on screen well enough, fast enough?

This mission sits on top of OtakuBench v4. It doesn't produce a leaderboard. It runs each model the way a VN screen translator would actually use it.

| Setting | Value | Why |
|---|---|---|
| Context | 2048 | A page plus dialogue history fits in about 1k tokens |
| Output cap | 256 tokens | A line is 20–60 tokens. Hitting the cap means the model is thinking or rambling, which fails the run |
| Thinking | off (`--reasoning off` / `--reasoning-budget 0` + `enable_thinking:false`) | Nobody waits 40 s for a line |
| GPU | one, pinned by PCI bus order (`--gpu 0` = nvidia-smi index 0) | GPU 1 on tiger is busy with vLLM |
| Order | smallest file first | The big memory edge cases come last |

## Per model, one at a time

1. **Fit check.** If file size plus 1.8 GB of headroom exceeds free VRAM, the model is recorded as `DEFER_5090` and never downloaded. A CUDA out-of-memory error at load is also recorded as `DEFER_5090`.
2. **Download** the pinned GGUF (repo SHA from `data/attested.json`), then start `llama-server -ngl 99 -c 2048`.
3. **Canary.** Five fixed lines must each produce a visible translation, or the model gets `CANARY_FAILED`.
4. **Latency gate plus history sweep.** 12 scenes × 0/3/6/12/24 preceding lines, streamed so time to first token is captured. The gate is at depth 6: median ≤ 2.0 s and p90 ≤ 3.0 s per line (both adjustable). Failing gives `LATENCY_FAIL`, and the quality arms are skipped.
5. **Quality arms**, written in the format `tools/judge.py` already reads: 250 lines (bare), plus the 31 scenes as bare, with context, and full.

The per-model output is in `results/screen/NN_model/` (`server.log`, `canary`, `latency`, the arm JSONLs). The run log is `results/screen/summary.jsonl`.

## Commands (on tiger)

```bash
./mission/setup.sh                         # venv, find llama-server, pin GGUFs (metadata only), print plan
BUILD_LLAMA=1 ./mission/setup.sh           # ...or build llama.cpp with CUDA into vendor/
./mission/run.sh --ranks 15,18,19,20,31,46 # pilot: six models, about an hour
./mission/run.sh                           # full sweep in tmux session 'otb'
./mission/run.sh --prune                   # same, deleting each GGUF after it runs (≈430 GB otherwise)
python mission/report.py                   # REPORT.md (latency table) + SKIM.md (side-by-side scenes)
```

Reruns are safe: finished models and finished items are skipped, and `--redo` forces a model to run again. Deferred models are retried on each pass, so on the 5090 host it's the same command with `--gpu N`. To build there, use `CUDA_ARCHS="86;120" BUILD_LLAMA=1 ./mission/setup.sh`.

## Scoring afterwards (metered, off the GPU box)

```bash
python tools/judge.py --responses results/screen/46_Qwen3-4B-Instruct-2507/scenes_full.jsonl \
  --dataset scenes --mode full --provider anthropic --model claude-opus-5-5 --output results/screen/judge.jsonl
```

A dry run is the default. Add `--execute` to spend money.

## Limits worth knowing

- Latency is cold prefill on the 3090. Real VN use, where history is append-only, gets prompt-cache hits and runs faster. Deck latency has to be measured on the Deck.
- The scenes only carry 2–3 lines of real context, so the 6/12/24 depths use earlier scenes as realistic filler. That measures the latency cost of history, not its quality benefit.
- TranslateGemma is skipped because its native template on llama-server is still unverified.
