#!/usr/bin/env python3
"""Stem export prep — disable mixing plugins, keep character/tone plugins enabled.

Usage:
    # Show what would change (dry run):
    python scripts/stem_prep.py scan

    # Disable all mixing plugins (prep for dry export):
    python scripts/stem_prep.py dry

    # Re-enable all mixing plugins (restore for wet export):
    python scripts/stem_prep.py wet

    # Show current state of all devices:
    python scripts/stem_prep.py status

Classification logic:
    KEEP ON (character/tone):
        - Instruments (Kontakt, Drum Rack, Simpler, Operator, Wavetable, etc.)
        - Auto-Tune / pitch correction (Waves Tune, Auto-Tune, etc.)
        - Amp/cabinet emulators (Cabinet, Amp, Guitar Rig, etc.)
        - Synths and samplers

    TURN OFF (mixing/processing):
        - EQ (EQ Eight, Pro-Q, etc.)
        - Compressors / limiters / gates
        - Reverb / delay
        - Utility / gain plugins
        - Vocal processing chains (Nectar, VocalRider, RVox, etc.)
        - Saturation / distortion (mixing context)
        - Stereo imaging / wideners
"""
from __future__ import annotations

import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.live_osc_helpers import _osc_request, osc_device_parameter_names

# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

# Substrings matched case-insensitively against device name.
# Order: first match wins.  More specific patterns before broad ones.

CHARACTER_PATTERNS: list[str] = [
    # Pitch correction / auto-tune
    "tune",
    "auto-tune",
    "autotune",
    "pitcher",
    "melodyne",
    # Amp / cabinet emulation
    "cabinet",
    "cab",
    "amp",
    "guitar rig",
    "amplitube",
    "helix",
    "archetype",
    "neural",
    "bias",
    "line 6",
    "kemper",
    # Instruments / samplers / synths — always keep
    "kontakt",
    "drum rack",
    "drum kit",
    "pad kit",
    "simpler",
    "sampler",
    "operator",
    "wavetable",
    "analog",
    "collision",
    "tension",
    "electric",
    "serum",
    "vital",
    "massive",
    "omnisphere",
    "pigments",
    "diva",
    "repro",
    "phase plant",
    "modo bass",
    "modo drum",
    "wurli",
    "rhodes",
    "keyscape",
    "piano",
    "tambourin",
    "instrument rack",
    # Ableton instruments
    "drift",
    "meld",
]

MIXING_PATTERNS: list[str] = [
    # Racks (user groups mixing plugins into racks for bulk toggle)
    "audio effect rack",
    # EQ
    "eq",
    "equalizer",
    "pro-q",
    "channelstrip",
    "channel strip",
    # Dynamics
    "compressor",
    "compress",
    "limiter",
    "gate",
    "expander",
    "glue",
    "multiband",
    "opto",
    "rvox",
    "vocal rider",
    "vocalrider",
    "cla bass",
    "cla vocal",
    "cla guitar",
    "ssl",
    "api",
    "dbx",
    "1176",
    "la-2a",
    "la2a",
    "fairchild",
    # Reverb / delay
    "reverb",
    "delay",
    "echo",
    "plate",
    "room",
    "hall",
    "spring",
    "convolution",
    "valhalla",
    "fabfilter pro-r",
    # Vocal processing suites
    "nectar",
    "vocal synth",
    # Saturation / distortion (mixing context)
    "saturator",
    "overdrive",
    "decapitator",
    "trash",
    "saturn",
    # Utility
    "utility",
    "gain",
    "spectrum",
    "analyzer",
    "meter",
    "loudness",
    # Stereo / imaging
    "stereo",
    "imager",
    "wider",
    "ozone",
    "izotope",
    # Distance / spatial (mixing)
    "ml.distance",
    "distance",
    # Misc mixing
    "de-esser",
    "deesser",
    "de-ess",
    "soothe",
    "smooth operator",
    "eiosis",
    "autopan",
    "auto pan",
    "chorus",
    "flanger",
    "phaser",
    "filter",
    "erosion",
    "redux",
    "vinyl",
    "corpus",
    "resonator",
    "frequency shifter",
    "ring modulator",
    "beat repeat",
    "looper",
    "grain",
]


def classify_device(name: str) -> str:
    """Return 'character', 'mixing', or 'unknown'."""
    low = name.lower()
    for pat in CHARACTER_PATTERNS:
        if pat in low:
            return "character"
    for pat in MIXING_PATTERNS:
        if pat in low:
            return "mixing"
    return "unknown"


# ---------------------------------------------------------------------------
# Live interaction
# ---------------------------------------------------------------------------

def get_all_tracks() -> list[dict]:
    """Scan Live session and return structured track/device info."""
    num_tracks_resp = _osc_request("/live/song/get/num_tracks", [], wait=3)
    num_tracks = num_tracks_resp[1] if len(num_tracks_resp) > 1 else num_tracks_resp[0]

    tracks = []
    for t in range(num_tracks):
        name_resp = _osc_request("/live/track/get/name", [t], wait=2)
        track_name = name_resp[1] if len(name_resp) > 1 else name_resp[0]

        nd_resp = _osc_request("/live/track/get/num_devices", [t], wait=2)
        num_devices = nd_resp[1] if len(nd_resp) > 1 else nd_resp[0]

        devices = []
        for d in range(num_devices):
            dname_resp = _osc_request("/live/device/get/name", [t, d], wait=2)
            device_name = dname_resp[2] if len(dname_resp) > 2 else dname_resp[-1]

            params = osc_device_parameter_names(t, d, wait=2)
            is_on = None
            if params and params[0] == "Device On":
                from scripts.live_osc_helpers import osc_device_parameter_values
                vals = osc_device_parameter_values(t, d, wait=2)
                is_on = bool(vals[0]) if vals else None

            classification = classify_device(str(device_name))

            devices.append({
                "index": d,
                "name": str(device_name),
                "classification": classification,
                "is_on": is_on,
            })

        tracks.append({
            "index": t,
            "name": str(track_name),
            "devices": devices,
        })

    return tracks


_osc_sock = None

def _osc_fire(addr: str, args: list) -> None:
    """Send an OSC message fire-and-forget (no reply expected)."""
    import struct as _st
    global _osc_sock
    if _osc_sock is None:
        import socket
        _osc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def pad(s: str) -> bytes:
        b = s.encode("utf-8") + b"\x00"
        return b + b"\x00" * ((4 - len(b) % 4) % 4)

    msg = pad(addr)
    type_tag = ","
    arg_data = b""
    for a in args:
        if isinstance(a, int):
            type_tag += "i"
            arg_data += _st.pack(">i", a)
        elif isinstance(a, float):
            type_tag += "f"
            arg_data += _st.pack(">f", a)
    msg += pad(type_tag) + arg_data
    _osc_sock.sendto(msg, ("127.0.0.1", 11000))


def set_device_on(track: int, device: int, on: bool) -> None:
    import time
    _osc_fire("/live/device/set/parameter/value",
              [track, device, 0, 1.0 if on else 0.0])
    time.sleep(0.03)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_scan(tracks: list[dict]) -> None:
    """Print classification for every device — no changes made."""
    print("=" * 70)
    print("STEM PREP SCAN — device classification (no changes)")
    print("=" * 70)
    unknowns = []
    for t in tracks:
        if not t["devices"]:
            continue
        print(f"\n  Track {t['index']}: {t['name']}")
        for d in t["devices"]:
            tag = d["classification"].upper()
            state = "ON" if d["is_on"] else "OFF" if d["is_on"] is not None else "?"
            marker = ""
            if d["classification"] == "mixing":
                marker = "  ← will disable for dry"
            elif d["classification"] == "unknown":
                marker = "  ← UNKNOWN — review needed"
                unknowns.append(f"  Track {t['index']} ({t['name']}) → {d['name']}")
            print(f"    [{state}] {d['name']:30s}  {tag}{marker}")

    if unknowns:
        print(f"\n⚠  {len(unknowns)} unclassified device(s) — will be LEFT ALONE:")
        for u in unknowns:
            print(u)
        print("  Add patterns to CHARACTER_PATTERNS or MIXING_PATTERNS in stem_prep.py")
    print()


def cmd_dry(tracks: list[dict]) -> None:
    """Disable all mixing-classified devices."""
    print("STEM PREP → DRY (disabling mixing plugins)")
    count = 0
    for t in tracks:
        for d in t["devices"]:
            if d["classification"] == "mixing" and d["is_on"]:
                set_device_on(t["index"], d["index"], False)
                print(f"  OFF  Track {t['index']} ({t['name']}) → {d['name']}")
                count += 1
    print(f"\nDisabled {count} mixing device(s). Character/instrument devices untouched.")
    print("Export your dry stems now, then run:  python scripts/stem_prep.py wet")


def cmd_wet(tracks: list[dict]) -> None:
    """Re-enable all mixing-classified devices."""
    print("STEM PREP → WET (re-enabling mixing plugins)")
    count = 0
    for t in tracks:
        for d in t["devices"]:
            if d["classification"] == "mixing" and not d["is_on"]:
                set_device_on(t["index"], d["index"], True)
                print(f"  ON   Track {t['index']} ({t['name']}) → {d['name']}")
                count += 1
    print(f"\nRe-enabled {count} mixing device(s).")


def cmd_status(tracks: list[dict]) -> None:
    """Show current on/off state of every device."""
    print("=" * 70)
    print("DEVICE STATUS")
    print("=" * 70)
    for t in tracks:
        if not t["devices"]:
            continue
        print(f"\n  Track {t['index']}: {t['name']}")
        for d in t["devices"]:
            state = "ON" if d["is_on"] else "OFF" if d["is_on"] is not None else "?"
            tag = d["classification"][0].upper()  # C/M/U
            print(f"    [{state}] [{tag}] {d['name']}")


COMMANDS = {
    "scan": cmd_scan,
    "dry": cmd_dry,
    "wet": cmd_wet,
    "status": cmd_status,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python scripts/stem_prep.py <{'|'.join(COMMANDS)}>")
        print("  scan   — show classification (no changes)")
        print("  dry    — disable mixing plugins for dry export")
        print("  wet    — re-enable mixing plugins")
        print("  status — show current on/off state")
        sys.exit(1)

    tracks = get_all_tracks()
    COMMANDS[sys.argv[1]](tracks)


if __name__ == "__main__":
    main()
