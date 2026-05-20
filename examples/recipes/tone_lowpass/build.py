#!/usr/bin/env python3
"""Build tone_lowpass recipe — Tone dial scales lores~ cutoff."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(REPO / "tooling"))

from spec_builder import audio_effect, save_spec


def build():
    d = audio_effect(
        "ToneLowpass",
        description="Tone knob → one-pole lores~ cutoff (200–18000 Hz).",
        devicewidth=220.0,
    )
    in_ = d.audio_in()
    lores = d.obj("lores~", numinlets=2, numoutlets=1, outlettype=["signal"])
    out = d.audio_out()
    tone = d.dial("Tone", min=0, max=100, default=50, unitstyle=1)
    scale = d.obj("* 178", outlettype=["float"])
    offset = d.obj("+ 200", outlettype=["float"])
    sig = d.sig()
    d.connect(in_, lores, dst_inlet=0)
    d.connect(lores, out)
    d.connect(tone, scale, src_outlet=1)
    d.connect(scale, offset)
    d.connect(offset, sig)
    d.connect(sig, lores, dst_inlet=1)
    return d


if __name__ == "__main__":
    spec_path = save_spec(build(), HERE / "spec.json")
    print(f"WROTE {spec_path}")
    print("RECIPE_BUILD_OK")
