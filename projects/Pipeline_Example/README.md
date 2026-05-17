# Pipeline Example (tutorial device)

A **minimal** Max for Live **MIDI effect** used to learn this repo’s workflow:

- JSON spec → **`m4l_pipeline.build_deploy_load`** (or **`build_amxd`**) → **`.amxd`**
- **Backend** = patch wires + `live.*` parameters (MCP/OSC verify this). **Frontend** = Presentation layer (`presentation` + `presentation_rect` on each control). If the rack face is **blank**, read **[`docs/M4L_FRONTEND_AND_BACKEND.md`](../../docs/M4L_FRONTEND_AND_BACKEND.md)**.
- Each build gets a **version folder**: **`projects/Pipeline_Example/Pipeline_Example 1.1/`**, **`1.2/`**, … with **`spec.json`**, **`VERSION.txt`**, and the device binary (**gitignored** — present locally after you build; not committed upstream).
- Copy into **User Library/…/Max MIDI Effect/Imported/** (done automatically for this example) + **load on a new track** in Live via AbletonMCP (unless **`--no-live`**). Track type follows **`device_type`** in the spec (`midi_effect` → new MIDI track; `audio_effect` → new audio track after bootstrap patch).

You need Live **Suite** or **Standard + Max for Live** to run this device (**README** → *Max for Live and your Ableton edition*).

## Build + load (recommended)

From the **cloned `m4l-pipeline-public` repo root** (after **`./bootstrap.sh`** so **`venv`** exists), with **Live open** and **AbletonMCP** enabled:

```bash
./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py
```

Artifacts-only (no Live / MCP):

```bash
./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py --no-live
```

Load onto an existing track instead of creating a new one:

```bash
./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py --track 0
```

## Verify (AbletonOSC + MCP checks)

From repo root (this runs the builder with **`--no-live`**, then its **own** load test):

```bash
./venv/bin/python scripts/m4l_verify.py --device-name Pipeline_Example --build pipeline_example
```

See **`docs/SETUP_AUTOMATED.md`** if remote scripts are not installed yet.

**UI contrast:** if parameter names look invisible on the device face, see **[`docs/M4L_FRONTEND_AND_BACKEND.md`](../../docs/M4L_FRONTEND_AND_BACKEND.md)** (`textcolor`). Preflight: `./venv/bin/python scripts/check_spec_ui.py projects/Pipeline_Example/pipeline_example_spec.json`

**First-time / AI IDE:** **`docs/AGENT_IDE_BEGINNER_GUIDE.md`**

Open **`Pipeline_Example + Tooling.code-workspace`** (repo root + this project folder) in Cursor.

## Files

| File | Role |
|------|------|
| **`pipeline_example_spec.json`** | Device graph (`midiin` → `midiout` + a few `live.*` parameters) |
| **`build_pipeline_example.py`** | Versioned build + deploy + optional MCP load |
| **`*/*.amxd`** (under version folders) | Generated on build (**`.gitignore`**); version **`Pipeline_Example */`** dirs are ignored too |

**Your own plugins:** use **`projects/workspace/`** + **`M4L_PROJECTS_PREFIX=workspace`** — see **[`../workspace/README.md`](../workspace/README.md)**.

