"""Surgical UI edits on existing .amxd files."""

from __future__ import annotations

import json
import re
import shutil
import struct
import sys
from copy import deepcopy
from pathlib import Path

from amxd.binary import _amxd_json_starts_at_32, _extract_amxd_parts, _pack_amxd
from deploy import sidecar_path_for_artifact


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
