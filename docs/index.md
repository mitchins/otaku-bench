# OtakuBench

**Question:** which local GGUF model translates the visual-novel line on screen well enough, and fast enough, to read along with?

OtakuBench doesn't try to produce a general leaderboard of Japanese ability. It runs each model the way a screen translator really runs, and keeps only what matters for that job:

- **Short context.** A 2k context window: the line on screen, plus a few lines of dialogue history.
- **Short output.** A 256-token output cap. A line is 20–60 tokens; hitting the cap means the model is thinking or rambling.
- **Thinking off.** Nobody waits 40 seconds for one line of dialogue.
- **Latency first.** Before any quality testing, each model must finish a line in under 2 s (median) and 3 s (slowest 10%), measured with 6 lines of history. Models that fail are never scored.
- **Quality second.** Survivors are scored by an LLM judge on 200 hard single lines (idioms, keigo, negation, ellipsis, dialect) and 31 full scenes.

## Status

| | |
|---|---|
| Models in the catalog | 50 (0.6–35B, chosen for laboratory provenance and Japanese focus) |
| Ran on RTX 3090 | 44 produced output · 5 are out for screen use (thinking can't be switched off) · 1 deferred to a larger GPU |
| Judged | in progress; a daily queue runs inside the judge's free token allowance |

Start with the **[ranking](ranking.md)**, or see **[latency](latency.md)** for every model's speed and memory use.

!!! note "Early results"
    One judge (GPT-6.1 Sol) and one run per model. Differences of a few tenths of a point between neighbouring models are within noise until a paired comparison says otherwise.
