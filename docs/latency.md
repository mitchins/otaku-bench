# Latency and fit

Every model in the catalog, run one at a time on GPU 0 of an RTX 3090 (24 GB): 2k context, 256-token cap, thinking off.

--8<-- "results/screen/REPORT.md:2:"

## Follow-up arms

Some models can't run under the baseline profile, so they get a labelled variant instead. Variant results never replace the baseline row.

| Variant | Applies to | What changes |
|---|---|---|
| `effort-low` | gpt-oss-20b, GPT-OSS-Swallow-20B | Harmony format has no true "thinking off"; uses `reasoning_effort: low` and a 1024-token cap |
| `empty-think` | LFM2.5-24B-A2B | Its template always opens `<think>`; pre-fills an empty think block (unofficial) |
| `primed` | rinna-llama-3-youko-8b (base model) | Few-shot frame where every answer ends in `<sep>`, which acts as a stop |

### effort-low

--8<-- "results/screen_variants/effort-low/REPORT.md:2:"

### empty-think

--8<-- "results/screen_variants/empty-think/REPORT.md:2:"

### primed

--8<-- "results/screen_variants/primed/REPORT.md:2:"
