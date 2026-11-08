#!/usr/bin/env bash
# Daily judge queue: works down the shortlist with gpt-6.1-sol inside the free data-sharing allowance.
# Each run judges full scenes, then eval lines, for each model in order. Already-judged items are skipped,
# so the queue resumes where yesterday's run hit the cap. Then it refreshes results/judge/RANKING.md.
#   ./mission/judge_queue.sh                        # cron 00:20 UTC: keeps 20K reserved for other keys
#   RESERVE=0 STOP=23:58 ./mission/judge_queue.sh   # cron 23:45 UTC: spend what other keys left unused
set -uo pipefail
cd "$(dirname "$0")/.."
# cron's PATH is /usr/bin:/bin; git-crypt (brew) must be found or git status/add fail on the encrypted paths
export PATH="/home/linuxbrew/.linuxbrew/bin:$HOME/.local/bin:$PATH"
# shellcheck disable=SC1091
. .venv/bin/activate
set -a
# shellcheck disable=SC1091
. ./.env
set +a
# Daily cap from the org Usage API: what's left of the shared 250K after other keys' reserve and a margin,
# added to what the local ledger already counted today (the judge checks ledger + next call against it).
# Static 200K if the Usage API is unreachable.
if [ -z "${CAP:-}" ]; then
  if REM=$(python tools/openai_usage.py --remaining --reserve "${RESERVE:-20000}" 2>/dev/null); then
    LEDGER=$(python - <<'PY'
import json, time
from pathlib import Path
p, d = Path('results/judge/token_ledger.jsonl'), time.strftime('%Y-%m-%d', time.gmtime())
print(sum(json.loads(l)['tokens'] for l in p.open() if json.loads(l)['day'] == d) if p.exists() else 0)
PY
)
    CAP=$((LEDGER + REM))
  else
    CAP=200000
  fi
fi
unset OPENAI_ADMIN_API_KEY   # only the usage monitor needs it; keep it out of the judge
OUT=results/judge/sol
LOG="results/judge/queue_$(date -u +%Y%m%d).log"
mkdir -p "$OUT" results/judge/slices/hard

# priority order: complete, deployable, fast. Paths are response dirs relative to results/.
QUEUE=(
  screen/03_Qwen3.6-35B-A3B
  screen/05_Gemma_4_26B-A4B_IT
  # the two strongest dense candidates: existing Q4 responses (same footing as every other model)
  screen/01_Qwen3.8-27B
  screen/02_Gemma_4_31B_IT
  # then their largest quant that fits 24 GB, to see whether the extra memory buys quality
  screen_quants/UD-Q6_K_L/01_Qwen3.8-27B
  screen_quants/Q5_K_M/02_Gemma_4_31B_IT
  # 24B MoE at 0.16 s/line; single-block empty-think prefill (corrected run)
  screen_variants/empty-think/36_LFM2.5-24B-A2B
  # hardware-rule admission: 40B MoE, fits 24 GB at IQ4_XS; needs the empty-think prefill (always thinks otherwise)
  screen_variants/empty-think/51_Flint_40B-A2.5B   # single-block empty-think prefill (studies/flint_adapter.py)
  screen/21_Sugoi-14B-Ultra
  screen/32_TranslateGemma_27B_IT
  # edge picks moved up: Gemma 4 E2B / E4B (3.2 / 5.1 GB, clean outputs) are the realistic Deck-class candidates, and take images
  screen/42_Gemma_4_E2B_IT
  screen/41_Gemma_4_E4B_IT
  # qualification only (off the board): Gemma 4 31B NVFP4 on vLLM / RTX 5090; 139/200 lines reuse Q4/Q5 judgments
  screen_quants/NVFP4-vllm/02_Gemma_4_31B_IT
  # qualification only (off the board): the LAN workhorse, Gemma 4 26B-A4B QAT W4A16 (compressed-tensors) on vLLM / local GPU 1
  screen_quants/W4A16-vllm/05_Gemma_4_26B-A4B_IT
  # official Gemma 4 QAT q4_0 GGUFs (user, 2026-11-06: "negligent NOT to score them"); llama.cpp on the 3090, on the board
  screen_quants/QAT-Q4_0/02_Gemma_4_31B_IT
  screen_quants/QAT-Q4_0/05_Gemma_4_26B-A4B_IT
  screen_quants/QAT-Q4_0/08_Gemma_4_12B_IT
  screen_quants/QAT-Q4_0/41_Gemma_4_E4B_IT
  screen_quants/QAT-Q4_0/42_Gemma_4_E2B_IT
  # Google's mobile QAT E2B (wNa8o8: 2-bit deep MLPs/embeddings, 4-bit attention, 8-bit vision, int8 activations; 2.6 GB),
  # vLLM 0.32 on GPU 0 (quality only, off the board like W4A16); user 2026-11-08: quality verification before any Deck trial
  screen_quants/QAT-mobile-vllm/42_Gemma_4_E2B_IT
  # edge memory budget (Deck): bigger model at 2-bit vs smaller at 4-bit, Unsloth dynamic quants of the QAT weights
  screen_quants/QAT-UD-Q2_K_XL/41_Gemma_4_E4B_IT
  screen_quants/QAT-UD-Q4_K_XL/42_Gemma_4_E2B_IT
  screen_quants/QAT-UD-Q2_K_XL/42_Gemma_4_E2B_IT
  # 12B QAT below 4-bit (unified vision; Deck candidates vs E4B), mradermacher imatrix quants.
  # i1-IQ2_M (canary failed) and i1-IQ3_XXS (garbage runaways on 31/167 hard turns) emit garbage on CUDA b11836: not judged
  screen_quants/QAT-i1-Q2_K/08_Gemma_4_12B_IT
  screen_quants/QAT-i1-IQ3_M/08_Gemma_4_12B_IT
  # cloud reference (off the board): cheapest Google cloud model vs the home Gemmas; responses via the LAN proxy, paced to the key's ~5 req/min
  screen/C01_Gemini-3.5-Flash-Lite
  screen_variants/short-system/C01_Gemini-3.5-Flash-Lite   # indicative, not parity: short system prompt for scenes (the shared one makes Lite echo); lines copied from the shared-prompt run
  # cloud reference: Claude Haiku 5.5 via OpenRouter, shared prompt, thinking off (reasoning disabled; 0 reasoning tokens)
  screen/C02_Claude-Haiku-5.5
  # cloud reference: Claude Sonnet 5.5 via OpenRouter, shared prompt, thinking off (thinking between_tools; 0 reasoning tokens)
  screen/C03_Claude-Sonnet-5.5
  # cloud reference: Gemini 3.8 Flash via OpenRouter, shared prompt, reasoning effort minimal (cannot be switched off)
  screen/C04_Gemini-3.8-Flash
  # user pick: Ornith-1.5 (self-improvement RL on the Qwen3.5/3.6-35B-A3B MoE, coding/agentic); does it beat its Qwen3.6 base? 0.41 s/line, 66/200 lines reuse
  screen/66_Ornith-1.5-35B-A3B
  # community request: Hy-MT2 30B-A3B looked Gemma-26B-class on idioms in the informal review (0.17 s/line, 18 GB)
  screen/64_Hy-MT2-30B-A3B
  # the 12B pair, back to back: general Gemma 4 12B vs the TranslateGemma 12B fine-tune
  screen/08_Gemma_4_12B_IT
  screen/33_TranslateGemma_12B_IT
  screen/63_Hy-MT2-7B   # community request: dedicated-translator group; HY-MT1.5-7B successor
  screen/65_Hy-MT2-1.8B   # Deck-class edge translator (1.1 GB, 0.08 s/line); HY-MT1.5-1.8B successor
  screen/67_Hy-MT2-1.8B-JP-Manga-v5   # community request (Reddit): manga finetune of 65, card prompt; clean lines, merges scene lines on 6-7/31
  # community request (Reddit): heretic (abliterated) QAT Q4_0 26B with experts pruned on Japanese; clean, 13.6 / 9.0 GB vs 17.0 GB for 05.
  # 96e screened too (results/screen_quants/96e, 11.3 GB), not queued: judge it only if 120e and 72e land far apart
  screen/68_Gemma_4_26B-A4B_heretic_JP-pruned_120e
  screen_quants/72e/68_Gemma_4_26B-A4B_heretic_JP-pruned_120e
  screen/69_Ternary-Bonsai-2-27B   # PrismML ternary Qwen3.8-27B (PQ2_0, ~/llama.cpp-prism); PTQ1_0 screened too (screen_quants/PTQ1_0), 95% identical outputs, not queued
  screen/70_Nemotron_3.5_Bolt_74B-A9B_24GB   # NVIDIA 74B-A9B 24GB GGUF (IQ2_XXS/NVFP4 mix), text only, stock llama.cpp; context arm echoes 3/31
  screen_variants/effort-low/39_gpt-oss-20b
  screen/15_Shisa-v2.1-qwen3-8B
  # edge-size comparisons (Deck-class and below)
  screen/46_Qwen3-4B-Instruct-2507
  screen/31_Qwen3.5-4B
  screen/44_Qwen3.5-2B
  # screen/52_Qwen3-1.7B   # dropped from paid judging: 4 failed + 22 untranslated; kept as diagnostic evidence
  screen/53_Ling-3.0-tiny   # low-active MoE comparison point for LFM/Flint; eyeball says same league or worse
  # current-gen LFM sweep (2.5 + 3), newest first; last on purpose: confirms the family is weak at this task. Not paid-judged: 350M (returns the Japanese on 200/200),
  # 230M (chatty/echo), 8B-A1B (42 echoes even with empty-think, latency gate FAIL), 1.2B-Thinking (can't stop thinking)
  screen/60_LFM3-1.7B
  screen/61_LFM3-VL-2B
  screen_variants/respond-in-text/62_LFM3-Omni-2B
  screen_variants/empty-think/57_LFM2.5-2.6B
  screen/59_LFM2.5-VL-3B
  screen/19_LFM2.5-1.2B-JP-202606
  screen/45_LFM2.5-1.2B_Instruct
  # backlog tail (user, 2026-11-07: "if we have models ran but not judged then yes... low priority"): every COMPLETE screen run
  # from the first 3090 sweep that was never shortlisted, most interesting first. Seed-X-PPO-7B is left out: no scenes arm.
  screen/13_NVIDIA-Nemotron-Nano-9B-v2-Japanese   # NVIDIA first-party Japanese adaptation
  screen/04_Qwen3.6-27B
  screen/11_Qwen3-Swallow-32B-RL-v0.2
  screen/22_Sugoi-32B-Ultra
  screen/37_GLM-4.7-Flash
  screen/20_VNTL-Llama3-8B-v2
  screen/14_Shisa-v2.1-unphi4-14B   # 62/250 lines still contain kana
  screen/10_CAT-Translate-7B
  screen/23_HY-MT1.5-7B
  screen/30_Qwen3.5-9B
  screen/38_Qwen3-8B
  screen/43_Ministral_3_8B_Instruct
  screen/48_Qwen2.5-14B-Instruct
  screen/49_Phi-4_14B
  screen/34_TranslateGemma_4B_IT
  screen/28_HY-MT1.5-1.8B
  screen/16_Shisa-v2.1-llama3.2-3B
  screen/18_TinySwallow-1.5B-Instruct
  screen/17_Shisa-v2.1-lfm2-1.2B   # 21/250 lines still contain kana
  screen/27_CAT-Translate-1.4B     # 21/250 lines still contain kana
  screen/29_CAT-Translate-0.8B
)

# hard-slice runs that are not the board's: Gemini Lite's board hard result is the short-system run
HARD_SKIP=(screen/C01_Gemini-3.5-Flash-Lite)
# Hard pilot (user, 2026-11-05: verify the hard slice spreads models before committing to it): a spread across
# strength and family, strongest/weakest first, judged before anything else in both queues.
HARD_PILOT=(screen/02_Gemma_4_31B_IT screen/65_Hy-MT2-1.8B screen/C03_Claude-Sonnet-5.5 screen/41_Gemma_4_E4B_IT
            screen/05_Gemma_4_26B-A4B_IT screen/01_Qwen3.8-27B screen/C04_Gemini-3.8-Flash
            screen_quants/W4A16-vllm/05_Gemma_4_26B-A4B_IT   # LAN workhorse, against its Q4 base; user 2026-11-06
            screen_quants/QAT-Q4_0/02_Gemma_4_31B_IT screen_quants/QAT-Q4_0/05_Gemma_4_26B-A4B_IT
            screen_quants/QAT-Q4_0/41_Gemma_4_E4B_IT   # official QAT builds of the pilot's Gemmas
            screen_quants/QAT-Q4_0/42_Gemma_4_E2B_IT screen_quants/QAT-UD-Q2_K_XL/41_Gemma_4_E4B_IT
            screen_quants/QAT-UD-Q4_K_XL/42_Gemma_4_E2B_IT screen_quants/QAT-UD-Q2_K_XL/42_Gemma_4_E2B_IT   # edge budget
            screen_quants/QAT-Q4_0/08_Gemma_4_12B_IT screen_quants/QAT-i1-Q2_K/08_Gemma_4_12B_IT
            screen_quants/QAT-i1-IQ3_M/08_Gemma_4_12B_IT   # 12B unified-vision Deck candidates
            screen_quants/QAT-mobile-vllm/42_Gemma_4_E2B_IT   # Google mobile QAT E2B, vs QAT Q4_0
)  # keep this ')' alone on its line: mission/ero_judge_queue.sh extracts the array up to '^)'
# 0 until the pilot is reviewed: the rest of the hard slice (and the dev lines after it) stays unjudged
HARD_FULL=0

hard_one() {  # dir [extra judge_slice args]; returns non-zero when this run must stop
  local dir=$1 base tag resp out; shift
  case $dir in "${HARD_SKIP[@]}") return 0;; esac
  base=$(basename "$dir"); tag=""; case $dir in screen_variants/*|screen_quants/*) tag=$(basename "$(dirname "$dir")");; esac
  resp="results/screen_slices/${tag:+$tag/}$base/hard_turns.jsonl"
  [ -f "$resp" ] || return 0
  echo "--- hard $dir"
  out=$(python tools/judge_slice.py --slice hard --responses "$resp" --output "results/judge/slices/hard/$base${tag:++$tag}.jsonl" \
    --daily-token-cap "$CAP" ${STOP:+--stop-before-utc "$STOP"} --budget-usd 5 --execute "$@" 2>&1)
  grep -vE '^[0-9]+/[0-9]+ ' <<<"$out"
  ! grep -qE 'Daily token cap reached|Stop time .* reached|Cost limit reached' <<<"$out"
}

judge() {  # dir dataset mode split tag; returns non-zero when this run must stop (cap or stop time)
  local dir=$1 name out; name=$(basename "$1")
  [ -n "${5:-}" ] && name="$name+$5"
  out=$(python tools/judge.py --responses "results/$dir/$2_$([ "$2" = lines ] && echo bare || echo "$3").jsonl" \
    --dataset "$2" --mode "$3" --split "$4" --budget-usd 5 --daily-token-cap "$CAP" ${STOP:+--stop-before-utc "$STOP"} \
    --output "$OUT/$name.$2_$([ "$2" = lines ] && echo "$4" || echo "$3").jsonl" --execute 2>&1)
  grep -vE '^[0-9]+/[0-9]+ .* => ' <<<"$out"  # the caller's block appends this to $LOG
  ! grep -qE 'Daily token cap reached|Stop time .* reached' <<<"$out"
}

{
  echo "=== $(date -u +%FT%TZ) judge queue, cap $CAP, reserve ${RESERVE:-20000}${STOP:+, stop $STOP UTC}"
  python tools/openai_usage.py --reserve "${RESERVE:-20000}" 2>&1 || true
  go=1
  for dir in "${HARD_PILOT[@]}"; do hard_one "$dir" || { go=0; break; }; done
  std_ok=0
  if [ "$go" = 1 ]; then
    std_ok=1
    for dir in "${QUEUE[@]}"; do
      tag=""; case $dir in screen_variants/*|screen_quants/*) tag=$(basename "$(dirname "$dir")");; esac
      echo "--- $dir"
      judge "$dir" scenes full all "$tag" || { std_ok=0; break; }
      judge "$dir" lines bare eval "$tag" || { std_ok=0; break; }
    done
  fi
  # rest of the hard slice once every standard arm is judged and HARD_FULL=1 (same order, key, ledger and cap)
  hard_ok=0
  if [ "$std_ok" = 1 ] && [ "$HARD_FULL" = 1 ]; then
    hard_ok=1
    for dir in "${QUEUE[@]}"; do hard_one "$dir" || { hard_ok=0; break; }; done
  fi
  # lowest priority: the 50 public dev lines (off the board), so failures can later be shown with quotable examples
  # (user, 2026-11-04). Every model already translated them in its screen run: judging only, no inference.
  if [ "$hard_ok" = 1 ]; then
    for dir in "${QUEUE[@]}"; do
      tag=""; case $dir in screen_variants/*|screen_quants/*) tag=$(basename "$(dirname "$dir")");; esac
      echo "--- dev $dir"
      judge "$dir" lines bare dev "$tag" || break
    done
  fi
} >>"$LOG" 2>&1
python mission/judge_table.py >>"$LOG" 2>&1

# publish: commit the refreshed ranking (judgment JSONL is git-crypted) and push, which redeploys the docs
if [ "${PUBLISH:-1}" = "1" ]; then
  if ! CHANGED=$(git status --porcelain -- results/judge 2>>"$LOG"); then
    echo "⚠️  publish failed: git status error (git-crypt on PATH?)" >>"$LOG"
  elif [ -n "$CHANGED" ]; then
  {
    git add results/judge &&
    git commit -q -m "Judge queue $(date -u +%F): refresh ranking" &&
    git push -q origin main
  } >>"$LOG" 2>&1 || echo "⚠️  publish failed" >>"$LOG"
  fi
fi
