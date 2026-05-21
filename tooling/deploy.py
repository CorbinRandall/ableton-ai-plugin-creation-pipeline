"""Deploy M4L artifacts to the Ableton User Library."""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from amxd.adv import build_adv
from amxd.binary import _get_reference
from amxd.builder import _resolve_appversion, build_amxd
from paths import (
    allocate_version_directory,
    amxd_filename_for_spec,
    _user_lib_presets,
)

# User Library destinations by device type (lazy — reads ABLETON_HOME per call).
_DEVICE_TYPE_FOLDERS = {
    "midi_effect": ("MIDI Effects", "Max MIDI Effect"),
    "audio_effect": ("Audio Effects", "Max Audio Effect"),
    "instrument": ("Instruments", "Max Instrument"),
}


def _dest_dir(device_type: str) -> Path:
    """User Library folder for one M4L device class (category root, not Imported/)."""
    parts = _DEVICE_TYPE_FOLDERS.get(device_type)
    if parts is None:
        raise ValueError(f"Unknown device_type: {device_type!r}")
    return _user_lib_presets() / parts[0] / parts[1]


def _browser_root(device_type: str) -> str:
    parts = _DEVICE_TYPE_FOLDERS.get(device_type)
    if parts is None:
        raise ValueError(f"Unknown device_type: {device_type!r}")
    return f"user_library/Presets/{parts[0]}/{parts[1]}"


class _LazyDestMap:
    """Backward-compatible ``_DEST_MAP`` that resolves paths lazily."""

    def get(self, key: str, default=None):
        try:
            return _dest_dir(key)
        except ValueError:
            return default

    def __getitem__(self, key: str) -> Path:
        return _dest_dir(key)

    def __contains__(self, key: object) -> bool:
        return key in _DEVICE_TYPE_FOLDERS

    def keys(self):
        return _DEVICE_TYPE_FOLDERS.keys()

    def values(self):
        return (_dest_dir(k) for k in _DEVICE_TYPE_FOLDERS)

    def items(self):
        return ((k, _dest_dir(k)) for k in _DEVICE_TYPE_FOLDERS)


class _LazyBrowserMap:
    def get(self, key: str, default=None):
        try:
            return _browser_root(key)
        except ValueError:
            return default

    def __getitem__(self, key: str) -> str:
        return _browser_root(key)


_DEST_MAP = _LazyDestMap()
_BROWSER_MAP = _LazyBrowserMap()

# Sidecar filename: ``MyDevice.amxd`` → ``MyDevice.device_type`` (one-line text).
_DEVICE_TYPE_SIDECAR_SUFFIX = ".device_type"

_VALID_DEVICE_TYPES = frozenset(_DEVICE_TYPE_FOLDERS.keys())


def sidecar_path_for_artifact(artifact_path: Path) -> Path:
    """``foo.amxd`` → ``foo.device_type``."""
    return artifact_path.with_name(artifact_path.stem + _DEVICE_TYPE_SIDECAR_SUFFIX)


def write_device_type_sidecar(artifact_path: Path, device_type: str) -> Path:
    if device_type not in _VALID_DEVICE_TYPES:
        raise ValueError(f"Unknown device_type: {device_type!r}")
    sidecar = sidecar_path_for_artifact(artifact_path)
    sidecar.write_text(device_type + "\n", encoding="utf-8")
    return sidecar


def read_device_type_sidecar(artifact_path: Path) -> str | None:
    sidecar = sidecar_path_for_artifact(artifact_path)
    if not sidecar.is_file():
        return None
    text = sidecar.read_text(encoding="utf-8").strip()
    return text or None


def assert_device_type_sidecar(artifact_path: Path, expected: str) -> None:
    """Raise ``ValueError`` when a sidecar exists and disagrees with ``expected``."""
    found = read_device_type_sidecar(artifact_path)
    if found is None:
        return
    if found != expected:
        raise ValueError(
            f"device_type sidecar mismatch for {artifact_path.name}: "
            f"sidecar={found!r}, expected={expected!r}. "
            "Deploy/load using the matching User Library category "
            "(see docs/TROUBLESHOOTING_M4L.md)."
        )


def deploy_artifact_for_device_type(
    artifact_path: Path,
    device_type: str,
    *,
    imported: bool = True,
) -> list[Path]:
    """Copy one artifact into the User Library tree for a single ``device_type``.

    Default destination is ``…/Imported/`` (MCP/browser load path). Never copies into
    multiple device-class folders — that mismatch causes Max ``CreateDevice`` error 6.
    """
    artifact_path = Path(artifact_path)
    if not artifact_path.is_file():
        raise FileNotFoundError(artifact_path)
    if device_type not in _VALID_DEVICE_TYPES:
        raise ValueError(f"Unknown device_type: {device_type!r}")

    assert_device_type_sidecar(artifact_path, device_type)

    import m4l_pipeline

    dest_root = m4l_pipeline._dest_dir(device_type)
    destinations: list[Path] = []
    if imported:
        dest_dir = dest_root / "Imported"
    else:
        dest_dir = dest_root
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / artifact_path.name
    shutil.copy2(artifact_path, dest)
    print(f"Deployed → {dest}")
    destinations.append(dest)

    sidecar = sidecar_path_for_artifact(artifact_path)
    if sidecar.is_file():
        sidecar_dest = dest_dir / sidecar.name
        shutil.copy2(sidecar, sidecar_dest)

    return destinations


def deploy_amxd(
    amxd_path: Path,
    device_type: str = "midi_effect",
    *,
    imported: bool = True,
) -> Path:
    """Copy .amxd to the User Library (default: ``Imported/``)."""
    dests = deploy_artifact_for_device_type(amxd_path, device_type, imported=imported)
    return dests[0]


def deploy_adv(
    adv_path: Path,
    device_type: str = "midi_effect",
    *,
    imported: bool = True,
) -> Path:
    """Copy .adv to the User Library (default: ``Imported/``)."""
    dests = deploy_artifact_for_device_type(adv_path, device_type, imported=imported)
    return dests[0]


def build_deploy_load(
    spec: dict,
    track_index: int | None = None,
    *,
    skip_live: bool = False,
    skip_validate: bool = False,
    with_adv: bool = False,
    bump_major: bool = False,
) -> dict:
    """Build into ``projects/<slug>/{name X.Y}/``, deploy to Imported/, load in Live.

    When ``track_index`` is None, appends a **new** Live track and loads there:
    MIDI track for ``midi_effect`` / ``instrument``, audio track for ``audio_effect``.

    Stock AbletonMCP loads via browser URI (see ``load_browser_item_by_browser_path``).
    Audio-track creation uses a **bootstrap patch** to AbletonMCP (see ``install_remote_scripts.py``).
    """
    from live.mcp_client import _ableton_cmd
    from live.browser import _wait_load_browser_imported
    from live.tracks import (
        _create_new_track_for_device_type,
        assert_loaded_device_matches_spec,
        get_track_info,
    )

    device_type = spec.get("device_type", "midi_effect")
    name = spec.get("name", "Untitled")

    vdir, ver = allocate_version_directory(spec, bump_major=bump_major)
    amxd_file = amxd_filename_for_spec(name)
    built = vdir / amxd_file
    build_amxd(spec, built, skip_validate=skip_validate)

    donor_av = "unknown"
    try:
        _h, _s, donor_patch, _t = _get_reference(device_type)
        donor_av = str(_resolve_appversion(donor_patch).get("major", "?"))
    except Exception:
        pass

    version_lines = [
        ver,
        f"donor_appversion_major: {donor_av}",
        f"built_at: {datetime.now(timezone.utc).isoformat()}",
    ]
    (vdir / "spec.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (vdir / "VERSION.txt").write_text("\n".join(version_lines) + "\n", encoding="utf-8")
    print(f"Versioned build → {built} ({ver})")

    deployed = deploy_artifact_for_device_type(built, device_type, imported=True)
    amxd_deploy = deployed[0]

    build_adv_flag = with_adv or os.environ.get("M4L_BUILD_ADV") == "1"
    if build_adv_flag:
        adv_built = vdir / f"{name}.adv"
        build_adv(spec, amxd_deploy, adv_built)
        write_device_type_sidecar(adv_built, device_type)
        deploy_artifact_for_device_type(adv_built, device_type, imported=True)

    result: dict = {
        "version": ver,
        "version_dir": str(vdir),
        "amxd_built": str(built),
        "amxd_path": str(amxd_deploy),
    }

    if skip_live or os.environ.get("M4L_SKIP_LIVE") == "1":
        result["load_result"] = {"status": "skipped", "message": "skip_live or M4L_SKIP_LIVE"}
        return result

    track_kind: str | None = None
    if track_index is None:
        track_index, track_kind = _create_new_track_for_device_type(device_type)
        # Friendly: rename so the device row is easy to find in Session View
        short = name[:40] + ("…" if len(name) > 40 else "")
        tag = "audio" if track_kind == "audio" else "midi"
        _ableton_cmd(
            "set_track_name",
            {"track_index": track_index, "name": f"M4L [{tag}] {short} {ver}"},
        )
        print(f"Using new {track_kind.upper()} track index {track_index}")
    else:
        print(f"Using track index {track_index}")

    stem = amxd_deploy.stem
    load_result = _wait_load_browser_imported(track_index, stem, device_type)
    print(f"Load result: {json.dumps(load_result, indent=2)}")

    track_info = get_track_info(track_index)
    devices = track_info.get("devices", [])
    print(f"Track {track_index} devices after load: {[d.get('name') for d in devices]}")
    assert_loaded_device_matches_spec(device_type, track_info, track_kind=track_kind)

    # Note: stock AbletonMCP selects the target track before load; the device appears on that track.
    result["track_index"] = track_index
    if track_kind is not None:
        result["track_kind"] = track_kind
    result["load_result"] = load_result
    result["track_info"] = track_info
    return result
