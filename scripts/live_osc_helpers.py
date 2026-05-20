"""Shared AbletonMCP (TCP) and AbletonOSC (UDP) helpers for verify scripts."""
from __future__ import annotations

import json
import socket
import time
from typing import Any

ABLETON_HOST = "127.0.0.1"
ABLETON_MCP_PORT = 9877
OSC_SEND = ("127.0.0.1", 11000)
OSC_RECV_BIND = ("127.0.0.1", 11001)

# Default UDP port in tooling/templates/midi_effect_selftest_ping.json — keep in sync with template `udpsend`.
DEFAULT_SELFTEST_UDP_PORT = 39129


def udp_selftest_bind(port: int, bind_host: str = ABLETON_HOST) -> socket.socket:
    """Open and bind a UDP socket — call **before** triggering Live so Max pings are not dropped."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((bind_host, port))
    sock.settimeout(0.2)
    return sock


def udp_selftest_receive_until(
    sock: socket.socket,
    marker: bytes,
    deadline_monotonic: float,
) -> bool:
    """Receive until ``marker`` appears in a datagram or ``deadline_monotonic`` passes."""
    while time.monotonic() < deadline_monotonic:
        try:
            data, _ = sock.recvfrom(8192)
        except socket.timeout:
            continue
        if marker in data:
            return True
    return False


def ableton_cmd(cmd_type: str, params: dict, timeout: float = 25.0) -> dict:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((ABLETON_HOST, ABLETON_MCP_PORT))
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


def coerce_dict(val: Any) -> dict:
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        return json.loads(val)
    return {}


def poll_browser_imported(
    browser_parent: str,
    device_stem: str,
    *,
    attempts: int = 12,
    delay: float = 1.0,
) -> bool:
    for _ in range(attempts):
        r = ableton_cmd("get_browser_items_at_path", {"path": browser_parent})
        items = coerce_dict(r.get("result"))
        names = [x.get("name", "") for x in items.get("items", [])]
        stem_lower = device_stem.lower()
        for n in names:
            if (
                n == device_stem
                or n == f"{device_stem}.amxd"
                or n == f"{device_stem}.adv"
                or stem_lower in n.lower()
            ):
                return True
        time.sleep(delay)
    return False


def _osc_request(address: str, args: list, wait: float = 5.0) -> tuple:
    from pythonosc import udp_client, osc_message

    time.sleep(0.15)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(wait)
    try:
        sock.bind(OSC_RECV_BIND)
    except OSError as e:
        raise RuntimeError(
            f"Cannot bind OSC receive {OSC_RECV_BIND}: {e}. "
            "Enable AbletonOSC in Live or close other listeners on 11001."
        ) from e
    client = udp_client.SimpleUDPClient(*OSC_SEND)
    try:
        client.send_message(address, args)
        data, _ = sock.recvfrom(65536)
    finally:
        sock.close()
    msg = osc_message.OscMessage(data)
    return tuple(msg.params)


def osc_device_parameter_names(track: int, device: int, wait: float = 5.0) -> tuple[str, ...]:
    params = _osc_request("/live/device/get/parameters/name", [int(track), int(device)], wait)
    if len(params) < 3:
        return ()
    return tuple(str(p) for p in params[2:])


def osc_device_parameter_values(track: int, device: int, wait: float = 5.0) -> tuple[float, ...]:
    params = _osc_request("/live/device/get/parameters/value", [int(track), int(device)], wait)
    if len(params) < 3:
        return ()
    return tuple(float(p) for p in params[2:])


def osc_set_device_parameter(
    track: int,
    device: int,
    parameter_index: int,
    value: float,
    wait: float = 5.0,
) -> None:
    _osc_request(
        "/live/device/set/parameter/value",
        [int(track), int(device), int(parameter_index), float(value)],
        wait,
    )


def expected_param_names_from_spec(spec: dict) -> tuple[str, ...]:
    names: list[str] = []
    for entry in spec.get("boxes") or []:
        box = entry.get("box") or {}
        if not box.get("parameter_enable"):
            continue
        vo = (box.get("saved_attribute_attributes") or {}).get("valueof") or {}
        ln = vo.get("parameter_longname")
        if ln:
            names.append(str(ln))
    return tuple(names)
