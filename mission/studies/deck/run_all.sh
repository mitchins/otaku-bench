#!/usr/bin/env bash
# waits for fetch.sh, verifies sha256, then runs the gate payloads + llama-bench per model, one model at a time
cd ~/otakubench-deck
B=$PWD/llama-b11836
until grep -q "ALL DONE" models/fetch.log; do sleep 10; done
declare -A SHA=(
 [gemma-4-E4B-it-qat-UD-Q2_K_XL.gguf]=79dde517866c
 [gemma-4-E2B_q4_0-it.gguf]=E2BQ40
 [gemma-4-E4B_q4_0-it.gguf]=E4BQ40
 [gemma-4-E2B-it-qat-UD-Q4_K_XL.gguf]=e531007218df )
mkdir -p results
for m in gemma-4-E2B_q4_0-it.gguf gemma-4-E2B-it-qat-UD-Q4_K_XL.gguf gemma-4-E4B-it-qat-UD-Q2_K_XL.gguf gemma-4-E4B_q4_0-it.gguf; do
  echo "=== $(date +%T) $m"; sha256sum models/$m | cut -c1-64 > results/$m.sha256; cat results/$m.sha256
  python3 deck_bench.py $B models/$m results/$m.lat.jsonl && echo "gate done"
  LD_LIBRARY_PATH=$B $B/llama-bench -m models/$m -ngl 99 -p 512 -n 64 -r 3 -o json > results/$m.bench.json 2>results/$m.bench.err && echo "bench done"
done
echo "=== ALL BENCH DONE $(date +%T)"
