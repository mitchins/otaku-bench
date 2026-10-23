# OtakuBench screen mission — run report

Latency is full-line wall time on the mission GPU (cold prefill, no cross-request cache reuse). `d0` = line alone, `d6` = six preceding dialogue lines (gate), `d24` = long history.

| # | model | style | GB | VRAM MiB | status | ttft d6 | line d0 | line d6 | line d24 | tok/s | arms |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| 2 | Gemma 4 31B IT | chat | 22.609 | 23400 | COMPLETE | 0.54s | 1.313s | 1.21s | 1.631s | 21.723 | L=250/250 s_bare=31/31 s_context=31/31 s_full=31/31 |
