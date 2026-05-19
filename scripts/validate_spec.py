#!/usr/bin/env python3
"""Validate a device spec JSON (structure + optional UI).

Usage (repo root):

  ./venv/bin/python scripts/validate_spec.py path/to/spec.json
  ./venv/bin/python scripts/validate_spec.py path/to/spec.json --structure-only
  ./venv/bin/python scripts/validate_spec.py path/to/spec.json --ui-only

Exit 0 prints SPEC_VALIDATE_OK. Exit 1 on errors.
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

from spec_validate import validate_spec, validate_structure, validate_ui  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path, help="Path to device spec JSON")
    ap.add_argument("--structure-only", action="store_true", help="JSON Schema + graph hints only")
    ap.add_argument("--ui-only", action="store_true", help="Presentation / textcolor checks only")
    ap.add_argument("--no-layout", action="store_true", help="Skip presentation overlap checks")
    args = ap.parse_args(argv)

    if not args.spec.is_file():
        print(f"ERROR: not found: {args.spec}", file=sys.stderr)
        return 1

    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 1

    if sum([args.structure_only, args.ui_only]) > 1:
        print("ERROR: use at most one of --structure-only, --ui-only", file=sys.stderr)
        return 1

    if args.structure_only:
        errors, warnings = validate_structure(spec)
    elif args.ui_only:
        errors, warnings = validate_ui(spec)
    else:
        errors, warnings = validate_spec(spec, include_layout=not args.no_layout)

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        return 1
    print("SPEC_VALIDATE_OK", args.spec.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
