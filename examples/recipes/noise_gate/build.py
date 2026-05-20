#!/usr/bin/env python3
"""Build noise_gate recipe."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(REPO / "tooling"))

from spec_builder import audio_effect, save_spec


def build():
    d = audio_effect(
        "NoiseGate",
        description="Threshold + Attack + Release gate shell using live.gain~.",
        devicewidth=280.0,
    )
    in_ = d.audio_in()
    gate = d.obj("live.gain~", numinlets=2, numoutlets=1, outlettype=["signal"])
    out = d.audio_out()
    thresh = d.dial("Threshold", min=-60, max=0, default=-24, unitstyle=4)
    attack = d.dial("Attack", min=0, max=500, default=10, unitstyle=3)
    release = d.dial("Release", min=0, max=2000, default=100, unitstyle=3)
    d.connect(in_, gate, dst_inlet=0)
    d.connect(gate, out)
    return d


if __name__ == "__main__":
    spec_path = save_spec(build(), HERE / "spec.json")
    print(f"WROTE {spec_path}")
    print("RECIPE_BUILD_OK")
