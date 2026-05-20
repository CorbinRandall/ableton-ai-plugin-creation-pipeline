"""AbletonMCP TCP socket helpers."""

from __future__ import annotations

import json
import socket

_ABLETON_HOST = "127.0.0.1"
_ABLETON_PORT = 9877


def _ableton_cmd(cmd_type: str, params: dict, timeout: float = 15.0) -> dict:
    """Send a command to AbletonMCP Remote Script via socket."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((_ABLETON_HOST, _ABLETON_PORT))
    msg = json.dumps({"type": cmd_type, "params": params})
    s.sendall(msg.encode("utf-8"))

    chunks: list[bytes] = []
    while True:
        try:
            chunk = s.recv(16384)
            if not chunk:
                break
            chunks.append(chunk)
            try:
                json.loads(b"".join(chunks))
                break
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        except socket.timeout:
            break
    s.close()
    if not chunks:
        return {"status": "error", "message": "No response"}
    return json.loads(b"".join(chunks))


def _coerce_dict(blob: dict | str | None) -> dict:
    if isinstance(blob, dict):
        return blob
    if isinstance(blob, str) and blob.strip():
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            return {}
    return {}


def _normalize_browser_leaf(name: str) -> str:
    """Strip ``.amxd`` / ``.adv`` for comparisons — Live browser names include a suffix."""
    n = (name or "").strip()
    lower = n.lower()
    if lower.endswith(".amxd"):
        n = n[:-5].strip()
    elif lower.endswith(".adv"):
        n = n[:-4].strip()
    return n
