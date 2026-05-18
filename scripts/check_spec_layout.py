#!/usr/bin/env python3
"""Detect overlapping presentation_rect regions in a device spec.

Usage (any OS, repo root):

  python scripts/check_spec_layout.py path/to/spec.json
  ./venv/bin/python scripts/check_spec_layout.py path/to/spec.json   # macOS/Linux
  .\\venv\\Scripts\\python.exe scripts\\check_spec_layout.py path\\to\\spec.json   # Windows
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _rects(spec: dict) -> list[tuple[str, float, float, float, float]]:
    out: list[tuple[str, float, float, float, float]] = []
    for entry in spec.get("boxes") or []:
        box = entry.get("box") or {}
        if box.get("presentation") != 1:
            continue
        prect = box.get("presentation_rect")
        if not prect or len(prect) < 4:
            continue
        label = box.get("id") or box.get("maxclass") or "box"
        x, y, w, h = float(prect[0]), float(prect[1]), float(prect[2]), float(prect[3])
        out.append((str(label), x, y, w, h))
    return out


def _overlap(a: tuple, b: tuple) -> bool:
    _, ax, ay, aw, ah = a
    _, bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def check_layout(spec: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    rects = _rects(spec)
    for i, ra in enumerate(rects):
        for rb in rects[i + 1 :]:
            if _overlap(ra, rb):
                warnings.append(
                    f"presentation overlap: {ra[0]} {ra[1:]} vs {rb[0]} {rb[1:]}"
                )
    if len(rects) > 1:
        widths = [r[3] for r in rects]
        rights = [r[1] + r[3] for r in rects]
        dev_w = float(spec.get("devicewidth") or 0)
        if dev_w > 0 and max(rights) > dev_w + 2:
            warnings.append(
                f"presentation extends past devicewidth={dev_w} (max right edge {max(rights):.1f})"
            )
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path)
    args = ap.parse_args(argv)
    if not args.spec.is_file():
        print(f"ERROR: not found: {args.spec}", file=sys.stderr)
        return 1
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    errors, warnings = check_layout(spec)
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    if errors:
        return 1
    print("SPEC_LAYOUT_OK", args.spec.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
