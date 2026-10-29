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

**Cause (2026-10-29 ablation, P003 full, 3–4 calls per row).** The echo is triggered by the constraint wording in the shared
system prompt, not by the user message missing a target language. An `explicit-target` variant naming "from Japanese to English" in the
user message still echoed the same 4 full scenes (results/screen_variants/explicit-target/). Echo rate by system prompt: the full
prompt echoed nearly every time; no system prompt translated 3/3; only "Translate the supplied Japanese into faithful, natural English."
translated 3/3; adding "Output only the translation with no commentary." translated 1/3; "Preserve nuance, speaker tags, line breaks, …"
echoed 3/3. Temperature (0, 1.0, default) and streaming make no difference. Local models get the same prompt and don't echo, so the
benchmark prompt stays as it is.

**Indicative arm: `short-system` (user decision 2026-10-29; not parity).** The scenes were re-run with only the first sentence of the
system prompt plus the explicit-target user turn (results/screen_variants/short-system/). Lines are copied from the shared-prompt run
(they never echoed), so all 200 line judgments are reused. Result: 0/93 echoes with no retries needed, but compliance slips appear without
"Output only the translation": in full scenes, 1 commentary item (P007: a preamble, and the Japanese interleaved line by line) and 2 format
items (e.g. P003 invents `**Grandmother:**` speaker labels on narration). They're judged as they are.
