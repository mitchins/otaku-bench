# OtakuBench screen mission — run report

Latency is full-line wall time on the mission GPU with a warm server: weights resident, kernels warmed by the canary, and the instruction prefix served from the prompt cache. Dialogue history is prefilled fresh on every request, as a sliding-window client would send it. `d0` = line alone (minimal-context baseline); `d6` = six preceding lines (headline latency and gate); `d24` = long history (context scaling). Append-only clients that keep history cached have not been measured yet.

| # | model | style | GB | VRAM MiB | status | ttft d6 | line d0 | line d6 | line d24 | tok/s | arms |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| 47 | rinna-llama-3-youko-8b | base_primed | 4.921 | 5094 | PARTIAL | 0.021s | 0.143s | 0.143s | — | 116.871 | L=250/250 s_bare=31/31 s_full=29/31 |

## Needs a look

- 47 rinna-llama-3-youko-8b — PARTIAL 
