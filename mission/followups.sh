#!/usr/bin/env bash
# Follow-up arms for models the baseline screen profile can't run (see VARIANTS in screen_mission.py).
# Each variant writes to results/screen_variants/<variant>/ with its own run_id; baseline results are untouched.
#   ./mission/followups.sh            # in tmux session 'otb-fu'
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck disable=SC1091
. mission/.env
# shellcheck disable=SC1091
. .venv/bin/activate
LOG="results/screen/followups_$(date +%Y%m%d_%H%M%S).log"
RUN="python mission/screen_mission.py --llama-server $(printf '%q' "$LLAMA_SERVER") --gpu ${GPU:-0} --prune"
CMDS="$RUN --variant effort-low --ranks 39,12; $RUN --variant empty-think --ranks 36; $RUN --variant primed --ranks 47"
tmux new-session -d -s otb-fu "cd $(printf '%q' "$(pwd)") && ( $CMDS ) 2>&1 | tee -a $LOG; echo '🏁 follow-ups done — press enter'; read"
echo "🚀 follow-ups in tmux session 'otb-fu'  ·  log: $LOG"
