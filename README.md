# OtakuBench

Which local GGUF model translates the visual-novel line on screen well enough, and fast enough, to read along with?

**Docs and results: https://mitchins.github.io/otaku-bench/**

- **Screen-translator profile:** 2k context, 256-token cap, thinking off, one model at a time on a single GPU.
- **Latency first:** a line must finish in under 2 s (median) with 6 lines of history, or the model is never scored.
- **Quality second:** an LLM judge scores the survivors on 200 hard single lines and 31 full scenes.

```bash
./mission/setup.sh && ./mission/run.sh --prune   # sweep on the GPU host
./mission/judge_queue.sh                         # judge inside a daily token cap
zensical serve                                   # docs locally
```

The eval split's gold, the raw model outputs and the per-item judgments are encrypted with git-crypt so they stay out of training data. See [Data policy](docs/data.md). The dev split is public in `benchmark/otakubench/data/public/`.

The full v4 design notes are in `README_V4.md`, `PROTOCOL.md`, `CATALOG.md` and `ELIGIBILITY_POLICY.md`.
