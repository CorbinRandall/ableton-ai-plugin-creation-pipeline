"""Low-level .amxd binary parse/pack helpers."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from paths import reference_amxd_path


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
