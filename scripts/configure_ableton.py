#!/usr/bin/env python3
"""
Optional Ableton preferences helpers.

Live persists Control Surface choices in Preferences.cfg, which uses an opaque/binary
Ableton-specific format — this script does **not** modify it.

What it *does*:
  • Finds `Live x.x.x` preference folders and writes/overlays `Options.txt` lines that
    you request (Ableton-supported flags only — see Ableton KB “Options.txt”).
  • Prints the remaining manual MIDI step (select AbletonOSC + AbletonMCP).

Examples:
  python3 scripts/configure_ableton.py
  python3 scripts/configure_ableton.py --option -EnableLOM --option '-ReWireMaster Off'
"""
from __future__ import annotations

import argparse
import subprocess
import sys

import ableton_bootstrap_common as abc


def macos_live_app_names() -> list[str]:
    return sorted({p.name for p in abc.find_installed_live_app_bundles()}, key=len)


def try_open_preferences_ui() -> bool:
    """Best-effort: bring Live forward on macOS (user still selects Control Surfaces)."""

    if sys.platform != "darwin":
        return False
    for name in macos_live_app_names():
        r = subprocess.run(  # noqa: S603
            ["osascript", "-e", f'tell application "{name.removesuffix(".app")}" to activate'],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if r.returncode == 0:
            print(f"Tried activating {name} (open Preferences → Link / Tempo / MIDI yourself).")
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--option",
        action="append",
        default=[],
        metavar="LINE",
        help="Append one Options.txt flag (repeatable); must start with '-' per Ableton format.",
    )
    ap.add_argument(
        "--write-options-empty",
        action="store_true",
        help='Write only managed block (no extras). Same as omitting "--option".',
    )
    ap.add_argument(
        "--open-live",
        action="store_true",
        help='macOS: run AppleScript activate on the newest matching "Ableton Live *.app"',
    )
    args = ap.parse_args()

    opts_to_write = list(dict.fromkeys(args.option)) if args.option else []

    dirs = abc.live_pref_dirs()
    print(f"Ableton preferences root: {abc.ableton_prefs_root()}")
    if dirs:
        print("Detected Live prefs folders:")
        for d in dirs[:6]:
            print(f"  {d}")
        if len(dirs) > 6:
            print(f"  … +{len(dirs) - 6} older")
        for pref in dirs[:3]:
            if opts_to_write or args.write_options_empty:
                pth = abc.write_options_txt(pref, opts_to_write)
                print(f"Wrote guarded block → {pth}")

    else:
        print(
            "WARN: No `Live x.x.x` folder under preferences yet — Launch Live once, quit, rerun."
        )

    print(
        "\nManual step (cannot be scripted reliably):\n"
        "  Preferences → Link / Tempo / MIDI → Control Surface → AbletonOSC (Input/Output: None).\n"
        "  Optionally add AbletonMCP (same).\n"
        '  AbletonOSC should show “Listening on port 11000”.'
    )

    if args.open_live:
        if not try_open_preferences_ui():
            print("WARN: Could not activate Live (install under /Applications or open Live manually).")

    print("\nOPTIONS_TXT_NOTE: Only use flags Ableton documents; undocumented flags may crash Live.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
