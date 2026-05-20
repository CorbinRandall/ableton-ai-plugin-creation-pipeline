#!/usr/bin/env bash
# T5 helper — interactive screenshot for human / vision-assisted rack verification.
# macOS: uses screencapture(1) -i (window or region). See docs/VERIFICATION_TIERS.md.
set -euo pipefail

OUT="${1:-live_rack_capture.png}"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "capture_live_window.sh: macOS only (screencapture)." >&2
  exit 1
fi

echo "Select the Ableton Live window or drag a region (Cancel = exit)." >&2
screencapture -i "$OUT"
echo "Saved: $(pwd)/$OUT" >&2
