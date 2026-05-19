# `./run` — one command after clone

**Human checklist (Ableton open or not, agent prompts):** **[`GETTING_STARTED.md`](GETTING_STARTED.md)**.

This repo is meant to be **agent-friendly**: after cloning, you or your IDE assistant should only need to say **“run”** (or run one script) to set up Python, install **AbletonOSC** + **AbletonMCP** into your User Library, copy local env defaults, and verify the stack.

**Step 1:** quit Ableton. **Step 2:** `./run`. **Step 3:** agent guides Control Surfaces; user says **continue**. **Step 4:** `./run --live`. **Step 5:** **`M4L_PIPELINE_READY`** — describe your plugin. See **[`GETTING_STARTED.md`](GETTING_STARTED.md)**.

## Command

From the **repository root**:

| Platform | Command |
|----------|---------|
| macOS / Linux | `chmod +x run && ./run` |
| Windows | `powershell -ExecutionPolicy Bypass -File .\run.ps1` |

## Modes

| Flag | What it does |
|------|----------------|
| *(none)* | Bootstrap (or refresh scripts) → `.env` → allowlist check → **preflight** → prints **Live / MCP checklist** → tutorial **build + deploy** with `--no-live` |
| **`--live`** | Same setup, then **waits for TCP 9877**, tutorial **build + load on new track**, **`m4l_verify.py`** |
| **`--no-live`** | Setup + preflight + tutorial build/deploy **only** (no Ableton socket) |
| **`--setup-only`** | Bootstrap + preflight **only** (no tutorial build) |
| **`--skip-bootstrap`** | Skip bootstrap / script refresh (venv must already exist) |

Success markers on stdout (agents can grep):

| Marker | When |
|--------|------|
| **`M4L_RUN_OK`** | Step 2 or 4 command finished |
| **`M4L_PIPELINE_READY`** | Step 4 — Live connected, tutorial loaded |

## What gets installed (automated)

1. **Python `venv/`** + **`python-osc`** (via **`bootstrap.sh`** / **`bootstrap.ps1`** on first run).
2. **AbletonOSC** and **AbletonMCP** under **`$ABLETON_HOME/User Library/Remote Scripts/`** (AbletonMCP includes this repo’s **`create_audio_track`** patch).
3. **`.env`** from **`.env.example`** if missing (`M4L_PROJECTS_PREFIX=workspace` for personal plugins).
4. **Preflight**: donors in **`tooling/donors/`**, imports, Remote Script folders.

## Step 3 in Ableton (manual — agent guides you)

Live cannot enable Control Surfaces from the CLI. After step 2, your **IDE agent** should walk you through **AbletonOSC** + **AbletonMCP**, then wait for **“continue”** before **`./run --live`**. Details: **[`GETTING_STARTED.md`](GETTING_STARTED.md)** · ports: **[`SETUP_AUTOMATED.md`](SETUP_AUTOMATED.md)**.

## Coding-only machine (no Ableton)

```bash
./run
# or explicitly:
./run --no-live
```

Preflight should pass after bootstrap. Live/MCP steps are skipped or print guidance only.

## For AI agents (any agentic IDE)

When the user says **run** (first time after clone):

1. **Step 1:** Ableton **closed**.
2. **Step 2:** `./run` from repo root → **`M4L_RUN_OK`**.
3. **Step 3:** **Do not run commands** — guide OSC/MCP setup; ask them to reply **continue** when done.
4. **Step 4:** On **continue** / **ready**: `./run --live` → **`M4L_PIPELINE_READY`**.
5. **Step 5:** Confirm pipeline connected; ask what **midi_effect** / **audio_effect** / **instrument** they want.

Agent contract: **[`AGENTS.md`](../AGENTS.md)** · Per editor: **[`AGENTIC_IDES.md`](AGENTIC_IDES.md)**.

## After `M4L_PIPELINE_READY` (step 5)

- Agent tools: **[`AGENT_TOOLS.md`](AGENT_TOOLS.md)** (validate, scaffold, export, build).
- Personal plugins: **`projects/workspace/`** + **`M4L_PROJECTS_PREFIX=workspace`** — **[`PRIVATE_PLUGINS.md`](PRIVATE_PLUGINS.md)**.
- Spec flags: **`--with-adv`**, **`--skip-validate`**; env **`M4L_BUILD_ADV`**, **`M4L_SKIP_VALIDATE`**.
- UI / presentation: **[`M4L_FRONTEND_AND_BACKEND.md`](M4L_FRONTEND_AND_BACKEND.md)**.
