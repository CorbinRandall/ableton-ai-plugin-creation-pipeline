#!/usr/bin/env bash
# OS-agnostic bootstrap wrapper (macOS, Linux, WSL). Run from repo root:
#   bash examples/sdk-run-setup/run.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
chmod +x run bootstrap.sh 2>/dev/null || true
exec ./run "$@"
