#!/usr/bin/env python3
"""Build delay_feedback recipe."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(REPO / "tooling"))

from spec_builder import audio_effect, save_spec


def build():
    d = audio_effect(
        "DelayFeedback",
        description="Time + Feedback + Mix delay using tapin~/tapout~.",
        devicewidth=260.0,
    )
    in_ = d.audio_in()
    tapin = d.obj("tapin~ 2000", numinlets=1, numoutlets=1, outlettype=["signal"])
    tapout = d.obj("tapout~ 500", numinlets=1, numoutlets=1, outlettype=["signal"])
    fb = d.multiply_signal()
    fb_sig = d.sig()
    mix = d.multiply_signal()
    dry_sig = d.sig()
    wet_sig = d.sig()
    out = d.audio_out()
    time_d = d.dial("Time", min=1, max=2000, default=500, unitstyle=3)
    fb_d = d.dial("Feedback", min=0, max=95, default=30, unitstyle=1)
    mix_d = d.dial("Mix", min=0, max=100, default=50, unitstyle=1)
    fb_scale = d.obj("* 0.01", outlettype=["float"])
    mix_scale = d.obj("* 0.01", outlettype=["float"])
    d.connect(in_, tapin)
    d.connect(tapin, tapout)
    d.connect(tapout, fb, dst_inlet=0)
    d.connect(fb_sig, fb, dst_inlet=1)
    d.connect(fb, tapin)
    d.connect(in_, mix, dst_inlet=0)
    d.connect(dry_sig, mix, dst_inlet=1)
    d.connect(tapout, wet_sig)
    d.connect(wet_sig, mix)
    d.connect(mix, out)
    d.connect(fb_d, fb_scale, src_outlet=1)
    d.connect(fb_scale, fb_sig)
    d.connect(mix_d, mix_scale, src_outlet=1)
    d.connect(mix_scale, dry_sig)
    return d


if __name__ == "__main__":
    spec_path = save_spec(build(), HERE / "spec.json")
    print(f"WROTE {spec_path}")
    print("RECIPE_BUILD_OK")
