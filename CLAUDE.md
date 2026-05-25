# Claude Code — project instructions

Follow **[`AGENTS.md`](AGENTS.md)** for onboarding steps 1–5 and **[`docs/AGENT_TOOLS.md`](docs/AGENT_TOOLS.md)** for shell commands.

## Hard rules — every build, every iteration

1. **ALWAYS use `m4l_pipeline.py all spec.json --with-adv`** — never `build` alone. `all` builds, deploys, AND loads the device on a new track in Ableton. `build` only writes a file — the user would have to drag it into Ableton manually.
2. **ALWAYS pass `--with-adv`** — generates the `.adv` preset so parameters appear in Live.
3. **Every change = new patch version.** Default: 1.1 → 1.2 → 1.3. Use **`--bump-major`** only when the user wants a new major line (2.1). See [`docs/VERSIONING.md`](docs/VERSIONING.md).
4. **Every version lands on a new track automatically.** The user never drags anything from the browser.
5. **Only use `--no-live` when Ableton is explicitly closed.**
6. **After automated checks (T3), say "ready for you to verify in Live"** — never "confirmed working" until the user confirms (T5).
7. **Use `M4L_PROJECTS_PREFIX=workspace`** for user devices — keeps them gitignored.
8. **Never commit `projects/workspace/`** contents or private plugin names in public branches.

## Setup flow

- First setup: **`./run`** (Ableton closed), then guide user through AbletonOSC + AbletonMCP, then **`./run --live`** after they say **Continue**.
- **AbletonMCP** in Live (Control Surface) is **not** the same as optional Claude Desktop MCP servers.
- Personal plugins: **`projects/workspace/`** — see **`docs/PRIVATE_PLUGINS.md`**.
- End-to-end Live check (after MCP + OSC): **`./venv/bin/python scripts/m4l_verify.py`** — see **`docs/VERIFY_GUIDE.md`**.

Other IDEs: **`docs/AGENTIC_IDES.md`**.

## MCP server — AI-native Live control

`tooling/m4l_mcp_server.py` is a **FastMCP stdio server** that exposes the full pipeline + Live control to any MCP-capable client (Claude Code, Claude Desktop, Cursor, etc.).

### Tools available

| Tool | What it does |
|---|---|
| `list_recipes` / `read_recipe_spec` | Browse built-in device examples |
| `compose_spec_from_dsl` | Build a spec dict from Python DSL code |
| `validate_spec` | Validate a spec dict |
| `spec_to_svg` | Render device UI preview as SVG |
| `build_amxd_tool` | Build `.amxd` file (no Live) |
| `deploy` | Copy `.amxd` to User Library Imported/ |
| `load_in_live` | Build + deploy + load on a new track |
| `diagnose` | Map error text to known fixes |
| **`live_session_state`** | **Full session snapshot (all tracks, devices, tempo)** |
| **`live_track_devices`** | **Devices on one track with param names/values/ranges** |
| **`live_set_param`** | **Set a device parameter by name or index** |
| **`live_transport`** | **play / stop / set_tempo** |
| **`live_create_midi_clip`** | **Create a MIDI clip with notes** |
| **`live_fire_clip`** / **`live_stop_clip`** | **Launch / stop a clip slot** |
| **`live_delete_track`** | **Delete a track by index** |
| **`live_rename_track`** | **Rename a track** |
| **`live_clear_track`** | **Remove all devices from a track** |
| **`live_build_and_verify`** | **Full pipeline + OSC verify in one call** |

### Configure in Claude Code (CLI)

```bash
claude mcp add m4l-pipeline \
  --env M4L_PROJECTS_PREFIX=workspace \
  -- /abs/path/to/repo/venv/bin/python /abs/path/to/repo/tooling/m4l_mcp_server.py
```

Restart Claude Code after adding. Full per-IDE matrix (Claude Desktop, Cursor, Gemini, Copilot, etc.) + critical warnings about which files Claude Code does **NOT** read: **[`docs/AGENT_REFERENCE.md#pipeline-mcp-server-optional-ide-mcp`](docs/AGENT_REFERENCE.md#pipeline-mcp-server-optional-ide-mcp)** — single source of truth, do not duplicate config blocks here.

### Typical AI workflow via MCP

1. **Orient**: `live_session_state()` → know what tracks and devices are loaded
2. **Design**: `compose_spec_from_dsl(...)` or hand-write spec → `validate_spec`
3. **Build + load**: `live_build_and_verify(spec)` → device appears on a new track
4. **Inspect**: `live_track_devices(track_index)` → see all params with current values
5. **Tweak**: `live_set_param(track, device, "Gain", -6.0)` → real-time adjustment
6. **Perform**: `live_transport("play")` / `live_create_midi_clip(...)` / `live_fire_clip(...)`
7. **Clean up**: `live_delete_track(index)` or `live_clear_track(index)`
