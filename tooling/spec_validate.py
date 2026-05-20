"""Validate device spec JSON (structure + optional UI checks)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parent / "spec.schema.json"

_DEVICE_IO_HINTS: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "midi_effect": (frozenset({"midiin"}), frozenset({"midiout"})),
    "audio_effect": (frozenset({"plugin~", "in"}), frozenset({"plugout~", "out"})),
    "instrument": (frozenset({"in"}), frozenset({"plugout~", "out"})),
}


def _box_classes(spec: dict) -> set[str]:
    out: set[str] = set()
    for entry in spec.get("boxes") or []:
        box = entry.get("box") or {}
        mc = (box.get("maxclass") or "").lower()
        if mc:
            out.add(mc)
    return out


def validate_structure(spec: dict) -> tuple[list[str], list[str]]:
    """JSON Schema + device-type hints. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        import jsonschema
    except ImportError as e:
        errors.append(f"jsonschema not installed: {e}")
        return errors, warnings

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(spec), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in err.path) or "(root)"
        errors.append(f"{path}: {err.message}")

    device_type = spec.get("device_type", "midi_effect")
    explicit_device_type = "device_type" in spec
    hints = _DEVICE_IO_HINTS.get(device_type)
    if hints:
        expected_in, expected_out = hints
        classes = _box_classes(spec)
        if not classes & expected_in:
            msg = (
                f"device_type={device_type}: no typical input object "
                f"({', '.join(sorted(expected_in))}) — patch may not route I/O correctly"
            )
            if explicit_device_type:
                errors.append(msg)
            else:
                warnings.append(msg)
        if not classes & expected_out:
            msg = (
                f"device_type={device_type}: no typical output object "
                f"({', '.join(sorted(expected_out))})"
            )
            if explicit_device_type:
                errors.append(msg)
            else:
                warnings.append(msg)

    box_ids: set[str] = set()
    for entry in spec.get("boxes") or []:
        bid = (entry.get("box") or {}).get("id")
        if bid:
            if bid in box_ids:
                errors.append(f"duplicate box id: {bid}")
            box_ids.add(bid)

    for i, entry in enumerate(spec.get("lines") or []):
        pl = entry.get("patchline") or {}
        for role in ("source", "destination"):
            end = pl.get(role)
            if not end or len(end) < 1:
                errors.append(f"lines[{i}].patchline.{role}: missing")
                continue
            ref = end[0]
            if ref not in box_ids:
                warnings.append(f"lines[{i}].patchline.{role} references unknown id {ref!r}")

    return errors, warnings


def validate_layout(spec: dict) -> tuple[list[str], list[str]]:
    import sys

    scripts = Path(__file__).resolve().parent.parent / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from check_spec_layout import check_layout  # noqa: WPS433

    return check_layout(spec)


def validate_ui(spec: dict) -> tuple[list[str], list[str]]:
    """Presentation UI checks (same rules as scripts/check_spec_ui.py)."""
    import sys

    scripts = Path(__file__).resolve().parent.parent / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from check_spec_ui import check_spec  # noqa: WPS433

    return check_spec(spec)


def validate_spec(
    spec: dict,
    *,
    check_ui: bool = True,
    include_layout: bool = True,
) -> tuple[list[str], list[str]]:
    """Full validation. Returns merged (errors, warnings)."""
    errors, warnings = validate_structure(spec)
    if check_ui:
        ui_errors, ui_warnings = validate_ui(spec)
        errors.extend(ui_errors)
        warnings.extend(ui_warnings)
    if include_layout:
        lay_errors, lay_warnings = validate_layout(spec)
        errors.extend(lay_errors)
        warnings.extend(lay_warnings)
    return errors, warnings


def require_valid_spec(spec: dict, *, check_ui: bool = True) -> None:
    errors, warnings = validate_spec(spec, check_ui=check_ui)
    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}", flush=True)
        raise ValueError("spec validation failed: " + "; ".join(errors[:5]))
