# Copilot instructions

When helping with this repository, follow **[`AGENTS.md`](../AGENTS.md)** and **[`docs/AGENT_TOOLS.md`](../docs/AGENT_TOOLS.md)**.

## Hard rules — every build, every iteration

1. **ALWAYS use `m4l_pipeline.py all spec.json --with-adv`** — never `build` alone. `all` builds, deploys, AND loads the device on a new track in Ableton.
2. **ALWAYS pass `--with-adv`** — generates the `.adv` preset so parameters appear in Live.
3. **Patch bumps by default** (1.1 → 1.2). **`--bump-major`** only when directed. See `docs/VERSIONING.md`.
4. **Every version lands on a new track automatically.** The user never drags from the browser.
5. **Only use `--no-live` when Ableton is explicitly closed.**
6. **Use `M4L_PROJECTS_PREFIX=workspace`** for user devices.
7. **Say "ready for you to verify in Live"** after automated checks — never "confirmed working" until the user confirms.

## Setup

- Run **`./run`** from the repo root on first setup (Ableton quit).
- After user enables **AbletonOSC** and **AbletonMCP** in Live, run **`./run --live`**.
- Use **`./venv/bin/python scripts/validate_spec.py`** before building specs.
- **AbletonMCP** (Live Control Surface, port 9877) is required for Live load; it is separate from GitHub Copilot or IDE MCP products.

Human walkthrough: **[`docs/GETTING_STARTED.md`](../docs/GETTING_STARTED.md)** · All IDEs: **[`docs/AGENTIC_IDES.md`](../docs/AGENTIC_IDES.md)**.

## MCP server (optional)

`tooling/m4l_mcp_server.py` exposes the full pipeline plus Live control tools (`live_session_state`, `live_build_and_verify`, `live_track_devices`, `live_set_param`, `live_transport`, `live_create_midi_clip`, `live_delete_track`, etc.) as an IDE MCP server.

Install matrix per IDE (Copilot/VS Code, Cursor, Claude Code CLI, Claude Desktop, Gemini, etc.): **[`docs/AGENT_REFERENCE.md#pipeline-mcp-server-optional-ide-mcp`](../docs/AGENT_REFERENCE.md#pipeline-mcp-server-optional-ide-mcp)** — single source of truth. Full tool list: **[`docs/AGENT_TOOLS.md`](../docs/AGENT_TOOLS.md)**.
