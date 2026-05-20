"""Load devices from the Ableton browser via AbletonMCP."""

from __future__ import annotations

import json
import time
from pathlib import Path

from deploy import _browser_root, _dest_dir, assert_device_type_sidecar
from live.mcp_client import _ableton_cmd, _coerce_dict, _normalize_browser_leaf


def load_browser_item_by_browser_path(track_index: int, path: str) -> dict:
    """Load from a slash-separated browser path (e.g. user_library/.../Imported/Device).

    Tries ``load_browser_item_at_path`` (some forks); falls back to ``get_browser_items_at_path``
    + ``load_browser_item`` with URI (stock ahujasid/ableton-mcp).
    """
    path = path.strip().strip("/")
    parts = path.split("/")
    if len(parts) < 2:
        return {"status": "error", "message": f"invalid browser path: {path!r}"}
    leaf = parts[-1]
    parent = "/".join(parts[:-1])

    low_leaf = leaf.lower()
    path_attempts: list[str] = []
    if low_leaf.endswith(".adv") or low_leaf.endswith(".amxd"):
        path_attempts.append(path)
    else:
        # Prefer sibling .adv (Ableton preset wrapping the .amxd) so automation/OSC see parameters.
        path_attempts.append(f"{parent}/{leaf}.adv")
        path_attempts.append(f"{parent}/{leaf}.amxd")
        path_attempts.append(path)

    last_at: dict = {}
    for trial_path in path_attempts:
        last_at = _ableton_cmd(
            "load_browser_item_at_path",
            {"track_index": track_index, "path": trial_path},
        )
        if last_at.get("status") == "success":
            res = _coerce_dict(last_at.get("result"))
            if res.get("loaded", True):
                return last_at
    msg = str(last_at.get("message", ""))
    if msg and "unknown command" not in msg.lower():
        return last_at

    browse = _ableton_cmd("get_browser_items_at_path", {"path": parent})
    if browse.get("status") != "success":
        return browse
    items = _coerce_dict(browse.get("result"))
    item_list = items.get("items", [])
    leaf_key = _normalize_browser_leaf(leaf).lower()
    uri = None
    for it in item_list:
        raw = it.get("name") or ""
        if _normalize_browser_leaf(raw).lower() == leaf_key or raw.lower() == leaf.lower():
            uri = it.get("uri")
            break
    if not uri:
        names = [i.get("name") for i in item_list]
        return {"status": "error", "message": f"{leaf!r} not under {parent!r}; items={names}"}

    loaded = _ableton_cmd("load_browser_item", {"track_index": track_index, "item_uri": uri})
    if loaded.get("status") == "success":
        return loaded
    return loaded


def load_device(
    track_index: int,
    device_name: str,
    device_type: str = "midi_effect",
) -> dict:
    """Load a device from User Library → Imported/ onto a track (stem matches ``device_name``)."""
    browser_root = _browser_root(device_type)
    path = f"{browser_root}/Imported/{device_name}"
    imported_amxd = _dest_dir(device_type) / "Imported" / f"{device_name}.amxd"
    if imported_amxd.is_file():
        assert_device_type_sidecar(imported_amxd, device_type)
    result = load_browser_item_by_browser_path(track_index, path)
    print(f"Load result: {json.dumps(result, indent=2)}")
    return result


def _wait_load_browser_imported(
    track_index: int,
    stem: str,
    device_type: str,
    *,
    max_retries: int = 24,
    retry_sleep_s: float = 1.25,
) -> dict:
    """Try loading ``stem`` from Imported/ repeatedly (browser indexing is asynchronous).

    Earlier logic required an exact string match in ``get_browser_items_at_path``, but Live often
    lists devices as ``Foo.amxd`` while callers pass ``Foo`` — so we never loaded. We always call
    the loader (which normalizes ``.amxd``) and back off until success or max retries.
    """
    browser_root = _browser_root(device_type)
    parent_path = f"{browser_root}/Imported"
    load_path = f"{parent_path}/{stem}"

    imported_amxd = _dest_dir(device_type) / "Imported" / f"{stem}.amxd"
    if imported_amxd.is_file():
        assert_device_type_sidecar(imported_amxd, device_type)

    last: dict = {"status": "error", "message": "no load attempts"}
    for attempt in range(max_retries):
        last = load_browser_item_by_browser_path(track_index, load_path)
        if last.get("status") == "success":
            inner = _coerce_dict(last.get("result"))
            if inner.get("loaded", True):
                return last

        hint = ""
        br = _ableton_cmd("get_browser_items_at_path", {"path": parent_path})
        if br.get("status") == "success":
            items = _coerce_dict(br.get("result"))
            norms = [_normalize_browser_leaf(i.get("name", "")) for i in items.get("items", [])]
            want = _normalize_browser_leaf(stem).lower()
            similar = [s for s in norms if want and want in s.lower()]
            hint = (
                f" (stems containing {want!r}: {similar[:8]})"
                if similar
                else f" (Imported count={len(norms)})"
            )
            if want in [s.lower() for s in norms]:
                hint += " [listed in browser — retrying load]"
        else:
            hint = f" (browse failed: {br.get('message', br)})"

        if attempt < max_retries - 1:
            print(f"  Load retry {attempt + 1}/{max_retries} '{stem}'…{hint}")
            time.sleep(retry_sleep_s)

    return last


def load_imported_device_new_track(
    device_stem: str,
    device_type: str = "midi_effect",
    *,
    skip_live: bool = False,
    track_display_name: str | None = None,
) -> dict:
    """Create a new Live track, then load ``device_stem`` from Imported/ (browser must list it).

    ``device_stem`` is the .amxd filename without extension (e.g. ``MyDevice_v1_3``).
    """
    import os

    from live.tracks import (
        _create_new_track_for_device_type,
        assert_loaded_device_matches_spec,
        get_track_info,
    )

    result: dict[str, object] = {"device_stem": device_stem}
    if skip_live or os.environ.get("M4L_SKIP_LIVE") == "1":
        result["load_result"] = {"status": "skipped", "message": "skip_live or M4L_SKIP_LIVE"}
        return result

    track_index, track_kind = _create_new_track_for_device_type(device_type)
    result["track_index"] = track_index
    result["track_kind"] = track_kind

    name = track_display_name or f"M4L [{track_kind}] {device_stem}"
    _ableton_cmd("set_track_name", {"track_index": track_index, "name": name})
    print(f"Using new {track_kind.upper()} track index {track_index}")

    load_result = _wait_load_browser_imported(track_index, device_stem, device_type)
    print(f"Load result: {json.dumps(load_result, indent=2)}")
    result["load_result"] = load_result

    track_info = get_track_info(track_index)
    devices = track_info.get("devices", [])
    print(f"Track {track_index} devices after load: {[d.get('name') for d in devices]}")
    assert_loaded_device_matches_spec(device_type, track_info, track_kind=track_kind)
    result["track_info"] = track_info
    return result
