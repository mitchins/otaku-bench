# OtakuBench screen mission — run report

Latency is full-line wall time on the mission GPU with a warm server: weights resident, kernels warmed by the canary, and the instruction prefix served from the prompt cache. Dialogue history is prefilled fresh on every request, as a sliding-window client would send it. `d0` = line alone (minimal-context baseline); `d6` = six preceding lines (headline latency and gate); `d24` = long history (context scaling). Append-only clients that keep history cached have not been measured yet.

| # | model | style | GB | VRAM MiB | status | ttft d6 | line d0 | line d6 | line d24 | tok/s | arms |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| 36 | LFM2.5-24B-A2B | chat | 15.352 | 15080 | COMPLETE | 0.083s | 0.143s | 0.162s | 0.192s | 190.034 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 51 | Flint 40B-A2.5B | chat | 22.446 | 21642 | PARTIAL | 0.147s | 0.249s | 0.282s | 0.345s | 109.662 | L=250/250 s_bare=29/31 s_context=26/31 s_full=27/31 |

## Needs a look

- 51 Flint 40B-A2.5B — PARTIAL 
