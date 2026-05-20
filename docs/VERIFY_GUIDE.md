# Verify guide (`m4l_verify.py`)

End-to-end check on a **Mac or Windows** machine with **Ableton Live** running. Host scripts also run on **Linux** for build-only workflows; Live control requires Ableton’s supported OS.

Works with **any agentic IDE** or plain terminal.

**Honest scope:** this script proves MCP load + (optional) OSC tuples — **not** that the rack looks healthy or that Max has no DSP error. Read **[`VERIFICATION_TIERS.md`](VERIFICATION_TIERS.md)** for **T0–T5** and the wording agents should use.

## What it checks

1. **Build + deploy** (unless `--skip-build`) from a spec or the tutorial project — uses **`build_deploy_load(..., with_adv=True)`**, which copies a sibling **`.adv`** next to the **`.amxd`** under **`Imported/`**. Without that preset wrapper, Live often exposes only **Device On** to OSC/automation for Max devices.
2. **Browser** lists the device under **Imported/** (matches stem, **`.amxd`**, or **`.adv`**).
3. **Load** on a new track via **AbletonMCP** (MIDI or audio per `device_type`) — **`load_browser_item_by_browser_path`** prefers **`{stem}.adv`** when present, then **`{stem}.amxd`**.
4. **Alignment (T2)** — asserts **`track_kind`** matches **`device_type`** (when this pipeline creates the track) and that **`get_track_info`** device entries match **`device_type`** (including **`devices[-2]`** when the outermost device is an Effect **`rack`** — see **`tooling/m4l_pipeline.assert_loaded_device_matches_spec`**).
5. **OSC** parameter names (unless `--no-osc`) — **T3**; the script **polls for a short window** after load while Max finishes registering parameters.
6. **Optional UDP self-test (T4)** — bind **before** load; expect payload containing **`m4l_selftest`**. Use **`--selftest-default-port`** ( **`39129`**, matches the template) or **`--require-selftest-udp-port PORT`** with **[`tooling/templates/midi_effect_selftest_ping.json`](../tooling/templates/midi_effect_selftest_ping.json)** (**`udpsend`** must match).
7. **Browser polling** — **`--skip-build`** uses a shorter poll (**5 × 0.35s** typ.) so typos fail faster; override with **`--browser-poll-attempts`** / **`--browser-poll-delay`** if Live’s browser indexer is slow.

Success: **`M4L_VERIFY_OK`** · Optional **`DEVICE_SELFTEST_OK`** line when **T4** passes.

### Human rack screenshot (**T5**, macOS)

```bash
./scripts/capture_live_window.sh ~/Desktop/live_rack.png
```

Interactive window/region grab via **`screencapture -i`** — attach the image when asking an agent or teammate for **HUMAN_RACK_OK**.

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
./venv/bin/python scripts/test_verification_helpers.py
```

**Windows:**

```powershell
.\venv\Scripts\python.exe scripts\m4l_verify.py
.\venv\Scripts\python.exe scripts\m4l_verify.py --spec projects\Pipeline_Example\pipeline_example_spec.json
.\venv\Scripts\python.exe scripts\m4l_verify.py --device-type audio_effect --device-name MyFx --skip-build
.\venv\Scripts\python.exe scripts\test_verification_helpers.py
```

## Flags

| Flag | Meaning |
|------|---------|
| `--spec PATH` | Build/deploy from spec JSON (default: tutorial spec under **`projects/Pipeline_Example/`**) |
| `--build pipeline_example` | Run **`build_pipeline_example.py`** instead of **`build_deploy_load`** from **`--spec`** |
| `--device-type` | `midi_effect` \| `audio_effect` \| `instrument` (default: from spec) |
| `--device-name` | `.amxd` stem in **Imported/** (default: spec **`name`**) |
| `--expect-params` | Comma-separated name substrings (default: from spec or tutorial defaults) |
| `--skip-build` | Device already deployed (uses **faster** browser polling unless overridden) |
| `--browser-poll-attempts N` | MCP **`get_browser_items_at_path`** retries (default **5** if `--skip-build`, else **12**) |
| `--browser-poll-delay SEC` | Pause between retries (default **0.35** if `--skip-build`, else **1.0**) |
| `--no-osc` | MCP load only (**skips T3**) |
| `--require-selftest-udp-port PORT` | **T4** — UDP listener bound before load; expects **`m4l_selftest`** in payload |
| `--selftest-default-port` | Same as **`--require-selftest-udp-port 39129`** (must match template **`udpsend`**) |
| `--print-mcp-device-health` | Log **`get_device_health`** snapshot (**requires MCP patch** — see [`MCP_DEVICE_HEALTH_SPIKE.md`](MCP_DEVICE_HEALTH_SPIKE.md)) |
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

- [`VERIFICATION_TIERS.md`](VERIFICATION_TIERS.md)  
- [`AGENT_TOOLS.md`](AGENT_TOOLS.md)  
- [`scripts/m4l_ci.sh`](../scripts/m4l_ci.sh) — thin wrapper
