#!/usr/bin/env python3
"""Build + deploy + load the tutorial **Pipeline_Example** MIDI effect.

Each run allocates the next version folder under ``projects/Pipeline_Example/``, e.g.
``Pipeline_Example 1.2/``, copies ``spec.json`` + ``VERSION.txt``, builds the ``.amxd``,
deploys to Ableton User Library ``Imported/`` via ``deploy_artifact_for_device_type`` (inside
``build_deploy_load``), then (unless ``--no-live``) creates a **new**
Live track (MIDI vs audio follows ``device_type`` in ``pipeline_example_spec.json``) and loads
the device there via AbletonMCP so you do not have to drag from Finder.

Run from repo root (recommended, after ``./bootstrap.sh``):

  ./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py

Or ``--no-live`` if Live / MCP is not running (artifacts + deploy only).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_TOOLING = Path(__file__).resolve().parent.parent.parent / "tooling"
sys.path.insert(0, str(_TOOLING))

from m4l_pipeline import build_deploy_load  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--no-live",
        action="store_true",
        help="Skip AbletonMCP (no new track / load). Still builds versioned folder + deploys to User Library.",
    )
    ap.add_argument(
        "--track",
        type=int,
        default=None,
        metavar="N",
        help="0-based track index to load onto. Default: create a new track (type from spec device_type).",
    )
    args = ap.parse_args(argv)

    here = Path(__file__).resolve().parent
    spec = json.loads((here / "pipeline_example_spec.json").read_text(encoding="utf-8"))
    _pfx = os.environ.get("M4L_PROJECTS_PREFIX")
    try:
        # Tutorial output always uses projects/Pipeline_Example/, not projects/workspace/.
        os.environ.pop("M4L_PROJECTS_PREFIX", None)
        # Deploy sibling .adv so Live/AbletonOSC expose parameters (not only "Device On").
        result = build_deploy_load(spec, args.track, skip_live=args.no_live, with_adv=True)
    except OSError as e:
        print(f"ERROR: network/socket to AbletonMCP failed: {e}", file=sys.stderr)
        print("  Fix: open Live, enable AbletonMCP control surface, or pass --no-live.", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    finally:
        if _pfx is not None:
            os.environ["M4L_PROJECTS_PREFIX"] = _pfx
        else:
            os.environ.pop("M4L_PROJECTS_PREFIX", None)

    if not args.no_live:
        lr = result.get("load_result") or {}
        if lr.get("status") != "success":
            print(f"ERROR: Live load failed: {lr}", file=sys.stderr)
            print(
                "  Fix: open Live, enable AbletonMCP, or pass --no-live for build-only.",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
