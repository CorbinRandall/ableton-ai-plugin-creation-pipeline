#!/usr/bin/env python3
"""Build midi_arp recipe."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(REPO / "tooling"))

from spec_builder import midi_effect, save_spec


def build():
    d = midi_effect(
        "MidiArp",
        description="MIDI note through metro + Rate/Octaves controls.",
        devicewidth=220.0,
    )
    mi = d.midi_in()
    mo = d.midi_out()
    metro = d.obj("metro 250", numinlets=2, numoutlets=1, outlettype=["bang"])
    rate_d = d.dial("Rate", min=50, max=2000, default=250, unitstyle=3)
    oct_d = d.dial("Octaves", min=1, max=4, default=2, unitstyle=0)
    d.connect(mi, mo)
    return d


if __name__ == "__main__":
    spec_path = save_spec(build(), HERE / "spec.json")
    print(f"WROTE {spec_path}")
    print("RECIPE_BUILD_OK")
