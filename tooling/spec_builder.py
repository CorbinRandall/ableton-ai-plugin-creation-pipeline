"""High-level DSL for composing Max for Live device specs.

Produces dicts identical in shape to examples/*.json — same JSON the rest of
the pipeline already consumes. Use save_spec() to write to disk.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

_TEXTCOLOR_DEFAULT = [0.811764705882353, 0.811764705882353, 0.827450980392157, 1.0]


class Device:
    def __init__(
        self,
        name: str,
        device_type: str,
        *,
        description: str = "",
        devicewidth: float = 200.0,
    ):
        self.spec: dict = {
            "name": name,
            "description": description,
            "device_type": device_type,
            "devicewidth": devicewidth,
            "openinpresentation": 1,
            "boxes": [],
            "lines": [],
        }
        self._next_id = 1
        self._patch_y = 30
        self._pres_x = 20
        self._pres_y = 40

    def _new_id(self) -> str:
        i = self._next_id
        self._next_id += 1
        return f"obj-{i}"

    def _patch_rect(self, w: float = 80, h: float = 22) -> list[float]:
        rect = [30.0, float(self._patch_y), float(w), float(h)]
        self._patch_y += h + 8
        return rect

    def _pres_rect(self, w: float = 41, h: float = 48) -> list[float]:
        rect = [float(self._pres_x), float(self._pres_y), float(w), float(h)]
        self._pres_x += w + 16
        return rect

    def audio_in(self) -> str:
        return self._add(
            {
                "maxclass": "plugin~",
                "numinlets": 1,
                "numoutlets": 1,
                "outlettype": ["signal"],
            },
            w=80,
        )

    def audio_out(self) -> str:
        return self._add(
            {"maxclass": "plugout~", "numinlets": 1, "numoutlets": 0},
            w=80,
        )

    def midi_in(self) -> str:
        return self._add(
            {
                "maxclass": "midiin",
                "numinlets": 1,
                "numoutlets": 1,
                "outlettype": [""],
            },
            w=80,
        )

    def midi_out(self) -> str:
        return self._add(
            {"maxclass": "midiout", "numinlets": 1, "numoutlets": 0},
            w=80,
        )

    def dial(
        self,
        longname: str,
        *,
        min: float = 0,
        max: float = 1,
        default: float = 0,
        shortname: str | None = None,
        unitstyle: int = 0,
    ) -> str:
        box = {
            "maxclass": "live.dial",
            "numinlets": 1,
            "numoutlets": 2,
            "outlettype": ["", "float"],
            "parameter_enable": 1,
            "presentation": 1,
            "presentation_rect": self._pres_rect(),
            "textcolor": list(_TEXTCOLOR_DEFAULT),
            "showname": 1,
            "shownumber": 1,
            "saved_attribute_attributes": {
                "valueof": {
                    "parameter_longname": longname,
                    "parameter_shortname": shortname or longname,
                    "parameter_type": 0,
                    "parameter_mmin": float(min),
                    "parameter_mmax": float(max),
                    "parameter_initial_enable": 1,
                    "parameter_initial": [float(default)],
                    "parameter_unitstyle": unitstyle,
                },
            },
        }
        return self._add(box, w=41, h=48)

    def toggle(
        self,
        longname: str,
        *,
        default: int = 0,
        shortname: str | None = None,
    ) -> str:
        box = {
            "maxclass": "live.toggle",
            "numinlets": 1,
            "numoutlets": 1,
            "outlettype": [""],
            "parameter_enable": 1,
            "presentation": 1,
            "presentation_rect": self._pres_rect(w=20, h=20),
            "textcolor": list(_TEXTCOLOR_DEFAULT),
            "saved_attribute_attributes": {
                "valueof": {
                    "parameter_longname": longname,
                    "parameter_shortname": shortname or longname,
                    "parameter_type": 1,
                    "parameter_initial_enable": 1,
                    "parameter_initial": [float(default)],
                },
            },
        }
        return self._add(box, w=20, h=20)

    def obj(
        self,
        text: str,
        *,
        maxclass: str = "newobj",
        numinlets: int = 1,
        numoutlets: int = 1,
        outlettype: list[str] | None = None,
    ) -> str:
        box: dict = {
            "maxclass": maxclass,
            "numinlets": numinlets,
            "numoutlets": numoutlets,
            "outlettype": outlettype or ["float"],
        }
        if maxclass == "newobj":
            box["text"] = text
        return self._add(box, w=max(40, len(text) * 7))

    def multiply_signal(self) -> str:
        return self._add(
            {
                "maxclass": "*~",
                "numinlets": 2,
                "numoutlets": 1,
                "outlettype": ["signal"],
            },
            w=37,
        )

    def sig(self) -> str:
        return self._add(
            {
                "maxclass": "sig~",
                "numinlets": 1,
                "numoutlets": 1,
                "outlettype": ["signal"],
            },
            w=37,
        )

    def connect(
        self,
        src: str,
        dst: str,
        *,
        src_outlet: int = 0,
        dst_inlet: int = 0,
    ) -> None:
        self.spec["lines"].append(
            {
                "patchline": {
                    "source": [src, src_outlet],
                    "destination": [dst, dst_inlet],
                }
            }
        )

    def _add(self, box: dict, *, w: float = 80, h: float = 22) -> str:
        bid = self._new_id()
        full = {"id": bid, **box}
        full.setdefault("patching_rect", self._patch_rect(w, h))
        self.spec["boxes"].append({"box": full})
        return bid

    def to_dict(self) -> dict:
        return deepcopy(self.spec)


def audio_effect(name: str, **kw) -> Device:
    return Device(name, "audio_effect", **kw)


def midi_effect(name: str, **kw) -> Device:
    return Device(name, "midi_effect", **kw)


def instrument(name: str, **kw) -> Device:
    return Device(name, "instrument", **kw)


def save_spec(device: Device | dict, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    spec = device.to_dict() if isinstance(device, Device) else device
    p.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p
