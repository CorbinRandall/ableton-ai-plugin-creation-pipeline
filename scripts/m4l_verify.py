#!/usr/bin/env python3
"""
M4L verify (public pipeline): build Pipeline_Example → poll browser → load → OSC params.

Requires AbletonMCP (TCP 9877) and (unless --no-osc) AbletonOSC + host python-osc.

Usage (from the root of this repository clone, next to ~/Music/Ableton User Library by default):

  python3 scripts/m4l_verify.py

See: docs/VERIFY_GUIDE.md
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_EXAMPLE_PROJECT = REPO_ROOT / "projects" / "Pipeline_Example"
_TOOLING = REPO_ROOT / "tooling"
if str(_TOOLING) not in sys.path:
    sys.path.insert(0, str(_TOOLING))
from m4l_pipeline import load_browser_item_by_browser_path  # noqa: E402

_BROWSER_PARENT = "user_library/Presets/MIDI Effects/Max MIDI Effect/Imported"
_ABLETON_HOST = "127.0.0.1"
_ABLETON_PORT = 9877
_OSC_SEND = ("127.0.0.1", 11000)
_OSC_RECV_BIND = ("127.0.0.1", 11001)


def _ableton_cmd(cmd_type: str, params: dict, timeout: float = 25.0) -> dict:
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


def _poll_browser_item(name: str, attempts: int = 12, delay: float = 1.0) -> bool:
    path = _BROWSER_PARENT
    for _ in range(attempts):
        r = _ableton_cmd("get_browser_items_at_path", {"path": path})
        items = r.get("result", {})
        if isinstance(items, str):
            items = json.loads(items)
        names = [x.get("name", "") for x in items.get("items", [])]
        if name in names:
            return True
        time.sleep(delay)
    return False


def _osc_device_param_names(track: int, device: int, wait: float = 5.0) -> tuple:
    """AbletonOSC replies to (sender_ip, 11001); bind 11001 with SO_REUSEADDR."""
    from pythonosc import udp_client, osc_message

    time.sleep(0.25)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(wait)
    try:
        sock.bind(_OSC_RECV_BIND)
    except OSError as e:
        raise RuntimeError(
            f"Cannot bind OSC receive {_OSC_RECV_BIND}: {e}. "
            "Close other listeners on 11001 or disable conflicting tools."
        ) from e
    client = udp_client.SimpleUDPClient(*_OSC_SEND)
    try:
        client.send_message("/live/device/get/parameters/name", [int(track), int(device)])
        data, _ = sock.recvfrom(65536)
    finally:
        sock.close()
    msg = osc_message.OscMessage(data)
    args = list(msg.params)
    if len(args) < 3:
        return tuple()
    return tuple(args[2:])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--device-name",
        default="Pipeline_Example",
        help="Leaf name under Imported/ (matches deployed .amxd stem).",
    )
    ap.add_argument(
        "--build",
        choices=("pipeline_example",),
        default="pipeline_example",
        help="Which builder to run before verify (ignored if --skip-build).",
    )
    ap.add_argument(
        "--expect-params",
        default="",
        help="Comma-separated parameter longname substrings (default derives from device name).",
    )
    ap.add_argument("--skip-build", action="store_true", help="Skip builder; device must already be in Imported/")
    ap.add_argument("--no-cleanup", action="store_true", help="Leave MIDI track and devices in place")
    ap.add_argument(
        "--no-osc",
        action="store_true",
        help="Skip AbletonOSC parameter checks (MCP-only load).",
    )
    args = ap.parse_args()

    name = args.device_name
    if args.expect_params.strip():
        expected = tuple(s.strip() for s in args.expect_params.split(",") if s.strip())
    elif name == "Pipeline_Example":
        expected = ("Rate", "Depth", "Active")
    else:
        expected = ()

    if not args.skip_build:
        if not PIPELINE_EXAMPLE_PROJECT.is_dir():
            print(f"ERROR: Missing project at {PIPELINE_EXAMPLE_PROJECT}", file=sys.stderr)
            return 1
        if args.build == "pipeline_example":
            sys.path.insert(0, str(PIPELINE_EXAMPLE_PROJECT))
            import build_pipeline_example as bpe  # noqa: E402

            rc = bpe.main(["--no-live"])
            if rc != 0:
                return rc

    try:
        ping = _ableton_cmd("get_session_info", {})
        if ping.get("status") != "success":
            print(f"ERROR: get_session_info: {ping}", file=sys.stderr)
            return 1
    except OSError as e:
        print(f"ERROR: Cannot reach AbletonMCP at {_ABLETON_HOST}:{_ABLETON_PORT}: {e}", file=sys.stderr)
        return 1

    if not _poll_browser_item(name):
        print(f"ERROR: '{name}' not found under {_BROWSER_PARENT} after polling", file=sys.stderr)
        return 1
    print(f"OK: browser lists '{name}'")

    created = _ableton_cmd("create_midi_track", {"index": -1})
    if created.get("status") != "success":
        print(f"ERROR: create_midi_track: {created}", file=sys.stderr)
        return 1
    res = created.get("result", {})
    if isinstance(res, str):
        res = json.loads(res)
    track = res.get("index")
    if track is None:
        print(f"ERROR: No track index in response: {created}", file=sys.stderr)
        return 1

    load_path = f"{_BROWSER_PARENT}/{name}"
    loaded = load_browser_item_by_browser_path(track, load_path)
    if loaded.get("status") != "success":
        print(f"ERROR: load device at {load_path!r}: {loaded}", file=sys.stderr)
        return 1
    print(f"OK: loaded onto track {track}")

    time.sleep(0.35)

    info = _ableton_cmd("get_track_info", {"track_index": track})
    if info.get("status") != "success":
        print(f"ERROR: get_track_info: {info}", file=sys.stderr)
        return 1
    tinfo = info.get("result", {})
    if isinstance(tinfo, str):
        tinfo = json.loads(tinfo)
    devices = tinfo.get("devices", [])
    if not devices:
        print("ERROR: No devices on track after load", file=sys.stderr)
        return 1
    dev_index = devices[-1]["index"]
    dev_name = devices[-1].get("name", "")
    print(f"OK: target device index {dev_index} name={dev_name!r}")

    if name not in dev_name and dev_name not in name:
        print(
            f"WARNING: loaded device name {dev_name!r} does not contain expected {name!r}",
            file=sys.stderr,
        )

    if args.no_osc:
        print("NOTE: --no-osc: skipping /live/device/get/parameters/name checks")
    else:
        try:
            names = _osc_device_param_names(track, dev_index)
        except socket.timeout:
            print(
                "ERROR: AbletonOSC timed out on 11001. Install/configure AbletonOSC, "
                "quit Live completely, reopen, then enable it under Preferences → "
                "Link, Tempo & MIDI → Control Surface. Or use --no-osc. "
                "Ensure nothing else binds UDP 11001.",
                file=sys.stderr,
            )
            return 1
        except Exception as e:
            print(f"ERROR: OSC read failed: {e}", file=sys.stderr)
            return 1

        if expected:
            missing = [e for e in expected if e not in names]
            if missing:
                print(f"ERROR: Missing parameters {missing}; got {names}", file=sys.stderr)
                return 1
            print(f"OK: OSC parameters include {expected}")
        else:
            print(f"NOTE: listing OSC parameter names: {names[:12]}...")

    sess = _ableton_cmd("get_session_info", {})
    print("OK: session snapshot:", json.dumps(sess.get("result", sess), indent=2)[:500])

    if not args.no_cleanup:
        try:
            clr = _ableton_cmd("clear_devices_on_track", {"track_index": track})
            if clr.get("status") == "success":
                print(f"OK: cleared devices on track {track} ({clr.get('result')})")
            else:
                print(f"NOTE: clear_devices_on_track: {clr.get('message', clr)}")
        except Exception:
            print("NOTE: clear_devices_on_track not available; leaving devices in place")

    print("M4L_VERIFY_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
