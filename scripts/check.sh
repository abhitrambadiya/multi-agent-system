#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python -m pytest -q
(cd frontend && npm run build)
.venv/bin/python -m compileall -q backend scripts eval
