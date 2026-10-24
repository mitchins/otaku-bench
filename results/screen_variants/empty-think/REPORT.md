# OtakuBench screen mission — run report

Latency is full-line wall time on the mission GPU with a warm server: weights resident, kernels warmed by the canary, and the instruction prefix served from the prompt cache. Dialogue history is prefilled fresh on every request, as a sliding-window client would send it. `d0` = line alone (minimal-context baseline); `d6` = six preceding lines (headline latency and gate); `d24` = long history (context scaling). Append-only clients that keep history cached have not been measured yet.

| # | model | style | GB | VRAM MiB | status | ttft d6 | line d0 | line d6 | line d24 | tok/s | arms |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| 36 | LFM2.5-24B-A2B | chat | 15.352 | 15080 | PARTIAL | 0.083s | 0.139s | 0.156s | 0.192s | 189.617 | L=249/250 s_bare=31/31 s_context=31/31 s_full=30/31 |
| 51 | Flint 40B-A2.5B | chat | 22.446 | 21642 | PARTIAL | 0.146s | 0.236s | 0.274s | 0.372s | 110.616 | L=248/250 s_bare=31/31 s_context=30/31 s_full=31/31 |

## Needs a look

- 36 LFM2.5-24B-A2B — PARTIAL 
- 51 Flint 40B-A2.5B — PARTIAL 
