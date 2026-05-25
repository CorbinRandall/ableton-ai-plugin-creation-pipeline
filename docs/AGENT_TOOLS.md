# Agent tools — any agentic IDE, any host OS

Commands run from the **repository root** after `./run` (step 2). Same flow in **Cursor, Claude Code, Copilot, Windsurf, Zed**, terminal-only, etc.

| Doc | Purpose |
|-----|---------|
| [`AGENTIC_IDES.md`](AGENTIC_IDES.md) | Optional per-editor notes |
| [`CROSS_PLATFORM.md`](CROSS_PLATFORM.md) | macOS / Windows / Linux commands |
| [`AGENTS.md`](../AGENTS.md) | Onboarding steps 1–5 |

## Ableton MCP vs IDE MCP

| | AbletonMCP (required for Live) | IDE MCP servers (optional) |
|---|-------------------------------|---------------------------|
| **Where** | Live → Control Surface | Your editor’s settings file |
| **Port** | TCP **9877** | Varies |
| **This repo** | Used by Python tools | **Not required** |

## Python invocation

| Platform | Example |
|----------|---------|
| macOS / Linux | `./venv/bin/python scripts/validate_spec.py spec.json` |
| Windows | `.\venv\Scripts\python.exe scripts\validate_spec.py spec.json` |

## Tool table

| User intent | Command |
|-------------|---------|
| First validated custom device (Gain dial, audio FX shell) | `scripts/validate_spec.py examples/simple_gain_audio_spec.json` then `tooling/m4l_pipeline.py all examples/simple_gain_audio_spec.json --with-adv` |
| Validate spec (schema + UI + layout) | `scripts/validate_spec.py path/to/spec.json` |
| UI only | `scripts/check_spec_ui.py …` |
| Layout overlaps | `scripts/check_spec_layout.py …` |
| Scaffold workspace plugin | `scripts/scaffold_plugin.py --name MyPlugin --type midi_effect` |
| Export `.amxd` → spec | `scripts/export_spec_from_amxd.py device.amxd -o spec.json` |
| Build `.amxd` only | `tooling/m4l_pipeline.py build spec.json` |
| Offline verify (validate + build + sidecar) | `tooling/m4l_pipeline.py verify spec.json` |
| Patch UI on existing `.amxd` (Max-first) | `tooling/m4l_pipeline.py patch device.amxd --bgcolor 0,0,0,1 [--deploy midi_effect]` |
| Deploy artifact to Imported/ | `tooling/m4l_pipeline.py deploy device.amxd [device_type]` |
| Build + deploy + load | `tooling/m4l_pipeline.py all spec.json` |
| Same, no Live | `… all spec.json --no-live` |
| Include `.adv` | `… all spec.json --with-adv` or `M4L_BUILD_ADV=1` |
| Start new major line (2.1) | `… all spec.json --bump-major` or `M4L_VERSION_BUMP=major` (only when user asks) |
| Versioning policy | [`VERSIONING.md`](VERSIONING.md) |
| Skip validation | `… --skip-validate` or `M4L_SKIP_VALIDATE=1` |
| Wait for MCP | `scripts/verify_setup.py --wait-mcp 120` |
| Confirm MCP can create **audio** tracks (after Live restart post-install) | `scripts/verify_setup.py --wait-mcp 120 --assert-create-audio-track` |
| Preflight | `scripts/verify_setup.py --preflight` |
| Live verify | `scripts/m4l_verify.py` (see [`VERIFY_GUIDE.md`](VERIFY_GUIDE.md)) |
| Donor appversion consistency | `scripts/check_donor_consistency.py` |
| Deploy / patch unit tests (offline) | `scripts/test_m4l_pipeline_deploy.py` |
| Block staging workspace content | `scripts/check_workspace_not_staged.py` |
| Install workspace pre-commit hook | `scripts/install_workspace_pre_commit.py` |
| Troubleshooting CreateDevice errors | [`TROUBLESHOOTING_M4L.md`](TROUBLESHOOTING_M4L.md) |
| Parameter sweep | `scripts/m4l_parameter_sweep.py --track N --device D` |
| Audio checklist (manual) | [`AUDIO_SMOKE_TEST.md`](AUDIO_SMOKE_TEST.md) |

## Entry scripts (OS-specific)

| Platform | Setup | Live open |
|----------|-------|-----------|
| macOS / Linux | `./run` | `./run --live` |
| Windows | `.\run.ps1` | `.\run.ps1 -Live` |

## Markers (grep stdout)

| Marker | Meaning |
|--------|---------|
| `M4L_RUN_OK` | `./run` step finished |
| `M4L_PIPELINE_READY` | Live connected + tutorial loaded |
| `SPEC_VALIDATE_OK` | Spec passed checks |
| `SPEC_UI_OK` | UI check only |
| `SPEC_LAYOUT_OK` | Layout check only |
| `SCAFFOLD_OK` | Workspace project created |
| `EXPORT_SPEC_OK` | Export from `.amxd` done |
| `M4L_VERIFY_OK` | Live verify passed |
| `M4L_VERIFY_OFFLINE_OK` | `m4l_pipeline.py verify` passed (no Live) |
| `M4L_AUDIO_MCP_OK` | `verify_setup.py --assert-create-audio-track` succeeded |
| `M4L_PARAM_SWEEP_OK` | Parameter OSC read/write OK |

## Environment

| Variable | Purpose |
|----------|---------|
| `M4L_PROJECTS_PREFIX=workspace` | Builds under `projects/workspace/` |
| `M4L_SKIP_LIVE=1` | Skip MCP load in `all` |
| `M4L_SKIP_VALIDATE=1` | Skip spec validation before build |
| `M4L_BUILD_ADV=1` | Generate/deploy `.adv` with `all` |
| `M4L_VERSION_BUMP=major` | Next `all` uses major bump (default: patch — see [`VERSIONING.md`](VERSIONING.md)) |
| `M4L_APPVERSION=9.1.4` | Override Max appversion stamp on build (default: preserve donor) |
| `M4L_APPVERSION_JSON_FILE=/path` | Full appversion dict override (rare) |
| `M4L_ALLOW_AUDIO_ON_MIDI=1` | Debug only: load `audio_effect` on MIDI if MCP lacks `create_audio_track` (usually breaks in Live) |
| `ABLETON_HOME` | Override Ableton user folder |

## Templates

[`tooling/templates/README.md`](../tooling/templates/README.md)

## Optional editor config (do not auto-overwrite)

| Editor | Pointer file |
|--------|----------------|
| Any | [`AGENTS.md`](../AGENTS.md) |
| Cursor | [`.cursor/rules/m4l-pipeline.mdc`](../.cursor/rules/m4l-pipeline.mdc) |
| Claude Code | [`CLAUDE.md`](../CLAUDE.md) |
| GitHub Copilot | [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) |

See [`examples/README.md`](../examples/README.md).

## Pipeline MCP server (optional IDE MCP)

**AbletonMCP** in Live (Control Surface, TCP 9877) is **not** this server.

`tooling/m4l_mcp_server.py` is a **FastMCP stdio server** exposing the full pipeline plus direct Live control. When wired as an IDE MCP server, you use tool calls instead of shell commands.

### Build + recipe tools
| Tool | Purpose |
|------|---------|
| `list_recipes` | Browse built-in device examples |
| `read_recipe_spec(slug)` | Get spec dict for a named recipe |
| `compose_spec_from_dsl(python_source)` | Build spec from Python DSL snippet |
| `validate_spec(spec)` | Validate spec dict |
| `spec_to_svg(spec)` | Render UI preview as SVG |
| `build_amxd_tool(spec, out_path?)` | Build `.amxd` file (no Live) |
| `deploy(amxd_path, device_type)` | Copy `.amxd` to User Library Imported/ |
| `load_in_live(spec, with_adv?)` | Build + deploy + load on a new track |
| `diagnose(error_text)` | Map error text to known fixes |

### Live-control tools (require Live + AbletonMCP + AbletonOSC running)
| Tool | Purpose |
|------|---------|
| `live_session_state()` | Full session snapshot: all tracks, devices, tempo |
| `live_track_devices(track_index)` | Devices + param names/values/ranges on one track |
| `live_set_param(track, device, param, value)` | Set device parameter by name or index |
| `live_transport(action, bpm?)` | `"play"` / `"stop"` / `"set_tempo"` |
| `live_create_midi_clip(track, slot, notes, length_beats?)` | Create MIDI clip with notes |
| `live_fire_clip(track, slot)` | Launch a clip slot |
| `live_stop_clip(track, slot)` | Stop a clip slot |
| `live_delete_track(track_index)` | Delete a track |
| `live_rename_track(track_index, name)` | Rename a track |
| `live_clear_track(track_index)` | Remove all devices from a track |
| `live_build_and_verify(spec, with_adv?)` | Full build→deploy→load→OSC verify in one call |

### Install

```bash
pip install 'mcp>=1.2.0'   # already in requirements.txt
```

### Config — per IDE

The right config file differs per editor and **Claude Code in particular requires a non-obvious location** (`~/.claude.json` or `claude mcp add`, NOT `settings.json`). The full matrix lives in **[`AGENT_REFERENCE.md#pipeline-mcp-server-optional-ide-mcp`](AGENT_REFERENCE.md#pipeline-mcp-server-optional-ide-mcp)** — single source of truth. Do not paste a generic JSON template here; agents will pick the wrong file and config will silently fail to load.

### Typical AI workflow via MCP

1. `live_session_state()` — see all tracks and devices before acting
2. `compose_spec_from_dsl(...)` → `validate_spec(...)` — design the device
3. `live_build_and_verify(spec)` — one call: build + load + verify; returns track index + params
4. `live_track_devices(track_index)` — inspect params with current values and ranges
5. `live_set_param(track, device, "Gain", -6.0)` — real-time tweak
6. `live_transport("play")` / `live_create_midi_clip(...)` / `live_fire_clip(...)` — perform
7. `live_delete_track(index)` / `live_clear_track(index)` — clean up test tracks

Full v2 plan: [`docs/AGENT_IMPLEMENTATION_PLAN.md`](AGENT_IMPLEMENTATION_PLAN.md).

