#!/usr/bin/env bash
# Launch the screen mission detached (tmux if available, else nohup). Extra args pass through:
#   ./mission/run.sh --ranks 15,18,19,20,31,46
#   GPU=0 ./mission/run.sh --prune
#   ./mission/run.sh -- -fa on        # extra llama-server flags after --
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f mission/.env ] || { echo "❌ run ./mission/setup.sh first"; exit 1; }
# shellcheck disable=SC1091
. mission/.env
# shellcheck disable=SC1091
. .venv/bin/activate
mkdir -p results/screen
LOG="results/screen/mission_$(date +%Y%m%d_%H%M%S).log"
CMD=(python mission/screen_mission.py --llama-server "$LLAMA_SERVER" --gpu "${GPU:-0}" "$@")
QUOTED="$(printf '%q ' "${CMD[@]}")"
if command -v tmux >/dev/null; then
  if tmux has-session -t otb 2>/dev/null; then
    echo "❌ tmux session 'otb' already running — attach with: tmux attach -t otb"; exit 1
  fi
  tmux new-session -d -s otb "cd $(printf '%q' "$(pwd)") && . .venv/bin/activate && $QUOTED 2>&1 | tee -a $LOG; echo '🏁 done — press enter'; read"
  echo "🚀 started in tmux session 'otb'  →  tmux attach -t otb"
else
  nohup "${CMD[@]}" >>"$LOG" 2>&1 &
  echo "🚀 started (pid $!)  →  tail -f $LOG"
fi
echo "📄 log: $LOG   ·   report afterwards: python mission/report.py"
