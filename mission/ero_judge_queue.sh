#!/usr/bin/env bash
# Daily ero-slice judge queue on the SECOND OpenAI account (OPENAI2_API_KEY, its own free data-sharing allowance).
# Runs beside the main queue: the main and admin keys are unset before anything runs, so a provider-side flag on
# adult content can only reach the second account. Resumes where the cap stopped it; commits only its own files.
#   ./mission/ero_judge_queue.sh            # cron 12:30 UTC (clear of the main queue's 00:20 / 23:45 git steps)
#   CAP=50000 ./mission/ero_judge_queue.sh  # smaller daily cap
set -uo pipefail
cd "$(dirname "$0")/.."
export PATH="/home/linuxbrew/.linuxbrew/bin:$HOME/.local/bin:$PATH"
# shellcheck disable=SC1091
. .venv/bin/activate
set -a
# shellcheck disable=SC1091
. ./.env
set +a
unset OPENAI_API_KEY OPENAI_ADMIN_API_KEY OTB_OPENAI_KEY_ID
CAP=${CAP:-200000}
OUT=results/judge/slices/ero
LOG="results/judge/ero_queue_$(date -u +%Y%m%d).log"
mkdir -p "$OUT"

# board order, best first; response dirs relative to results/screen_slices
QUEUE=(
  02_Gemma_4_31B_IT 05_Gemma_4_26B-A4B_IT 01_Qwen3.8-27B 03_Qwen3.6-35B-A3B 08_Gemma_4_12B_IT
  66_Ornith-1.5-35B-A3B 68_Gemma_4_26B-A4B_heretic_JP-pruned_120e 64_Hy-MT2-30B-A3B 63_Hy-MT2-7B
  32_TranslateGemma_27B_IT 33_TranslateGemma_12B_IT 21_Sugoi-14B-Ultra 42_Gemma_4_E2B_IT 41_Gemma_4_E4B_IT
  65_Hy-MT2-1.8B 67_Hy-MT2-1.8B-JP-Manga-v5 empty-think/36_LFM2.5-24B-A2B empty-think/51_Flint_40B-A2.5B
)

{
  echo "=== $(date -u +%FT%TZ) ero judge queue (OPENAI2_API_KEY), cap $CAP"
  for dir in "${QUEUE[@]}"; do
    name=$(basename "$dir"); case $dir in */*) name="$name+$(dirname "$dir")";; esac
    echo "--- $dir"
    out=$(python tools/judge_slice.py --slice ero --responses "results/screen_slices/$dir/ero_turns.jsonl" \
      --output "$OUT/$name.jsonl" --daily-token-cap "$CAP" --budget-usd 5 --execute 2>&1)
    grep -vE '^[0-9]+/[0-9]+ ' <<<"$out"
    grep -qE 'Daily token cap reached|Cost limit reached' <<<"$out" && break
  done
} >>"$LOG" 2>&1

if [ "${PUBLISH:-1}" = "1" ]; then
  if ! CHANGED=$(git status --porcelain -- "$OUT" results/judge/token_ledger_openai2.jsonl 2>>"$LOG"); then
    echo "⚠️  publish failed: git status error (git-crypt on PATH?)" >>"$LOG"
  elif [ -n "$CHANGED" ]; then
  {
    git add "$OUT" results/judge/token_ledger_openai2.jsonl &&
    git commit -q -m "Ero judge queue $(date -u +%F)" -- "$OUT" results/judge/token_ledger_openai2.jsonl &&
    git push -q origin main
  } >>"$LOG" 2>&1 || echo "⚠️  publish failed" >>"$LOG"
  fi
fi
