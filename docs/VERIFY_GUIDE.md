# Verify guide (`m4l_verify.py`)

End-to-end check that your **agentic IDE + Ableton** stack can:

1. **Build** (unless `--skip-build`) — tutorial **`Pipeline_Example`** or **`--spec`** via **`build_deploy_load(..., with_adv=True)`**, which copies a sibling **`.adv`** next to the **`.amxd`** under **`Imported/`**. Without that preset wrapper, Live often exposes only **Device On** to OSC/automation for Max devices.
2. **Load** in Live via **AbletonMCP** — **`load_browser_item_by_browser_path`** prefers **`{stem}.adv`** when present, then **`{stem}.amxd`**.
3. **Read** parameter names via **AbletonOSC** (unless `--no-osc`) — the script **polls for a short window** after load while Max finishes registering parameters.

## Prereqs

- Ableton Live running (**Suite**, or **Standard + Max for Live add-on** — Lite / Intro editions do **not** include Max for Live; see **`README.md`**)
- **AbletonMCP** + **AbletonOSC** installed and enabled (bootstrap: **`./bootstrap.sh`**, then Preferences → Link, Tempo & MIDI → Control Surfaces — see **`docs/SETUP_AUTOMATED.md`**)  
- Host Python: **`./venv/bin/python`** after bootstrap (or `pip install python-osc` in any env)  
- This repo’s root on disk; `tooling/m4l_pipeline.py` deploys under **`$ABLETON_HOME/User Library`** (default macOS **`~/Music/Ableton`**, Windows **`~/Documents/Ableton`**)

## Commands

From the **root of this repository** (recommended after bootstrap):

```bash
./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py
./venv/bin/python scripts/m4l_verify.py
./venv/bin/python scripts/m4l_verify.py --spec projects/Pipeline_Example/pipeline_example_spec.json
```

Or with a system interpreter:

```bash
python3 projects/Pipeline_Example/build_pipeline_example.py
python3 scripts/m4l_verify.py
python3 scripts/m4l_verify.py --spec projects/Pipeline_Example/pipeline_example_spec.json
```

Success ends with **`M4L_VERIFY_OK`**.

## Flags

| Flag | Meaning |
|------|--------|
| `--spec PATH` | Build/deploy from this JSON (default: tutorial spec under **`projects/Pipeline_Example/`**) |
| `--build pipeline_example` | Run the tutorial **`build_pipeline_example.py`** instead of **`build_deploy_load` from --spec** |
| `--device-type` | `midi_effect` \| `audio_effect` \| `instrument` (default: from spec) |
| `--skip-build` | Do not run the builder; device must already be under **`Imported/`** |
| `--no-osc` | MCP load only (no UDP parameter read) |
| `--device-name` | `.amxd` stem in **`Imported/`** (default: spec **`name`**) |
| `--expect-params` | Override expected parameter **name** substrings (comma-separated) |
| `--no-cleanup` | Leave track/devices on the session |
