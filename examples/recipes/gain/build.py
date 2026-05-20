#!/usr/bin/env python3
"""Build the gain recipe spec.json next to this file."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(REPO / "tooling"))

from spec_builder import audio_effect, save_spec


def build():
    d = audio_effect("Gain", description="One Gain dial (0–100%) scaling audio via *~.")
    in_ = d.audio_in()
    mul = d.multiply_signal()
    sig = d.sig()
    scale = d.obj("* 0.01", outlettype=["float"])
    out = d.audio_out()
    dial = d.dial("Gain", min=0, max=100, default=100, unitstyle=1)
    d.connect(in_, mul, dst_inlet=0)
    d.connect(sig, mul, dst_inlet=1)
    d.connect(mul, out)
    d.connect(dial, scale, src_outlet=1)
    d.connect(scale, sig)
    return d


if __name__ == "__main__":
    spec_path = save_spec(build(), HERE / "spec.json")
    print(f"WROTE {spec_path}")
    print("RECIPE_BUILD_OK")
