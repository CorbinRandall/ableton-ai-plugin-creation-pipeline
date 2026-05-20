#!/usr/bin/env python3
"""Offline audio smoke test (stub — full render/compare in a future PR).

Usage:
  ./venv/bin/python scripts/m4l_audio_smoke.py --spec examples/simple_gain_audio_spec.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", type=Path, required=True, help="Device spec JSON")
    args = ap.parse_args(argv)

    if not args.spec.is_file():
        print(f"ERROR: not found: {args.spec}", file=sys.stderr)
        return 2

    print(
        "M4L audio smoke test is not yet implemented.\n"
        "Manual check: load the device on an audio track, send signal, adjust knobs.\n"
        "See docs/AUDIO_SMOKE_TEST.md.",
        file=sys.stderr,
    )
    print("M4L_AUDIO_SMOKE_STUB")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
