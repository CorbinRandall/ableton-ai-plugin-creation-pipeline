#!/usr/bin/env python3
"""
Install a known-good Live Set as the user default: copy factory DefaultLiveSet.als from the
Ableton install into User Library/Templates and point Library.cfg DefaultTemplateSet at it.

Quit Live before running if Library.cfg is locked on your OS.

Works on macOS and Windows (same paths as tooling/m4l_pipeline.py via ABLETON_HOME).
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import ableton_bootstrap_common as abc


def _library_cfgs_for_pref(pref_dir: Path) -> list[Path]:
    candidates = [pref_dir / "Library.cfg", pref_dir / "Preferences" / "Library.cfg"]
    return [p for p in candidates if p.is_file()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--skip-library-cfg",
        action="store_true",
        help="Only copy the .als into User Library/Templates (do not edit Library.cfg).",
    )
    args = ap.parse_args()

    factory = abc.find_factory_default_live_set_als()
    if not factory:
        print(
            "[install_default_template] WARN: factory DefaultLiveSet.als not found "
            "(install Ableton under /Applications or Program Files\\Ableton). Skipping.",
            file=sys.stderr,
        )
        return 0

    dest = abc.pipeline_startup_als_path()
    print(f"Ableton home:           {abc.ableton_home()}")
    print(f"Factory DefaultLiveSet: {factory}")
    print(f"Pipeline template:      {dest}")

    if args.dry_run:
        print("(dry-run) no files written.")
        return 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(factory, dest)

    if args.skip_library_cfg:
        print("Skipping Library.cfg (--skip-library-cfg).")
        return 0

    prefs = abc.live_pref_dirs()
    if not prefs:
        print(
            "[install_default_template] WARN: no Live x.x.x preferences folder — open Live once, "
            "quit, then re-run this script to set DefaultTemplateSet in Library.cfg.",
            file=sys.stderr,
        )
        return 0

    abs_dest = dest.resolve()
    patched = 0
    for pref in prefs:
        for cfg in _library_cfgs_for_pref(pref):
            if abc.patch_library_cfg_default_template(cfg, abs_dest):
                print(f"Patched DefaultTemplateSet → {cfg}")
                patched += 1

    if patched == 0:
        print(
            "[install_default_template] WARN: Library.cfg not found under preferences; "
            "template .als is installed but default set was not registered.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
