"""Offline spec verification (no Ableton Live required)."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from amxd.binary import _amxd_json_starts_at_32
from amxd.builder import build_amxd
from deploy import read_device_type_sidecar
from paths import amxd_filename_for_spec


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
