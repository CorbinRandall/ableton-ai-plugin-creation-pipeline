#!/usr/bin/env python3
"""Unit tests for verification helpers (no Ableton Live required).

Run from repo root:

  ./venv/bin/python scripts/test_verification_helpers.py
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = REPO_ROOT / "scripts"
_TOOLING = REPO_ROOT / "tooling"
for p in (_SCRIPTS, _TOOLING):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from install_remote_scripts import patch_abletonmcp_get_device_health  # noqa: E402
from m4l_pipeline import assert_loaded_device_matches_spec  # noqa: E402


# Minimal AbletonMCP __init__.py fragment: ``get_track_info`` branch matches patch needles exactly.
_MCP_STUB_MINIMAL = '''\
class DummyMCP:
    def log_message(self, m):
        pass

    def _process_command(self, command):
        command_type = command.get("type", "")
        params = command.get("params", {})
        response = {"status": "success", "result": {}}
        try:
            if command_type == "get_session_info":
                response["result"] = {}
            elif command_type == "get_track_info":
                track_index = params.get("track_index", 0)
                response["result"] = self._get_track_info(track_index)
        except Exception:
            pass
        return response

    def _get_track_info(self, track_index):
        try:
            return {}
        except Exception as e:
            self.log_message("Error getting track info: " + str(e))
            raise
    
    def _create_midi_track(self, index):
        return {}
'''

_MCP_STUB_AUDIO_FIRST = '''\
class DummyMCP:
    def log_message(self, m):
        pass

    def _process_command(self, command):
        command_type = command.get("type", "")
        params = command.get("params", {})
        response = {"status": "success", "result": {}}
        try:
            if command_type == "get_session_info":
                response["result"] = {}
            elif command_type == "get_track_info":
                track_index = params.get("track_index", 0)
                response["result"] = self._get_track_info(track_index)
        except Exception:
            pass
        return response

    def _get_track_info(self, track_index):
        try:
            return {}
        except Exception as e:
            self.log_message("Error getting track info: " + str(e))
            raise
    
    def _create_audio_track(self, index):
        return {}

    def _create_midi_track(self, index):
        return {}
'''


class TestAssertLoadedDevice(unittest.TestCase):
    def test_direct_match(self) -> None:
        assert_loaded_device_matches_spec(
            "audio_effect",
            {
                "devices": [
                    {"index": 0, "type": "audio_effect", "class_name": "MxDeviceAudioEffect"},
                ]
            },
            track_kind="audio",
        )

    def test_unknown_heuristic(self) -> None:
        assert_loaded_device_matches_spec(
            "midi_effect",
            {
                "devices": [
                    {"index": 0, "type": "unknown", "class_name": "MxDeviceMidiEffect"},
                ]
            },
            track_kind="midi",
        )

    def test_rack_inner_matches(self) -> None:
        assert_loaded_device_matches_spec(
            "audio_effect",
            {
                "devices": [
                    {"index": 0, "type": "audio_effect", "class_name": "MxDeviceAudioEffect"},
                    {"index": 1, "type": "rack", "class_name": "AudioEffectGroupDevice"},
                ]
            },
            track_kind="audio",
        )

    def test_mismatch_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            assert_loaded_device_matches_spec(
                "audio_effect",
                {
                    "devices": [
                        {"index": 0, "type": "midi_effect", "class_name": "MxDeviceMidiEffect"},
                    ]
                },
                track_kind="audio",
            )


class TestMcpHealthPatch(unittest.TestCase):
    def test_patch_inserts_route_and_handler(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            mcp = Path(td) / "AbletonMCP"
            mcp.mkdir()
            init_py = mcp / "__init__.py"
            init_py.write_text(_MCP_STUB_MINIMAL, encoding="utf-8")
            self.assertTrue(patch_abletonmcp_get_device_health(mcp))
            text = init_py.read_text(encoding="utf-8")
            self.assertIn('elif command_type == "get_device_health":', text)
            self.assertIn("def _get_device_health(self, track_index, device_index):", text)
            self.assertFalse(patch_abletonmcp_get_device_health(mcp))

    def test_patch_audio_track_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            mcp = Path(td) / "AbletonMCP"
            mcp.mkdir()
            init_py = mcp / "__init__.py"
            init_py.write_text(_MCP_STUB_AUDIO_FIRST, encoding="utf-8")
            self.assertTrue(patch_abletonmcp_get_device_health(mcp))
            text = init_py.read_text(encoding="utf-8")
            self.assertIn("def _get_device_health(self, track_index, device_index):", text)
            self.assertLess(text.index("_get_device_health"), text.index("_create_audio_track"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
