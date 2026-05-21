"""Shared path helpers and repo constants for the M4L pipeline."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))
REPO_ROOT = WORKSPACE.parent

VERSION_BUMP_PATCH = "patch"
VERSION_BUMP_MAJOR = "major"
_VALID_VERSION_BUMPS = frozenset({VERSION_BUMP_PATCH, VERSION_BUMP_MAJOR})


def plugin_slug_from_name(name: str) -> str:
    """Filesystem-safe folder slug under projects/."""

    s = re.sub(r"\s+", "_", (name or "Untitled").strip())
    s = re.sub(r"[^\w\-.]+", "_", s, flags=re.UNICODE).strip("_")
    return s or "Untitled"


def amxd_filename_for_spec(name: str) -> str:
    """Cross-platform .amxd filename; avoids reserved characters on Windows."""

    forbidden = '<>:"/\\|?*'
    base = name.strip() or "Untitled"
    if any(c in base for c in forbidden) or base in (".", ".."):
        base = plugin_slug_from_name(name)
    return f"{base}.amxd"


def plugin_projects_base() -> Path:
    """Directory under ``projects/`` where versioned plugin trees are rooted.

    When **M4L_PROJECTS_PREFIX** is unset or empty, layouts match the tutorial:
    ``projects/<slug>/``.

    Set **M4L_PROJECTS_PREFIX=workspace** (recommended for your own devices) so builds
    land under ``projects/workspace/<slug>/``. That tree is **gitignored** by default,
    so ``git pull`` never deletes your sandboxes and you are not prompted to commit them.

    Use a single path segment (e.g. ``workspace``, ``local``). Slashes are stripped.
    """

    extra_raw = (os.environ.get("M4L_PROJECTS_PREFIX") or "").strip()
    extra = extra_raw.strip("/\\")
    if extra_raw and not extra:
        print(
            "WARN: M4L_PROJECTS_PREFIX was set but stripped to empty — using default projects/",
            file=sys.stderr,
        )
    base = REPO_ROOT / "projects"
    return (base / extra) if extra else base


def resolve_version_bump(bump: str | None = None, *, bump_major: bool = False) -> str:
    """Resolve bump mode: CLI ``bump_major`` wins, then explicit ``bump``, then env."""

    if bump_major:
        return VERSION_BUMP_MAJOR
    if bump is not None:
        b = bump.strip().lower()
        if b not in _VALID_VERSION_BUMPS:
            raise ValueError(f"version bump must be 'patch' or 'major', got {bump!r}")
        return b
    env = (os.environ.get("M4L_VERSION_BUMP") or VERSION_BUMP_PATCH).strip().lower()
    if env not in _VALID_VERSION_BUMPS:
        raise ValueError(
            f"M4L_VERSION_BUMP must be 'patch' or 'major', got {os.environ.get('M4L_VERSION_BUMP')!r}"
        )
    return env


def _parse_existing_versions(project_parent: Path, spec_name: str) -> list[tuple[int, int]]:
    pat = re.compile(r"^" + re.escape(spec_name) + r" (\d+)\.(\d+)$")
    found: list[tuple[int, int]] = []
    if not project_parent.is_dir():
        return found
    for p in project_parent.iterdir():
        if not p.is_dir():
            continue
        m = pat.match(p.name)
        if m:
            found.append((int(m.group(1)), int(m.group(2))))
    return found


def compute_next_version(
    existing: list[tuple[int, int]],
    bump: str = VERSION_BUMP_PATCH,
) -> str:
    """Next ``major.minor`` label from prior builds.

    **patch** (default): increment the minor on the highest line — ``1.3`` → ``1.4``.
    First build with no history: ``1.1``.

    **major** (only when user/agent passes ``--bump-major`` or ``M4L_VERSION_BUMP=major``):
    start a new major line — ``1.9`` → ``2.1`` (not ``2.0``; matches first-build convention).
    """

    if bump not in _VALID_VERSION_BUMPS:
        raise ValueError(f"version bump must be 'patch' or 'major', got {bump!r}")
    if not existing:
        return "1.1"
    maj, mi = max(existing, key=lambda t: (t[0], t[1]))
    if bump == VERSION_BUMP_MAJOR:
        return f"{maj + 1}.1"
    return f"{maj}.{mi + 1}"


def parse_version_label(label: str) -> tuple[int, int]:
    """Parse ``major.minor`` from a version string."""

    m = re.fullmatch(r"(\d+)\.(\d+)", label.strip())
    if not m:
        raise ValueError(f"expected major.minor version label, got {label!r}")
    return int(m.group(1)), int(m.group(2))


def next_plugin_version(
    spec_name: str,
    bump: str | None = None,
    *,
    bump_major: bool = False,
    extra_versions: list[tuple[int, int]] | None = None,
) -> str:
    """Next version folder label for ``{spec_name} X.Y``."""

    slug = plugin_slug_from_name(spec_name)
    parent = plugin_projects_base() / slug
    vers = _parse_existing_versions(parent, spec_name)
    if extra_versions:
        vers = vers + list(extra_versions)
    mode = resolve_version_bump(bump, bump_major=bump_major)
    return compute_next_version(vers, mode)


def allocate_version_directory(
    spec: dict,
    bump: str | None = None,
    *,
    bump_major: bool = False,
) -> tuple[Path, str]:
    """Create ``{plugin_projects_base()}/<slug>/{spec_name X.Y}/`` for this build."""

    name = spec.get("name", "Untitled")
    ver = next_plugin_version(name, bump, bump_major=bump_major)
    slug = plugin_slug_from_name(name)
    proj_parent = plugin_projects_base() / slug
    proj_parent.mkdir(parents=True, exist_ok=True)
    label = f"{name} {ver}"
    vdir = proj_parent / label
    vdir.mkdir(parents=False)
    return vdir, ver


def _ableton_home() -> Path:
    """Default: ~/Music/Ableton (POSIX) or ~/Documents/Ableton (Windows).

    Override with env ABLETON_HOME.
    """

    if env := os.environ.get("ABLETON_HOME"):
        return Path(env)
    if os.name == "nt" or sys.platform == "win32":
        return Path.home() / "Documents" / "Ableton"
    return Path.home() / "Music" / "Ableton"


def _user_lib_presets() -> Path:
    return _ableton_home() / "User Library/Presets"


def reference_amxd_path(device_type: str = "midi_effect") -> Path:
    """Header donor for packed .amxd (mmmmm/meta JSON slice).

    Default: ``tooling/donors/<device_type>.amxd``.

    Override with **M4L_REFERENCE_AMXD** (absolute path to any compatible .amxd) when you store
    the donor outside the repo.
    """

    env = os.environ.get("M4L_REFERENCE_AMXD")
    if env:
        return Path(env)

    # Local in-repo donors
    local = REPO_ROOT / "tooling" / "donors" / f"{device_type}.amxd"
    if local.is_file():
        return local

    # Fallback to User Library (legacy behavior)
    return (
        _ableton_home()
        / "User Library/Presets/MIDI Effects/Max MIDI Effect/Imported/"
        "Reference_Donor.amxd"
    )
