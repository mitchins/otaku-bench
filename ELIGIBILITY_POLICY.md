# OtakuBench v4 — frozen model-eligibility policy

**Version:** 4.0, **date:** 2026-10-23. This defines entry to the **model-selection matrix**, not qualification of weights, performance, safety, or runtime compatibility.

## Admission rules

1. **Size and task — the hardware rule (2026-10-23):** the question is *the best Japanese translation you can get from one consumer 24 GB GPU (RTX 3090 class, or Radeon / Apple Silicon equivalents), fast enough to use while playing*. The original 0.6–35B total-parameter range was a proxy for that, and is now applied in spirit, not as a hard limit. A larger model, typically a MoE with few active parameters, is eligible as a normal candidate if all of the following hold:
   - it loads **fully GPU-resident on one 24 GB card**: no CPU layer offload, no multi-GPU;
   - it uses a **recommended, quality-oriented quant** from the origin lab or Bartowski/Unsloth, never a degraded quant picked only to squeeze it in;
   - it runs at the **2k-context screen profile**;
   - it passes the **same latency gate** (median ≤ 2 s, p90 ≤ 3 s at 6 lines of history).

   Fit is measured at load, not estimated: a model that runs out of memory is deferred, not excluded on paper. The model must also accept text-based Japanese→English translation tasks. Check base-model lineage and total weights. First admission under this rule: Flint 40B-A2.5B at IQ4_XS (rank 51).
2. **Publisher and provenance:** a first-party model from an identifiable lab/organisation is eligible. Original weights are separate from their GGUF *conversions*, even when a converter owns the Hugging Face quant repo. Exact quant files are never inferred from a naming convention; they need to appear in the repo tree and then be verified via HF metadata/SHA.
3. **Substantial adaptions:** laboratory/organisation Japanese CPT plus SFT/RL, or substantial, described bilingual SFT/DPO/RL or distillation, qualify as independent model candidates. For undisclosed token counts, require both documentation of training and published relative evaluation against the base. Dataset source and size are evidence, not a fixed threshold. A merge may be one stage of a broader training pipeline, but an untrained merge-only release is excluded.
4. **Domain exception:** models explicitly trained for Japanese→English **VN/game dialogue translation** can qualify without billions of training tokens, if the publisher provides its own model card, training purpose/dataset description, and a runnable public weight or GGUF. Distinctly mark these `domain_exception`, including incomplete training/licence provenance. Exceptions must be narrow, reproducible and capped (v4 contains only VNTL and Sugoi families).
5. **One *current* checkpoint per publisher family and parameter variant** unless architecturally distinct variants (e.g. dense 32B vs MoE 30B-A3B) matter. Superseded versions may remain only for explicit base-vs-adaptation experiments; do not keep multiple slight version increments just to pad the 50.
6. **Disallowed:** unsubstantiated character/roleplay tunes, generic one-person LoRAs, abliterations, untrained merges, arbitrary checkpoint soups and models without public provenance. A community conversion of unchanged published weights is **not** a community fine-tune. The domain exception is the only intentional relaxation of the source-training rule.
7. **Utility over popularity:** break ties by expected Japanese→English literary translation ability, documented Japanese gains, release adoption, Deck feasibility and independent family diversity. Keep a few original bases as **controls** to quantify improvements, not as likely winners. Selection ranks are hypothesis, not scores.

## Quantization and runtime qualification

- Test a common recommended Q4_K_M/UD-Q4 or first-party published quant as primary; preserve publisher-native formats. VNTL and Sakana TinySwallow publish **Q5_K_M** as their recommended convenience choice. Their default should not be flattened to Q4 to fit a template.
- Compare **Q6_K and/or Q8_0** on 1–9B when actual files exist and memory tests permit. Q8 can change the ranking, so results must identify quant/params/template/reasoning/device.
- Track **quantization publisher separately** from the training publisher. Prefer origin-lab or Bartowski/Unsloth. Other convertors (mmnga, mradermacher, XpressAI, etc.) can be provisional, with exact-file inspection followed by SHA attestation, model-card/weight ancestry check and runtime canary. A listed GGUF file alone is not proof of identical weights or model correctness. `ultimatechris/Qwen3-Swallow-32B-RL-v0.2-GGUF` is specifically **provisional** pending independently verified conversion parity. Do not automate large downloads from nonapproved publishers without review.
- A model is **not qualified** until its expected GGUF and source linkage are attested and it has passed a canary under the native prompt, plus an actual translation-quality evaluation. This v4 release performs *none* of the runtime and translation-quality stages.
- Steam Deck capacity is NOT determined by file size alone; Deck test requires OS/VRAM/KV/context and actual load measurements on 16GB shared memory. The `deck_default_candidate` field means **file size <=9GB only**, not 'it fits'. A 14B Q4 GGUF at 8.99GB should still be treated cautiously.
- Preserve the five-case canary and all 250 original lines plus 31 scenes for evaluation; do not use scene answers in the translator prompt. Domain specialists may have their own native prompt templates; compare native and standard formats as separate arms rather than penalising models for mismatched prompt contracts.

## Selected adaptations (unchanged in v4)

| Family | Candidates | Training basis / evidence | Lane |
|---|---|---|---|
| Qwen3 Swallow | 8B RL, 30B-A3B RL (retained), 32B RL (new) | Institute of Science Tokyo/AIST CPT→SFT→RL, https://huggingface.co/tokyotech-llm/Qwen3-Swallow-32B-RL-v0.2 | `heavy_adaptation` |
| GPT-OSS Swallow | 20B RL | CPT→SFT→RL and Japanese reasoning, https://swallow-llm.github.io/gptoss-swallow.en.html | `heavy_adaptation` |
| Nemotron Nano Japanese | 9B v2 | NVIDIA first-party CPT/SFT, https://huggingface.co/blog/nvidia/nemotron-nano-9b-v2-japanese | `first_party_japanese` |
| Shisa V2.1 | 1.2B, 3B, 8B, 14B | Shisa organization bilingual SFT/DPO/RL + measurements: https://huggingface.co/shisa-ai/shisa-v2.1-qwen3-8b | `large_sft_rl` |
| TinySwallow | 1.5B | Sakana lab TAID distillation and JA tuning https://huggingface.co/SakanaAI/TinySwallow-1.5B-Instruct-GGUF | `lab_distillation` |
| LFM2.5 JP | 1.2B 202606 | Liquid first-party JA specialization and official GGUF https://huggingface.co/LiquidAI/LFM2.5-1.2B-JP-202606 | `first_party_japanese` |
| VNTL | Llama 3 8B v2 | VN-only QLoRA; model card, dataset and VN leaderboard https://huggingface.co/lmg-anon/vntl-llama3-8b-v2-gguf | `domain_exception` |
| Sugoi LLM | 14B Ultra, 32B Ultra | VN/game translation-specific training; first-party quants; source weights/checkpoints must be independently audited for 32B https://huggingface.co/sugoitoolkit/Sugoi-14B-Ultra-GGUF | `domain_exception` |

## Deliberately omitted, not judged failures

Llama-3.1 Swallow, older Bakeneko, ELYZA-JP and other old-generation Japanese models remain eligible **in principle**; they are not inserted just because the policy permits them. The 50-slot constraint favors latest/relevant models and retaining a handful of base control models. `Llama-3.2-3B-Instruct` has been **restored in v4 specifically as the Shisa 3B base-control arm**, not as a predicted Japanese winner. Qwen2.5-14B and Phi-4 are likewise restored parent controls.

## Required files and status semantics

`data/otakubench50.json` is the active matrix. `data/otakubench50_v2.json` retains the previous selection. `data/model_selection_delta_v3.json` and `data/model_selection_delta_v4.json` list revisions with traceability. Source URLs are row-specific in CSV/JSON. Web page/file trees were checked on 2026-10-23 for the 12 added models; *none* of the 12 new repositories has a live Hugging Face API revision attestation in the working container; *none* has been run or translation-scored. Re-running the web checks or fetching recent model metadata can change admission.
