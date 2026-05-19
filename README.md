# Ableton + Max for Live — AI-friendly pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Sanity CI](https://github.com/CorbinRandall/ableton-ai-plugin-creation-pipeline/actions/workflows/sanity.yml/badge.svg)](https://github.com/CorbinRandall/ableton-ai-plugin-creation-pipeline/actions/workflows/sanity.yml)

Use this repo with an **agent-style IDE** (Cursor, Claude Code, Antigravity, Copilot in agent mode, etc.) to **describe Max for Live devices in plain language** and turn them into **`.amxd`** files: validated JSON specs → build → deploy to your **Ableton User Library** → load on a **new track** via **[AbletonMCP](https://github.com/ahujasid/ableton-mcp)** (optional **[AbletonOSC](https://github.com/ideoforms/AbletonOSC)** for checks and automation).

---

## Five-minute setup

| Step | Ableton Live | What you do |
|------|----------------|-------------|
| **1** | **Quit** | Close Live completely. |
| **2** | **Closed** | Clone this repo → open the folder in your IDE → tell the agent **`run`** (or run **`./run`** yourself). |
| **3** | **Open** | Follow the agent’s steps to enable **AbletonOSC** and **AbletonMCP** under **Preferences → Link, Tempo & MIDI → Control Surface** (two rows, like picking MIDI controllers). When both are on, tell the agent **`continue`**. |
| **4** | **Open** | Agent runs **`./run --live`** — bootstrap finishes and the **tutorial** device loads on a **new track**. |
| **5** | **Open** | **Pipeline ready** — describe what you want next, e.g. *“Build the simple gain audio effect from `examples/simple_gain_audio_spec.json` and load it.”* |

Steps **2–4** match **[`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)** and **[`AGENTS.md`](AGENTS.md)** in more detail.

---

## First device to build (recommended smoke test)

This path is **validated in CI**: schema/UI/layout checks plus **`m4l_pipeline.py build`**.

**SimpleGain** — one **Gain** knob on an **audio effect** using the same **dry audio path** as our CI template (`plugin~` → `plugout~`). The knob is real in Live (automation/MIDI map); wire it to `*~` / `line~` in Max when you want audible level control—see **`tooling/templates/audio_effect_stub.json`**.

From the **repo root** (after **`./run`** created **`venv/`**):

```bash
./venv/bin/python scripts/validate_spec.py examples/simple_gain_audio_spec.json
./venv/bin/python tooling/m4l_pipeline.py all examples/simple_gain_audio_spec.json --with-adv
```

Use **`all --no-live`** if Live is closed (artifacts + deploy only). Personal forks of this idea belong under **`projects/workspace/`** — see **[`docs/PRIVATE_PLUGINS.md`](docs/PRIVATE_PLUGINS.md)**.

Natural-language prompts work once the agent knows the workflow: *validate → `m4l_pipeline.py all …`* for **`examples/simple_gain_audio_spec.json`** (or a copy you edit). See **[`docs/AGENT_TOOLS.md`](docs/AGENT_TOOLS.md)**.

---

**Human walkthrough:** **[`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)** · **Any agentic IDE:** **[`docs/AGENTIC_IDES.md`](docs/AGENTIC_IDES.md)** · **macOS / Windows / Linux:** **[`docs/CROSS_PLATFORM.md`](docs/CROSS_PLATFORM.md)** · **Agents:** **[`AGENTS.md`](AGENTS.md)**

---

## Requirements

| Requirement | Notes |
|-------------|-------|
| **Ableton Live** | **Suite**, or **Standard + [Max for Live add-on](https://help.ableton.com/hc/en-us/articles/206407124-Buying-Max-for-Live)** — not Lite/Intro ([Ableton Help](https://help.ableton.com/hc/en-us/articles/360000036850-Max-for-Live-bundled-in-Live)). |
| **Python** | **3.10+** — ensured by **`bootstrap.sh`** / **`bootstrap.ps1`** when possible. |
| **Header donor `.amxd`** | Pipeline packs JSON into an existing device wrapper ([**`docs/REFERENCE_HEADER_AND_IMPORT.md`**](docs/REFERENCE_HEADER_AND_IMPORT.md)). Generic starters are included in **`tooling/donors/`**. |

---

## Quick start

**`venv/` is not in git** — each clone runs **`./run`** to create it locally.

```bash
# Step 1: quit Ableton first
git clone https://github.com/CorbinRandall/ableton-ai-plugin-creation-pipeline.git
cd ableton-ai-plugin-creation-pipeline
chmod +x run bootstrap.sh    # macOS / Linux
./run                        # step 2 — Live closed
# step 3: agent guides OSC/MCP → you say "continue"
./run --live                 # step 4 — agent (or you) after step 3
```

Windows: `powershell -ExecutionPolicy Bypass -File .\run.ps1` (add `-Live` for step 4).

Step-by-step (permissions, coding-only Mac, agent prompts): **[`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)**. Flags: [**`docs/RUN.md`**](docs/RUN.md) · [**`AGENTS.md`**](AGENTS.md).

### Individual commands (if a step fails)

| Step | Command |
|------|---------|
| Preflight only | `./venv/bin/python scripts/verify_setup.py --preflight` |
| Live health | `./venv/bin/python scripts/verify_setup.py --wait-mcp 120` |
| Tutorial + load | `./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py` |

Pipeline behavior: versioned **`projects/<Plugin>/<Plugin X.Y>/`** (or **`projects/workspace/…`** with **`M4L_PROJECTS_PREFIX=workspace`**). **`m4l_pipeline.py all`** / **`build_deploy_load`** **deploy** to User Library **Imported/** and by default **insert the device on a new Live track** via AbletonMCP (**`all --no-live`** or **`M4L_SKIP_LIVE=1`** skips Live). **`build`** only writes **`.amxd`**. Track type (**MIDI** vs **audio**) follows **`device_type`**. See **`projects/workspace/README.md`**.

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [**`docs/GETTING_STARTED.md`**](docs/GETTING_STARTED.md) | **Start here (humans)** — phases 1–4, what to open when |
| [**`docs/AGENTIC_IDES.md`**](docs/AGENTIC_IDES.md) | Any agentic IDE — same workflow |
| [**`docs/CROSS_PLATFORM.md`**](docs/CROSS_PLATFORM.md) | macOS, Windows, Linux commands |
| [**`docs/VERIFY_GUIDE.md`**](docs/VERIFY_GUIDE.md) | Live verify + parameter sweep |
| [**`docs/AUDIO_SMOKE_TEST.md`**](docs/AUDIO_SMOKE_TEST.md) | Manual audio checklist |
| [**`docs/AGENT_TOOLS.md`**](docs/AGENT_TOOLS.md) | Shell commands for agents (validate, scaffold, export, build) |
| [**`docs/ROADMAP.md`**](docs/ROADMAP.md) | Phased improvements and feasibility |
| [**`docs/MAX_TO_SPEC.md`**](docs/MAX_TO_SPEC.md) | Export `.amxd` → spec (Max-first workflow) |
| [**`docs/RUN.md`**](docs/RUN.md) | **`./run`** flags and behavior |
| [**`AGENTS.md`**](AGENTS.md) | What AI agents should do when the user says **run** |
| [**`docs/AGENT_IDE_BEGINNER_GUIDE.md`**](docs/AGENT_IDE_BEGINNER_GUIDE.md) | Cursor / similar — links to getting started |
| [**`docs/SETUP_AUTOMATED.md`**](docs/SETUP_AUTOMATED.md) | Bootstrap, Remote Scripts, MCP patch, troubleshooting |
| [**`docs/REFERENCE_HEADER_AND_IMPORT.md`**](docs/REFERENCE_HEADER_AND_IMPORT.md) | Donor `.amxd`, **`M4L_REFERENCE_AMXD`**, extra **`projects/*`** layouts |
| [**`docs/PRIVATE_PLUGINS.md`**](docs/PRIVATE_PLUGINS.md) | Keep personal / commercial devices out of this public repo (generic allowlist) |
| [**`docs/M4L_FRONTEND_AND_BACKEND.md`**](docs/M4L_FRONTEND_AND_BACKEND.md) | **Presentation vs patching**, `textcolor` / label contrast, UI checklist |
| [**`docs/GITHUB_CREATE_REPO.md`**](docs/GITHUB_CREATE_REPO.md) | GitHub **About** text, topics, visibility (**Public**) checklist |

---

## Repository layout

| Path | Role |
|------|------|
| **`run`** / **`run.ps1`** | **Start here** — bootstrap + env + preflight + optional Live tutorial |
| **`bootstrap.sh`** / **`bootstrap.ps1`** | Lower-level install (called by **`./run`**) |
| **`requirements.txt`** | **`python-osc`** |
| **`examples/simple_gain_audio_spec.json`** | **First-build smoke test** — validated gain utility spec |
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
| **`M4L_SKIP_VALIDATE`** | **`1`** to skip spec validation before `build` / `all` |
| **`M4L_BUILD_ADV`** | **`1`** to generate/deploy `.adv` with `all` (or use `--with-adv`) |

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
