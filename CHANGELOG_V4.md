# v3 → v4 — final Claude-review repair disposition

| Finding | Change made | Verification/limit |
|---|---|---|
| `JMB-047` clunky keigo | `ご存じだったのなら...` | source updated, stable ID retained |
| `JMB-093` gold forces sarcasm | Added three admiration/neutral readings, removed context leakage | bare Japanese remains genuinely ambiguous |
| `JMB-199` repeats home-greeting/absence trope | Changed to 回覧板 neighborhood exclusion | distinct cultural social-context item |
| `風の便り` only unit test | Added as `JMB-073`, preserving 250 count, original idiom category and split | tests hearsay vs mistranslated “wind chime” |
| Scene targets trivially easy | Retargeted P001/P002/P005/P025/P027/P031, made full-scene outcome primary | 31 scenes still diagnostic only |
| Mature / violence / profanity not challenging | Expanded P019–P021 to consensual adult sexual language, graphic fictional injury and profanity | provenance is synthetic; review for grade appropriateness before public release |
| Fake text-hook “noise” | P009/P025 include duplicated UI and mid-word/midutterance breaks; differentiate intentional stutter | reference English normalizes extraction artifacts |
| P011 voice inconsistent | Laugh verb consistent, smile alternate accepted | bilingual judge to adjudicate any residual ambiguity |
| P029 stiff double negative | “So everyone understands, then?” | irony preserved |
| Candidate judgement globally quarantines gold | Global exclusions **only** from two material/invalid gold-audit flags on different providers. One auditor conflict blocks publishing; per-model candidate uncertainty stays local | regression test for contaminated denominator |
| No paired model comparisons | Same-item paired bootstrap deltas, context benefit utility, bounded default adjacent pairs | exploratory unadjusted confidence intervals |
| 25 eval scenes might be published as rank | minimum 60 independent scene cases + gold/judge/coverage gates | v4 scenes always diagnostic-only |
| Old inference results reused after changing corpus | Source SHA required by judges, gold SHA required by aggregator | rejects stale/unfingerprinted outputs |
| Unpinned models could reach a trusted score | Inference and judge records now retain revision SHA, weight-attestation and five-case canary results; publication gate requires all three | synthetic provenance regressions |
| Nonchat `base_completion` mistakenly decoded as chat | Parses `/completions` response `.choices[].text` | offline mocked transport regression test |
| `llama-server` reasoning unknown | explicit `--reasoning`, `--jinja`, `--alias` capability preflight before launch | requires actual llama-server locally |
| VNTL incorrect parent and double BOS | original ancestor `rinna/llama-3-youko-8b`; Metadata/Japanese/English formatting, no literal BOS; supports bare multiline/full scenes | model-card-based, GGUF canary still required |
| Hunyuan old and new overlap | remove older Hunyuan-MT-7B | HY-MT1.5 retained |
| Missing adaptation controls | restored Phi-4, Qwen2.5-14B, Llama-3.2-3B and actual rinna-Youko base | original-base controls ≠ predicted top models |
| Strong nonthinking Deck Qwen missing | added Qwen3-4B-Instruct-2507 | GGUF source provisional until SHA attestation |
| v3 tools might overwrite current catalog | v4 regeneration reads frozen v3; legacy curation guard in place; v4 renderer separate | regeneration idempotent |
| Q8 arm needs separate attestation | explicit examples for separate Q8 manifest and matching `--quant Q8_0` | no variant guessed or silently substituted |
| Developer may mistake 50 candidate priorities for scores | all docs and JSON distinguish screen/attestation/canary/judge/audited rank | no inference or paid judgment run here |

**Unresolved outside local development:** 281 references still await bilingual-AI audit; native templates and GGUFs await real canaries; 31 scenes have too little power for VN-level ranking. **Next task is the small real pilot, not more scene polishing.**

## v4.0.1 (2026-10-24): misattached alternates

Four line items carried an alternate reference belonging to a different line, left over from the positional-attachment bug: JMB-048 and JMB-069 (eval), JMB-041 and JMB-241 (dev). Their alternates are removed (`tools/patch_corpus_v4_0_1.py`), and the reference translations are unchanged. Judgments made against the old gold no longer match its `gold_sha256`, so the ranking treats them as pending until they're re-judged: 2 eval lines for each of the 4 judged models.
