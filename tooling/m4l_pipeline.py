#!/usr/bin/env python3
"""
M4L Pipeline — Build, deploy, and load Max for Live devices programmatically.

Versioning: each ``build_deploy_load`` run creates ``{plugin_projects_base()}/<slug>/{name X.Y}/`` with
``spec.json``, ``VERSION.txt``, and the ``.amxd``. With **M4L_PROJECTS_PREFIX=workspace**, that is under
``projects/workspace/<slug>/`` (gitignored local sandboxes — safe across ``git pull``).
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
    python3 m4l_pipeline.py all     spec.json [track_index|new] [--no-live] [--skip-validate] [--with-adv]
        # Default: versioned build → deploy → NEW Live track + load (AbletonMCP).
        # Omit track or pass ``new`` for a new track; pass ``0`` etc. for an existing track.
        # ``--no-live``: skip MCP (artifacts + deploy only). Env ``M4L_SKIP_LIVE=1`` same effect.
        # ``--with-adv``: build/deploy .adv (preset) alongside .amxd; also copied next to .amxd under Imported/.
        # Env ``M4L_BUILD_ADV=1`` enables .adv from Python callers of ``build_deploy_load``.
        # ``--skip-validate``: skip schema/UI checks (``build`` / ``all``).
"""

from __future__ import annotations

import json
import os
import re
import struct
import shutil
import socket
import sys
from copy import deepcopy
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

WORKSPACE = Path(__file__).resolve().parent
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))
REPO_ROOT = Path(__file__).resolve().parent.parent


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


def next_plugin_version(spec_name: str) -> str:
    slug = plugin_slug_from_name(spec_name)
    parent = plugin_projects_base() / slug
    vers = _parse_existing_versions(parent, spec_name)
    if not vers:
        return "1.1"
    maj, mi = max(vers, key=lambda t: (t[0], t[1]))
    return f"{maj}.{mi + 1}"


def allocate_version_directory(spec: dict) -> tuple[Path, str]:
    """Create ``{plugin_projects_base()}/<slug>/{spec_name X.Y}/`` for this build."""

    name = spec.get("name", "Untitled")
    ver = next_plugin_version(name)
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



# User Library destinations by device type (lazy — reads ABLETON_HOME per call).
_DEVICE_TYPE_FOLDERS = {
    "midi_effect": ("MIDI Effects", "Max MIDI Effect"),
    "audio_effect": ("Audio Effects", "Max Audio Effect"),
    "instrument": ("Instruments", "Max Instrument"),
}


def _user_lib_presets() -> Path:
    return _ableton_home() / "User Library/Presets"


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

# AbletonMCP socket
_ABLETON_HOST = "127.0.0.1"
_ABLETON_PORT = 9877

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

    dest_root = _dest_dir(device_type)
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


# ── Binary format ────────────────────────────────────────────────────────────

def _amxd_json_starts_at_32(data: bytes) -> bool:
    """True when JSON root begins at byte 32 (compact pipeline / blank templates)."""
    return len(data) > 34 and data[32:34] == b'{"'


def _decode_amxd_json_at(data: bytes, offset: int) -> tuple[dict, bytes]:
    body = data[offset:]
    end = len(body)
    while end:
        try:
            s = body[:end].decode("utf-8")
            break
        except UnicodeDecodeError:
            end -= 1
    else:
        raise ValueError("Could not decode UTF-8 from .amxd body")
    dec = json.JSONDecoder()
    obj, char_end = dec.raw_decode(s)
    json_byte_len = len(s[:char_end].encode("utf-8"))
    trailing = data[offset + json_byte_len :]
    return obj, trailing


def _extract_amxd_parts(data: bytes) -> tuple[bytes, bytes, dict, bytes]:
    """Parse an .amxd file and return the inner patcher dict.

    Supports compact JSON-at-32 (pipeline builds, midi/audio donors) and legacy
    subheader + JSON-at-48 (instrument donor, Max saves with dlst trailer).
    Returns (header_32, subheader_16, patcher_dict, trailing_bytes).
    """
    header = data[:32]
    subheader = data[32:48]

    offset = 32 if _amxd_json_starts_at_32(data) else 48
    obj, trailing = _decode_amxd_json_at(data, offset)

    if "patcher" in obj and isinstance(obj.get("patcher"), dict):
        patcher = obj["patcher"]
    else:
        patcher = obj
    return header, subheader, patcher, trailing



def _pack_amxd(header_32: bytes, root: dict, device_name: str = "Untitled") -> bytes:
    """Assemble .amxd bytes: 32-byte header + JSON content.

    Matches the official blank Max for Live template format: JSON starts
    directly at byte 32, no binary subheader, no dlst trailer.
    section_size at header[28:32] (LE) = len(JSON bytes).
    """
    json_bytes = json.dumps(root, ensure_ascii=False).encode("utf-8")

    hdr = bytearray(header_32)
    struct.pack_into("<I", hdr, 28, len(json_bytes))

    return bytes(hdr) + json_bytes


def _get_reference(device_type: str = "midi_effect") -> tuple[bytes, bytes, dict, bytes]:
    """Load and parse the reference .amxd file."""
    path = reference_amxd_path(device_type)
    if not path.is_file():
        raise FileNotFoundError(
            f"Reference .amxd not found: {path}\n"
            f"Could not find local donor for {device_type} or legacy Reference_Donor.amxd.\n"
            "See docs/REFERENCE_HEADER_AND_IMPORT.md."
        )
    data = path.read_bytes()
    return _extract_amxd_parts(data)


# ── Spec format ──────────────────────────────────────────────────────────────
#
# A spec is a JSON dict:
# {
#   "name": "MyDevice",
#   "description": "What it does",
#   "device_type": "midi_effect",    // midi_effect | audio_effect | instrument — picks deploy folder,
#                                     // browser category, .adv wrapper, and new Live track (MIDI vs audio)
#   "devicewidth": 180.0,            // device panel width in Live (pixels)
#   "openinpresentation": 1,           // optional; default from donor patcher (usually 1)
#   "boxes": [ {box dict}, ... ],    // Max patcher boxes — UI needs presentation + presentation_rect
#   "lines": [ {patchline dict}, ... ],
#   "parameters": { ... }            // optional Live parameter mapping
#
# Frontend vs backend: patching_rect wires the graph; presentation_rect is the rack UI.
# See docs/M4L_FRONTEND_AND_BACKEND.md.
# }

_APPVERSION_FALLBACK = {"major": 8, "minor": 6, "revision": 4, "architecture": "x64", "modernui": 1}


def _resolve_appversion(donor_patcher: dict) -> dict:
    """Choose Max ``appversion`` stamp for a built device.

    Default: preserve donor. Override with ``M4L_APPVERSION=9.1.4`` or
    ``M4L_APPVERSION_JSON_FILE=/path/to.json`` (full dict).
    """
    json_file = (os.environ.get("M4L_APPVERSION_JSON_FILE") or "").strip()
    if json_file:
        return json.loads(Path(json_file).read_text(encoding="utf-8"))

    env_ver = (os.environ.get("M4L_APPVERSION") or "").strip()
    if env_ver:
        m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", env_ver)
        if not m:
            raise ValueError(
                f"M4L_APPVERSION must match MAJOR.MINOR.REVISION, got {env_ver!r}"
            )
        return {
            "major": int(m.group(1)),
            "minor": int(m.group(2)),
            "revision": int(m.group(3)),
            "architecture": "x64",
            "modernui": 1,
        }

    donor_av = donor_patcher.get("appversion")
    if isinstance(donor_av, dict) and donor_av.get("major") is not None:
        return deepcopy(donor_av)
    return deepcopy(_APPVERSION_FALLBACK)


# Legacy name kept for tests/docs that reference the fallback stamp.
_APPVERSION = _APPVERSION_FALLBACK

# Max classes that are normally patch-only (not shown on the device face).
# Light label/value text on dark M4L device backgrounds (~Live rack gray).
_LIVE_TEXT_ON_DARK = [0.811764705882353, 0.811764705882353, 0.827450980392157, 1.0]

_PATCH_ONLY_MAXCLASSES = frozenset(
    {
        "midiin",
        "midiout",
        "in",
        "out",
        "plugout~",
        "plugin~",
        "ezadc~",
        "ezdac~",
        "adc~",
        "dac~",
    }
)


def _ensure_presentation_boxes(boxes: list) -> list:
    """Ensure UI objects appear in Live Presentation mode.

    Specs often define only ``patching_rect`` (backend). Live's rack uses
    ``presentation`` + ``presentation_rect`` per box — without them the device
    face is blank even when parameters work. See docs/M4L_FRONTEND_AND_BACKEND.md.
    """
    out: list = []
    for entry in boxes:
        b = deepcopy(entry)
        box = b.setdefault("box", {})
        if box.get("presentation") == 1 and box.get("presentation_rect"):
            out.append(b)
            continue
        maxclass = (box.get("maxclass") or "").lower()
        if maxclass in _PATCH_ONLY_MAXCLASSES:
            out.append(b)
            continue
        is_ui = bool(box.get("parameter_enable")) or maxclass.startswith("live.")
        if not is_ui:
            out.append(b)
            continue
        prect = box.get("presentation_rect")
        if not prect and box.get("patching_rect"):
            prect = list(box["patching_rect"])
        if prect:
            box["presentation"] = 1
            box["presentation_rect"] = prect
        out.append(b)
    return out


def _apply_live_ui_contrast(boxes: list) -> list:
    """Set readable label colors on ``live.*`` controls (spec-first builds often omit these).

    Without ``textcolor``, Live theme defaults can render parameter names/values nearly
    the same as ``patcher.bgcolor`` — labels look invisible. See docs/M4L_FRONTEND_AND_BACKEND.md.
    """
    out: list = []
    for entry in boxes:
        b = deepcopy(entry)
        box = b.setdefault("box", {})
        maxclass = box.get("maxclass") or ""
        if maxclass == "live.dial":
            box.setdefault("textcolor", list(_LIVE_TEXT_ON_DARK))
            box.setdefault("showname", 1)
            box.setdefault("shownumber", 1)
        elif maxclass == "live.toggle":
            box.setdefault("textcolor", list(_LIVE_TEXT_ON_DARK))
        elif maxclass in ("live.numbox", "live.slider"):
            box.setdefault("textcolor", list(_LIVE_TEXT_ON_DARK))
            if maxclass == "live.numbox":
                box.setdefault("lcdcolor", list(_LIVE_TEXT_ON_DARK))
        elif maxclass == "live.text":
            box.setdefault("textcolor", list(_LIVE_TEXT_ON_DARK))
        elif maxclass == "comment" and box.get("presentation") == 1:
            box.setdefault("textcolor", list(_LIVE_TEXT_ON_DARK))
        out.append(b)
    return out


def build_amxd(
    spec: dict,
    output: Path | None = None,
    *,
    skip_validate: bool = False,
) -> Path:
    """Build an .amxd from a device spec dict.

    Returns the path to the generated file.
    """
    if not skip_validate and os.environ.get("M4L_SKIP_VALIDATE") != "1":
        from spec_validate import require_valid_spec

        require_valid_spec(spec)
    device_type = spec.get("device_type", "midi_effect")
    header_32, _subheader, ref_root, _trailing = _get_reference(device_type)
    # Start from the donor's full patcher to carry over required fields like
    # fileversion and classnamespace — without these Max rejects the file with
    # "createdevice" error 6 ("device file broken").
    patch = deepcopy(ref_root)

    # Override with spec content
    patch["appversion"] = _resolve_appversion(patch)
    boxes = _ensure_presentation_boxes(spec["boxes"])
    patch["boxes"] = _apply_live_ui_contrast(boxes)
    patch["lines"] = spec.get("lines", [])
    patch["dependency_cache"] = []
    patch["devicewidth"] = spec.get("devicewidth", 180.0)
    if "openinpresentation" in spec:
        patch["openinpresentation"] = spec["openinpresentation"]
    patch["description"] = spec.get("description", "")
    patch["digest"] = spec.get("name", "Untitled")

    if spec.get("bgcolor") is not None:
        patch["bgcolor"] = list(spec["bgcolor"])

    if "parameters" in spec:
        patch["parameters"] = spec["parameters"]

    # Explicitly replace project and styles so no reference-device identity leaks
    # into the built .amxd (prevents hot swap navigating to the reference file).
    # amxdtype encodes the M4L device type in the binary header — must match the
    # donor (audio=0x61616161, midi=0x6D6D6D6D, instrument=0x69696969).
    donor_amxdtype = ref_root.get("project", {}).get("amxdtype", 1835887981)
    patch["project"] = {
        "version": 1,
        "creationdate": 3590052786,
        "modificationdate": 3590052786,
        "viewrect": [0.0, 0.0, 300.0, 500.0],
        "autoorganize": 1,
        "hideprojectwindow": 1,
        "showdependencies": 1,
        "autolocalize": 0,
        "contents": {"patchers": {}, "media": {}},
        "layout": {},
        "searchpath": {},
        "detailsvisible": 0,
        "amxdtype": donor_amxdtype,
        "readonly": 0,
        "devpathtype": 0,
        "devpath": ".",
        "sortmode": 0,
        "viewmode": 0,
        "includepackages": 0,
    }
    patch["styles"] = []

    root = {"patcher": patch}
    # Trailing bytes after JSON (donor SVGs, etc.) are omitted so identity/artwork
    # does not leak from the header donor. Basic live.* UI does not need them;
    # rack controls require presentation flags on boxes (see M4L_FRONTEND_AND_BACKEND.md).
    name = spec.get("name", "Untitled")
    amxd_bytes = _pack_amxd(header_32, root, device_name=name)
    if output is None:
        output = WORKSPACE / f"{name}.amxd"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(amxd_bytes)
    write_device_type_sidecar(output, device_type)
    print(f"Built {output} ({len(amxd_bytes)} bytes)")
    return output


def build_adv(spec: dict, amxd_deploy_path: Path, output: Path | None = None) -> Path:
    """Build an .adv (Ableton Device Preset) that wraps the .amxd with parameter definitions.

    Live reads parameters from the .adv XML, not the .amxd JSON.
    Without an .adv, only 'Device On' shows up.
    """
    import gzip

    name = spec.get("name", "Untitled")
    device_type = spec.get("device_type", "midi_effect")

    # Device class tag in Ableton XML
    device_class = {
        "midi_effect":  "MxDeviceMidiEffect",
        "audio_effect": "MxDeviceAudioEffect",
        "instrument":   "MxDeviceInstrument",
    }.get(device_type, "MxDeviceMidiEffect")

    # Collect parameters from spec boxes that have parameter_enable
    params = []
    for b in spec.get("boxes", []):
        box = b.get("box", {})
        if not box.get("parameter_enable"):
            continue
        saa = box.get("saved_attribute_attributes", {})
        vo = saa.get("valueof", {})
        if not vo.get("parameter_longname"):
            continue
        params.append({
            "name": vo["parameter_longname"],
            "shortname": vo.get("parameter_shortname", vo["parameter_longname"]),
            "min": vo.get("parameter_mmin", 0.0),
            "max": vo.get("parameter_mmax", 1.0),
            "default": vo.get("parameter_initial", [0.0])[0] if isinstance(vo.get("parameter_initial"), list) else vo.get("parameter_initial", 0.0),
            "type": vo.get("parameter_type", 0),  # 0=float, 2=enum
            "obj_id": box.get("id", ""),
        })

    # Build parameter XML
    param_xml = ""
    for i, p in enumerate(params):
        default_val = p["default"] if p["default"] is not None else p["min"]
        param_xml += f"""
				<MxDFloatParameter Id="{i}">
					<Index Value="{i}" />
					<Type Value="{p['type']}" />
					<Name Value="{p['name']}" />
					<ShortName Value="{p['shortname']}" />
					<MinValue Value="{p['min']}" />
					<MaxValue Value="{p['max']}" />
					<Default Value="{default_val}" />
					<ModType Value="0" />
					<MinMod Value="-1" />
					<MaxMod Value="1" />
					<Timeable>
						<LomId Value="0" />
						<Manual Value="{default_val}" />
						<MidiControllerRange>
							<Min Value="{p['min']}" />
							<Max Value="{p['max']}" />
						</MidiControllerRange>
						<AutomationTarget Id="{i}">
							<LockEnvelope Value="0" />
						</AutomationTarget>
						<ModulationTarget Id="{i}">
							<LockEnvelope Value="0" />
						</ModulationTarget>
					</Timeable>
				</MxDFloatParameter>"""

    # Relative path from User Library root
    rel_path = str(amxd_deploy_path).replace(str(_user_lib_presets().parent) + os.sep, "")
    rel_path = rel_path.replace(str(_user_lib_presets().parent) + "/", "")
    abs_path = str(amxd_deploy_path)
    file_size = amxd_deploy_path.stat().st_size if amxd_deploy_path.exists() else 0

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Ableton MajorVersion="5" MinorVersion="12.0_12120" Creator="m4l_pipeline" Revision="">
	<{device_class}>
		<LomId Value="0" />
		<LomIdView Value="0" />
		<IsExpanded Value="true" />
		<BreakoutIsExpanded Value="false" />
		<On>
			<LomId Value="0" />
			<Manual Value="true" />
			<AutomationTarget Id="100">
				<LockEnvelope Value="0" />
			</AutomationTarget>
			<MidiCCOnOffThresholds>
				<Min Value="64" />
				<Max Value="127" />
			</MidiCCOnOffThresholds>
		</On>
		<ModulationSourceCount Value="0" />
		<ParametersListWrapper LomId="0" />
		<Pointee Id="0" />
		<LastSelectedTimeableIndex Value="0" />
		<LastSelectedClipEnvelopeIndex Value="0" />
		<LastPresetRef>
			<Value />
		</LastPresetRef>
		<LockedScripts />
		<IsFolded Value="false" />
		<ShouldShowPresetName Value="true" />
		<UserName Value="{name}" />
		<Annotation Value="" />
		<SourceContext>
			<Value />
		</SourceContext>
		<MpePitchBendUsesTuning Value="true" />
		<OverwriteProtectionNumber Value="3073" />
		<AudioOutputsListWrapper LomId="0" />
		<AudioInputsListWrapper LomId="0" />
		<MidiOutputsListWrapper LomId="0" />
		<MidiInputsListWrapper LomId="0" />
		<PatchSlot>
			<Value>
				<MxPatchRef Id="1">
					<FileRef>
						<RelativePathType Value="6" />
						<RelativePath Value="{rel_path}" />
						<Path Value="{abs_path}" />
						<Type Value="2" />
						<LivePackName Value="" />
						<LivePackId Value="" />
						<OriginalFileSize Value="{file_size}" />
						<OriginalCrc Value="0" />
					</FileRef>
					<LastModDate Value="0" />
					<SourceContext />
					<SampleUsageHint Value="0" />
				</MxPatchRef>
			</Value>
		</PatchSlot>
		<ParameterList>
			<ParameterList>{param_xml}
			</ParameterList>
		</ParameterList>
		<FileDropList>
			<FileDropList />
		</FileDropList>
		<IdRefList>
			<IdRefList />
		</IdRefList>
		<BlobSlot>
			<Value>
				<MxDBlob Id="99">
					<Blob />
					<HasData Value="false" />
				</MxDBlob>
			</Value>
		</BlobSlot>
		<Routables>
			<InRoutings />
			<OutRoutings />
			<MidiInRoutings />
			<MidiOutRoutings />
		</Routables>
		<MpeEnabled Value="false" />
	</{device_class}>
</Ableton>"""

    if output is None:
        output = WORKSPACE / f"{name}.adv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output, "wb") as f:
        f.write(xml.encode("utf-8"))
    print(f"Built {output} (adv preset, {len(params)} parameters)")
    return output


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


def _patcher_dict_from_amxd_root(obj: dict) -> dict:
    if "patcher" in obj and isinstance(obj["patcher"], dict):
        return obj["patcher"]
    return obj


def _find_title_comment_box(patcher: dict) -> dict | None:
    boxes = patcher.get("boxes") or []
    candidates: list[dict] = []
    for entry in boxes:
        box = entry.get("box") or {}
        if box.get("maxclass") != "comment":
            continue
        if box.get("presentation") != 1:
            continue
        candidates.append(box)
    for box in candidates:
        if box.get("fontface") == 1:
            return box
    return candidates[0] if candidates else None


def _parse_rgba_csv(value: str) -> list[float]:
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != 4:
        raise ValueError(f"RGBA must have 4 comma-separated values, got {value!r}")
    return [float(p) for p in parts]


def _repack_amxd_patched(
    data: bytes,
    patcher: dict,
    *,
    device_name: str,
    allow_dlst_rebuild: bool = False,
) -> bytes:
    header, subheader, _old_root, trailing = _extract_amxd_parts(data)
    root = {"patcher": patcher}

    if _amxd_json_starts_at_32(data):
        return _pack_amxd(header, root, device_name=device_name)

    json_bytes = json.dumps(root, ensure_ascii=False).encode("utf-8")
    json_pad = (4 - len(json_bytes) % 4) % 4
    json_padded = json_bytes + b"\x00" * json_pad

    old_content_size = struct.unpack(">I", subheader[12:16])[0]
    old_json_padded_len = old_content_size - 16

    if len(json_padded) == old_json_padded_len:
        new_content_size = 16 + len(json_padded)
        new_section_size = new_content_size + len(trailing)
        hdr = bytearray(header)
        struct.pack_into("<I", hdr, 28, new_section_size)
        sub = bytearray(subheader)
        struct.pack_into(">I", sub, 12, new_content_size)
        return bytes(hdr) + bytes(sub) + json_padded + trailing

    if not allow_dlst_rebuild:
        raise ValueError(
            "Patch changed JSON byte length; embedded dlst cannot be preserved. "
            "Pass allow_dlst_rebuild=True or use a smaller edit."
        )
    print(
        "WARN: Rebuilding dlst — trailing embeds from Max save may be lost.",
        file=sys.stderr,
    )
    return _pack_amxd(header, root, device_name=device_name)


def _next_patch_output_path(src: Path) -> Path:
    parent = src.parent
    stem = src.stem
    if stem.endswith(".amxd"):
        stem = stem[:-5]
    pat = re.compile(r"^(?P<base>.+)_patch(?P<n>\d+)$")
    m = pat.match(stem)
    base = m.group("base") if m else stem
    n = int(m.group("n")) + 1 if m else 1
    while (parent / f"{base}_patch{n}.amxd").exists():
        n += 1
    return parent / f"{base}_patch{n}.amxd"


def patch_amxd_field(
    amxd_path: Path,
    *,
    bgcolor: list[float] | None = None,
    editing_bgcolor: list[float] | None = None,
    title_text: str | None = None,
    title_color: list[float] | None = None,
    in_place: bool = False,
    allow_dlst_rebuild: bool = False,
    output: Path | None = None,
) -> Path:
    """Surgical UI edit on an existing ``.amxd`` without ``build_amxd`` mutators."""
    amxd_path = Path(amxd_path)
    if not amxd_path.is_file():
        raise FileNotFoundError(amxd_path)

    data = amxd_path.read_bytes()
    _header, _sub, root_obj, _trail = _extract_amxd_parts(data)
    patcher = deepcopy(_patcher_dict_from_amxd_root(root_obj))

    if bgcolor is not None:
        patcher["bgcolor"] = list(bgcolor)
    if editing_bgcolor is not None:
        patcher["editing_bgcolor"] = list(editing_bgcolor)
    if title_text is not None or title_color is not None:
        title_box = _find_title_comment_box(patcher)
        if title_box is None:
            raise ValueError("No presentation title comment box found to patch")
        if title_text is not None:
            title_box["text"] = title_text
        if title_color is not None:
            title_box["textcolor"] = list(title_color)

    if not any(v is not None for v in (bgcolor, editing_bgcolor, title_text, title_color)):
        raise ValueError("No patch fields specified")

    device_name = amxd_path.stem
    out_bytes = _repack_amxd_patched(
        data,
        patcher,
        device_name=device_name,
        allow_dlst_rebuild=allow_dlst_rebuild,
    )

    if in_place:
        out_path = amxd_path
    elif output is not None:
        out_path = Path(output)
    else:
        out_path = _next_patch_output_path(amxd_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out_bytes)

    sidecar_src = sidecar_path_for_artifact(amxd_path)
    if sidecar_src.is_file():
        shutil.copy2(sidecar_src, sidecar_path_for_artifact(out_path))
    elif not in_place:
        pass

    print(f"Patched → {out_path} ({len(out_bytes)} bytes)")
    return out_path


def _lint_amxd_dlst(amxd_path: Path) -> list[str]:
    """Lint dlst only for legacy subheader .amxd files (compact builds omit dlst)."""
    data = amxd_path.read_bytes()
    if _amxd_json_starts_at_32(data):
        return []
    if b"dlst" not in data:
        return ["missing dlst section"]
    return []


def verify_spec_offline(spec: dict, *, skip_validate: bool = False) -> dict:
    """Validate spec, build to a temp file, and lint sidecar + dlst (no Live)."""
    from tempfile import TemporaryDirectory

    if not skip_validate:
        from spec_validate import require_valid_spec

        require_valid_spec(spec)

    device_type = spec.get("device_type", "midi_effect")
    with TemporaryDirectory(prefix="m4l_verify_") as tmp:
        out = Path(tmp) / amxd_filename_for_spec(spec.get("name", "Untitled"))
        build_amxd(spec, out, skip_validate=True)
        sidecar = read_device_type_sidecar(out)
        if sidecar != device_type:
            raise ValueError(
                f"sidecar device_type {sidecar!r} != spec {device_type!r}"
            )
        dlst_errors = _lint_amxd_dlst(out)
        if dlst_errors:
            raise ValueError("; ".join(dlst_errors))
        return {
            "status": "ok",
            "amxd_bytes": out.stat().st_size,
            "device_type": device_type,
            "sidecar": sidecar,
        }


# ── AbletonMCP socket helpers ────────────────────────────────────────────────

def _ableton_cmd(cmd_type: str, params: dict, timeout: float = 15.0) -> dict:
    """Send a command to AbletonMCP Remote Script via socket."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((_ABLETON_HOST, _ABLETON_PORT))
    msg = json.dumps({"type": cmd_type, "params": params})
    s.sendall(msg.encode("utf-8"))

    chunks: list[bytes] = []
    while True:
        try:
            chunk = s.recv(16384)
            if not chunk:
                break
            chunks.append(chunk)
            try:
                json.loads(b"".join(chunks))
                break
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        except socket.timeout:
            break
    s.close()
    if not chunks:
        return {"status": "error", "message": "No response"}
    return json.loads(b"".join(chunks))


def _coerce_dict(blob: dict | str | None) -> dict:
    if isinstance(blob, dict):
        return blob
    if isinstance(blob, str) and blob.strip():
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            return {}
    return {}


def _normalize_browser_leaf(name: str) -> str:
    """Strip ``.amxd`` / ``.adv`` for comparisons — Live browser names include a suffix."""
    n = (name or "").strip()
    lower = n.lower()
    if lower.endswith(".amxd"):
        n = n[:-5].strip()
    elif lower.endswith(".adv"):
        n = n[:-4].strip()
    return n


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


def _create_midi_track_index() -> int:
    created = _ableton_cmd("create_midi_track", {"index": -1})
    if created.get("status") != "success":
        raise RuntimeError(f"create_midi_track failed: {created}")
    res = _coerce_dict(created.get("result"))
    idx = res.get("index")
    if idx is None:
        raise RuntimeError(f"create_midi_track: no index in {created}")
    return int(idx)


def _create_audio_track_index() -> int:
    """Requires AbletonMCP patched by ``scripts/install_remote_scripts.py`` (adds ``create_audio_track``)."""
    created = _ableton_cmd("create_audio_track", {"index": -1})
    if created.get("status") != "success":
        raise RuntimeError(f"create_audio_track failed: {created}")
    res = _coerce_dict(created.get("result"))
    idx = res.get("index")
    if idx is None:
        raise RuntimeError(f"create_audio_track: no index in {created}")
    return int(idx)


def assert_loaded_device_matches_spec(
    device_type: str,
    track_info: dict,
    *,
    track_kind: str | None = None,
) -> None:
    """Raise ``RuntimeError`` if the track/device after MCP load disagrees with ``device_type``.

    Uses AbletonMCP ``get_track_info`` payload (``devices[-1].type``, ``class_name``) plus optional
    ``track_kind`` from :func:`_create_new_track_for_device_type` when this pipeline created the track.

    Note: If the outermost device is an Effect Rack (``type == rack``), we try ``devices[-2]`` for a
    matching Max device entry; if that fails we warn and skip strict alignment (nested chains are not
    fully enumerated by stock MCP).
    """
    if track_kind is not None:
        if device_type == "audio_effect" and track_kind != "audio":
            raise RuntimeError(
                f"Track kind is {track_kind!r} but device_type is audio_effect "
                "(expected an audio track — ensure create_audio_track works and Live restarted after MCP updates)."
            )
        if device_type in ("midi_effect", "instrument") and track_kind != "midi":
            raise RuntimeError(
                f"Track kind is {track_kind!r} but device_type is {device_type!r} (expected a MIDI track)."
            )

    devices = track_info.get("devices") or []
    if not devices:
        raise RuntimeError("No devices on track after load — cannot verify device class.")

    def _matches_unknown_heuristic(reported: str, cname: str) -> bool:
        if reported != "unknown":
            return False
        if device_type == "audio_effect":
            return "mxdeviceaudioeffect" in cname or ("audio" in cname and "effect" in cname)
        if device_type == "midi_effect":
            return "mxdeviceminieffect" in cname or ("midi" in cname and "effect" in cname)
        if device_type == "instrument":
            return "mxdeviceinstrument" in cname or "instrument" in cname
        return False

    def _entry_matches(dev: dict) -> bool:
        r = (dev.get("type") or "").strip().lower()
        cn = (dev.get("class_name") or "").lower().replace(" ", "")
        return r == device_type or _matches_unknown_heuristic(r, cn)

    last = devices[-1]
    reported = (last.get("type") or "").strip().lower()

    if reported == "rack":
        if len(devices) >= 2 and _entry_matches(devices[-2]):
            print(
                "NOTE: Outermost Live device is a Rack; devices[-2] matches "
                f"{device_type!r} — treating T2 device alignment as OK.",
                file=sys.stderr,
            )
            return
        print(
            "WARN: Outermost device is a Rack and no preceding device entry matched "
            f"{device_type!r} — skipping strict T2 device-type check (nested chains not fully visible via MCP).",
            file=sys.stderr,
        )
        return

    if _entry_matches(last):
        return

    cname = (last.get("class_name") or "").lower().replace(" ", "")
    raise RuntimeError(
        "Loaded device type does not match spec device_type "
        f"{device_type!r}: MCP reports type={reported!r}, class_name={last.get('class_name')!r}. "
        "Live may have inserted a placeholder or wrong device category."
    )


def _create_new_track_for_device_type(device_type: str) -> tuple[int, str]:
    """Create an empty Live track appropriate for ``device_type``.

    Returns ``(track_index, track_kind)`` where ``track_kind`` is ``\"midi\"`` or ``\"audio\"``.

    **Important:** ``audio_effect`` requires AbletonMCP to expose ``create_audio_track`` (this repo
    patches it in ``install_remote_scripts.py``). Loading a Max **audio** device on a **MIDI** track
    usually breaks the device in Live (often a generic Max error such as “error 6”). We therefore
    **do not** fall back to MIDI unless ``M4L_ALLOW_AUDIO_ON_MIDI=1`` (debug only).
    """
    if device_type == "audio_effect":
        try:
            return _create_audio_track_index(), "audio"
        except RuntimeError as exc:
            if os.environ.get("M4L_ALLOW_AUDIO_ON_MIDI") == "1":
                print(
                    "WARN: M4L_ALLOW_AUDIO_ON_MIDI=1 — loading audio_effect onto a MIDI track "
                    "(unsupported; expect Live/Max errors).",
                    file=sys.stderr,
                )
                return _create_midi_track_index(), "midi"
            raise RuntimeError(
                "AbletonMCP does not support create_audio_track — cannot load audio_effect safely.\n\n"
                "Common cause: Live was still running while Remote Scripts were updated; the control "
                "surface keeps the old MCP until you restart Live.\n\n"
                "Fix:\n"
                "  1. ./venv/bin/python scripts/install_remote_scripts.py\n"
                "  2. Quit Ableton Live completely, then reopen.\n"
                "  3. Confirm MCP exposes the command:\n"
                "       ./venv/bin/python scripts/verify_setup.py --wait-mcp 120 "
                "--assert-create-audio-track\n\n"
                "Debug-only escape hatch (will likely break Max Audio Effects): "
                "M4L_ALLOW_AUDIO_ON_MIDI=1\n\n"
                f"Underlying error: {exc}"
            ) from exc
    return _create_midi_track_index(), "midi"


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
    import time

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


def get_track_info(track_index: int) -> dict:
    """Get track info including devices."""
    result = _ableton_cmd("get_track_info", {"track_index": track_index})
    data = result.get("result", {})
    if isinstance(data, str):
        data = json.loads(data)
    return data


def get_session_info() -> dict:
    """Get Ableton session info."""
    result = _ableton_cmd("get_session_info", {})
    data = result.get("result", {})
    if isinstance(data, str):
        data = json.loads(data)
    return data


def set_tempo(bpm: float) -> dict:
    """Set session tempo via AbletonMCP TCP (slow, ~490ms)."""
    return _ableton_cmd("set_tempo", {"tempo": bpm})


# ── AbletonOSC UDP helpers (low-latency) ────────────────────────────────────

_osc_client = None

def _get_osc_client():
    global _osc_client
    if _osc_client is None:
        from pythonosc import udp_client
        _osc_client = udp_client.SimpleUDPClient("127.0.0.1", 11000)
    return _osc_client


def set_tempo_osc(bpm: float):
    """Set session tempo via AbletonOSC UDP (~0.02ms)."""
    _get_osc_client().send_message("/live/song/set/tempo", [float(bpm)])


# ── Full pipeline ────────────────────────────────────────────────────────────

def build_deploy_load(
    spec: dict,
    track_index: int | None = None,
    *,
    skip_live: bool = False,
    skip_validate: bool = False,
    with_adv: bool = False,
) -> dict:
    """Build into ``projects/<slug>/{name X.Y}/``, deploy to Imported/, load in Live.

    When ``track_index`` is None, appends a **new** Live track and loads there:
    MIDI track for ``midi_effect`` / ``instrument``, audio track for ``audio_effect``.

    Stock AbletonMCP loads via browser URI (see ``load_browser_item_by_browser_path``).
    Audio-track creation uses a **bootstrap patch** to AbletonMCP (see ``install_remote_scripts.py``).
    """
    device_type = spec.get("device_type", "midi_effect")
    name = spec.get("name", "Untitled")

    vdir, ver = allocate_version_directory(spec)
    amxd_file = amxd_filename_for_spec(name)
    built = vdir / amxd_file
    build_amxd(spec, built, skip_validate=skip_validate)

    donor_av = "unknown"
    try:
        _h, _s, donor_patch, _t = _get_reference(device_type)
        donor_av = str(_resolve_appversion(donor_patch).get("major", "?"))
    except Exception:
        pass
    from datetime import datetime, timezone

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


# ── CLI ──────────────────────────────────────────────────────────────────────

def _cli():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "build":
        argv_tail = sys.argv[2:]
        skip_validate = "--skip-validate" in argv_tail
        filtered = [a for a in argv_tail if a != "--skip-validate"]
        if not filtered:
            print("usage: m4l_pipeline.py build <spec.json> [output.amxd] [--skip-validate]", file=sys.stderr)
            sys.exit(1)
        spec_path = Path(filtered[0])
        output = Path(filtered[1]) if len(filtered) > 1 else None
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        build_amxd(spec, output, skip_validate=skip_validate)
        out = output or (WORKSPACE / f"{spec.get('name', 'Untitled')}.amxd")
        print(
            "\nNOTE: No Ableton Live step ran. To deploy + insert on a NEW track (default):\n"
            f"  python3 {Path(__file__).resolve()} all {spec_path}\n"
            "Or deploy then load manually: deploy → load",
            file=sys.stderr,
        )

    elif cmd == "deploy":
        argv_tail = sys.argv[2:]
        imported = "--category-root" not in argv_tail
        filtered = [a for a in argv_tail if a != "--category-root"]
        if not filtered:
            print(
                "usage: m4l_pipeline.py deploy <path.amxd|.adv> [device_type] [--category-root]",
                file=sys.stderr,
            )
            sys.exit(1)
        artifact = Path(filtered[0])
        device_type = filtered[1] if len(filtered) > 1 else "midi_effect"
        deploy_artifact_for_device_type(artifact, device_type, imported=imported)

    elif cmd == "patch":
        argv_tail = sys.argv[2:]
        if not argv_tail:
            print(
                "usage: m4l_pipeline.py patch <file.amxd> [--bgcolor R,G,B,A] "
                "[--editing-bgcolor R,G,B,A] [--title-text TEXT] [--title-color R,G,B,A] "
                "[--in-place] [--allow-dlst-rebuild] [--deploy device_type]",
                file=sys.stderr,
            )
            sys.exit(1)
        amxd = Path(argv_tail[0])
        bgcolor = editing_bgcolor = title_text = title_color = None
        in_place = False
        allow_dlst_rebuild = False
        deploy_type: str | None = None
        i = 1
        while i < len(argv_tail):
            a = argv_tail[i]
            if a == "--bgcolor" and i + 1 < len(argv_tail):
                bgcolor = _parse_rgba_csv(argv_tail[i + 1])
                i += 2
            elif a == "--editing-bgcolor" and i + 1 < len(argv_tail):
                editing_bgcolor = _parse_rgba_csv(argv_tail[i + 1])
                i += 2
            elif a == "--title-text" and i + 1 < len(argv_tail):
                title_text = argv_tail[i + 1]
                i += 2
            elif a == "--title-color" and i + 1 < len(argv_tail):
                title_color = _parse_rgba_csv(argv_tail[i + 1])
                i += 2
            elif a == "--in-place":
                in_place = True
                i += 1
            elif a == "--allow-dlst-rebuild":
                allow_dlst_rebuild = True
                i += 1
            elif a == "--deploy" and i + 1 < len(argv_tail):
                deploy_type = argv_tail[i + 1]
                i += 2
            else:
                print(f"Unknown patch argument: {a}", file=sys.stderr)
                sys.exit(1)
        out = patch_amxd_field(
            amxd,
            bgcolor=bgcolor,
            editing_bgcolor=editing_bgcolor,
            title_text=title_text,
            title_color=title_color,
            in_place=in_place,
            allow_dlst_rebuild=allow_dlst_rebuild,
        )
        if deploy_type:
            deploy_artifact_for_device_type(out, deploy_type, imported=True)

    elif cmd == "verify":
        argv_tail = sys.argv[2:]
        skip_validate = "--skip-validate" in argv_tail
        filtered = [a for a in argv_tail if a != "--skip-validate"]
        if not filtered:
            print("usage: m4l_pipeline.py verify <spec.json> [--skip-validate]", file=sys.stderr)
            sys.exit(1)
        spec = json.loads(Path(filtered[0]).read_text(encoding="utf-8"))
        result = verify_spec_offline(spec, skip_validate=skip_validate)
        print(json.dumps(result, indent=2))
        print("M4L_VERIFY_OFFLINE_OK")

    elif cmd == "load":
        track = int(sys.argv[2])
        name = sys.argv[3]
        device_type = sys.argv[4] if len(sys.argv) > 4 else "midi_effect"
        load_device(track, name, device_type)

    elif cmd == "info":
        track = int(sys.argv[2])
        info = get_track_info(track)
        print(json.dumps(info, indent=2))

    elif cmd == "session":
        info = get_session_info()
        print(json.dumps(info, indent=2))

    elif cmd == "all":
        argv_tail = sys.argv[2:]
        skip_live = False
        skip_validate = False
        with_adv = False
        filtered: list[str] = []
        for a in argv_tail:
            if a in ("--no-live", "--skip-live"):
                skip_live = True
            elif a == "--skip-validate":
                skip_validate = True
            elif a == "--with-adv":
                with_adv = True
            else:
                filtered.append(a)
        if not filtered:
            print(
                "usage: m4l_pipeline.py all <spec.json> [track_index|new] "
                "[--no-live] [--skip-validate] [--with-adv]",
                file=sys.stderr,
            )
            sys.exit(1)
        spec_path = Path(filtered[0])
        track: int | None = None
        if len(filtered) > 1:
            raw = filtered[1].lower()
            if raw not in ("new", "auto", "-1"):
                track = int(filtered[1])
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        result = build_deploy_load(
            spec,
            track,
            skip_live=skip_live,
            skip_validate=skip_validate,
            with_adv=with_adv,
        )
        print(json.dumps(result, indent=2, default=str))
        if not skip_live:
            lr = result.get("load_result") or {}
            if lr.get("status") != "success":
                print(
                    "\nERROR: Device did not load in Live. Common fixes: Live running, "
                    "AbletonMCP control surface enabled (TCP 9877), browser finished indexing "
                    "— or use --no-live and load by hand.",
                    file=sys.stderr,
                )
                sys.exit(1)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    _cli()
