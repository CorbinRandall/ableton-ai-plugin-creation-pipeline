#!/usr/bin/env python3
"""Build the existing examples via spec_builder; validate via validate_spec."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tooling"))

from spec_builder import audio_effect  # noqa: E402
from spec_validate import validate_spec  # noqa: E402


def build_simple_gain():
    d = audio_effect(
        "SimpleGain",
        description="One Gain dial — dry pass-through (plugin~ → plugout~).",
        devicewidth=220.0,
    )
    in_ = d.audio_in()
    out = d.audio_out()
    d.dial("Gain", min=0, max=100, default=100, unitstyle=1)
    d.connect(in_, out)
    return d.to_dict()


def build_volume_knob():
    d = audio_effect(
        "VolumeKnob",
        description="Volume dial scales audio via *~.",
        devicewidth=200.0,
    )
    in_ = d.audio_in()
    mul = d.multiply_signal()
    s = d.sig()
    scale = d.obj("* 0.01", outlettype=["float"])
    out = d.audio_out()
    dial = d.dial("Volume", min=0, max=100, default=100, unitstyle=1)
    d.connect(in_, mul, dst_inlet=0)
    d.connect(s, mul, dst_inlet=1)
    d.connect(mul, out)
    d.connect(dial, scale, src_outlet=1)
    d.connect(scale, s)
    return d.to_dict()


def main() -> int:
    ok = True
    for fn in (build_simple_gain, build_volume_knob):
        spec = fn()
        errs, warns = validate_spec(spec)
        print(f"{spec['name']}: {len(errs)} err / {len(warns)} warn")
        for e in errs:
            print(f"  ERROR: {e}")
            ok = False
    if ok:
        print("SPEC_BUILDER_OK")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
