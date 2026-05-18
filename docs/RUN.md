# `./run` — one command after clone

This repo is meant to be **agent-friendly**: after cloning, you or your IDE assistant should only need to say **“run”** (or run one script) to set up Python, install **AbletonOSC** + **AbletonMCP** into your User Library, copy local env defaults, and verify the stack.

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

Success ends with **`M4L_RUN_OK`** on stdout (agents can grep for it).

## What gets installed (automated)

1. **Python `venv/`** + **`python-osc`** (via **`bootstrap.sh`** / **`bootstrap.ps1`** on first run).
2. **AbletonOSC** and **AbletonMCP** under **`$ABLETON_HOME/User Library/Remote Scripts/`** (AbletonMCP includes this repo’s **`create_audio_track`** patch).
3. **`.env`** from **`.env.example`** if missing (`M4L_PROJECTS_PREFIX=workspace` for personal plugins).
4. **Preflight**: donors in **`tooling/donors/`**, imports, Remote Script folders.

## What you still do once in Ableton (manual)

Live does not let tools flip Control Surfaces from the command line. After **`./run`**:

1. **Quit Live completely**, reopen.
2. **Preferences → Link / Tempo / MIDI**
3. **Control Surface** → **AbletonOSC** (port **11000**).
4. Second row → **AbletonMCP** (TCP **9877**).
5. Run again with Live open: **`./run --live`**

See **[`SETUP_AUTOMATED.md`](SETUP_AUTOMATED.md)** for ports and troubleshooting.

## Coding-only machine (no Ableton)

```bash
./run
# or explicitly:
./run --no-live
```

Preflight should pass after bootstrap. Live/MCP steps are skipped or print guidance only.

## For AI agents (Cursor, Claude, etc.)

When the user says **run**, **set up**, **bootstrap the pipeline**, or **get this working**:

1. **Working directory:** repository root (folder containing **`run`** and **`bootstrap.sh`**).
2. **Execute:** `./run` (macOS/Linux) or `.\run.ps1` (Windows).
3. If they mention **Live is open** or want **load device on track**: `./run --live`.
4. **Do not** ask them to run five separate commands unless a step failed — use flags above.
5. On success, look for **`M4L_RUN_OK`**.

Full agent contract: **[`AGENTS.md`](../AGENTS.md)**.

## After `M4L_RUN_OK`

- Personal plugins: **`projects/workspace/`** + **`M4L_PROJECTS_PREFIX=workspace`** — **[`PRIVATE_PLUGINS.md`](PRIVATE_PLUGINS.md)**.
- Custom devices: **`tooling/m4l_pipeline.py`**, specs under **`projects/workspace/<YourPlugin>/`**.
- UI / presentation: **[`M4L_FRONTEND_AND_BACKEND.md`](M4L_FRONTEND_AND_BACKEND.md)**.
