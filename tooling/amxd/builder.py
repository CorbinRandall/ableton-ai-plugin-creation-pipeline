"""Build .amxd devices from JSON specs."""

from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from pathlib import Path

from amxd.binary import _get_reference, _pack_amxd
from paths import WORKSPACE

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
    from deploy import write_device_type_sidecar

    write_device_type_sidecar(output, device_type)
    print(f"Built {output} ({len(amxd_bytes)} bytes)")
    return output
