# Gemini 3.5 Flash-Lite (cloud)*

\* Full scenes use only the first sentence of the system prompt; with the full prompt it returns some scenes untranslated.

Answers "how does a local model compare with even the cheapest paid API?" On the board as one entry: lines from the shared
prompt (results/screen/C01_…), scenes from the short prompt (results/screen_variants/short-system/C01_…). Same payloads
otherwise, temperature 0, through the LAN proxy at 12 s pacing. There are no timings or VRAM, since it's a cloud round-trip.

Evidence for the footnote (2026-10-29): with the shared prompt, 5 scenes echoed the Japanese on every retry. An ablation on
P003 traced it to the "Preserve … speaker tags, line breaks …" sentence (temperature and the user turn made no difference;
results/screen_variants/explicit-target/). With the short prompt there were 0/93 echoes, plus 1 commentary and 2 format slips,
judged as they are.
