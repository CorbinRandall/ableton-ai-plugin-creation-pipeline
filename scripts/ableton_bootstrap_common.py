#!/usr/bin/env python3
"""
Shared paths and helpers for bootstrap / install_remote_scripts / configure scripts.
"""
from __future__ import annotations

import os
import re
import sys
import urllib.request
from pathlib import Path

DEFAULT_ABLETON_OSC_ARCHIVE = (
    "https://github.com/ideoforms/AbletonOSC/archive/refs/heads/master.zip"
)
DEFAULT_ABLETON_MCP_ARCHIVE = (
    "https://github.com/ahujasid/ableton-mcp/archive/refs/heads/main.zip"
)

# Shown after bootstrap / preflight. Sources: Ableton Help + Live manual (edition rules).
MAX_FOR_LIVE_EDITION_NOTICE = """
Max for Live vs your Ableton edition
  Live Suite — Max for Live is included and installs together with Ableton Live. You do not
             download Cycling ’74 Max separately for normal patching (“Edit”, Max editor ships
             as part of this bundle). See Ableton:
             https://help.ableton.com/hc/en-us/articles/360000036850-Max-for-Live-bundled-in-Live
  Live Standard — Max for Live is not included; buy it as an add-on from Ableton:
             https://help.ableton.com/hc/en-us/articles/206407124-Buying-Max-for-Live
  Live Lite / Intro — Max for Live is not available on these editions.
  Optional advanced setup — Install standalone Max from Cycling ’74 only if you want Live to use
             an external Max build (Preferences → File/Folder → path to Max). See:
             https://help.ableton.com/hc/en-us/articles/209070309-Using-a-separate-Max-for-Live-installation

Pipeline note — This repo can build/deploy .amxd files from Python without opening Max.app, but Live
still needs a Max-for-Live–capable edition to load/run those devices in a set.
"""

_MARK_BEGIN = "# === m4l-pipeline-managed begin ==="
_MARK_END = "# === m4l-pipeline-managed end ==="


def repo_root(start: Path | None = None) -> Path:
    return (start or Path(__file__).resolve()).parent.parent


def ableton_home() -> Path:
    if env := os.environ.get("ABLETON_HOME"):
        return Path(env)
    if sys.platform == "win32":
        return Path.home() / "Documents" / "Ableton"
    return Path.home() / "Music" / "Ableton"


def user_library_remote_scripts() -> Path:
    """Third-party MIDI Remote Scripts (Live 10.1.13+) — writable without admin."""

    return ableton_home() / "User Library" / "Remote Scripts"


def ableton_prefs_root() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", Path.home())) / "Ableton"
    return Path.home() / "Library" / "Preferences" / "Ableton"


def live_pref_dirs(version_glob: str = "Live *.*.*") -> list[Path]:
    root = ableton_prefs_root()
    if not root.is_dir():
        return []
    out = sorted(root.glob(version_glob), key=lambda p: p.name, reverse=True)
    return [p for p in out if p.is_dir()]


_LIVE_APP_RE = re.compile(r"^Ableton Live .+\.app$", re.IGNORECASE)


def find_installed_live_app_bundles(applications: Path | None = None) -> list[Path]:
    """Best-effort: macOS Ableton bundles under /Applications."""

    if os.name != "posix" or sys.platform != "darwin":
        return []
    base = applications or Path("/Applications")
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir() if p.is_dir() and _LIVE_APP_RE.match(p.name))


def download_zip_archive(url: str, dest_zip: Path) -> None:
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(  # noqa: S310
        url,
        headers={"User-Agent": "m4l-pipeline-bootstrap/1.0"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        dest_zip.write_bytes(r.read())


def strip_managed_block(text: str) -> tuple[str, str]:
    """Return (outside_managed, managed_inner) where managed_inner excludes markers."""

    if _MARK_BEGIN not in text:
        return text, ""

    head, _, rest = text.partition(_MARK_BEGIN)
    mid, _, tail = rest.partition(_MARK_END)
    inner = mid.strip("\n")
    outer = head + tail
    return outer, inner


def write_options_txt(pref_dir: Path, option_lines: list[str]) -> Path:
    """Merge `option_lines` into Options.txt beneath a guarded block."""

    opts = pref_dir / "Options.txt"
    pref_dir.mkdir(parents=True, exist_ok=True)
    raw = ""
    if opts.is_file():
        raw = opts.read_text(encoding="utf-8", errors="replace")

    outer, _ = strip_managed_block(raw)
    # dedupe normalized option flags
    normalized: list[str] = []
    seen: set[str] = set()
    for ln in option_lines:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        token = s.split()[0]
        if token.startswith("-") and token in seen:
            continue
        if token.startswith("-"):
            seen.add(token)
        normalized.append(s)

    inner = (_MARK_BEGIN + "\n") + ("\n".join(normalized) + ("\n" if normalized else "")) + _MARK_END + "\n"

    combined = outer.rstrip() + ("\n\n" if outer.strip() else "") + inner + "\n"
    opts.write_text(combined, encoding="utf-8")
    return opts


def user_library_templates_dir() -> Path:
    return ableton_home() / "User Library" / "Templates"


def pipeline_template_subdir() -> Path:
    return user_library_templates_dir() / "M4L Pipeline"


def pipeline_startup_als_path() -> Path:
    return pipeline_template_subdir() / "m4l_pipeline_startup.als"


def _live_major_from_bundle_name(name: str) -> int:
    m = re.search(r"Live\s+(\d+)", name, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def _bundle_path_from_mac_factory_als(factory_als: Path) -> Path:
    """Walk parents until we find *.app (bundle layout varies slightly)."""

    for p in factory_als.parents:
        if p.suffix.lower() == ".app":
            return p
    raise RuntimeError(f"Cannot locate .app bundle for {factory_als}")


def find_factory_default_live_set_als() -> Path | None:
    """Locate Ableton's factory DefaultLiveSet.als (newest / highest Live major on macOS)."""

    candidates: list[Path] = []
    if sys.platform == "darwin":
        for bundle in find_installed_live_app_bundles():
            p = bundle / "Contents/App-Resources/Builtin/Templates/DefaultLiveSet.als"
            if p.is_file():
                candidates.append(p)
        if not candidates:
            return None
        return max(candidates, key=lambda p: (_live_major_from_bundle_name(_bundle_path_from_mac_factory_als(p).name), p.stat().st_mtime))

    if sys.platform == "win32":
        for key in ("ProgramFiles", "ProgramFiles(x86)"):
            root = os.environ.get(key, "")
            if not root:
                continue
            ableton_root = Path(root) / "Ableton"
            if not ableton_root.is_dir():
                continue
            for child in ableton_root.iterdir():
                if not child.is_dir():
                    continue
                for rel in (
                    ("Resources", "Builtin", "Templates", "DefaultLiveSet.als"),
                    ("App-Resources", "Builtin", "Templates", "DefaultLiveSet.als"),
                ):
                    p = child.joinpath(*rel)
                    if p.is_file():
                        candidates.append(p)
        if not candidates:
            return None
        return max(candidates, key=lambda p: (p.stat().st_mtime, str(p)))

    return None


def xml_attr_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def patch_library_cfg_default_template(library_cfg: Path, als_absolute: Path) -> bool:
    """Set <DefaultTemplateSet Value=\"…\"/> to an absolute path. Returns False if cfg missing."""

    if not library_cfg.is_file():
        return False
    raw = library_cfg.read_text(encoding="utf-8", errors="replace")
    path_norm = str(als_absolute.resolve()).replace("\\", "/")
    replacement = f'<DefaultTemplateSet Value="{xml_attr_escape(path_norm)}" />'
    new_raw, n = re.subn(
        r'<DefaultTemplateSet\s+Value="[^"]*"\s*/>',
        replacement,
        raw,
        count=1,
    )
    if n != 1:
        raise RuntimeError(f"Could not find DefaultTemplateSet entry in {library_cfg}")
    library_cfg.write_text(new_raw, encoding="utf-8")
    return True
