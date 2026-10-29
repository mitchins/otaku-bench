# Gemini 3.5 Flash-Lite: cloud reference (off the board)

Served through the user's LAN proxy (`gemini-3.5-flash-lite [google]`), with the same screen-profile payloads as every
local model (system prompt, temperature 0, 256-token cap). The key allows about 5 requests a minute, so requests were paced
at 12 s with retries on HTTP 429. Its timings are cloud round-trips and aren't comparable with the 3090 numbers.

**Footnote: echoes.** On multi-line scenes the endpoint sometimes returns the Japanese source unchanged. This is
non-deterministic: the identical request at temperature 0 has translated on one call and echoed on the next. At the user's
direction (2026-10-29), an echo was treated as a bad run rather than indicative, and re-requested (`remote_arm.py --retry-echo`).
`echo_retries` on each record counts the re-asks in the final pass only.

| arm | echoed on first pass | still echoing after retries |
|---|---:|---:|
| lines (250) | 0 | 0 |
| scenes bare (31) | 5 | 0 |
| scenes context (31) | 4 | 1 (P022) |
| scenes full (31) | 11 | 4 (P003, P007, P016, P021) |

The five that remain echoed on every attempt, roughly 24–29 each across four passes, so for these inputs it's systematic.
They keep the standard automatic zero, like any model's echo. Lines were never affected.
