# OtakuBench screen mission — run report

Latency is full-line wall time on the mission GPU with a warm server: weights resident, kernels warmed by the canary, and the instruction prefix served from the prompt cache. Dialogue history is prefilled fresh on every request, as a sliding-window client would send it. `d0` = line alone (minimal-context baseline); `d6` = six preceding lines (headline latency and gate); `d24` = long history (context scaling). Append-only clients that keep history cached have not been measured yet.

| # | model | style | GB | VRAM MiB | status | ttft d6 | line d0 | line d6 | line d24 | tok/s | arms |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| 39 | gpt-oss-20b | chat | 11.673 | 11216 | PARTIAL | 0.419s | 0.525s | 0.493s | 0.518s | 176.604 | L=249/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
| 12 | GPT-OSS-Swallow-20B-RL-v0.1 | chat | 15.805 | 15156 | LATENCY_FAIL | 2.724s | 2.571s | 2.864s | 3.009s | 164.058 |  |

## Needs a look

- 39 gpt-oss-20b — PARTIAL 
