"""Ableton Live integration via AbletonMCP and AbletonOSC."""

from live.browser import (
    _wait_load_browser_imported,
    load_browser_item_by_browser_path,
    load_device,
    load_imported_device_new_track,
)
from live.mcp_client import _ableton_cmd, _coerce_dict, _normalize_browser_leaf
from live.tracks import (
    _create_audio_track_index,
    _create_midi_track_index,
    _create_new_track_for_device_type,
    _get_osc_client,
    assert_loaded_device_matches_spec,
    get_session_info,
    get_track_info,
    set_tempo,
    set_tempo_osc,
)

__all__ = [
    "_ableton_cmd",
    "_coerce_dict",
    "_create_audio_track_index",
    "_create_midi_track_index",
    "_create_new_track_for_device_type",
    "_get_osc_client",
    "_normalize_browser_leaf",
    "_wait_load_browser_imported",
    "assert_loaded_device_matches_spec",
    "get_session_info",
    "get_track_info",
    "load_browser_item_by_browser_path",
    "load_device",
    "load_imported_device_new_track",
    "set_tempo",
    "set_tempo_osc",
]
