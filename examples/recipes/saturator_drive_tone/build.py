#!/usr/bin/env python3
"""Build saturator_drive_tone recipe."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(REPO / "tooling"))

from spec_builder import audio_effect, save_spec


def build():
    d = audio_effect(
        "SaturatorDriveTone",
        description="Drive into tanh~, Tone lowpass, dry/wet Mix.",
        devicewidth=260.0,
    )
    in_ = d.audio_in()
    drive_mul = d.multiply_signal()
    drive_sig = d.sig()
    drive_scale = d.obj("* 0.1", outlettype=["float"])
    tanh = d.obj("tanh~", numinlets=1, numoutlets=1, outlettype=["signal"])
    lores = d.obj("lores~", numinlets=2, numoutlets=1, outlettype=["signal"])
    mix = d.multiply_signal()
    dry_sig = d.sig()
    wet_sig = d.sig()
    mix_scale = d.obj("* 0.01", outlettype=["float"])
    out = d.audio_out()
    drive_d = d.dial("Drive", min=0, max=10, default=5, unitstyle=0)
    tone_d = d.dial("Tone", min=0, max=100, default=50, unitstyle=1)
    mix_d = d.dial("Mix", min=0, max=100, default=100, unitstyle=1)
    tone_scale = d.obj("* 178", outlettype=["float"])
    tone_off = d.obj("+ 200", outlettype=["float"])
    tone_sig = d.sig()
    d.connect(in_, drive_mul, dst_inlet=0)
    d.connect(drive_sig, drive_mul, dst_inlet=1)
    d.connect(drive_mul, tanh)
    d.connect(tanh, lores, dst_inlet=0)
    d.connect(in_, mix, dst_inlet=0)
    d.connect(dry_sig, mix, dst_inlet=1)
    d.connect(lores, wet_sig)
    d.connect(wet_sig, mix)
    d.connect(mix, out)
    d.connect(drive_d, drive_scale, src_outlet=1)
    d.connect(drive_scale, drive_sig)
    d.connect(tone_d, tone_scale, src_outlet=1)
    d.connect(tone_scale, tone_off)
    d.connect(tone_off, tone_sig)
    d.connect(tone_sig, lores, dst_inlet=1)
    d.connect(mix_d, mix_scale, src_outlet=1)
    d.connect(mix_scale, dry_sig)
    return d


if __name__ == "__main__":
    spec_path = save_spec(build(), HERE / "spec.json")
    print(f"WROTE {spec_path}")
    print("RECIPE_BUILD_OK")
