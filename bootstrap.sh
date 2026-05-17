#!/usr/bin/env bash
# Zero-to-pipeline: ensure Python 3.10+ → venv → pip deps → Remote Scripts →
# default Live template → prefs helper (+ Max edition notice).
#
# Prerequisites: Ableton Live (Suite includes Max for Live; Standard requires the MFL add-on;
#   Lite / Intro cannot run Max-for-Live devices per Ableton KB). Python 3.10+ is ensured by
#   scripts/ensure_python.sh (brew on macOS) or scripts/ensure_python.ps1 (winget on Windows).
#
# Usage:
#   ./bootstrap.sh
# Afterward (once per Ableton prefs DB): Preferences → Link/Tempo/MIDI → select
# AbletonOSC + AbletonMCP, then quit/reopen Live and run:
#   ./venv/bin/python scripts/verify_setup.py --wait-mcp 180
#
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# shellcheck source=scripts/ensure_python.sh
. "$ROOT/scripts/ensure_python.sh"

PY="${BOOTSTRAP_PYTHON:?}"

venv="${M4L_VENV:-$ROOT/venv}"
if [[ ! -d "$venv" ]]; then
  echo "Creating venv → $venv"
  "$PY" -m venv "$venv"
fi

PIP=( "$venv/bin/python" -m pip )
"${PIP[@]}" install --upgrade pip setuptools wheel
"${PIP[@]}" install -r "$ROOT/requirements.txt"

"$venv/bin/python" "$ROOT/scripts/install_remote_scripts.py"
"$venv/bin/python" "$ROOT/scripts/configure_ableton.py"

if [[ "${M4L_SKIP_TEMPLATE:-}" != "1" ]]; then
  "$venv/bin/python" "$ROOT/scripts/install_default_template.py"
fi

PYTHONPATH="$ROOT/scripts" "$venv/bin/python" -c \
  "import ableton_bootstrap_common as a; print(a.MAX_FOR_LIVE_EDITION_NOTICE.strip())"

echo ""
echo "Bootstrap finished."
echo '  • If Live has never opened on this login, launch it once before verify.'
echo "  • Prefer: $venv/bin/python scripts/verify_setup.py --launch-ableton --wait-mcp 120"
echo "  • Preflight (no Ableton needed): $venv/bin/python scripts/verify_setup.py --preflight"
