"""Shared --json stdout helper for CLI scripts.

When --json is set, scripts should emit exactly one JSON object on stdout
(no trailing marker line). Human markers and logs go to stderr or are omitted.
"""

from __future__ import annotations

import json
import sys


def emit_json(payload: dict, *, ok: bool) -> None:
    payload.setdefault("ok", ok)
    sys.stdout.write(json.dumps(payload) + "\n")
