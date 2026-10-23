#!/usr/bin/env bash
# Daily judge queue: works down the shortlist with gpt-6.1-sol inside the free data-sharing allowance.
# Each run judges full scenes, then eval lines, for each model in order. Already-judged items are skipped,
# so the queue resumes where yesterday's run hit the cap. Then it refreshes results/judge/RANKING.md.
#   ./mission/judge_queue.sh          # cron: 20 0 * * * (tiger runs on UTC)
set -uo pipefail
cd "$(dirname "$0")/.."
# shellcheck disable=SC1091
. .venv/bin/activate
set -a
# shellcheck disable=SC1091
. ./.env
set +a
CAP="${CAP:-200000}"   # org-wide Build allowance is 250K/day; leave room for EasyDict etc.
OUT=results/judge/sol
LOG="results/judge/queue_$(date -u +%Y%m%d).log"
mkdir -p "$OUT"

# priority order: complete, deployable, fast. Paths are response dirs relative to results/.
QUEUE=(
  # Highest-priority 3090-fit ceiling probes: inference complete, judging pending.
  screen/01_Qwen3.8-27B
  screen/02_Gemma_4_31B_IT
  # Existing completed/partial judges remain resumable; keep as comparisons.
  screen/03_Qwen3.6-35B-A3B
  screen/05_Gemma_4_26B-A4B_IT
  screen/21_Sugoi-14B-Ultra
  screen/32_TranslateGemma_27B_IT
  screen/33_TranslateGemma_12B_IT
  screen_variants/empty-think/36_LFM2.5-24B-A2B
  screen_variants/effort-low/39_gpt-oss-20b
  screen/15_Shisa-v2.1-qwen3-8B
  screen/46_Qwen3-4B-Instruct-2507
)

judge() {  # dir dataset mode split tag
  local dir=$1 name; name=$(basename "$1")
  [ -n "${5:-}" ] && name="$name+$5"
  python tools/judge.py --responses "results/$dir/$2_$([ "$2" = lines ] && echo bare || echo "$3").jsonl" \
    --dataset "$2" --mode "$3" --split "$4" --budget-usd 5 --daily-token-cap "$CAP" \
    --output "$OUT/$name.$2_$([ "$2" = lines ] && echo "$4" || echo "$3").jsonl" --execute 2>&1 \
    | grep -vE '^[0-9]+/[0-9]+ .* => '  # the caller's block already appends to $LOG
  ! grep -q 'Daily token cap reached' "$LOG"
}

{
  echo "=== $(date -u +%FT%TZ) judge queue, cap $CAP"
  for dir in "${QUEUE[@]}"; do
    tag=""; case $dir in screen_variants/*) tag=$(basename "$(dirname "$dir")");; esac
    echo "--- $dir"
    judge "$dir" scenes full all "$tag" || break
    judge "$dir" lines bare eval "$tag" || break
  done
} >>"$LOG" 2>&1
python mission/judge_table.py >>"$LOG" 2>&1

# publish: commit the refreshed ranking (judgment JSONL is git-crypted) and push, which redeploys the docs
if [ "${PUBLISH:-1}" = "1" ] && [ -n "$(git status --porcelain -- results/judge)" ]; then
  {
    git add results/judge &&
    git commit -q -m "Judge queue $(date -u +%F): refresh ranking" &&
    git push -q origin main
  } >>"$LOG" 2>&1 || echo "⚠️  publish failed" >>"$LOG"
fi
