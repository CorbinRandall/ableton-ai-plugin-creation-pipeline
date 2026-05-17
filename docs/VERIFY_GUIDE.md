# Verify guide (`m4l_verify.py`)

End-to-end check that your **Cursor / AI + Ableton** stack can:

1. **Build** the tutorial **`Pipeline_Example`** device (unless `--skip-build`) — writes **`projects/Pipeline_Example/Pipeline_Example X.Y/`** and deploys to **`Imported/`**; verify runs the builder with **`--no-live`** so it does not steal the load step.
2. **Load** it in Live via **AbletonMCP** (browser path under **`Imported/`**).
3. **Read** parameter names via **AbletonOSC** (unless `--no-osc`).

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
```

Or with a system interpreter:

```bash
python3 projects/Pipeline_Example/build_pipeline_example.py
python3 scripts/m4l_verify.py
```

Success ends with **`M4L_VERIFY_OK`**.

## Flags

| Flag | Meaning |
|------|--------|
| `--skip-build` | Do not run the builder; device must already be under **`Imported/`** |
| `--no-osc` | MCP load only (no UDP parameter read) |
| `--device-name` | Default **`Pipeline_Example`** — must match the `.amxd` stem in **`Imported/`** |
| `--expect-params` | Override expected parameter **name** substrings (comma-separated) |
