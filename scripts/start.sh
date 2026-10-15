#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export OLLAMA_MODELS="$PWD/data/models/ollama"
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_NO_CLOUD=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export MPLCONFIGDIR="$PWD/tmp/matplotlib"
mkdir -p data/runtime
ollama_pid=""
cleanup(){ if [ -n "$ollama_pid" ]; then kill "$ollama_pid" 2>/dev/null || true; fi; }
trap cleanup EXIT INT TERM
if [ "${AIEOS_MODE:-LOCAL_LLM}" = "LOCAL_LLM" ]; then
  if ! curl --silent --fail http://127.0.0.1:11434/api/tags >/dev/null; then
    command -v ollama >/dev/null || { echo 'Install Ollama first; see README.md.'; exit 1; }
    ollama serve >data/runtime/ollama.log 2>&1 &
    ollama_pid=$!
    for attempt in {1..20}; do
      if curl --silent --fail http://127.0.0.1:11434/api/tags >/dev/null; then break; fi
      sleep 1
    done
  fi
fi
[ -f data/processed/olist.sqlite ] || { echo 'Dataset missing: run scripts/ingest.py after downloading Olist.'; exit 1; }
[ -d frontend/dist ] || (cd frontend && npm ci && npm run build)
echo 'Open http://localhost:8010 — Ctrl-C stops the app.'
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010
