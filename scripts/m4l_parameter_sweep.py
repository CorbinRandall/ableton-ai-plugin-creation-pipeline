#!/usr/bin/env python3
"""OSC parameter read/write smoke test on the selected device in Live.

Requires Live open with AbletonOSC + AbletonMCP. Works on macOS, Windows, and Linux
(host Python only — Ableton itself is not on Linux for Live).

Usage (repo root):

  python scripts/m4l_parameter_sweep.py --track 0 --device 0
  python scripts/m4l_parameter_sweep.py --track 0 --device 0 --set-index 0 --set-value 0.5

After m4l_verify or m4l_pipeline load, use get_track_info to find indices.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from live_osc_helpers import (  # noqa: E402
    ableton_cmd,
    coerce_dict,
    osc_device_parameter_names,
    osc_device_parameter_values,
    osc_set_device_parameter,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--track", type=int, required=True, help="0-based track index")
    ap.add_argument("--device", type=int, required=True, help="0-based device index on track")
    ap.add_argument("--set-index", type=int, default=None, help="Parameter index to write")
    ap.add_argument("--set-value", type=float, default=None, help="Value for --set-index")
    ap.add_argument("--list-only", action="store_true", help="Print names/values only")
    args = ap.parse_args(argv)

    if (args.set_index is None) ^ (args.set_value is None):
        print("ERROR: use both --set-index and --set-value together", file=sys.stderr)
        return 1

    try:
        ping = ableton_cmd("get_session_info", {})
        if ping.get("status") != "success":
            print(f"ERROR: AbletonMCP: {ping}", file=sys.stderr)
            return 1
    except OSError as e:
        print(
            f"ERROR: Cannot reach AbletonMCP (127.0.0.1:9877): {e}\n"
            "  Live running? AbletonMCP control surface enabled?",
            file=sys.stderr,
        )
        return 1

    try:
        names = osc_device_parameter_names(args.track, args.device)
        values_before = osc_device_parameter_values(args.track, args.device)
    except Exception as e:
        print(f"ERROR: AbletonOSC read failed: {e}", file=sys.stderr)
        return 1

    print(f"OK: {len(names)} parameters on track {args.track} device {args.device}")
    for i, (n, v) in enumerate(zip(names, values_before)):
        print(f"  [{i}] {n!r} = {v}")

    if args.list_only:
        print("M4L_PARAM_SWEEP_OK (list only)")
        return 0

    if args.set_index is not None:
        if args.set_index < 0 or args.set_index >= len(names):
            print(f"ERROR: --set-index out of range (0..{len(names) - 1})", file=sys.stderr)
            return 1
        try:
            osc_set_device_parameter(args.track, args.device, args.set_index, args.set_value)
            values_after = osc_device_parameter_values(args.track, args.device)
        except Exception as e:
            print(f"ERROR: AbletonOSC set failed: {e}", file=sys.stderr)
            return 1
        got = values_after[args.set_index] if args.set_index < len(values_after) else None
        print(f"OK: set [{args.set_index}] {names[args.set_index]!r} -> {args.set_value} (read back {got})")

    print("M4L_PARAM_SWEEP_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
