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
mkdir -p "$OUT"

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
  # community request: Hy-MT2 30B-A3B looked Gemma-26B-class on idioms in the informal review (0.17 s/line, 18 GB)
  screen/64_Hy-MT2-30B-A3B
  # the 12B pair, back to back: general Gemma 4 12B vs the TranslateGemma 12B fine-tune
  screen/08_Gemma_4_12B_IT
  screen/33_TranslateGemma_12B_IT
  screen/63_Hy-MT2-7B   # community request: dedicated-translator group; HY-MT1.5-7B successor
  screen/65_Hy-MT2-1.8B   # Deck-class edge translator (1.1 GB, 0.08 s/line); HY-MT1.5-1.8B successor
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
)

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
  for dir in "${QUEUE[@]}"; do
    tag=""; case $dir in screen_variants/*|screen_quants/*) tag=$(basename "$(dirname "$dir")");; esac
    echo "--- $dir"
    judge "$dir" scenes full all "$tag" || break
    judge "$dir" lines bare eval "$tag" || break
  done
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
