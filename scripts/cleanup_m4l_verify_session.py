#!/usr/bin/env python3
"""
Collapse the Live set to one MIDI track and load a device from the browser for MCP/OSC tests.

Uses AbletonMCP (TCP 9877) + AbletonOSC (/live/song/delete_track).

Usage (with Live running, from this repository root):

  python3 scripts/cleanup_m4l_verify_session.py
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from pathlib import Path

import ableton_bootstrap_common as abc

REPO_ROOT = Path(__file__).resolve().parent.parent
_TOOLING = REPO_ROOT / "tooling"
if str(_TOOLING) not in sys.path:
    sys.path.insert(0, str(_TOOLING))
from m4l_pipeline import load_browser_item_by_browser_path  # noqa: E402

DEFAULT_SAVE = abc.ableton_home() / "User Library" / "Templates" / "M4L Pipeline Verify.als"

_ABLETON_HOST = "127.0.0.1"
_ABLETON_PORT = 9877
_OSC_SEND = ("127.0.0.1", 11000)


def _ableton_cmd(cmd_type: str, params: dict, timeout: float = 45.0) -> dict:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((_ABLETON_HOST, _ABLETON_PORT))
    s.sendall(json.dumps({"type": cmd_type, "params": params}).encode())
    chunks: list[bytes] = []
    while True:
        chunk = s.recv(32768)
        if not chunk:
            break
        chunks.append(chunk)
        try:
            json.loads(b"".join(chunks))
            break
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    s.close()
    if not chunks:
        raise RuntimeError("No response from AbletonMCP")
    return json.loads(b"".join(chunks))


def _normalized_result(blob: dict) -> dict | str:
    r = blob.get("result", blob)
    if isinstance(r, str):
        try:
            return json.loads(r)
        except json.JSONDecodeError:
            pass
    return r if isinstance(r, dict) else {}


def _device_matches(name: str, needle: str) -> bool:
    n = (name or "").lower()
    return needle.lower() in n


def _osc_delete_track(track_index: int) -> None:
    from pythonosc import udp_client

    udp_client.SimpleUDPClient(*_OSC_SEND).send_message("/live/song/delete_track", [int(track_index)])
    time.sleep(0.08)


def _osc_stop() -> None:
    from pythonosc import udp_client

    udp_client.SimpleUDPClient(*_OSC_SEND).send_message("/live/song/stop_playing", [])
    time.sleep(0.05)


def main() -> int:
    ap = argparse.ArgumentParser(description="One MIDI track + reload device from Imported/")
    ap.add_argument(
        "--save",
        nargs="?",
        const=str(DEFAULT_SAVE),
        default=None,
        help=f"Save Live Set after cleanup (default: {DEFAULT_SAVE})",
    )
    ap.add_argument("--tempo", type=float, default=120.0, help="Song tempo after cleanup")
    ap.add_argument("--track-name", default="M4L Verify", help="Rename the keeper MIDI track")
    ap.add_argument(
        "--prefer-device-substring",
        default="Pipeline",
        help="Prefer a MIDI track that already has a device whose name contains this substring",
    )
    ap.add_argument(
        "--load-browser-path",
        default="user_library/Presets/MIDI Effects/Max MIDI Effect/Imported/Pipeline_Example",
        help="Full AbletonMCP browser path to load (no .amxd suffix)",
    )
    args = ap.parse_args()

    try:
        ping = _ableton_cmd("get_session_info", {})
        if ping.get("status") != "success":
            print(f"ERROR: get_session_info: {ping}", file=sys.stderr)
            return 1
    except OSError as e:
        print(f"ERROR: Cannot reach AbletonMCP at {_ABLETON_HOST}:{_ABLETON_PORT}: {e}", file=sys.stderr)
        return 1

    _osc_stop()

    st = _normalized_result(_ableton_cmd("get_session_info", {}))
    tc = int(st.get("track_count", 0))

    midi_indices: list[int] = []
    keeper_candidates: list[int] = []
    pref = args.prefer_device_substring

    for ti in range(tc):
        info = _ableton_cmd("get_track_info", {"track_index": ti})
        if info.get("status") != "success":
            continue
        tinfo = _normalized_result(info)
        if not tinfo.get("is_midi_track"):
            continue
        midi_indices.append(ti)
        devices = tinfo.get("devices", []) or []
        if pref and any(_device_matches(d.get("name", ""), pref) for d in devices):
            keeper_candidates.append(ti)

    if not midi_indices:
        created = _ableton_cmd("create_midi_track", {"index": -1})
        if created.get("status") != "success":
            print(f"ERROR: create_midi_track: {created}", file=sys.stderr)
            return 1
        res = _normalized_result(created)
        ki = res.get("index")
        if ki is None:
            print(f"ERROR: create_midi_track missing index: {created}", file=sys.stderr)
            return 1
        keeper_idx = int(ki)
    else:
        keeper_idx = min(keeper_candidates) if keeper_candidates else min(midi_indices)
        to_remove = sorted([i for i in midi_indices if i != keeper_idx], reverse=True)
        for idx in to_remove:
            adjusted = keeper_idx
            if idx > keeper_idx:
                _osc_delete_track(idx)
            elif idx < keeper_idx:
                _osc_delete_track(idx)
                adjusted -= 1
            keeper_idx = adjusted

    tempo_set = _ableton_cmd("set_tempo", {"tempo": float(args.tempo)})
    if tempo_set.get("status") != "success":
        print(f"WARN: set_tempo: {tempo_set}", file=sys.stderr)

    clr = _ableton_cmd("clear_devices_on_track", {"track_index": keeper_idx})
    if clr.get("status") != "success":
        print(f"ERROR: clear_devices_on_track: {clr}", file=sys.stderr)
        return 1

    loaded = load_browser_item_by_browser_path(keeper_idx, args.load_browser_path)
    if loaded.get("status") != "success":
        print(f"ERROR: load browser path {args.load_browser_path!r}: {loaded}", file=sys.stderr)
        return 1

    nm = _ableton_cmd("set_track_name", {"track_index": keeper_idx, "name": args.track_name})
    if nm.get("status") != "success":
        print(f"WARN: set_track_name: {nm}", file=sys.stderr)

    print(f"OK: single MIDI track index={keeper_idx!r} with device from {args.load_browser_path!r}")

    if args.save:
        save_path = str(Path(args.save).expanduser())
        sv = _ableton_cmd("save_live_set_as", {"path": save_path})
        if sv.get("status") != "success":
            print(
                "WARN: save_live_set_as failed — fully restart Live after deploying AbletonMCP, then:\n"
                f"  python3 scripts/cleanup_m4l_verify_session.py --save \"{save_path}\"",
                file=sys.stderr,
            )
            print(f"NOTE: Or use File → Save Live Set As… → {save_path}", file=sys.stderr)
            print(f"DETAIL: {sv}", file=sys.stderr)
            return 2
        print(f"OK: saved Live Set → {save_path}")
        print(json.dumps(_normalized_result(sv), indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
