"""Live track creation, session info, and device alignment checks."""

from __future__ import annotations

import json
import os
import sys

from live.mcp_client import _ableton_cmd, _coerce_dict


def _create_midi_track_index() -> int:
    created = _ableton_cmd("create_midi_track", {"index": -1})
    if created.get("status") != "success":
        raise RuntimeError(f"create_midi_track failed: {created}")
    res = _coerce_dict(created.get("result"))
    idx = res.get("index")
    if idx is None:
        raise RuntimeError(f"create_midi_track: no index in {created}")
    return int(idx)


def _create_audio_track_index() -> int:
    """Requires AbletonMCP patched by ``scripts/install_remote_scripts.py`` (adds ``create_audio_track``)."""
    created = _ableton_cmd("create_audio_track", {"index": -1})
    if created.get("status") != "success":
        raise RuntimeError(f"create_audio_track failed: {created}")
    res = _coerce_dict(created.get("result"))
    idx = res.get("index")
    if idx is None:
        raise RuntimeError(f"create_audio_track: no index in {created}")
    return int(idx)


def assert_loaded_device_matches_spec(
    device_type: str,
    track_info: dict,
    *,
    track_kind: str | None = None,
) -> None:
    """Raise ``RuntimeError`` if the track/device after MCP load disagrees with ``device_type``.

    Uses AbletonMCP ``get_track_info`` payload (``devices[-1].type``, ``class_name``) plus optional
    ``track_kind`` from :func:`_create_new_track_for_device_type` when this pipeline created the track.

    Note: If the outermost device is an Effect Rack (``type == rack``), we try ``devices[-2]`` for a
    matching Max device entry; if that fails we warn and skip strict alignment (nested chains are not
    fully enumerated by stock MCP).
    """
    if track_kind is not None:
        if device_type == "audio_effect" and track_kind != "audio":
            raise RuntimeError(
                f"Track kind is {track_kind!r} but device_type is audio_effect "
                "(expected an audio track — ensure create_audio_track works and Live restarted after MCP updates)."
            )
        if device_type in ("midi_effect", "instrument") and track_kind != "midi":
            raise RuntimeError(
                f"Track kind is {track_kind!r} but device_type is {device_type!r} (expected a MIDI track)."
            )

    devices = track_info.get("devices") or []
    if not devices:
        raise RuntimeError("No devices on track after load — cannot verify device class.")

    def _matches_unknown_heuristic(reported: str, cname: str) -> bool:
        if reported != "unknown":
            return False
        if device_type == "audio_effect":
            return "mxdeviceaudioeffect" in cname or ("audio" in cname and "effect" in cname)
        if device_type == "midi_effect":
            return "mxdeviceminieffect" in cname or ("midi" in cname and "effect" in cname)
        if device_type == "instrument":
            return "mxdeviceinstrument" in cname or "instrument" in cname
        return False

    def _entry_matches(dev: dict) -> bool:
        r = (dev.get("type") or "").strip().lower()
        cn = (dev.get("class_name") or "").lower().replace(" ", "")
        return r == device_type or _matches_unknown_heuristic(r, cn)

    last = devices[-1]
    reported = (last.get("type") or "").strip().lower()

    if reported == "rack":
        if len(devices) >= 2 and _entry_matches(devices[-2]):
            print(
                "NOTE: Outermost Live device is a Rack; devices[-2] matches "
                f"{device_type!r} — treating T2 device alignment as OK.",
                file=sys.stderr,
            )
            return
        print(
            "WARN: Outermost device is a Rack and no preceding device entry matched "
            f"{device_type!r} — skipping strict T2 device-type check (nested chains not fully visible via MCP).",
            file=sys.stderr,
        )
        return

    if _entry_matches(last):
        return

    cname = (last.get("class_name") or "").lower().replace(" ", "")
    raise RuntimeError(
        "Loaded device type does not match spec device_type "
        f"{device_type!r}: MCP reports type={reported!r}, class_name={last.get('class_name')!r}. "
        "Live may have inserted a placeholder or wrong device category."
    )


def _create_new_track_for_device_type(device_type: str) -> tuple[int, str]:
    """Create an empty Live track appropriate for ``device_type``.

    Returns ``(track_index, track_kind)`` where ``track_kind`` is ``\"midi\"`` or ``\"audio\"``.

    **Important:** ``audio_effect`` requires AbletonMCP to expose ``create_audio_track`` (this repo
    patches it in ``install_remote_scripts.py``). Loading a Max **audio** device on a **MIDI** track
    usually breaks the device in Live (often a generic Max error such as “error 6”). We therefore
    **do not** fall back to MIDI unless ``M4L_ALLOW_AUDIO_ON_MIDI=1`` (debug only).
    """
    if device_type == "audio_effect":
        try:
            return _create_audio_track_index(), "audio"
        except RuntimeError as exc:
            if os.environ.get("M4L_ALLOW_AUDIO_ON_MIDI") == "1":
                print(
                    "WARN: M4L_ALLOW_AUDIO_ON_MIDI=1 — loading audio_effect onto a MIDI track "
                    "(unsupported; expect Live/Max errors).",
                    file=sys.stderr,
                )
                return _create_midi_track_index(), "midi"
            raise RuntimeError(
                "AbletonMCP does not support create_audio_track — cannot load audio_effect safely.\n\n"
                "Common cause: Live was still running while Remote Scripts were updated; the control "
                "surface keeps the old MCP until you restart Live.\n\n"
                "Fix:\n"
                "  1. ./venv/bin/python scripts/install_remote_scripts.py\n"
                "  2. Quit Ableton Live completely, then reopen.\n"
                "  3. Confirm MCP exposes the command:\n"
                "       ./venv/bin/python scripts/verify_setup.py --wait-mcp 120 "
                "--assert-create-audio-track\n\n"
                "Debug-only escape hatch (will likely break Max Audio Effects): "
                "M4L_ALLOW_AUDIO_ON_MIDI=1\n\n"
                f"Underlying error: {exc}"
            ) from exc
    return _create_midi_track_index(), "midi"


def get_track_info(track_index: int) -> dict:
    """Get track info including devices."""
    result = _ableton_cmd("get_track_info", {"track_index": track_index})
    data = result.get("result", {})
    if isinstance(data, str):
        data = json.loads(data)
    return data


def get_session_info() -> dict:
    """Get Ableton session info."""
    result = _ableton_cmd("get_session_info", {})
    data = result.get("result", {})
    if isinstance(data, str):
        data = json.loads(data)
    return data


def set_tempo(bpm: float) -> dict:
    """Set session tempo via AbletonMCP TCP (slow, ~490ms)."""
    return _ableton_cmd("set_tempo", {"tempo": bpm})


_osc_client = None


def _get_osc_client():
    global _osc_client
    if _osc_client is None:
        from pythonosc import udp_client
        _osc_client = udp_client.SimpleUDPClient("127.0.0.1", 11000)
    return _osc_client


def set_tempo_osc(bpm: float):
    """Set session tempo via AbletonOSC UDP (~0.02ms)."""
    _get_osc_client().send_message("/live/song/set/tempo", [float(bpm)])
