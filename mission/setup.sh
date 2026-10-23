#!/usr/bin/env bash
# OtakuBench screen mission — one-time setup on the GPU host (tiger).
# Creates .venv, finds (or optionally builds) llama-server, pins GGUFs via the HF API
# (metadata only, no weight downloads) and prints the run plan.
#
#   ./mission/setup.sh                 # use llama-server from PATH or $LLAMA_SERVER
#   BUILD_LLAMA=1 ./mission/setup.sh   # clone + build llama.cpp with CUDA into vendor/
#   CUDA_ARCHS="86;120" BUILD_LLAMA=1 ./mission/setup.sh   # also target the 5090
set -euo pipefail
cd "$(dirname "$0")/.."
echo "🔎 OtakuBench mission setup on $(hostname) in $(pwd)"

# ssh sessions skip conda's .bashrc hook, so look for a usable Python explicitly
PY=""
for c in "${PYTHON:-}" ~/miniconda3/bin/python ~/anaconda3/bin/python ~/miniforge3/bin/python python3.13 python3.12 python3.11 python3; do
  [ -n "$c" ] && command -v "$c" >/dev/null 2>&1 || continue
  "$c" -c 'import sys, ensurepip; assert sys.version_info >= (3, 11)' 2>/dev/null && { PY="$c"; break; }
done
[ -n "$PY" ] || { echo "❌ need Python 3.11+ with venv/ensurepip"; exit 1; }
echo "🐍 python: $PY ($("$PY" --version))"
# a half-built .venv from a failed run has no pip; rebuild it
[ -x .venv/bin/pip ] || { rm -rf .venv; "$PY" -m venv .venv; }
# shellcheck disable=SC1091
. .venv/bin/activate
pip install -q --upgrade pip huggingface_hub pytest
echo "🧪 offline tests"
python -m pytest -q -p no:cacheprovider tests | tail -1

LS="${LLAMA_SERVER:-$(command -v llama-server || true)}"
if [ -z "$LS" ] && [ -x ~/llama.cpp/build/bin/llama-server ]; then
  LS="$(realpath ~/llama.cpp/build/bin/llama-server)"
fi
if [ -z "$LS" ] && [ -x vendor/llama.cpp/build/bin/llama-server ]; then
  LS="$(pwd)/vendor/llama.cpp/build/bin/llama-server"
fi
if [ -z "$LS" ]; then
  if [ "${BUILD_LLAMA:-0}" = "1" ]; then
    command -v nvcc >/dev/null || { echo "❌ nvcc (CUDA toolkit) not found; install it or point LLAMA_SERVER at an existing build"; exit 1; }
    command -v cmake >/dev/null || { echo "❌ cmake not found"; exit 1; }
    echo "🔨 building llama.cpp (CUDA archs ${CUDA_ARCHS:-86})"
    [ -d vendor/llama.cpp ] || git clone --depth 1 https://github.com/ggml-org/llama.cpp vendor/llama.cpp
    cmake -S vendor/llama.cpp -B vendor/llama.cpp/build -DGGML_CUDA=ON \
      -DCMAKE_CUDA_ARCHITECTURES="${CUDA_ARCHS:-86}" -DCMAKE_BUILD_TYPE=Release
    cmake --build vendor/llama.cpp/build -j"$(nproc)" --target llama-server
    LS="$(pwd)/vendor/llama.cpp/build/bin/llama-server"
  else
    echo "❌ llama-server not found. Either: export LLAMA_SERVER=/path/to/llama-server, or rerun with BUILD_LLAMA=1"
    exit 1
  fi
fi
echo "LLAMA_SERVER=$LS" > mission/.env
echo "🔧 llama-server: $LS"
"$LS" --version 2>&1 | head -3 || true

if [ ! -f data/attested.json ] || [ "${REATTEST:-0}" = "1" ]; then
  echo "📌 pinning GGUF files via Hugging Face metadata (no weights downloaded)"
  python tools/resolve_ggufs.py --catalog data/otakubench50.json --out data/attested.json \
    || echo "⚠️  some rows not fully attested — they still run, via pinned file if found or -hf otherwise (use --strict to skip them)"
fi

echo
echo "🗺️  plan for GPU ${GPU:-0}:"
python mission/screen_mission.py --dry-run --gpu "${GPU:-0}" --llama-server "$LS"
echo
echo "✅ setup done. Pilot:  ./mission/run.sh --ranks 15,18,19,20,31,46"
echo "   Full sweep:        ./mission/run.sh"
