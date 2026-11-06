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
mkdir -p "$OUT" results/judge/slices/hard

# board order, best first; response dirs relative to results/screen_slices
QUEUE=(
  02_Gemma_4_31B_IT 05_Gemma_4_26B-A4B_IT 01_Qwen3.8-27B 03_Qwen3.6-35B-A3B 08_Gemma_4_12B_IT
  66_Ornith-1.5-35B-A3B 68_Gemma_4_26B-A4B_heretic_JP-pruned_120e 64_Hy-MT2-30B-A3B 63_Hy-MT2-7B
  32_TranslateGemma_27B_IT 33_TranslateGemma_12B_IT 21_Sugoi-14B-Ultra 42_Gemma_4_E2B_IT 41_Gemma_4_E4B_IT
  65_Hy-MT2-1.8B 67_Hy-MT2-1.8B-JP-Manga-v5 empty-think/36_LFM2.5-24B-A2B empty-think/51_Flint_40B-A2.5B 69_Ternary-Bonsai-2-27B 70_Nemotron_3.5_Bolt_74B-A9B_24GB
  short-system/C01_Gemini-3.5-Flash-Lite   # cloud reference: ero turns via OpenRouter (same model, default payload), not the direct Google key;
                                           # vendor-recommended short system prompt, as on its scenes and hard slice
  C02_Claude-Haiku-5.5   # cloud reference via OpenRouter, shared prompt, thinking off
  C03_Claude-Sonnet-5.5  # cloud reference via OpenRouter, shared prompt, thinking off (8/97 turns refused by the model)
  C04_Gemini-3.8-Flash   # cloud reference via OpenRouter, shared prompt, reasoning effort minimal
  # board quant rows (slices run 2026-11-04, so their Adult and Hard columns fill like the Q4 rows)
  72e/68_Gemma_4_26B-A4B_heretic_JP-pruned_120e Q5_K_M/02_Gemma_4_31B_IT UD-Q6_K_L/01_Qwen3.8-27B
  W4A16-vllm/05_Gemma_4_26B-A4B_IT   # LAN workhorse on vLLM (qualification, off the board)
  # official Gemma 4 QAT q4_0 GGUFs
  QAT-Q4_0/02_Gemma_4_31B_IT QAT-Q4_0/05_Gemma_4_26B-A4B_IT QAT-Q4_0/08_Gemma_4_12B_IT QAT-Q4_0/41_Gemma_4_E4B_IT QAT-Q4_0/42_Gemma_4_E2B_IT
  QAT-UD-Q2_K_XL/41_Gemma_4_E4B_IT QAT-UD-Q4_K_XL/42_Gemma_4_E2B_IT QAT-UD-Q2_K_XL/42_Gemma_4_E2B_IT   # edge budget
)

{
  echo "=== $(date -u +%FT%TZ) ero judge queue (OPENAI2_API_KEY), cap $CAP"
  ero_ok=1
  for dir in "${QUEUE[@]}"; do
    name=$(basename "$dir"); case $dir in */*) name="$name+$(dirname "$dir")";; esac
    echo "--- $dir"
    out=$(python tools/judge_slice.py --slice ero --responses "results/screen_slices/$dir/ero_turns.jsonl" \
      --output "$OUT/$name.jsonl" --daily-token-cap "$CAP" --budget-usd 5 --execute 2>&1)
    grep -vE '^[0-9]+/[0-9]+ ' <<<"$out"
    grep -qE 'Daily token cap reached|Cost limit reached' <<<"$out" && { ero_ok=0; break; }
  done
  # spare capacity on this account goes to the hard slice (user, 2026-11-04: "either queue is fine for hard").
  # Same models, order and output files as the main queue's hard phase; judging is idempotent, so the two queues
  # just continue each other's files. Tokens count on this account's ledger.
  if [ "$ero_ok" = 1 ]; then
    # HARD_PILOT, HARD_FULL, HARD_SKIP, QUEUE and hard_one() come from the main queue (one definition)
    eval "$(sed -n '/^QUEUE=(/,/^)/p; /^HARD_SKIP=/p; /^HARD_PILOT=(/,/)$/p; /^HARD_FULL=/p; /^hard_one() {/,/^}/p' mission/judge_queue.sh)"
    list=("${HARD_PILOT[@]}"); [ "$HARD_FULL" = 1 ] && list+=("${QUEUE[@]}")
    STOP=""
    for dir in "${list[@]}"; do
      hard_one "$dir" --key-env OPENAI2_API_KEY --ledger "$PWD/results/judge/token_ledger_openai2.jsonl" || break
    done
  fi
} >>"$LOG" 2>&1

if [ "${PUBLISH:-1}" = "1" ]; then
  if ! CHANGED=$(git status --porcelain -- "$OUT" results/judge/slices/hard results/judge/token_ledger_openai2.jsonl 2>>"$LOG"); then
    echo "⚠️  publish failed: git status error (git-crypt on PATH?)" >>"$LOG"
  elif [ -n "$CHANGED" ]; then
  {
    git add "$OUT" results/judge/slices/hard results/judge/token_ledger_openai2.jsonl &&
    git commit -q -m "Ero judge queue $(date -u +%F)" -- "$OUT" results/judge/slices/hard results/judge/token_ledger_openai2.jsonl &&
    git push -q origin main
  } >>"$LOG" 2>&1 || echo "⚠️  publish failed" >>"$LOG"
  fi
fi
