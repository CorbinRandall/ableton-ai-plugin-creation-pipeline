# Verify guide (`m4l_verify.py`)

End-to-end check on a **Mac or Windows** machine with **Ableton Live** running. Host scripts also run on **Linux** for build-only workflows; Live control requires Ableton’s supported OS.

Works with **any agentic IDE** or plain terminal.

## What it checks

1. **Build + deploy** (unless `--skip-build`) from a spec or the tutorial project — uses **`build_deploy_load(..., with_adv=True)`**, which copies a sibling **`.adv`** next to the **`.amxd`** under **`Imported/`**. Without that preset wrapper, Live often exposes only **Device On** to OSC/automation for Max devices.
2. **Browser** lists the device under **Imported/** (matches stem, **`.amxd`**, or **`.adv`**).
3. **Load** on a new track via **AbletonMCP** (MIDI or audio per `device_type`) — **`load_browser_item_by_browser_path`** prefers **`{stem}.adv`** when present, then **`{stem}.amxd`**.
4. **OSC** parameter names (unless `--no-osc`) — the script **polls for a short window** after load while Max finishes registering parameters.

Success: **`M4L_VERIFY_OK`**

## Prerequisites

- Live **Suite** or **Standard + Max for Live** ([`README.md`](../README.md))  
- **AbletonMCP** + **AbletonOSC** in Preferences → Link / Tempo / MIDI ([`SETUP_AUTOMATED.md`](SETUP_AUTOMATED.md))  
- **`venv/`** after `./run` or bootstrap ([`CROSS_PLATFORM.md`](CROSS_PLATFORM.md))

## Commands

**macOS / Linux** (repo root):

```bash
./venv/bin/python scripts/m4l_verify.py
./venv/bin/python scripts/m4l_verify.py --spec projects/Pipeline_Example/pipeline_example_spec.json
./venv/bin/python scripts/m4l_verify.py --device-type audio_effect --device-name MyFx --skip-build
```

**Windows:**

```powershell
.\venv\Scripts\python.exe scripts\m4l_verify.py
.\venv\Scripts\python.exe scripts\m4l_verify.py --spec projects\Pipeline_Example\pipeline_example_spec.json
.\venv\Scripts\python.exe scripts\m4l_verify.py --device-type audio_effect --device-name MyFx --skip-build
```

## Flags

| Flag | Meaning |
|------|---------|
| `--spec PATH` | Build/deploy from spec JSON (default: tutorial spec under **`projects/Pipeline_Example/`**) |
| `--build pipeline_example` | Run **`build_pipeline_example.py`** instead of **`build_deploy_load`** from **`--spec`** |
| `--device-type` | `midi_effect` \| `audio_effect` \| `instrument` (default: from spec) |
| `--device-name` | `.amxd` stem in **Imported/** (default: spec **`name`**) |
| `--expect-params` | Comma-separated name substrings (default: from spec or tutorial defaults) |
| `--skip-build` | Device already deployed |
| `--no-osc` | MCP load only |
| `--no-cleanup` | Leave track/devices |

## Parameter sweep (after load)

Find track/device indices from verify output or `m4l_pipeline.py info`.

```bash
./venv/bin/python scripts/m4l_parameter_sweep.py --track 0 --device 0 --list-only
./venv/bin/python scripts/m4l_parameter_sweep.py --track 0 --device 0 --set-index 0 --set-value 0.5
```

Marker: **`M4L_PARAM_SWEEP_OK`**

## Audio (manual)

OSC cannot prove sound quality. See **[`AUDIO_SMOKE_TEST.md`](AUDIO_SMOKE_TEST.md)**.

## Related

- [`AGENT_TOOLS.md`](AGENT_TOOLS.md)  
- [`scripts/m4l_ci.sh`](../scripts/m4l_ci.sh) — thin wrapper
