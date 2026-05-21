#!/usr/bin/env python3
"""
M4L Pipeline — Build, deploy, and load Max for Live devices programmatically.

Versioning: each ``build_deploy_load`` run creates ``{plugin_projects_base()}/<slug>/{name X.Y}/`` with
``spec.json``, ``VERSION.txt``, and the ``.amxd``. Default bump is **patch** (``1.1`` → ``1.2`` → ``1.3``).
Use ``--bump-major`` or ``M4L_VERSION_BUMP=major`` only when starting a new major line (``2.1``). See
``docs/VERSIONING.md``. With **M4L_PROJECTS_PREFIX=workspace**, builds land under
``projects/workspace/<slug>/`` (gitignored).
Then deploys to User Library ``Imported/`` and loads the device in Live on a **new track** (unless you pass an existing **track index**, set **M4L_SKIP_LIVE**, or use **`all --no-live`**). Track type follows ``device_type``: **MIDI** for ``midi_effect`` / ``instrument``, **audio** for ``audio_effect``.

The **`build`** command only writes an ``.amxd`` — it does **not** open Live. Use **`all`** (default: create track + load) or **`deploy`** then **`load`**.

Live does not infer MIDI vs audio from the ``.amxd`` blob alone — classification comes from the spec
(browser folder + device wrapper match ``midi_effect`` | ``audio_effect`` | ``instrument``).

Pipeline: spec dict → versioned .amxd → User Library → AbletonMCP load (URI fallback for stock MCP)

The .amxd includes a dlst (dependency list) so Live can register device parameters.
This means parameters defined via live.numbox/live.toggle with parameter_enable
should appear in Live's device view (automatable, MIDI-mappable).

Building here does **not** require the Max standalone app — but Live must be a Max-for-Live-capable
edition (**Suite**, or **Standard + M4L add-on**) to open these devices (see **`README.md`**, Ableton KB).

Usage:
    python3 m4l_pipeline.py build   spec.json [output.amxd] [--skip-validate]    # .amxd only — no Ableton
    python3 m4l_pipeline.py deploy  path.amxd|.adv [device_type] [--category-root]
    python3 m4l_pipeline.py patch     path.amxd [--bgcolor R,G,B,A] [--in-place] [--deploy device_type]
    python3 m4l_pipeline.py verify    spec.json [--skip-validate]
    python3 m4l_pipeline.py load    track_index device_name [device_type]
    python3 m4l_pipeline.py info    track_index
    python3 m4l_pipeline.py session
    python3 m4l_pipeline.py all     spec.json [track_index|new] [--no-live] [--skip-validate] [--with-adv] [--bump-major]
        # Default: patch version bump (1.1 → 1.2). --bump-major → new line (e.g. 2.1).
        # Omit track or pass ``new`` for a new track; pass ``0`` etc. for an existing track.
        # ``--no-live``: skip MCP (artifacts + deploy only). Env ``M4L_SKIP_LIVE=1`` same effect.
        # ``--with-adv``: build/deploy .adv (preset) alongside .amxd; also copied next to .amxd under Imported/.
        # Env ``M4L_BUILD_ADV=1`` enables .adv from Python callers of ``build_deploy_load``.
        # ``--skip-validate``: skip schema/UI checks (``build`` / ``all``).
"""

from __future__ import annotations

# Ensure tooling/ is on sys.path (spec_validate, paths helpers).
import paths  # noqa: F401

from amxd.adv import build_adv
from amxd.binary import (
    _amxd_json_starts_at_32,
    _decode_amxd_json_at,
    _extract_amxd_parts,
    _get_reference,
    _pack_amxd,
)
from amxd.builder import (
    _APPVERSION,
    _APPVERSION_FALLBACK,
    _apply_live_ui_contrast,
    _ensure_presentation_boxes,
    _resolve_appversion,
    build_amxd,
)
from cli import _cli
from deploy import (
    _BROWSER_MAP,
    _DEST_MAP,
    _DEVICE_TYPE_FOLDERS,
    _DEVICE_TYPE_SIDECAR_SUFFIX,
    _LazyBrowserMap,
    _LazyDestMap,
    _VALID_DEVICE_TYPES,
    _browser_root,
    _dest_dir,
    assert_device_type_sidecar,
    build_deploy_load,
    deploy_adv,
    deploy_amxd,
    deploy_artifact_for_device_type,
    read_device_type_sidecar,
    sidecar_path_for_artifact,
    write_device_type_sidecar,
)
from live.browser import (
    _wait_load_browser_imported,
    load_browser_item_by_browser_path,
    load_device,
    load_imported_device_new_track,
)
from live.mcp_client import _ABLETON_HOST, _ABLETON_PORT, _ableton_cmd, _coerce_dict, _normalize_browser_leaf
from live.tracks import (
    _create_audio_track_index,
    _create_midi_track_index,
    _create_new_track_for_device_type,
    _get_osc_client,
    _osc_client,
    assert_loaded_device_matches_spec,
    get_session_info,
    get_track_info,
    set_tempo,
    set_tempo_osc,
)
from patch import (
    _find_title_comment_box,
    _next_patch_output_path,
    _parse_rgba_csv,
    _patcher_dict_from_amxd_root,
    _repack_amxd_patched,
    patch_amxd_field,
)
from paths import (
    REPO_ROOT,
    WORKSPACE,
    _ableton_home,
    _parse_existing_versions,
    _user_lib_presets,
    allocate_version_directory,
    amxd_filename_for_spec,
    next_plugin_version,
    plugin_projects_base,
    plugin_slug_from_name,
    reference_amxd_path,
)
from verify_offline import _lint_amxd_dlst, verify_spec_offline

__all__ = [
    "REPO_ROOT",
    "WORKSPACE",
    "_ABLETON_HOST",
    "_ABLETON_PORT",
    "_APPVERSION",
    "_APPVERSION_FALLBACK",
    "_BROWSER_MAP",
    "_DEST_MAP",
    "_DEVICE_TYPE_FOLDERS",
    "_DEVICE_TYPE_SIDECAR_SUFFIX",
    "_LazyBrowserMap",
    "_LazyDestMap",
    "_VALID_DEVICE_TYPES",
    "_amxd_json_starts_at_32",
    "_apply_live_ui_contrast",
    "_ableton_cmd",
    "_ableton_home",
    "_browser_root",
    "_coerce_dict",
    "_create_audio_track_index",
    "_create_midi_track_index",
    "_create_new_track_for_device_type",
    "_decode_amxd_json_at",
    "_dest_dir",
    "_ensure_presentation_boxes",
    "_extract_amxd_parts",
    "_find_title_comment_box",
    "_get_osc_client",
    "_get_reference",
    "_lint_amxd_dlst",
    "_next_patch_output_path",
    "_normalize_browser_leaf",
    "_osc_client",
    "_pack_amxd",
    "_parse_existing_versions",
    "_parse_rgba_csv",
    "_patcher_dict_from_amxd_root",
    "_repack_amxd_patched",
    "_resolve_appversion",
    "_user_lib_presets",
    "_wait_load_browser_imported",
    "allocate_version_directory",
    "amxd_filename_for_spec",
    "assert_device_type_sidecar",
    "assert_loaded_device_matches_spec",
    "build_adv",
    "build_amxd",
    "build_deploy_load",
    "deploy_adv",
    "deploy_amxd",
    "deploy_artifact_for_device_type",
    "get_session_info",
    "get_track_info",
    "load_browser_item_by_browser_path",
    "load_device",
    "load_imported_device_new_track",
    "next_plugin_version",
    "patch_amxd_field",
    "plugin_projects_base",
    "plugin_slug_from_name",
    "read_device_type_sidecar",
    "reference_amxd_path",
    "set_tempo",
    "set_tempo_osc",
    "sidecar_path_for_artifact",
    "verify_spec_offline",
    "write_device_type_sidecar",
]

if __name__ == "__main__":
    _cli()
