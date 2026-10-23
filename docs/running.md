# Running it

On the GPU host (Linux, CUDA, a recent llama.cpp build):

```bash
./mission/setup.sh                          # venv, find llama-server, pin GGUFs (metadata only), print plan
./mission/run.sh --ranks 15,18,19,20,31,46  # pilot
./mission/run.sh --prune                    # full sweep in tmux, deleting each GGUF after its run
./mission/followups.sh                      # variant arms (effort-low, empty-think, primed)
python mission/report.py                    # results/screen/REPORT.md + SKIM.md
```

Reruns are safe: finished models and finished items are skipped. Models deferred for memory reasons are retried on each pass, so on a bigger GPU it's the same command with `--gpu N`.

## Judging

```bash
./mission/judge_queue.sh       # daily, from cron: shortlist in priority order, stops at the token cap
python mission/judge_table.py  # results/judge/RANKING.md
```

The judge records every call's tokens in `results/judge/token_ledger.jsonl` and stops before `--daily-token-cap`. The queue sets that cap from the organisation Usage API (`python tools/openai_usage.py`): what is left of the shared 250K data-sharing pool after a 5K margin and a 20K reserve for other keys. It falls back to 200K if the API is unreachable. Judging needs the eval gold, so it needs the git-crypt key.

## Docs

```bash
pip install zensical
zensical serve                 # http://localhost:8000
```

Pushing to `main` publishes the site to GitHub Pages.
