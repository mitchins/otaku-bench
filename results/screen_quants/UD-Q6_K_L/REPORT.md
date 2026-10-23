# OtakuBench screen mission — run report

Latency is full-line wall time on the mission GPU (cold prefill, no cross-request cache reuse). `d0` = line alone, `d6` = six preceding dialogue lines (gate), `d24` = long history.

| # | model | style | GB | VRAM MiB | status | ttft d6 | line d0 | line d6 | line d24 | tok/s | arms |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| 1 | Qwen3.8-27B | chat | 24.194 | 22482 | COMPLETE | 0.754s | 1.258s | 1.334s | 1.53s | 24.115 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
