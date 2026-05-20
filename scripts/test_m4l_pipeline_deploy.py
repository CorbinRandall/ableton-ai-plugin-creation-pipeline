#!/usr/bin/env python3
"""Offline tests for deploy safety, appversion preservation, patch round-trip."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLING = REPO_ROOT / "tooling"
SCRIPTS = REPO_ROOT / "scripts"
if str(TOOLING) not in sys.path:
    sys.path.insert(0, str(TOOLING))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import m4l_pipeline as mp  # noqa: E402
from spec_validate import validate_structure  # noqa: E402


def _fake_dest_dirs(root: Path):
    def _dest_dir(device_type: str) -> Path:
        if device_type == "midi_effect":
            return root / "MIDI Effects/Max MIDI Effect"
        if device_type == "audio_effect":
            return root / "Audio Effects/Max Audio Effect"
        if device_type == "instrument":
            return root / "Instruments/Max Instrument"
        raise ValueError(device_type)

    return _dest_dir


class DeploySafetyTests(unittest.TestCase):
    def test_midi_deploy_only_imported_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = _fake_dest_dirs(root)
            amxd = root / "Dev.amxd"
            amxd.write_bytes(b"fake")
            mp.write_device_type_sidecar(amxd, "midi_effect")

            with patch.object(mp, "_dest_dir", fake):
                dests = mp.deploy_artifact_for_device_type(amxd, "midi_effect")

            self.assertEqual(len(dests), 1)
            self.assertIn("Imported", str(dests[0]))
            self.assertFalse((root / "Audio Effects").exists())
            self.assertFalse((root / "Instruments").exists())

    def test_sidecar_mismatch_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = _fake_dest_dirs(root)
            amxd = root / "Dev.amxd"
            amxd.write_bytes(b"fake")
            mp.write_device_type_sidecar(amxd, "audio_effect")

            with patch.object(mp, "_dest_dir", fake):
                with self.assertRaises(ValueError):
                    mp.deploy_artifact_for_device_type(amxd, "midi_effect")

    def test_adv_deploy_respects_device_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = _fake_dest_dirs(root)
            adv = root / "Dev.adv"
            adv.write_bytes(b"fake-adv")
            mp.write_device_type_sidecar(adv, "midi_effect")

            with patch.object(mp, "_dest_dir", fake):
                mp.deploy_artifact_for_device_type(adv, "midi_effect")

            self.assertTrue(
                (root / "MIDI Effects/Max MIDI Effect/Imported/Dev.adv").is_file()
            )
            self.assertFalse((root / "Audio Effects").exists())


class BuildMetadataTests(unittest.TestCase):
    def test_build_preserves_donor_appversion(self) -> None:
        spec_path = REPO_ROOT / "projects/Pipeline_Example/pipeline_example_spec.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        _h, _s, donor_patch, _t = mp._get_reference("midi_effect")
        expected = mp._resolve_appversion(donor_patch)

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "Test.amxd"
            mp.build_amxd(spec, out, skip_validate=True)
            _h2, _s2, patcher, _t2 = mp._extract_amxd_parts(out.read_bytes())
            self.assertEqual(patcher.get("appversion"), expected)
            self.assertIsNotNone(patcher.get("classnamespace"))
            self.assertIsNotNone(patcher.get("fileversion"))
            self.assertEqual(mp.read_device_type_sidecar(out), "midi_effect")

    def test_patch_preserves_appversion_on_compact_build(self) -> None:
        spec_path = REPO_ROOT / "projects/Pipeline_Example/pipeline_example_spec.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "Test.amxd"
            mp.build_amxd(spec, src, skip_validate=True)
            _h, _s, root_before, _trail = mp._extract_amxd_parts(src.read_bytes())
            av_before = root_before.get("appversion")

            out = mp.patch_amxd_field(src, bgcolor=[0.0, 0.0, 0.0, 1.0])
            after = out.read_bytes()
            _h2, _s2, patcher_after, _trail2 = mp._extract_amxd_parts(after)

            self.assertEqual(patcher_after.get("appversion"), av_before)
            self.assertEqual(patcher_after.get("bgcolor"), [0.0, 0.0, 0.0, 1.0])
            self.assertTrue(mp._amxd_json_starts_at_32(after))

    def test_patch_raises_when_legacy_json_grows_without_dlst_rebuild(self) -> None:
        legacy = REPO_ROOT / "tooling/donors/instrument.amxd"
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "Legacy.amxd"
            shutil.copy2(legacy, src)
            with self.assertRaises(ValueError):
                mp.patch_amxd_field(src, bgcolor=[0.0, 0.0, 0.0, 1.0])


class SpecValidateTests(unittest.TestCase):
    def test_missing_io_is_error_when_device_type_explicit(self) -> None:
        spec = json.loads(
            (REPO_ROOT / "tests/specs/midi_effect_missing_io.json").read_text(encoding="utf-8")
        )
        errors, warnings = validate_structure(spec)
        self.assertTrue(any("no typical input" in e for e in errors))
        self.assertFalse(any("no typical input" in w for w in warnings))


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
