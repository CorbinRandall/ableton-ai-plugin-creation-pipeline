# Audio smoke test (manual)

Automated CI **cannot** judge sound quality without Ableton on the runner. Use this **manual** checklist on a **Mac or Windows** machine with Live open after **`M4L_VERIFY_OK`** or a successful **`m4l_pipeline.py all`**.

Works with any agentic IDE or no IDE — headphones or monitors required.

## Prerequisites

- Device loaded on a track (**MIDI** or **audio** per `device_type`)
- **AbletonOSC** + **AbletonMCP** enabled
- Optional: **`m4l_parameter_sweep.py`** to exercise parameters before listening

## MIDI effect

1. Create or use a **MIDI track** with the device.
2. Drop a simple MIDI clip (one note or chord loop).
3. Confirm **MIDI flows** (meter on track moves).
4. Toggle each **`live.*`** control — hear or see parameter change if device processes MIDI.
5. Bypass device — audio/MIDI path should change predictably.

## Audio effect

1. **Audio track** with tone source (other track, external input, or test tone device).
2. Confirm **audio meter** on track with device on/off.
3. Sweep controls via UI or:

```bash
# macOS/Linux
./venv/bin/python scripts/m4l_parameter_sweep.py --track N --device D --list-only

# Windows
.\venv\Scripts\python.exe scripts\m4l_parameter_sweep.py --track N --device D --list-only
```

4. Set one parameter (example index 0):

```bash
./venv/bin/python scripts/m4l_parameter_sweep.py --track N --device D --set-index 0 --set-value 0.25
```

## Instrument

1. MIDI clip → expect **audio output** on instrument track.
2. Check **no clipping** at default parameter values.
3. Note CPU — heavy patches may need freeze/track freeze in Live.

## Pass criteria (you decide)

| Check | Pass? |
|-------|-------|
| No silence when signal expected | |
| Parameters affect sound or level | |
| No clicks when toggling **Device On** | |
| Presentation UI matches audible controls | |

## Future automation (Phase 2+)

Possible later: short bounce via Live export, level meter via OSC, or scripted test clips. Tracked in [`ROADMAP.md`](ROADMAP.md). Until then, this doc is the source of truth.

## Related

- [`VERIFY_GUIDE.md`](VERIFY_GUIDE.md) — MCP + OSC automated verify
- [`AGENT_TOOLS.md`](AGENT_TOOLS.md) — command reference
