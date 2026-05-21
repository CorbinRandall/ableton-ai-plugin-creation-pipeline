#!/usr/bin/env python3
"""Unit tests for plugin folder versioning (patch vs major bump)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tooling"))

from paths import (  # noqa: E402
    VERSION_BUMP_MAJOR,
    VERSION_BUMP_PATCH,
    _parse_existing_versions,
    compute_next_version,
    next_plugin_version,
    parse_version_label,
    resolve_version_bump,
)


class TestComputeNextVersion(unittest.TestCase):
    def test_empty_patch(self) -> None:
        self.assertEqual(compute_next_version([]), "1.1")

    def test_patch_increments_minor(self) -> None:
        self.assertEqual(compute_next_version([(1, 1)]), "1.2")
        self.assertEqual(compute_next_version([(1, 9)]), "1.10")
        self.assertEqual(compute_next_version([(1, 27), (1, 3)]), "1.28")

    def test_major_starts_new_line(self) -> None:
        self.assertEqual(compute_next_version([(1, 27)], VERSION_BUMP_MAJOR), "2.1")
        self.assertEqual(compute_next_version([(2, 5)], VERSION_BUMP_MAJOR), "3.1")

    def test_major_ignores_higher_minor_on_old_line(self) -> None:
        self.assertEqual(
            compute_next_version([(1, 99), (2, 1)], VERSION_BUMP_MAJOR),
            "3.1",
        )


class TestNextPluginVersion(unittest.TestCase):
    def test_reads_version_folders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "projects"
            slug = base / "VolumeKnob"
            slug.mkdir(parents=True)
            (slug / "VolumeKnob 1.3").mkdir()
            (slug / "VolumeKnob 1.7").mkdir()
            with mock.patch("paths.plugin_projects_base", return_value=base):
                self.assertEqual(next_plugin_version("VolumeKnob"), "1.8")

    def test_bump_major_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "projects"
            slug = base / "Gain"
            slug.mkdir(parents=True)
            (slug / "Gain 1.4").mkdir()
            with mock.patch("paths.plugin_projects_base", return_value=base):
                self.assertEqual(next_plugin_version("Gain", bump_major=True), "2.1")

    def test_env_major_bump(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "projects"
            slug = base / "Gain"
            slug.mkdir(parents=True)
            (slug / "Gain 1.1").mkdir()
            with mock.patch("paths.plugin_projects_base", return_value=base):
                with mock.patch.dict(os.environ, {"M4L_VERSION_BUMP": "major"}):
                    self.assertEqual(next_plugin_version("Gain"), "2.1")


class TestResolveVersionBump(unittest.TestCase):
    def test_default_patch(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("M4L_VERSION_BUMP", None)
            self.assertEqual(resolve_version_bump(), VERSION_BUMP_PATCH)

    def test_bump_major_wins(self) -> None:
        self.assertEqual(
            resolve_version_bump(VERSION_BUMP_PATCH, bump_major=True),
            VERSION_BUMP_MAJOR,
        )


class TestParseVersionLabel(unittest.TestCase):
    def test_round_trip(self) -> None:
        self.assertEqual(parse_version_label("1.28"), (1, 28))


class TestParseExistingVersions(unittest.TestCase):
    def test_ignores_non_matching_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MyPlugin 1.2").mkdir()
            (root / "MyPlugin 2").mkdir()
            (root / "MyPlugin vFinal").mkdir()
            found = _parse_existing_versions(root, "MyPlugin")
            self.assertEqual(found, [(1, 2)])


if __name__ == "__main__":
    unittest.main()
