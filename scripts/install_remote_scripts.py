#!/usr/bin/env python3
"""
Install AbletonOSC + AbletonMCP into Ableton User Library → Remote Scripts (no admin).

Per AbletonOSC upstream and Ableton KB, Live 10.1.13+ loads third‑party MIDI Remote
Scripts from:

  macOS/Linux: $ABLETON_HOME/User Library/Remote Scripts
  Windows: %USERPROFILE%\\Documents\\Ableton\\User Library\\Remote Scripts

After install you must quit Live completely, reopen, then assign Control Surfaces
in Preferences → Link / Tempo / MIDI (preferences file is opaque binary — see
configure_ableton.py for Options.txt hooks only).

The installer patches AbletonMCP to add TCP ``create_audio_track`` (upstream only had MIDI).
That lets ``tooling/m4l_pipeline.py`` open Max Audio devices on a **new audio track**.

Env:
  BOOTSTRAP_ABLETON_OSC_ARCHIVE   Override archive URL (default: master ZIP)
  BOOTSTRAP_ABLETON_MCP_ARCHIVE   Override archive URL (default: main ZIP)
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import ableton_bootstrap_common as abc


def _github_single_root(work: Path) -> Path:
    subs = [p for p in work.iterdir() if p.is_dir()]
    if len(subs) != 1:
        raise RuntimeError(f"Archive must contain exactly one root folder (got {[p.name for p in subs]})")
    return subs[0]


def install_abletonosc(base_dir: Path, zip_path_cache: Path, url: str) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    target = base_dir / "AbletonOSC"
    if zip_path_cache.is_file():
        print(f"AbletonOSC: using cached {zip_path_cache}")
    else:
        print(f"AbletonOSC: downloading → {zip_path_cache}")
        abc.download_zip_archive(url, zip_path_cache)

    if target.exists():
        shutil.rmtree(target)

    with tempfile.TemporaryDirectory(prefix="inst_osc_") as td:
        work = Path(td)
        with zipfile.ZipFile(zip_path_cache) as zf:
            zf.extractall(work)
        root = _github_single_root(work)
        shutil.move(str(root), str(target))
    return target


def install_abletonmcp(base_dir: Path, zip_path_cache: Path, url: str) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    target = base_dir / "AbletonMCP"
    if zip_path_cache.is_file():
        print(f"AbletonMCP: using cached {zip_path_cache}")
    else:
        print(f"AbletonMCP: downloading → {zip_path_cache}")
        abc.download_zip_archive(url, zip_path_cache)

    if target.exists():
        shutil.rmtree(target)

    with tempfile.TemporaryDirectory(prefix="inst_mcp_") as td:
        work = Path(td)
        with zipfile.ZipFile(zip_path_cache) as zf:
            zf.extractall(work)
        root = _github_single_root(work)
        src = root / "AbletonMCP_Remote_Script"
        if not src.is_dir():
            raise RuntimeError(
                f"No AbletonMCP_Remote_Script inside {root.name}; "
                "upstream layout may have changed — open an issue on ableton-plugin-pipeline."
            )
        shutil.move(str(src), str(target))
    return target


def patch_abletonmcp_create_audio_track(abletonmcp_dir: Path) -> bool:
    """Add TCP command ``create_audio_track`` (upstream ahujasid/ableton-mcp only had MIDI).

    ``tooling/m4l_pipeline.build_deploy_load`` creates an **audio** track for
    ``device_type == \"audio_effect\"``. Without this patch, that step falls back
    to a MIDI track and loads may be unreliable.

    Idempotent. Raises RuntimeError if the file layout is unrecognized (upstream drift).
    """
    init_py = abletonmcp_dir / "__init__.py"
    if not init_py.is_file():
        return False
    text = init_py.read_text(encoding="utf-8")
    if "def _create_audio_track" in text:
        return False

    old_tuple = 'elif command_type in ["create_midi_track", "set_track_name",'
    new_tuple = 'elif command_type in ["create_audio_track", "create_midi_track", "set_track_name",'
    if old_tuple not in text:
        raise RuntimeError(
            "AbletonMCP __init__.py: expected command tuple not found — upstream layout changed."
        )
    text = text.replace(old_tuple, new_tuple, 1)

    old_branch = (
        '                        if command_type == "create_midi_track":\n'
        '                            index = params.get("index", -1)\n'
        '                            result = self._create_midi_track(index)\n'
    )
    new_branch = (
        '                        if command_type == "create_audio_track":\n'
        '                            index = params.get("index", -1)\n'
        '                            result = self._create_audio_track(index)\n'
        '                        elif command_type == "create_midi_track":\n'
        '                            index = params.get("index", -1)\n'
        '                            result = self._create_midi_track(index)\n'
    )
    if old_branch not in text:
        raise RuntimeError(
            "AbletonMCP __init__.py: create_midi_track branch not found — upstream layout changed."
        )
    text = text.replace(old_branch, new_branch, 1)

    old_gap = (
        '            raise\n'
        '    \n'
        '    \n'
        '    def _set_track_name(self, track_index, name):'
    )
    new_gap = (
        '            raise\n'
        '    \n'
        '    def _create_audio_track(self, index):\n'
        '        """Create a new audio track (ableton-plugin-pipeline bootstrap patch)."""\n'
        '        try:\n'
        '            self._song.create_audio_track(index)\n'
        '            new_track_index = len(self._song.tracks) - 1 if index == -1 else index\n'
        '            new_track = self._song.tracks[new_track_index]\n'
        '            result = {\n'
        '                "index": new_track_index,\n'
        '                "name": new_track.name\n'
        '            }\n'
        '            return result\n'
        '        except Exception as e:\n'
        '            self.log_message("Error creating audio track: " + str(e))\n'
        '            raise\n'
        '    \n'
        '    \n'
        '    def _set_track_name(self, track_index, name):'
    )
    if old_gap not in text:
        raise RuntimeError(
            "AbletonMCP __init__.py: could not find insertion point after "
            "_create_midi_track — upstream layout changed."
        )
    text = text.replace(old_gap, new_gap, 1)

    init_py.write_text(text, encoding="utf-8")
    return True


def patch_abletonmcp_user_library_uri_lookup(abletonmcp_dir: Path) -> bool:
    """Include ``user_library`` in ``_find_browser_item_by_uri`` (stock MCP missed Imported/*.amxd)."""
    init_py = abletonmcp_dir / "__init__.py"
    if not init_py.is_file():
        return False
    text = init_py.read_text(encoding="utf-8")
    if "categories.append(browser_or_item.user_library)" in text:
        return False
    old = """                categories = [
                    browser_or_item.instruments,
                    browser_or_item.sounds,
                    browser_or_item.drums,
                    browser_or_item.audio_effects,
                    browser_or_item.midi_effects
                ]
                
                for category in categories:"""
    new = """                categories = [
                    browser_or_item.instruments,
                    browser_or_item.sounds,
                    browser_or_item.drums,
                    browser_or_item.audio_effects,
                    browser_or_item.midi_effects,
                ]
                if hasattr(browser_or_item, "user_library") and browser_or_item.user_library:
                    categories.append(browser_or_item.user_library)

                for category in categories:"""
    if old not in text:
        raise RuntimeError(
            "AbletonMCP __init__.py: _find_browser_item_by_uri categories block not found."
        )
    init_py.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache-dir", type=Path, default=abc.repo_root() / ".bootstrap_cache")
    ap.add_argument("--dry-run", action="store_true", help="Print paths only; do not download or write")
    ap.add_argument(
        "--skip-osc",
        action="store_true",
        help="Do not install AbletonOSC (useful when you vendor it elsewhere).",
    )
    ap.add_argument(
        "--skip-mcp",
        action="store_true",
        help="Do not install AbletonMCP.",
    )
    ap.add_argument(
        "--patch-mcp-only",
        action="store_true",
        help="Only apply MCP patches to existing Remote Scripts/AbletonMCP (no downloads).",
    )
    args = ap.parse_args()

    dest = abc.user_library_remote_scripts()
    print(f"Ableton home:              {abc.ableton_home()}")
    print(f"Remote Scripts target:      {dest}")

    if args.patch_mcp_only:
        mcp = dest / "AbletonMCP"
        if not mcp.is_dir():
            print(f"ERROR: {mcp} not found — install AbletonMCP first.", file=sys.stderr)
            return 1
        try:
            audio = patch_abletonmcp_create_audio_track(mcp)
            user_lib = patch_abletonmcp_user_library_uri_lookup(mcp)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        if audio:
            print("Patched AbletonMCP: added create_audio_track.")
        if user_lib:
            print("Patched AbletonMCP: user_library URI lookup for Imported/*.amxd.")
        if not audio and not user_lib:
            print("AbletonMCP patches already applied (no file changes).")
        print("Quit Live completely and reopen so the remote script reloads.")
        return 0

    bundles = abc.find_installed_live_app_bundles()
    if bundles:
        print("Detected Ableton bundles:   " + ", ".join(b.name for b in bundles[:4]))
        if len(bundles) > 4:
            print(f"                             … +{len(bundles) - 4} more")

    osc_url = os.environ.get("BOOTSTRAP_ABLETON_OSC_ARCHIVE", abc.DEFAULT_ABLETON_OSC_ARCHIVE)
    mcp_url = os.environ.get("BOOTSTRAP_ABLETON_MCP_ARCHIVE", abc.DEFAULT_ABLETON_MCP_ARCHIVE)
    osc_zip = args.cache_dir / "abletonosc-archive.zip"
    mcp_zip = args.cache_dir / "abletonmcp-archive.zip"

    if args.dry_run:
        print("(dry-run) would install from:")
        print("  AbletonOSC →", osc_url)
        print("  AbletonMCP →", mcp_url)
        return 0

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    dest.mkdir(parents=True, exist_ok=True)

    if not args.skip_osc:
        p = install_abletonosc(dest, osc_zip, osc_url)
        print(f"Installed AbletonOSC → {p}")

    if not args.skip_mcp:
        p = install_abletonmcp(dest, mcp_zip, mcp_url)
        print(f"Installed AbletonMCP → {p}")
        try:
            if patch_abletonmcp_create_audio_track(p):
                print(
                    "AbletonMCP: applied create_audio_track patch "
                    "(needed for Max Audio Effect → new audio track)."
                )
            if patch_abletonmcp_user_library_uri_lookup(p):
                print(
                    "AbletonMCP: applied user_library URI patch "
                    "(needed to load User Library → Imported/*.amxd)."
                )
        except RuntimeError as exc:
            print(f"WARN: AbletonMCP patch skipped: {exc}")

    print(
        "\nNext: Quit Live completely, reopen Live, then Preferences → Link / Tempo / MIDI →"
        '\n Control Surface → pick "AbletonOSC" (and optionally "AbletonMCP"; input/output = blank).'
    )
    print("Remote script ports: MCP TCP 9877; OSC UDP 11000→11001 (see docs/SETUP_AUTOMATED.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
