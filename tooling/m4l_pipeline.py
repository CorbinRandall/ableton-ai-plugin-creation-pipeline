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
    python3 m4l_pipeline.py build   spec.json [output.amxd]    # .amxd only — no Ableton
    python3 m4l_pipeline.py deploy  path.amxd [device_type]
    python3 m4l_pipeline.py load    track_index device_name [device_type]
    python3 m4l_pipeline.py info    track_index
    python3 m4l_pipeline.py session
    python3 m4l_pipeline.py all     spec.json [track_index|new] [--no-live]
        # Default: versioned build → deploy → NEW Live track + load (AbletonMCP).
        # Omit track or pass ``new`` for a new track; pass ``0`` etc. for an existing track.
        # ``--no-live``: skip MCP (artifacts + deploy only). Env ``M4L_SKIP_LIVE=1`` same effect.
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

    extra = (os.environ.get("M4L_PROJECTS_PREFIX") or "").strip().strip("/\\")
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


def reference_amxd_path() -> Path:
    """Header donor for packed .amxd (mmmmm/meta JSON slice).

    Default: ``$ABLETON_HOME/User Library/.../Imported/Reference_Donor.amxd``.

    Override with **M4L_REFERENCE_AMXD** (absolute path to any compatible .amxd) when you store
    the donor outside User Library — required for Python builds on a clean machine otherwise.
    """

    env = os.environ.get("M4L_REFERENCE_AMXD")
    if env:
        return Path(env)
    return (
        _ableton_home()
        / "User Library/Presets/MIDI Effects/Max MIDI Effect/Imported/"
        "Reference_Donor.amxd"
    )



# User Library destinations by device type
_USER_LIB = _ableton_home() / "User Library/Presets"
_DEST_MAP = {
    "midi_effect":  _USER_LIB / "MIDI Effects"  / "Max MIDI Effect",
    "audio_effect": _USER_LIB / "Audio Effects"  / "Max Audio Effect",
    "instrument":   _USER_LIB / "Instruments"    / "Max Instrument",
}

# Browser paths for AbletonMCP load — user_library is immediately available
# after deploy (max_for_live has delayed indexing).
_BROWSER_MAP = {
    "midi_effect":  "user_library/Presets/MIDI Effects/Max MIDI Effect",
    "audio_effect": "user_library/Presets/Audio Effects/Max Audio Effect",
    "instrument":   "user_library/Presets/Instruments/Max Instrument",
}

# AbletonMCP socket
_ABLETON_HOST = "127.0.0.1"
_ABLETON_PORT = 9877


# ── Binary format ────────────────────────────────────────────────────────────

def _extract_amxd_parts(data: bytes) -> tuple[bytes, bytes, dict, bytes]:
    """Split .amxd into (header_32, subheader_16, json_dict, trailing_bytes).

    The trailing bytes may contain SVGs, images, or other embedded resources.
    """
    header = data[:32]
    subheader = data[32:48]

    body = data[48:]
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
    trailing = data[48 + json_byte_len:]
    return header, subheader, obj, trailing


def _build_dlst(device_filename: str, json_padded_size: int) -> bytes:
    """Build a dlst (dependency list) with one JSON entry.

    The dlst tells Live where the JSON section is and its size.
    Without a valid dlst, Live can't register device parameters.

    All multi-byte integers are big-endian. Each field is:
        tag(4 bytes) + size(4 bytes, includes tag+size) + data(size-8 bytes)
    """
    def _tag(name: str, data: bytes) -> bytes:
        total = 8 + len(data)
        return name.encode("ascii") + struct.pack(">I", total) + data

    def _tag_u32(name: str, val: int) -> bytes:
        return _tag(name, struct.pack(">I", val))

    def _tag_str(name: str, s: str) -> bytes:
        raw = s.encode("ascii") + b"\x00"
        # Pad to 4-byte alignment
        pad = (4 - len(raw) % 4) % 4
        return _tag(name, raw + b"\x00" * pad)

    # Build the dire entry for JSON
    dire_body = (
        _tag_str("type", "JSON")
        + _tag_str("fnam", device_filename)
        + _tag_u32("sz32", json_padded_size)
        + _tag_u32("of32", 16)  # offset from byte 32 (mx@c subheader)
        + _tag_u32("vers", 0)
        + _tag_u32("flag", 0x11)  # 0x11 = standard JSON resource flag
        + _tag_u32("mdat", 0)
    )
    dire = b"dire" + struct.pack(">I", 8 + len(dire_body)) + dire_body

    # Wrap in dlst
    dlst = b"dlst" + struct.pack(">I", 8 + len(dire)) + dire
    return dlst


def _pack_amxd(header_32: bytes, subheader_16: bytes, root: dict,
               device_name: str = "Untitled") -> bytes:
    """Reassemble .amxd bytes: header + subheader + padded JSON + dlst.

    The dlst (dependency list) records the JSON section's byte offset and size.
    Live uses this to locate and parse device parameters.
    """
    json_bytes = json.dumps(root, ensure_ascii=False).encode("utf-8")

    # Pad JSON to 4-byte boundary (required by format)
    json_pad = (4 - len(json_bytes) % 4) % 4
    json_padded = json_bytes + b"\x00" * json_pad
    json_padded_size = len(json_padded)

    # Build dependency list
    device_filename = f"{device_name}.amxd"
    dlst = _build_dlst(device_filename, json_padded_size)

    # Content size = subheader(16) + json_padded (everything before dlst)
    # This goes in the subheader at offset 12 (big-endian).
    # Live uses it to locate the dlst boundary.
    content_size = 16 + json_padded_size

    # Section size = content_size + dlst (everything after the 32-byte header)
    section_size = content_size + len(dlst)

    hdr = bytearray(header_32)
    struct.pack_into("<I", hdr, 28, section_size)

    sub = bytearray(subheader_16)
    struct.pack_into(">I", sub, 12, content_size)

    return bytes(hdr) + bytes(sub) + json_padded + dlst


def _get_reference() -> tuple[bytes, bytes, dict, bytes]:
    """Load and parse the reference .amxd file."""
    path = reference_amxd_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"Reference .amxd not found: {path}\n"
            "Copy Reference_Donor.amxd (mmmmm/meta donor) under "
            "User Library … Max MIDI Effect … Imported/, or set M4L_REFERENCE_AMXD to its absolute path "
            "(see docs/REFERENCE_HEADER_AND_IMPORT.md)."
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

_APPVERSION = {"major": 8, "minor": 6, "revision": 4, "architecture": "x64", "modernui": 1}

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


def build_amxd(spec: dict, output: Path | None = None) -> Path:
    """Build an .amxd from a device spec dict.

    Returns the path to the generated file.
    """
    header_32, subheader_16, ref_root, trailing = _get_reference()
    patch = deepcopy(ref_root.get("patcher", {}))

    # Override with spec content
    patch["appversion"] = _APPVERSION
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
        "amxdtype": 1835887981,
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
    amxd_bytes = _pack_amxd(header_32, subheader_16, root, device_name=name)
    if output is None:
        output = WORKSPACE / f"{name}.amxd"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(amxd_bytes)
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
    rel_path = str(amxd_deploy_path).replace(str(_USER_LIB.parent) + "/", "")
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


def deploy_amxd(amxd_path: Path, device_type: str = "midi_effect") -> Path:
    """Copy .amxd to the User Library so Ableton's browser sees it."""
    dest_dir = _DEST_MAP.get(device_type)
    if dest_dir is None:
        raise ValueError(f"Unknown device_type: {device_type}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / amxd_path.name
    shutil.copy2(amxd_path, dest)
    print(f"Deployed → {dest}")
    return dest


def deploy_adv(adv_path: Path, device_type: str = "midi_effect") -> Path:
    """Copy .adv to the User Library."""
    dest_dir = _DEST_MAP.get(device_type)
    if dest_dir is None:
        raise ValueError(f"Unknown device_type: {device_type}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / adv_path.name
    shutil.copy2(adv_path, dest)
    print(f"Deployed → {dest}")
    return dest


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
    """Strip ``.amxd`` for comparisons — Live browser names usually include the suffix."""
    n = (name or "").strip()
    lower = n.lower()
    if lower.endswith(".amxd"):
        n = n[:-5].strip()
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

    path_attempts = [path]
    if not leaf.lower().endswith(".amxd"):
        path_attempts.append(f"{parent}/{leaf}.amxd")

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


def _create_new_track_for_device_type(device_type: str) -> tuple[int, str]:
    """Create an empty Live track appropriate for ``device_type``.

    Returns ``(track_index, track_kind)`` where ``track_kind`` is ``\"midi\"`` or ``\"audio\"``.
    """
    if device_type == "audio_effect":
        try:
            return _create_audio_track_index(), "audio"
        except RuntimeError as exc:
            print(
                f"WARN: Could not create audio track ({exc}). "
                "Re-run bootstrap (patches AbletonMCP) or upgrade MCP; falling back to MIDI track."
            )
            return _create_midi_track_index(), "midi"
    return _create_midi_track_index(), "midi"


def load_device(track_index: int, device_name: str,
                device_type: str = "midi_effect") -> dict:
    """Load a device from User Library → Imported/ onto a track (stem matches ``device_name``)."""
    browser_root = _BROWSER_MAP.get(device_type, _BROWSER_MAP["midi_effect"])
    path = f"{browser_root}/Imported/{device_name}"
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

    browser_root = _BROWSER_MAP.get(device_type, _BROWSER_MAP["midi_effect"])
    parent_path = f"{browser_root}/Imported"
    load_path = f"{parent_path}/{stem}"

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
    build_amxd(spec, built)
    (vdir / "spec.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (vdir / "VERSION.txt").write_text(ver + "\n", encoding="utf-8")
    print(f"Versioned build → {built} ({ver})")

    dest_dir = _DEST_MAP.get(device_type)
    imported_dir = dest_dir / "Imported"
    imported_dir.mkdir(parents=True, exist_ok=True)
    amxd_deploy = imported_dir / built.name
    shutil.copy2(built, amxd_deploy)
    print(f"Deployed .amxd → {amxd_deploy}")

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
        spec_path = Path(sys.argv[2])
        output = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        spec = json.loads(spec_path.read_text())
        build_amxd(spec, output)
        out = output or (WORKSPACE / f"{spec.get('name', 'Untitled')}.amxd")
        print(
            "\nNOTE: No Ableton Live step ran. To deploy + insert on a NEW track (default):\n"
            f"  python3 {Path(__file__).resolve()} all {spec_path}\n"
            "Or deploy then load manually: deploy → load",
            file=sys.stderr,
        )

    elif cmd == "deploy":
        amxd = Path(sys.argv[2])
        device_type = sys.argv[3] if len(sys.argv) > 3 else "midi_effect"
        deploy_amxd(amxd, device_type)

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
        filtered: list[str] = []
        for a in argv_tail:
            if a in ("--no-live", "--skip-live"):
                skip_live = True
            else:
                filtered.append(a)
        if not filtered:
            print("usage: m4l_pipeline.py all <spec.json> [track_index|new] [--no-live]", file=sys.stderr)
            sys.exit(1)
        spec_path = Path(filtered[0])
        track: int | None = None
        if len(filtered) > 1:
            raw = filtered[1].lower()
            if raw not in ("new", "auto", "-1"):
                track = int(filtered[1])
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        result = build_deploy_load(spec, track, skip_live=skip_live)
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
