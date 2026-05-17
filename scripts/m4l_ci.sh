#!/usr/bin/env bash
# Thin wrapper around m4l_verify.py (same directory).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/m4l_verify.py" "$@"
