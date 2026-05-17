#!/usr/bin/env bash
# Ensure Python 3.10+ exists; export BOOTSTRAP_PYTHON to a working interpreter.
# macOS: installs python@3.12 via Homebrew when brew is available.
# Linux: prints install hints (no unattended distro install).
#
# From bootstrap:  . "$ROOT/scripts/ensure_python.sh"
# When sourced, uses top-level "return" (never `exit` from inside a function — that won't stop the file).
# Do not source from zsh/fish; run ./bootstrap.sh (bash) instead.

if [ -z "${BASH_VERSION:-}" ]; then
  echo "ERROR: scripts/ensure_python.sh must run under bash (use ./bootstrap.sh from repo root)." >&2
  return 1 2>/dev/null || exit 1
fi

set -euo pipefail

_is_sourced() {
  [[ "${BASH_SOURCE[0]}" != "${0}" ]]
}

_report_python() {
  export BOOTSTRAP_PYTHON="$1"
  echo "Using Python: $BOOTSTRAP_PYTHON ($("$BOOTSTRAP_PYTHON" -c 'import sys; print(sys.version.split()[0])'))"
}

_py_ok() {
  local x="$1"
  command -v "$x" >/dev/null 2>&1 || return 1
  "$x" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null
}

_pick_python() {
  if [[ -n "${BOOTSTRAP_PYTHON:-}" ]] && _py_ok "$BOOTSTRAP_PYTHON"; then
    echo "$BOOTSTRAP_PYTHON"
    return 0
  fi
  local cand
  for cand in python3.12 python3.11 python3.10 python3 python; do
    if _py_ok "$cand"; then
      command -v "$cand"
      return 0
    fi
  done
  return 1
}

if py="$(_pick_python 2>/dev/null)"; then
  _report_python "$py"
  if _is_sourced; then return 0; fi
  exit 0
fi

case "$(uname -s)" in
Darwin)
  if ! command -v brew >/dev/null 2>&1; then
    echo "ERROR: Python 3.10+ not found and Homebrew is not installed." >&2
    echo "Install Homebrew: https://brew.sh  — or install Python from https://www.python.org/downloads/" >&2
    if _is_sourced; then return 1; fi
    exit 1
  fi
  echo "Python 3.10+ not found. Installing python@3.12 via Homebrew…"
  HOMEBREW_NO_INSTALL_CLEANUP="${HOMEBREW_NO_INSTALL_CLEANUP:-1}" brew install python@3.12
  PY_PREFIX="$(brew --prefix python@3.12 2>/dev/null || true)"
  if [[ -n "$PY_PREFIX" && -x "$PY_PREFIX/bin/python3.12" ]]; then
    export PATH="$PY_PREFIX/bin:$PATH"
  fi
  ;;
Linux)
  echo "ERROR: Python 3.10+ not found." >&2
  echo "Install e.g. Debian/Ubuntu: sudo apt install python3 python3-venv python3-pip" >&2
  echo "Fedora: sudo dnf install python3" >&2
  if _is_sourced; then return 1; fi
  exit 1
  ;;
*)
  echo "ERROR: Python 3.10+ not found. Install from https://www.python.org/downloads/" >&2
  if _is_sourced; then return 1; fi
  exit 1
  ;;
esac

if py="$(_pick_python 2>/dev/null)"; then
  _report_python "$py"
  if _is_sourced; then return 0; fi
  exit 0
fi

echo "ERROR: Python 3.10+ still not on PATH after install attempt." >&2
if _is_sourced; then return 1; fi
exit 1
