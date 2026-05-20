#!/usr/bin/env python3
"""Run validate_spec against tests/specs/bad/*.json; assert each fails."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tooling"))

from spec_validate import validate_spec  # noqa: E402

bad_dir = REPO / "tests" / "specs" / "bad"
failures: list[str] = []

for spec_path in sorted(bad_dir.glob("*.json")):
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    errors, _ = validate_spec(spec, check_ui=False, include_layout=False)
    if not errors:
        failures.append(spec_path.name)
        print(f"FAIL: {spec_path.name} should have failed validation but passed", file=sys.stderr)
    else:
        print(f"OK:   {spec_path.name} → {len(errors)} error(s)")

if failures:
    print(f"\n{len(failures)} bad spec(s) passed validation unexpectedly", file=sys.stderr)
    sys.exit(1)

print("SCHEMA_NEGATIVES_OK")
