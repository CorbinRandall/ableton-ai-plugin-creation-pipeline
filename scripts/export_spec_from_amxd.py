#!/usr/bin/env python3
"""Export a device spec JSON from an existing .amxd (Max-first workflow).

Usage:

  ./venv/bin/python scripts/export_spec_from_amxd.py path/to/device.amxd -o spec.json
  ./venv/bin/python scripts/export_spec_from_amxd.py device.amxd --device-type midi_effect --name MyDevice

Re-building with m4l_pipeline drops trailing binary embeds (SVG/skins) from the donor.
See docs/MAX_TO_SPEC.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_TOOLING = _REPO / "tooling"
if str(_TOOLING) not in sys.path:
    sys.path.insert(0, str(_TOOLING))

from m4l_pipeline import _extract_amxd_parts  # noqa: E402


def amxd_to_spec(
    amxd_path: Path,
    *,
    name: str | None = None,
    device_type: str = "midi_effect",
    description: str = "",
    minimal: bool = False,
) -> tuple[dict, bool]:
    """Return (spec dict, had_trailing_bytes)."""
    data = amxd_path.read_bytes()
    _hdr, _sub, root, trailing = _extract_amxd_parts(data)
    patcher = root.get("patcher") or {}

    stem = amxd_path.stem
    spec_name = name or stem.replace(" ", "_")
    spec: dict = {
        "name": spec_name,
        "description": description or f"Exported from {amxd_path.name}",
        "device_type": device_type,
        "boxes": patcher.get("boxes") or [],
        "lines": patcher.get("lines") or [],
    }

    if patcher.get("devicewidth") is not None:
        spec["devicewidth"] = patcher["devicewidth"]
    if patcher.get("openinpresentation") is not None:
        spec["openinpresentation"] = patcher["openinpresentation"]
    if patcher.get("bgcolor") is not None:
        spec["bgcolor"] = patcher["bgcolor"]
    if patcher.get("parameters") is not None and not minimal:
        spec["parameters"] = patcher["parameters"]

    if minimal:
        for entry in spec["boxes"]:
            box = entry.get("box") or {}
            for key in list(box.keys()):
                if key.startswith("_") or key in ("project",):
                    box.pop(key, None)

    return spec, len(trailing) > 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("amxd", type=Path, help="Source .amxd file")
    ap.add_argument("-o", "--output", type=Path, help="Output spec.json (default: stdout)")
    ap.add_argument("--name", help="Override spec name field")
    ap.add_argument(
        "--device-type",
        default="midi_effect",
        choices=["midi_effect", "audio_effect", "instrument"],
    )
    ap.add_argument("--description", default="", help="spec description field")
    ap.add_argument("--minimal", action="store_true", help="Omit nonessential patcher fields")
    ap.add_argument(
        "--warn-trailing",
        action="store_true",
        default=True,
        help="Warn if .amxd had trailing embeds (default: on)",
    )
    ap.add_argument("--no-warn-trailing", action="store_false", dest="warn_trailing")
    args = ap.parse_args(argv)

    if not args.amxd.is_file():
        print(f"ERROR: not found: {args.amxd}", file=sys.stderr)
        return 1

    try:
        spec, had_trailing = amxd_to_spec(
            args.amxd,
            name=args.name,
            device_type=args.device_type,
            description=args.description,
            minimal=args.minimal,
        )
    except (ValueError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.warn_trailing and had_trailing:
        print(
            "WARN: source .amxd had trailing binary data (e.g. embedded SVG). "
            "m4l_pipeline build will not preserve it.",
            file=sys.stderr,
        )

    text = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"EXPORT_SPEC_OK {args.output}")
    else:
        sys.stdout.write(text)
        print("EXPORT_SPEC_OK", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
