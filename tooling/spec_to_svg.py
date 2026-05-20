#!/usr/bin/env python3
"""Render a spec's presentation layer to SVG (preview without Live).

Usage:
  ./venv/bin/python tooling/spec_to_svg.py spec.json [-o preview.svg]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PAD = 8
H_DEFAULT = 200
LABEL_MAP = {
    "live.dial": ("dial", "#e0a020"),
    "live.toggle": ("toggle", "#20a0e0"),
    "live.slider": ("slider", "#20e0a0"),
    "live.numbox": ("numbox", "#e02080"),
    "live.menu": ("menu", "#a020e0"),
    "live.tab": ("tab", "#20e020"),
    "comment": ("text", "#cccccc"),
}


def label_for(box: dict) -> str:
    saa = box.get("saved_attribute_attributes", {}).get("valueof", {})
    return saa.get("parameter_longname") or box.get("text") or box.get("maxclass", "")


def render(spec: dict) -> str:
    width = float(spec.get("devicewidth", 200))
    pres_boxes: list[dict] = []
    for entry in spec.get("boxes", []):
        b = entry.get("box", {})
        if b.get("presentation") != 1:
            continue
        rect = b.get("presentation_rect")
        if not rect:
            continue
        pres_boxes.append(b)

    if not pres_boxes:
        height = H_DEFAULT
    else:
        height = max(r["presentation_rect"][1] + r["presentation_rect"][3] for r in pres_boxes) + PAD * 4

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#2a2a2a"/>',
        f'<text x="{PAD}" y="{PAD + 10}" font-family="sans-serif" font-size="11" fill="#ddd">'
        f'{spec.get("name", "Untitled")} ({spec.get("device_type", "?")})</text>',
    ]
    for b in pres_boxes:
        x, y, w, h = b["presentation_rect"]
        y_shifted = y + 24
        mc = b.get("maxclass", "")
        _, color = LABEL_MAP.get(mc, ("box", "#888"))
        label = label_for(b)
        parts.append(
            f'<rect x="{x}" y="{y_shifted}" width="{w}" height="{h}" '
            f'fill="{color}" fill-opacity="0.25" stroke="{color}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x + 2}" y="{y_shifted + h + 11}" font-family="sans-serif" '
            f'font-size="10" fill="#ccc">{label}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=None)
    args = ap.parse_args(argv)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    svg = render(spec)
    if args.out:
        args.out.write_text(svg, encoding="utf-8")
        print(f"WROTE {args.out}")
    else:
        sys.stdout.write(svg)
    print("\nSPEC_SVG_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
