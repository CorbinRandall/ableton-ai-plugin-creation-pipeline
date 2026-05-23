# Gemini CLI — project instructions

Follow **[`AGENTS.md`](AGENTS.md)** for onboarding steps 1–5 and **[`docs/AGENT_TOOLS.md`](docs/AGENT_TOOLS.md)** for shell commands.

- First setup: **`./run`** (Ableton closed), then guide user through AbletonOSC + AbletonMCP, then **`./run --live`** after they say **Continue**.
- **AbletonMCP** in Live (Control Surface, TCP 9877) is **not** an IDE MCP server.
- Personal plugins: **`projects/workspace/`** — see **`docs/PRIVATE_PLUGINS.md`**.

Other IDEs: **`docs/AGENTIC_IDES.md`**.

## MCP server — AI-native Live control

`tooling/m4l_mcp_server.py` is a **FastMCP stdio server** with full pipeline + Live control tools.

**New Live-control tools:** `live_session_state`, `live_track_devices`, `live_set_param`, `live_transport`, `live_create_midi_clip`, `live_fire_clip`, `live_stop_clip`, `live_delete_track`, `live_rename_track`, `live_clear_track`, `live_build_and_verify`

Configure in `~/.gemini/settings.json` (or equivalent):

````json
{
  "mcpServers": {
    "m4l-pipeline": {
      "command": "/abs/path/to/repo/venv/bin/python",
      "args": ["/abs/path/to/repo/tooling/m4l_mcp_server.py"],
      "env": { "M4L_PROJECTS_PREFIX": "workspace" }
    }
  }
}
````

Full tool reference: **[`docs/AGENT_TOOLS.md`](docs/AGENT_TOOLS.md)**.
