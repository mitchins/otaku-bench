# Review disposition — v1 → v2

| Claude audit | Disposition | Evidence |
| --- | --- | --- |
| Source text problems in JMB-036 / 047 / 096 | Corrected | `data/items/lines.jsonl`, `corrections.json` |
| Invented gender/narrative perspective (053,060,171,210) | Corrected | IDs stable; reference and source adjustments |
| Flattened voice, inaccurate alternative readings, weakened pragmatics | Corrected targeted cases | 076, 091, 111, 114, 141, 146, 172; alternates by ID |
| Near-duplicate probes | Partially mitigated | 196, 199, 224, 225 rewritten; all 250 strings remain unique but semantic distinctiveness is not empirically quantified |
| Round-robin VN/LN/game/anime labels | Demoted, not used in ranking | renamed `scenario_style_unvalidated`; no medium leaderboard |
| Single-line-only, missing speakers/contexts/hook noise | Partial feature extension | 31 authored short scenes, Japanese preceding dialogue, tags, ruby/hook/long-sentence examples. Still insufficient representative coverage |
| Editorial context leaks implicit answer | Fixed for v2 generation | `lines_bare.jsonl` does not carry scene hint; actual preceding Japanese only for P31-context |
| Row-number-based alternate gold breaks on edit | Fixed | records keyed by immutable stable ID, build script enforces set |
| Human-only evaluator and chrF-lite too weak | New judge suite | meaning/pragmatics/voice, confidence, flags, gold audit, pairwise calibration and shared-exclusion aggregation; no real API results yet |
| 200 output tokens can truncate thinker | Fixed with 4096 v2 matrix output cap and finish-reason gate | `run_translations.py`, `run_matrix_v2.py`; note latency tradeoff |
| Workbook depends on sandbox-only library | Avoided | Authoritative source JSONL, flat CSV; no runtime workbook requirement |
| TranslateGemma template may not work on llama-server | Not claimed supported | Explicit experimental opt-in and matrix skip until native template canary succeeds |
| `llama-server` Jinja flag | Explicit | `--jinja` passed; recent upstream may enable it by default |
| Poor Steam Deck weighting | Partly improved | size-filtered Deck candidate marker, separate LAN arms; requires measured RAM/KV and real load checks |
| Translation specialists omitted | Substantially fixed | Hunyuan-MT, HY-MT1.5 1.8B/7B official GGUF, Seed-X-PPO, CAT-Translate 0.8B/1.4B/3.3B-beta/7B, Swallow. PLaMo separate custom runtime; 3.3B CAT final not pretended to have beta's weights |
| Small models fixed Q4 | Separate Q6 and Q8 arms | no unverified quant fallback; recommended Q4 kept for typical user experience |
| Think/no-think latency not distinguished | Fixed in run identity | `run_id` includes model/quant/reasoning, matrix separates cases and timestamps |
| No automated gold native review | Infrastructure added | two AI gold audits for 281 cases, 48-trial swapped pair judge calibration; rankings gated; no paid results performed |

**Still not proven:** A trustworthy *real VN* translation ranking, native bilingual quality of 281 drafted references, actual production-ready local model runtime, representative long context, quant degradation, license suitability, and judged outputs. A program cannot substitute these with assertions that tests passed. All v2 scripts are a runnable framework for gathering that evidence.

Further candidate correction: Seed-X-PPO-7B replaces Seed-X-Instruct-7B in the 50: the lab specifically optimised PPO for translation; published third-party Q4_K_M file `Seed-X-PPO-7B.Q4_K_M.gguf` is 4.56 GB, but ByteDance recommends against unofficial quants. Its default bare prompt uses `/v1/completions` plus `<en>` and requires an execution canary before acceptance. Source: https://huggingface.co/ByteDance-Seed/Seed-X-PPO-7B and https://huggingface.co/mradermacher/Seed-X-PPO-7B-GGUF/tree/main .
