#!/usr/bin/env python3
"""Build simple_lfo tremolo recipe."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(REPO / "tooling"))

from spec_builder import audio_effect, save_spec


def build():
    d = audio_effect(
        "SimpleLFO",
        description="cycle~ LFO tremolo — Rate and Depth scale *~ on audio path.",
        devicewidth=220.0,
    )
    in_ = d.audio_in()
    mul = d.multiply_signal()
    lfo = d.obj("cycle~ 1", numinlets=2, numoutlets=1, outlettype=["signal"])
    depth_mul = d.multiply_signal()
    depth_sig = d.sig()
    lfo_sig = d.sig()
    out = d.audio_out()
    rate_d = d.dial("Rate", min=0.1, max=20, default=2, unitstyle=0)
    depth_d = d.dial("Depth", min=0, max=100, default=50, unitstyle=1)
    depth_scale = d.obj("* 0.01", outlettype=["float"])
    d.connect(in_, mul, dst_inlet=0)
    d.connect(lfo_sig, mul, dst_inlet=1)
    d.connect(mul, out)
    d.connect(lfo, depth_mul, dst_inlet=0)
    d.connect(depth_sig, depth_mul, dst_inlet=1)
    d.connect(depth_mul, lfo_sig)
    d.connect(depth_d, depth_scale, src_outlet=1)
    d.connect(depth_scale, depth_sig)
    return d


if __name__ == "__main__":
    spec_path = save_spec(build(), HERE / "spec.json")
    print(f"WROTE {spec_path}")
    print("RECIPE_BUILD_OK")
