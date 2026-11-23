#!/usr/bin/env bash
# Daily ero-slice judge queue on the SECOND OpenAI account (OPENAI2_API_KEY, its own free data-sharing allowance).
# Adult slice only. Runs beside the main queue: the main and admin keys are unset before anything runs, so a provider-side flag on
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
  empty-think/71_Inkling_2_Mini   # Thinking Machines, 2026-11-20 release
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
  QAT-i1-Q2_K/08_Gemma_4_12B_IT QAT-i1-IQ3_M/08_Gemma_4_12B_IT   # 12B Deck candidates
  QAT-mobile-vllm/42_Gemma_4_E2B_IT   # Google mobile QAT E2B (vLLM, quality only)
  Q4_K_L/02_Gemma_4_31B_IT   # community request (Reddit, 2026-11-16)
  # standard-only runs given slice translations 2026-11-16 (user: "let's get all outstanding scores done"), main queue order
  effort-low/39_gpt-oss-20b 15_Shisa-v2.1-qwen3-8B 46_Qwen3-4B-Instruct-2507 31_Qwen3.5-4B 44_Qwen3.5-2B 72_Qwen3.5-0.8B 73_Qwen3-0.6B 53_Ling-3.0-tiny
  60_LFM3-1.7B 61_LFM3-VL-2B respond-in-text/62_LFM3-Omni-2B empty-think/57_LFM2.5-2.6B 59_LFM2.5-VL-3B
  19_LFM2.5-1.2B-JP-202606 45_LFM2.5-1.2B_Instruct 13_NVIDIA-Nemotron-Nano-9B-v2-Japanese 04_Qwen3.6-27B
  11_Qwen3-Swallow-32B-RL-v0.2 22_Sugoi-32B-Ultra 37_GLM-4.7-Flash 20_VNTL-Llama3-8B-v2 14_Shisa-v2.1-unphi4-14B
  10_CAT-Translate-7B 23_HY-MT1.5-7B 30_Qwen3.5-9B 38_Qwen3-8B 43_Ministral_3_8B_Instruct 48_Qwen2.5-14B-Instruct
  49_Phi-4_14B 34_TranslateGemma_4B_IT 28_HY-MT1.5-1.8B 16_Shisa-v2.1-llama3.2-3B 18_TinySwallow-1.5B-Instruct
  17_Shisa-v2.1-lfm2-1.2B 27_CAT-Translate-1.4B 29_CAT-Translate-0.8B
)

{
  echo "=== $(date -u +%FT%TZ) ero judge queue (OPENAI2_API_KEY), cap $CAP"
  for dir in "${QUEUE[@]}"; do
    name=$(basename "$dir"); case $dir in */*) name="$name+$(dirname "$dir")";; esac
    [ -f "results/screen_slices/$dir/ero_turns.jsonl" ] || continue   # not translated yet
    echo "--- $dir"
    out=$(python tools/judge_slice.py --slice ero --responses "results/screen_slices/$dir/ero_turns.jsonl" \
      --output "$OUT/$name.jsonl" --daily-token-cap "$CAP" --budget-usd 5 --execute 2>&1)
    grep -vE '^[0-9]+/[0-9]+ ' <<<"$out"
    grep -qE 'Daily token cap reached|Cost limit reached' <<<"$out" && break
    if grep -qE 'HTTP Error 429' <<<"$out"; then   # no credit (insufficient_quota) or rate-limited: stop, don't burn the list
      echo "⚠️  OpenAI 429 on the second account: stopping (credit balance exhausted?)"; break
    fi
  done
  # Adult only (user, 2026-11-21): this account is billed despite its data-sharing enrolment (balance 9.39 -> 8.78 USD
  # over one run), so it no longer spends spare allowance on Hard or Standard; the main queue covers those.
} >>"$LOG" 2>&1

if [ "${PUBLISH:-1}" = "1" ]; then
  if ! CHANGED=$(git status --porcelain -- "$OUT" results/judge/slices/hard results/judge/sol results/judge/token_ledger_openai2.jsonl 2>>"$LOG"); then
    echo "⚠️  publish failed: git status error (git-crypt on PATH?)" >>"$LOG"
  elif [ -n "$CHANGED" ]; then
  {
    git add "$OUT" results/judge/slices/hard results/judge/sol results/judge/token_ledger_openai2.jsonl &&
    git commit -q -m "Ero judge queue $(date -u +%F)" -- "$OUT" results/judge/slices/hard results/judge/sol results/judge/token_ledger_openai2.jsonl &&
    git push -q origin main
  } >>"$LOG" 2>&1 || echo "⚠️  publish failed" >>"$LOG"
  fi
fi
