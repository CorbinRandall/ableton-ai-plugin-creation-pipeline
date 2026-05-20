#!/usr/bin/env python3
"""Build mono_synth instrument recipe."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(REPO / "tooling"))

from spec_builder import instrument, save_spec


def build():
    d = instrument(
        "MonoSynth",
        description="One-voice cycle~ with Pitch dial.",
        devicewidth=220.0,
    )
    d.obj("in", maxclass="in", numinlets=1, numoutlets=1, outlettype=["signal"])
    osc = d.obj("cycle~ 440", numinlets=2, numoutlets=1, outlettype=["signal"])
    out = d.audio_out()
    pitch = d.dial("Pitch", min=20, max=127, default=60, unitstyle=0)
    mtof = d.obj("mtof", outlettype=["float"])
    sig = d.sig()
    d.connect(osc, out)
    d.connect(pitch, mtof, src_outlet=1)
    d.connect(mtof, sig)
    d.connect(sig, osc, dst_inlet=0)
    return d


if __name__ == "__main__":
    spec_path = save_spec(build(), HERE / "spec.json")
    print(f"WROTE {spec_path}")
    print("RECIPE_BUILD_OK")
