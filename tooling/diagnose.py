"""Pattern-match Max/AbletonMCP error text to recommended fixes."""

from __future__ import annotations

import re

PATTERNS: list[tuple[str, str]] = [
    (
        r"createdevice.*error 6",
        "Donor/header bytes wrong. Confirm tooling/donors/<type>.amxd device-type marker "
        "(8–11: aaaa/mmmm/iiii). See HANDOFF.md bugs 1B, 2.",
    ),
    (
        r"does not contain a Max patch of type 'Max MIDI Effect'",
        "Audio-type donor used for a MIDI build. Confirm tooling/donors/midi_effect.amxd has 'mmmm' marker.",
    ),
    (
        r"Unknown command.*create_audio_track",
        "AbletonMCP not patched. Run scripts/install_remote_scripts.py then FULLY QUIT and reopen Live.",
    ),
    (
        r"Unknown command.*get_device_health",
        "MCP patch missing get_device_health. Same fix as create_audio_track.",
    ),
    (
        r"Timed out.*9877",
        "AbletonMCP control surface not enabled. In Live → Preferences → Link/Tempo/MIDI → "
        "Control Surface: AbletonMCP. Then quit + reopen.",
    ),
    (
        r"AbletonOSC.*not responding",
        "AbletonOSC control surface not enabled (UDP 11000). Enable in Live preferences.",
    ),
    (
        r"no presentation UI boxes found",
        "Spec has parameters but no presentation_rect. Use spec_builder which auto-sets these, "
        "or add presentation:1 + presentation_rect on each control.",
    ),
    (
        r"parameter_longname.*missing|required.*parameter_longname",
        "live.dial/toggle/slider missing parameter_longname in saved_attribute_attributes.valueof. "
        "Use spec_builder.dial(...) which sets it.",
    ),
    (
        r"duplicate box id",
        "Two boxes share the same id. spec_builder auto-assigns unique ids.",
    ),
    (
        r"references unknown id|unknown id",
        "patchline source/destination references a box id that doesn't exist. Check the connect() args.",
    ),
]


def diagnose(error_text: str) -> dict:
    matches = []
    for pattern, fix in PATTERNS:
        if re.search(pattern, error_text, re.IGNORECASE):
            matches.append({"pattern": pattern, "fix": fix})
    return {"matches": matches, "n": len(matches)}


if __name__ == "__main__":
    import json
    import sys

    text = sys.stdin.read()
    print(json.dumps(diagnose(text), indent=2))
