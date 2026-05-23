#!/usr/bin/env python3
"""M4L pipeline MCP server (stdio).

Run with:

  python tooling/m4l_mcp_server.py            # raw stdio
  mcp dev tooling/m4l_mcp_server.py             # interactive (requires mcp package)

Tools expose validate/build/deploy/load/diagnose so MCP-capable agents
can drive the pipeline without shell parsing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tooling"))
sys.path.insert(0, str(REPO / "scripts"))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    sys.stderr.write("mcp package not installed. pip install 'mcp>=1.2.0'\n")
    sys.exit(2)

from spec_validate import validate_spec as _validate_spec  # noqa: E402
import spec_builder  # noqa: E402
from m4l_pipeline import (  # noqa: E402
    build_amxd,
    build_deploy_load,
    deploy_artifact_for_device_type,
)
from spec_to_svg import render as _render_svg  # noqa: E402
from diagnose import diagnose as _diagnose  # noqa: E402

# Live-control helpers (scripts/ is on sys.path)
import live_osc_helpers as _osc  # noqa: E402
from live.mcp_client import _ableton_cmd  # noqa: E402

mcp = FastMCP("m4l-pipeline")

RECIPES_DIR = REPO / "examples" / "recipes"


@mcp.tool()
def list_recipes() -> dict:
    """List all built-in device recipes."""
    items = []
    for d in sorted(RECIPES_DIR.glob("*/")):
        readme = d / "README.md"
        desc = readme.read_text(encoding="utf-8").splitlines()[0] if readme.exists() else d.name
        spec_path = d / "spec.json"
        device_type = "?"
        if spec_path.exists():
            device_type = json.loads(spec_path.read_text(encoding="utf-8")).get("device_type", "?")
        items.append({"slug": d.name, "type": device_type, "description": desc})
    return {"recipes": items}


@mcp.tool()
def read_recipe_spec(slug: str) -> dict:
    """Return the spec dict for a named recipe (must be built first)."""
    spec_path = RECIPES_DIR / slug / "spec.json"
    if not spec_path.exists():
        return {
            "error": f"recipe {slug!r} has no spec.json — run examples/recipes/{slug}/build.py"
        }
    return {"spec": json.loads(spec_path.read_text(encoding="utf-8"))}


@mcp.tool()
def compose_spec_from_dsl(python_source: str) -> dict:
    """Evaluate spec_builder code; must assign `device = audio_effect(...)` (or similar)."""
    ns = {
        "audio_effect": spec_builder.audio_effect,
        "midi_effect": spec_builder.midi_effect,
        "instrument": spec_builder.instrument,
        "Device": spec_builder.Device,
        "json": json,
    }
    exec(python_source, ns)
    dev = ns.get("device")
    if not isinstance(dev, spec_builder.Device):
        return {"error": "snippet must assign `device = audio_effect(...)` etc."}
    return {"spec": dev.to_dict()}


@mcp.tool()
def validate_spec(spec: dict) -> dict:
    errors, warnings = _validate_spec(spec)
    return {"errors": errors, "warnings": warnings, "ok": not errors}


@mcp.tool()
def spec_to_svg(spec: dict) -> dict:
    return {"svg": _render_svg(spec)}


@mcp.tool()
def build_amxd_tool(spec: dict, out_path: str | None = None) -> dict:
    out = Path(out_path) if out_path else None
    built = build_amxd(spec, out)
    return {"amxd_path": str(built)}


@mcp.tool()
def deploy(amxd_path: str, device_type: str) -> dict:
    deployed = deploy_artifact_for_device_type(
        Path(amxd_path), device_type, imported=True
    )
    return {"deployed_paths": [str(p) for p in deployed]}


@mcp.tool()
def load_in_live(spec: dict, with_adv: bool = False) -> dict:
    result = build_deploy_load(spec, None, skip_live=False, with_adv=with_adv)
    return result


@mcp.tool()
def diagnose(error_text: str) -> dict:
    """Match known error patterns to recommended fixes."""
    return _diagnose(error_text)


# ---------------------------------------------------------------------------
# Live state — read
# ---------------------------------------------------------------------------

@mcp.tool()
def live_session_state() -> dict:
    """Return a full snapshot of the current Live session.

    Includes tempo, playing state, time signature, track count, and for each
    track: name, index, is_midi, clip-slot count, and device names.

    Use this before any build/load/param operation to orient yourself in the
    current session.

    Returns::

        {
          "tempo": 120.0,
          "is_playing": false,
          "sig": "4/4",
          "track_count": 3,
          "tracks": [
            {"index": 0, "name": "M4L [midi] SimpleGain 1.2", "is_midi": true,
             "clip_slots": 8, "devices": [{"index": 0, "name": "SimpleGain", "type": "midi_effect"}]}
          ]
        }
    """
    sess = _ableton_cmd("get_session_info", {})
    if sess.get("status") != "success":
        return {"error": sess.get("message", "get_session_info failed"), "raw": sess}

    result_raw = sess.get("result", {})
    if isinstance(result_raw, str):
        import json as _json
        result_raw = _json.loads(result_raw)

    track_count = int(result_raw.get("track_count", 0))
    tracks = []
    for i in range(track_count):
        ti = _ableton_cmd("get_track_info", {"track_index": i})
        if ti.get("status") != "success":
            tracks.append({"index": i, "error": ti.get("message", "")})
            continue
        traw = ti.get("result", {})
        if isinstance(traw, str):
            import json as _json
            traw = _json.loads(traw)
        devices = [
            {
                "index": d.get("index", j),
                "name": d.get("name", ""),
                "type": d.get("type", ""),
                "class_name": d.get("class_name", ""),
            }
            for j, d in enumerate(traw.get("devices") or [])
        ]
        tracks.append({
            "index": i,
            "name": traw.get("name", f"Track {i}"),
            "is_midi": bool(traw.get("is_midi_track")),
            "clip_slots": len(traw.get("clip_slots") or []),
            "devices": devices,
        })

    sig_num = int(result_raw.get("signature_numerator", 4))
    sig_den = int(result_raw.get("signature_denominator", 4))
    return {
        "tempo": result_raw.get("tempo"),
        "is_playing": result_raw.get("is_playing", False),
        "sig": f"{sig_num}/{sig_den}",
        "track_count": track_count,
        "tracks": tracks,
    }


@mcp.tool()
def live_track_devices(track_index: int) -> dict:
    """Return every device on ``track_index`` with full parameter info.

    Each device entry includes:
    - ``name``, ``type``, ``class_name``, ``device_index``
    - ``params``: list of ``{name, value, min, max}`` via AbletonOSC

    Requires AbletonOSC enabled in Live (UDP 11000/11001).

    Example::

        live_track_devices(2)
        # → {"devices": [{"device_index": 0, "name": "SimpleGain", "params": [
        #       {"name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
        #       {"name": "Gain", "value": 0.0, "min": -70.0, "max": 6.0}]}]}
    """
    ti = _ableton_cmd("get_track_info", {"track_index": int(track_index)})
    if ti.get("status") != "success":
        return {"error": ti.get("message", "get_track_info failed")}
    traw = ti.get("result", {})
    if isinstance(traw, str):
        import json as _json
        traw = _json.loads(traw)
    out_devices = []
    for j, d in enumerate(traw.get("devices") or []):
        dev_idx = d.get("index", j)
        try:
            params = _osc.osc_device_parameter_info(int(track_index), int(dev_idx))
        except Exception as e:
            params = [{"error": str(e)}]
        out_devices.append({
            "device_index": dev_idx,
            "name": d.get("name", ""),
            "type": d.get("type", ""),
            "class_name": d.get("class_name", ""),
            "params": params,
        })
    return {"track_index": track_index, "devices": out_devices}


# ---------------------------------------------------------------------------
# Live state — write (parameters, transport, clips, tracks)
# ---------------------------------------------------------------------------

@mcp.tool()
def live_set_param(
    track_index: int,
    device_index: int,
    param: str | int,
    value: float,
) -> dict:
    """Set a device parameter by name or zero-based index.

    - ``param`` as **str**: matched by exact name first, then case-insensitive substring.
    - ``param`` as **int**: used directly as the parameter index.

    Parameter index 0 is always "Device On" (0.0 = off, 1.0 = on).

    Requires AbletonOSC enabled in Live.

    Example::

        live_set_param(0, 0, "Gain", -12.0)
        live_set_param(0, 0, 0, 1.0)   # Device On
    """
    if isinstance(param, str):
        try:
            names = _osc.osc_device_parameter_names(int(track_index), int(device_index))
        except Exception as e:
            return {"error": f"Could not fetch parameter names: {e}"}
        # Exact match first
        idx = next((i for i, n in enumerate(names) if n == param), None)
        if idx is None:
            # Case-insensitive substring
            pl = param.lower()
            idx = next((i for i, n in enumerate(names) if pl in n.lower()), None)
        if idx is None:
            return {
                "error": f"Parameter {param!r} not found on device {device_index} "
                         f"(track {track_index}). Available: {list(names)}"
            }
        param_index = idx
    else:
        param_index = int(param)

    try:
        _osc.osc_set_device_parameter(
            int(track_index), int(device_index), int(param_index), float(value)
        )
    except Exception as e:
        return {"error": str(e)}
    return {
        "ok": True,
        "track_index": track_index,
        "device_index": device_index,
        "param_index": param_index,
        "value": value,
    }


@mcp.tool()
def live_transport(action: str, bpm: float | None = None) -> dict:
    """Control Live transport.

    ``action`` is one of:

    - ``"play"`` — start playback
    - ``"stop"`` — stop playback
    - ``"set_tempo"`` — set BPM (requires ``bpm`` argument)

    Example::

        live_transport("set_tempo", bpm=140)
        live_transport("play")
        live_transport("stop")
    """
    action = action.strip().lower()
    if action == "play":
        res = _ableton_cmd("start_playback", {})
    elif action == "stop":
        res = _ableton_cmd("stop_playback", {})
    elif action == "set_tempo":
        if bpm is None:
            return {"error": "bpm is required for action='set_tempo'"}
        res = _ableton_cmd("set_tempo", {"tempo": float(bpm)})
    else:
        return {"error": f"Unknown action {action!r}. Use 'play', 'stop', or 'set_tempo'."}
    return {"ok": res.get("status") == "success", "action": action, "bpm": bpm, "raw": res}


@mcp.tool()
def live_create_midi_clip(
    track_index: int,
    clip_slot: int,
    notes: list[dict],
    length_beats: float = 4.0,
) -> dict:
    """Create a MIDI clip on ``track_index`` at ``clip_slot`` and populate it with notes.

    Each note in ``notes`` is a dict::

        {"pitch": 60, "time": 0.0, "duration": 0.5, "velocity": 100}

    - ``pitch``: MIDI note number (0–127)
    - ``time``: start time in beats from clip start
    - ``duration``: note length in beats
    - ``velocity``: note velocity (1–127)

    Example (C-major arpeggio, 1-bar clip)::

        live_create_midi_clip(0, 0, [
            {"pitch": 60, "time": 0.0, "duration": 0.25, "velocity": 100},
            {"pitch": 64, "time": 0.5, "duration": 0.25, "velocity": 90},
            {"pitch": 67, "time": 1.0, "duration": 0.25, "velocity": 80},
        ], length_beats=4.0)
    """
    r1 = _ableton_cmd("create_clip", {
        "track_index": int(track_index),
        "clip_index": int(clip_slot),
        "length": float(length_beats),
    })
    if r1.get("status") != "success":
        return {"error": f"create_clip failed: {r1.get('message', r1)}", "raw": r1}

    r2 = _ableton_cmd("add_notes_to_clip", {
        "track_index": int(track_index),
        "clip_index": int(clip_slot),
        "notes": notes,
    })
    ok = r2.get("status") == "success"
    return {
        "ok": ok,
        "track_index": track_index,
        "clip_slot": clip_slot,
        "note_count": len(notes),
        "length_beats": length_beats,
        "error": None if ok else r2.get("message", str(r2)),
    }


@mcp.tool()
def live_fire_clip(track_index: int, clip_slot: int) -> dict:
    """Launch (fire) a clip slot. Starts Session View playback of that clip.

    Example::

        live_fire_clip(0, 0)
    """
    res = _ableton_cmd("fire_clip", {"track_index": int(track_index), "clip_index": int(clip_slot)})
    return {"ok": res.get("status") == "success", "track_index": track_index, "clip_slot": clip_slot}


@mcp.tool()
def live_stop_clip(track_index: int, clip_slot: int) -> dict:
    """Stop a clip slot.

    Example::

        live_stop_clip(0, 0)
    """
    res = _ableton_cmd("stop_clip", {"track_index": int(track_index), "clip_index": int(clip_slot)})
    return {"ok": res.get("status") == "success", "track_index": track_index, "clip_slot": clip_slot}


@mcp.tool()
def live_delete_track(track_index: int) -> dict:
    """Delete a track by index.

    Uses AbletonOSC ``/live/song/delete_track`` (fire-and-forget).
    After deletion all indices above ``track_index`` shift down by one — use
    ``live_session_state()`` to re-orient.

    Example::

        live_delete_track(3)
    """
    try:
        _osc.osc_delete_track(int(track_index))
    except Exception as e:
        return {"error": str(e)}
    return {"ok": True, "deleted_track_index": track_index}


@mcp.tool()
def live_rename_track(track_index: int, name: str) -> dict:
    """Rename a track.

    Example::

        live_rename_track(0, "Drums")
    """
    res = _ableton_cmd("set_track_name", {"track_index": int(track_index), "name": str(name)})
    return {"ok": res.get("status") == "success", "track_index": track_index, "name": name}


@mcp.tool()
def live_clear_track(track_index: int) -> dict:
    """Remove all devices from a track (leaves the track itself intact).

    Useful for reusing a track across multiple build iterations without
    accumulating ghost devices.

    Example::

        live_clear_track(0)
    """
    res = _ableton_cmd("clear_devices_on_track", {"track_index": int(track_index)})
    return {"ok": res.get("status") == "success", "track_index": track_index}


# ---------------------------------------------------------------------------
# End-to-end pipeline shortcut
# ---------------------------------------------------------------------------

@mcp.tool()
def live_build_and_verify(spec: dict, with_adv: bool = True) -> dict:
    """Build, deploy, load in Live, and verify parameter registration in one call.

    This is the AI-facing equivalent of running::

        python tooling/m4l_pipeline.py all spec.json --with-adv

    Returns a rich result dict so you can immediately inspect what Live sees::

        {
          "ok": true,
          "version": "SimpleGain 1.3",
          "track_index": 4,
          "device_index": 0,
          "params": [{"name": "Gain", "value": 0.0, "min": -70.0, "max": 6.0}],
          "errors": []
        }

    On error ``ok`` is false and ``errors`` describes what went wrong.

    .. note::
       Live must be running with AbletonMCP + AbletonOSC enabled.
       Set ``M4L_PROJECTS_PREFIX=workspace`` before calling to keep builds gitignored.
    """
    import time as _time
    errors: list[str] = []

    try:
        bdl = build_deploy_load(spec, None, skip_live=False, with_adv=with_adv)
    except Exception as e:
        return {"ok": False, "errors": [f"build_deploy_load failed: {e}"], "params": []}

    track_index = bdl.get("track_index")
    if track_index is None:
        return {"ok": False, "errors": ["build_deploy_load did not return a track_index"], "bdl": bdl, "params": []}

    # Get device index from track info
    track_info = bdl.get("track_info") or {}
    devices = track_info.get("devices") or []
    dev_index = devices[-1]["index"] if devices else 0

    # Poll OSC for parameters (devices need a moment to initialize)
    params: list[dict] = []
    name = spec.get("name", "")
    deadline = _time.monotonic() + 30.0
    while _time.monotonic() < deadline:
        try:
            params = _osc.osc_device_parameter_info(int(track_index), int(dev_index))
            # Consider initialized if we have more than just "Device On"
            if len(params) > 1 or not name:
                break
        except Exception as e:
            errors.append(f"OSC poll error: {e}")
            break
        _time.sleep(0.75)

    ok = not errors
    return {
        "ok": ok,
        "version": bdl.get("version", ""),
        "amxd_path": bdl.get("amxd_path", ""),
        "track_index": track_index,
        "device_index": dev_index,
        "params": params,
        "errors": errors,
    }


if __name__ == "__main__":
    mcp.run()
