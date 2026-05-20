"""Shared --json stdout helper for CLI scripts."""

from __future__ import annotations

import json
import sys


def emit_json(payload: dict, *, ok: bool) -> None:
    payload.setdefault("ok", ok)
    sys.stdout.write(json.dumps(payload) + "\n")
