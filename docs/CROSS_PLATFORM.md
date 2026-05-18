# Cross-platform notes (macOS, Windows, Linux)

This pipeline is **IDE-agnostic** (any agentic editor with shell access) and **host-OS-agnostic** for Python tooling. **Ableton Live** itself runs on **macOS and Windows only** — you need a Live machine for `./run --live` and verify scripts.

## Entry commands

| Platform | First-time setup | With Live open |
|----------|------------------|----------------|
| **macOS / Linux** | `chmod +x run bootstrap.sh && ./run` | `./run --live` |
| **Windows** | `powershell -ExecutionPolicy Bypass -File .\run.ps1` | `...\run.ps1 -Live` |

Linux is supported for **clone, validate, build `.amxd`, CI** on a coding machine. Run **Live steps** on a Mac or PC with Ableton installed.

## Python interpreter

Use the project **`venv`** after `./run` or `bootstrap`:

| Platform | Python |
|----------|--------|
| macOS / Linux | `./venv/bin/python scripts/validate_spec.py …` |
| Windows | `.\venv\Scripts\python.exe scripts\validate_spec.py …` |

If `venv` is missing, `python3` (macOS/Linux) or `py -3` / `python` (Windows) works after `pip install -r requirements.txt`.

## Paths

| Variable | macOS | Windows |
|----------|-------|---------|
| Default **`ABLETON_HOME`** | `~/Music/Ableton` | `~/Documents/Ableton` |
| Override | `export ABLETON_HOME=…` | `$env:ABLETON_HOME = "…"` |

User Library **Remote Scripts** and **Imported/** deploy paths follow Ableton’s layout on each OS (see **`tooling/m4l_pipeline.py`**).

## Agentic IDE (not tied to one product)

| Need | Doc |
|------|-----|
| Any editor | [`AGENTIC_IDES.md`](AGENTIC_IDES.md) |
| Shell tools | [`AGENT_TOOLS.md`](AGENT_TOOLS.md) |
| Human steps | [`GETTING_STARTED.md`](GETTING_STARTED.md) |

Optional editor-specific files (Cursor rules, `CLAUDE.md`, Copilot instructions) **add** hints; they are not required.

## Live control ports (all host OSes)

| Component | Address |
|-----------|---------|
| AbletonMCP | `127.0.0.1:9877` (TCP) |
| AbletonOSC send | `127.0.0.1:11000` (UDP) |
| AbletonOSC receive | `127.0.0.1:11001` (UDP) |

## Optional IDE config files (do not commit secrets)

| Editor | File (user home — merge manually) |
|--------|-----------------------------------|
| Cursor | `~/.cursor/mcp.json` |
| Others | Follow your product’s MCP/settings docs |

Bootstrap **must not** overwrite personal IDE config. See [`scripts/m4l_fresh_reset_backup_and_restore.md`](../scripts/m4l_fresh_reset_backup_and_restore.md).
