# First-time setup with an AI coding assistant (Cursor / similar)

This guide is for people who have **never** used an “agentic” IDE before. You will clone this repo, open it in a desktop editor that can run commands for you, and end with **Ableton Live** loading your Max for Live device **on a new track** without dragging files from Finder or Explorer.

## What you must already have

1. **A normal Ableton Live install** that you have **opened at least once** on this user account (so prefs and `User Library` folders exist). This is **not** a “net new” Ableton install straight from the downloader with zero launches — run Live once, then quit, before you rely on template or Library steps from [`SETUP_AUTOMATED.md`](SETUP_AUTOMATED.md).
2. **Suite**, or **Standard + Max for Live add-on** — not Lite/Intro for building/running M4L devices ([`README.md`](../README.md) → *Max for Live and your Ableton edition*).
3. **Internet** for the first bootstrap (downloads AbletonOSC + AbletonMCP archives, and may install Python).

## One-time pipeline bootstrap (terminal or agent)

From the **cloned folder root** (`m4l-pipeline-public`):

- **macOS / Linux:**  
  `chmod +x bootstrap.sh` then `./bootstrap.sh`
- **Windows (PowerShell):**  
  `powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1`

What this does (high level):

- Ensures **Python 3.10+** (Homebrew on macOS, `winget` on Windows when needed).
- Creates **`venv/`** and installs **`python-osc`**.
- Installs **AbletonOSC** + **AbletonMCP** remote scripts into your **User Library**.
- Optionally sets default template / `Library.cfg` (see [`SETUP_AUTOMATED.md`](SETUP_AUTOMATED.md)).
- **Does not** auto-select **Control Surfaces** — you still do that once in Live (below).

## Ableton checklist (manual but quick)

1. **Quit Live completely** (Cmd+Q / fully exit), then reopen.
2. **Preferences → Link / Tempo / MIDI**
   - **Control Surface** → **AbletonOSC** (inputs/outputs blank; port **11000**).
   - Second slot → **AbletonMCP** if you use MCP (TCP **9877**).

If TCP `9877` refuses connections, Live is closed or **AbletonMCP** is not selected — fix that before asking an agent to “load the device”.

## Verify the stack

With **Live running** and both surfaces enabled, from repo root:

```bash
./venv/bin/python scripts/verify_setup.py --wait-mcp 120
```

You want **`M4L_SETUP_VERIFY_OK`**. If something fails, read the message and [`SETUP_AUTOMATED.md`](SETUP_AUTOMATED.md) → Troubleshooting.

## Using Cursor (or similar) as a beginner

1. **File → Open Folder** and choose the **`m4l-pipeline-public`** directory (the repo root, not only `projects/`).
2. Open the **Chat / Agent** panel (name varies by product).
3. Say something concrete, for example:
   - *“Run `./bootstrap.sh` from the repo root and show me the output.”*
   - *“Run `./venv/bin/python scripts/verify_setup.py --wait-mcp 120` with Live open.”*
   - *“Run `./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py` with Live open.”*

The assistant should **run commands for you** and paste results. If it only “suggests” commands, look for a **“Run”** or **terminal** action in the UI, or paste the command into the integrated terminal yourself.

**Safety:** Don’t paste secrets (passwords, API keys) into chat. This repo does not need them for the tutorial pipeline.

## Building a plugin: versions + where files go

Every time you run a **full** tutorial build with Live integration, the pipeline:

- Creates **`projects/<PluginSlug>/<Plugin Name> X.Y/`** (e.g. **`projects/Pipeline_Example/Pipeline_Example 1.3/`**).
- Writes **`spec.json`**, **`VERSION.txt`**, and the **`.amxd`** into that folder (version numbers **increment automatically**: 1.1 → 1.2 → …).
- Copies the same **`.amxd`** into **User Library → … → Max … Effect → Imported/** so the browser sees it.
- By default, asks AbletonMCP to **create a new track** (MIDI for ``midi_effect`` / ``instrument``, audio for ``audio_effect``) and **load** the device there — you should **not** need to drag the file in. Live does not guess MIDI vs audio from the raw ``.amxd``; the spec’s ``device_type`` must match how the device is built.

**Own plugins:** set **`export M4L_PROJECTS_PREFIX=workspace`** so version folders land under **`projects/workspace/`** (gitignored; safe across **`git pull`**). The tutorial script **`build_pipeline_example.py`** still writes under **`projects/Pipeline_Example/`** only.

If Live is closed or MCP is down, use **`--no-live`** on the example builder; you still get the versioned folder + deploy, but no automatic track load.

## Common “gotchas” (real bugs / limitations)

| Symptom | Likely cause |
|--------|----------------|
| Device loads but **UI is blank** (Presentation empty) | Spec only had `patching_rect`, not **`presentation` / `presentation_rect`** — see **[`M4L_FRONTEND_AND_BACKEND.md`](M4L_FRONTEND_AND_BACKEND.md)**; rebuild after fixing spec |
| Knobs visible but **labels/values unreadable** (dark-on-dark) | Set **`textcolor`** on `live.dial` / `live.toggle`, or rebuild with current **`m4l_pipeline`** (`_apply_live_ui_contrast`) |
| MCP connection refused | Live not running, or **AbletonMCP** not enabled in MIDI prefs, or wrong Live instance |
| `/live/test` / OSC failures | **AbletonOSC** not enabled, or another app bound UDP **11001** |
| Browser never lists the device | Deploy path wrong, or Live still indexing — wait a few seconds; script retries |
| “Unknown command” in very old MCP | Use the **AbletonMCP** version installed by this repo’s bootstrap (ZIP from GitHub **main**) |
| Audio device landed on wrong / MIDI-only track | Set ``device_type`` to ``audio_effect`` and run bootstrap (patches AbletonMCP ``create_audio_track``), or ``./venv/bin/python scripts/install_remote_scripts.py --patch-mcp-only`` |
| Template / `Library.cfg` step skipped | You never launched Live on this account — open Live once, quit, rerun bootstrap or [`install_default_template.py`](../scripts/install_default_template.py) |

## What to do after the tutorial

- Change **`pipeline_example_spec.json`** or duplicate **`Pipeline_Example`** into **`projects/workspace/MyPlugin/`** (recommended: set **`M4L_PROJECTS_PREFIX=workspace`** — see **[`projects/workspace/README.md`](../projects/workspace/README.md)**).
- **`m4l_pipeline`** needs a header **donor** `.amxd` on disk (`M4L_REFERENCE_AMXD` or default under Imported — see **[`REFERENCE_HEADER_AND_IMPORT.md`](REFERENCE_HEADER_AND_IMPORT.md)**).
- Run **`./venv/bin/python tooling/m4l_pipeline.py all projects/MyThing/spec.json`**  
  Omit the track argument to **create a new track** (type follows ``device_type``); pass **`0`** to load on the first track.
- Read [`VERIFY_GUIDE.md`](VERIFY_GUIDE.md) and [`LIVE_API_PATTERNS.md`](LIVE_API_PATTERNS.md) when you add real device logic.

You do **not** need prior “agent” experience: treat the assistant as a **junior engineer** that can run shell commands — you steer, it executes, you read the output.
