# Ableton + Max for Live — AI-friendly pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Sanity CI](https://github.com/CorbinRandall/m4l-pipeline-public/actions/workflows/sanity.yml/badge.svg)](https://github.com/CorbinRandall/m4l-pipeline-public/actions/workflows/sanity.yml)

**Clone → bootstrap → build `.amxd` devices from JSON specs → deploy to your Ableton User Library → load on a new track via [AbletonMCP](https://github.com/ahujasid/ableton-mcp)** (optional **[AbletonOSC](https://github.com/ideoforms/AbletonOSC)** checks).

Use this repo from any terminal or **agent-style IDE**: describe a device, generate a spec, run **`tooling/m4l_pipeline.py`**, and iterate in **Live** without hand-dragging files from Finder/Explorer.

---

## Requirements

| Requirement | Notes |
|-------------|--------|
| **Ableton Live** | **Suite**, or **Standard + [Max for Live add-on](https://help.ableton.com/hc/en-us/articles/206407124-Buying-Max-for-Live)** — not Lite/Intro ([Ableton Help](https://help.ableton.com/hc/en-us/articles/360000036850-Max-for-Live-bundled-in-Live)). |
| **Python** | **3.10+** — ensured by **`bootstrap.sh`** / **`bootstrap.ps1`** when possible. |
| **Header donor `.amxd`** | Pipeline packs JSON into an existing device wrapper ([**`docs/REFERENCE_HEADER_AND_IMPORT.md`**](docs/REFERENCE_HEADER_AND_IMPORT.md)). Default path uses **`Reference_Donor.amxd`** or set **`M4L_REFERENCE_AMXD`**. |

---

## Quick start

**`venv/` is not in git** — each clone creates it locally via bootstrap.

```bash
git clone https://github.com/CorbinRandall/m4l-pipeline-public.git
cd m4l-pipeline-public
chmod +x bootstrap.sh    # macOS / Linux
./bootstrap.sh           # or: powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1
```

1. **Quit Live completely**, reopen.
2. **Preferences → Link / Tempo / MIDI** → Control Surface: **AbletonOSC**, **AbletonMCP** (see [**`docs/SETUP_AUTOMATED.md`**](docs/SETUP_AUTOMATED.md)).

**Preflight** (no Live needed):

```bash
./venv/bin/python scripts/verify_setup.py --preflight
```

**Full check** (Live running):

```bash
./venv/bin/python scripts/verify_setup.py --wait-mcp 120
```

**Tutorial build + verify**:

```bash
./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py
./venv/bin/python scripts/m4l_verify.py
```

Pipeline behavior: versioned **`projects/<Plugin>/<Plugin X.Y>/`** (or **`projects/workspace/…`** with **`M4L_PROJECTS_PREFIX=workspace`**). **`m4l_pipeline.py all`** / **`build_deploy_load`** **deploy** to User Library **Imported/** and by default **insert the device on a new Live track** via AbletonMCP (**`all --no-live`** or **`M4L_SKIP_LIVE=1`** skips Live). **`build`** only writes **`.amxd`**. Track type (**MIDI** vs **audio**) follows **`device_type`**. See **`projects/workspace/README.md`**.

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [**`docs/SETUP_AUTOMATED.md`**](docs/SETUP_AUTOMATED.md) | Bootstrap, Remote Scripts, MCP patch, troubleshooting |
| [**`docs/AGENT_IDE_BEGINNER_GUIDE.md`**](docs/AGENT_IDE_BEGINNER_GUIDE.md) | First-time setup with Cursor / similar agents |
| [**`docs/REFERENCE_HEADER_AND_IMPORT.md`**](docs/REFERENCE_HEADER_AND_IMPORT.md) | Donor `.amxd`, **`M4L_REFERENCE_AMXD`**, extra **`projects/*`** layouts |
| [**`docs/M4L_FRONTEND_AND_BACKEND.md`**](docs/M4L_FRONTEND_AND_BACKEND.md) | **Presentation vs patching**, `textcolor` / label contrast, UI checklist |
| [**`docs/GITHUB_CREATE_REPO.md`**](docs/GITHUB_CREATE_REPO.md) | GitHub **About** text, topics, visibility (**Public**) checklist |

---

## Repository layout

| Path | Role |
|------|------|
| **`bootstrap.sh`** / **`bootstrap.ps1`** | Python → **`venv`** → AbletonOSC + AbletonMCP → template helpers |
| **`requirements.txt`** | **`python-osc`** |
| **`scripts/install_remote_scripts.py`** | Download/install Remote Scripts (patches MCP for **`create_audio_track`**) |
| **`scripts/verify_setup.py`** | MCP + OSC health (**`--preflight`** = filesystem only) |
| **`tooling/m4l_pipeline.py`** | Spec → **`.amxd`**, deploy, Ableton load |
| [**`projects/workspace/README.md`**](projects/workspace/README.md) | **Local sandboxes** — gitignored; use with **`M4L_PROJECTS_PREFIX=workspace`** |

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| **`ABLETON_HOME`** | Folder containing **`User Library`** (default: macOS `~/Music/Ableton`, Windows `~/Documents/Ableton`) |
| **`M4L_REFERENCE_AMXD`** | Absolute path to header donor **`.amxd`** |
| **`M4L_PROJECTS_PREFIX`** | e.g. **`workspace`** → builds land in **`projects/workspace/<slug>/`** (gitignored local sandboxes) |
| **`M4L_SKIP_LIVE`** | **`1`** → **`build_deploy_load`** / **`all`** skip AbletonMCP (same idea as **`all --no-live`**) |
| **`BOOTSTRAP_PYTHON`** | Interpreter for **`venv`** creation |
| **`M4L_VENV`** | Alternate venv directory (default **`./venv`**) |
| **`M4L_SKIP_TEMPLATE`** | **`1`** to skip default Live set template install |

---

## Contributing

See [**`CONTRIBUTING.md`**](CONTRIBUTING.md). **Do not commit `venv/`**, **`.env`**, or Ableton pack binaries you do not have rights to redistribute.

---

## Third-party components

Installed into **`User Library/Remote Scripts`** by bootstrap (upstream licenses apply):

- **[AbletonOSC](https://github.com/ideoforms/AbletonOSC)** — OSC control surface.
- **[AbletonMCP](https://github.com/ahujasid/ableton-mcp)** — TCP bridge used by **`m4l_pipeline`** load steps (this repo applies a small **`create_audio_track`** patch during install).

---

## Security

See [**`SECURITY.md`**](SECURITY.md).

---

## License

**MIT** — see [**`LICENSE`**](LICENSE).
