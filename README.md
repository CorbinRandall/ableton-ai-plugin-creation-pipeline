# Ableton + Max for Live — AI-friendly pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Sanity CI](https://github.com/CorbinRandall/ableton-ai-plugin-creation-pipeline/actions/workflows/sanity.yml/badge.svg)](https://github.com/CorbinRandall/ableton-ai-plugin-creation-pipeline/actions/workflows/sanity.yml)

**Make your own Ableton devices by describing them in normal words.**

You do not need to know coding, GitHub, or what an “IDE” is. You open this project in an **AI chat app** (we recommend **Cursor**), tell it what you want — like *“an effect with a volume knob”* — and it handles the boring setup: checking your idea, building the device, putting it in Ableton’s browser, and loading it on a track so you can **hear it and turn the knobs**. First-time setup is mostly automated: you say **“run”**, click a couple of settings in Ableton when the AI tells you to, say **“continue”**, and you’re connected. After that you just **describe → listen in Live → tell the AI to fix or improve** until it feels right. The AI is simply the easiest way to drive the same tools a developer could run by hand — nothing different happens under the hood.

**New here?** Step-by-step with zero jargon: **[`docs/START_HERE.md`](docs/START_HERE.md)**

---

## Five-minute setup (you talk — the AI runs)

| Step | Ableton Live | What **you** do |
|------|----------------|-----------------|
| **1** | **Quit** | Close Live completely. |
| **2** | **Closed** | Open this folder in **Cursor** (or similar) → tell the AI **`run`**. |
| **3** | **Open** | AI tells you what to click in Live (**AbletonOSC** + **AbletonMCP**). Say **`continue`**. |
| **4** | **Open** | AI connects — tutorial device appears on a track. |
| **5** | **Open** | Describe your device: *“Build a volume knob effect and load it for me to try.”* |

Details: **[`docs/START_HERE.md`](docs/START_HERE.md)** · **[`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)** · **[`AGENTS.md`](AGENTS.md)** (for the AI)

---

## First device to build (recommended smoke test)

This path is covered by **`sanity` CI**: schema/UI/layout checks plus **`m4l_pipeline.py build`** — **not** a Live rack proof (see **[docs/VERIFICATION_TIERS.md](docs/VERIFICATION_TIERS.md)**).

**VolumeKnob** — same **`audio_effect`** category with an **audible** path: **`plugin~` → `*~` → `plugout~`**, **`Volume`** dial **0–100** scaled by **`* 0.01` → `sig~`** into the multiplier. Build/deploy (recommended: gitignored sandbox):

```bash
./venv/bin/python scripts/validate_spec.py examples/volume_knob_audio_spec.json
M4L_PROJECTS_PREFIX=workspace ./venv/bin/python tooling/m4l_pipeline.py all examples/volume_knob_audio_spec.json --with-adv
```

Then **`scripts/m4l_verify.py --spec examples/volume_knob_audio_spec.json --skip-build --expect-params Volume`** after Live sees a patched MCP (**full quit + reopen** if you just ran **`install_remote_scripts.py`**).

**SimpleGain** — one **Gain** knob on an **audio effect** using the same **dry audio path** as our CI template (`plugin~` → `plugout~`). The knob is real in Live (automation/MIDI map); wire it to `*~` / `line~` in Max when you want audible level control—see **`tooling/templates/audio_effect_stub.json`** or copy **`examples/volume_knob_audio_spec.json`**.

From the **repo root** (after **`./run`** created **`venv/`**):

```bash
./venv/bin/python scripts/validate_spec.py examples/simple_gain_audio_spec.json
./venv/bin/python tooling/m4l_pipeline.py all examples/simple_gain_audio_spec.json --with-adv
```

Use **`all --no-live`** if Live is closed (artifacts + deploy only). Personal forks of this idea belong under **`projects/workspace/`** — see **[`docs/PRIVATE_PLUGINS.md`](docs/PRIVATE_PLUGINS.md)**.

**If SimpleGain (or any `audio_effect`) shows a generic Max error in Live:** you were probably missing **`create_audio_track`** in the **running** AbletonMCP (script updates require a **full Live restart**). The pipeline no longer loads audio effects onto MIDI tracks as a fallback. Fix: **`install_remote_scripts.py` → quit Live completely → reopen**, then verify:

```bash
./venv/bin/python scripts/verify_setup.py --wait-mcp 120 --assert-create-audio-track
```

Then **`m4l_pipeline.py all examples/simple_gain_audio_spec.json --with-adv`** again. See **`docs/LIVE_API_PATTERNS.md`**.

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
| Preflight (repo + donors only, CI-friendly) | `./venv/bin/python scripts/verify_setup.py --preflight --repo-only` |
| Preflight (full, needs Ableton User Library paths) | `./venv/bin/python scripts/verify_setup.py --preflight` |
| Live MCP socket wait | `./venv/bin/python scripts/verify_setup.py --wait-mcp 120` |
| Full verify (Live + MCP + OSC) | `./venv/bin/python scripts/m4l_verify.py` — **[docs/VERIFY_GUIDE.md](docs/VERIFY_GUIDE.md)** |
| Verify unit tests (no Live) | `./venv/bin/python scripts/test_verification_helpers.py` |
| Tutorial + load | `./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py` |

Pipeline behavior: versioned **`projects/<Plugin>/<Plugin X.Y>/`** (or **`projects/workspace/…`** with **`M4L_PROJECTS_PREFIX=workspace`**). **`m4l_pipeline.py all`** / **`build_deploy_load`** **deploy** to User Library **Imported/** and by default **insert the device on a new Live track** via AbletonMCP (**`all --no-live`** or **`M4L_SKIP_LIVE=1`** skips Live). **`build`** only writes **`.amxd`**. Track type (**MIDI** vs **audio**) follows **`device_type`**. See **`projects/workspace/README.md`**.

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [**`docs/START_HERE.md`**](docs/START_HERE.md) | **Total beginners** — no Git/terminal; AI does setup; plain language |
| [**`docs/GETTING_STARTED.md`**](docs/GETTING_STARTED.md) | Setup checklist (agent-first; same steps as START_HERE) |
| [**`docs/AGENTIC_IDES.md`**](docs/AGENTIC_IDES.md) | Any agentic IDE — same workflow |
| [**`docs/CROSS_PLATFORM.md`**](docs/CROSS_PLATFORM.md) | macOS, Windows, Linux commands |
| [**`docs/VERIFY_GUIDE.md`**](docs/VERIFY_GUIDE.md) | Live verify + parameter sweep |
| [**`docs/VERIFICATION_TIERS.md`**](docs/VERIFICATION_TIERS.md) | **T0–T5** — what automation vs humans actually prove |
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
| **`examples/simple_gain_audio_spec.json`** | **First-build smoke test** — dry **`plugin~` → `plugout~`** + Gain dial |
| **`examples/volume_knob_audio_spec.json`** | **Audible volume** — **`Volume`** dial scales audio via **`*~`** / **`sig~`** |
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
