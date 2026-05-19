#!/usr/bin/env python3
"""Preflight a device spec JSON for Presentation UI + readable labels.

Usage (repo root):

  ./venv/bin/python scripts/check_spec_ui.py projects/Pipeline_Example/pipeline_example_spec.json

Exit 0 = OK (warnings may still print). Exit 1 = errors.
See docs/M4L_FRONTEND_AND_BACKEND.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_UI_CLASSES = frozenset(
    {
        "live.dial",
        "live.toggle",
        "live.slider",
        "live.numbox",
        "live.text",
        "live.menu",
        "live.tab",
    }
)
_PATCH_ONLY = frozenset(
    {"midiin", "midiout", "in", "out", "plugout~", "plugin~", "ezadc~", "ezdac~"}
)


def check_spec(spec: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    boxes = spec.get("boxes") or []
    if not boxes:
        errors.append("spec has no boxes")
        return errors, warnings

    pres_count = 0
    for entry in boxes:
        box = entry.get("box") or {}
        maxclass = (box.get("maxclass") or "").lower()
        if maxclass in _PATCH_ONLY:
            continue
        is_ui = bool(box.get("parameter_enable")) or maxclass in _UI_CLASSES or maxclass == "comment"
        if not is_ui:
            continue
        name = box.get("id") or maxclass
        if box.get("presentation") != 1:
            warnings.append(
                f"{name} ({maxclass}): no presentation:1 — build_amxd may auto-add for live.* / parameter_enable"
            )
        elif not box.get("presentation_rect"):
            warnings.append(f"{name}: presentation:1 but no presentation_rect")
        else:
            pres_count += 1

        if maxclass in _UI_CLASSES or (maxclass == "comment" and box.get("presentation") == 1):
            if maxclass == "live.numbox":
                if "lcdcolor" not in box and "textcolor" not in box:
                    warnings.append(
                        f"{name}: no lcdcolor/textcolor — build_amxd applies defaults; set explicitly for theme control"
                    )
            elif "textcolor" not in box:
                warnings.append(
                    f"{name}: no textcolor — build_amxd applies light gray default; set explicitly to match your theme"
                )

    open_pres = spec.get("openinpresentation", 1)
    if pres_count == 0:
        if open_pres != 0:
            errors.append(
                "no presentation UI boxes found (device face will be blank in Live; "
                "set presentation:1 + presentation_rect on controls, or openinpresentation:0)"
            )
        else:
            warnings.append("openinpresentation is 0 and no presentation boxes — Edit mode only")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path, help="Path to device spec JSON")
    args = ap.parse_args(argv)

    if not args.spec.is_file():
        print(f"ERROR: not found: {args.spec}", file=sys.stderr)
        return 1

    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 1

    errors, warnings = check_spec(spec)
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        return 1
    print("SPEC_UI_OK", args.spec.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
