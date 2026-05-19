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
| First validated custom device (gain knob, audio) | `scripts/validate_spec.py examples/simple_gain_audio_spec.json` then `tooling/m4l_pipeline.py all examples/simple_gain_audio_spec.json --with-adv` |
| Validate spec (schema + UI + layout) | `scripts/validate_spec.py path/to/spec.json` |
| UI only | `scripts/check_spec_ui.py …` |
| Layout overlaps | `scripts/check_spec_layout.py …` |
| Scaffold workspace plugin | `scripts/scaffold_plugin.py --name MyPlugin --type midi_effect` |
| Export `.amxd` → spec | `scripts/export_spec_from_amxd.py device.amxd -o spec.json` |
| Build `.amxd` only | `tooling/m4l_pipeline.py build spec.json` |
| Build + deploy + load | `tooling/m4l_pipeline.py all spec.json` |
| Same, no Live | `… all spec.json --no-live` |
| Include `.adv` | `… all spec.json --with-adv` or `M4L_BUILD_ADV=1` |
| Skip validation | `… --skip-validate` or `M4L_SKIP_VALIDATE=1` |
| Preflight | `scripts/verify_setup.py --preflight` |
| Wait for MCP | `scripts/verify_setup.py --wait-mcp 120` |
| Live verify | `scripts/m4l_verify.py` (see [`VERIFY_GUIDE.md`](VERIFY_GUIDE.md)) |
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
| `M4L_PARAM_SWEEP_OK` | Parameter OSC read/write OK |

## Environment

| Variable | Purpose |
|----------|---------|
| `M4L_PROJECTS_PREFIX=workspace` | Builds under `projects/workspace/` |
| `M4L_SKIP_LIVE=1` | Skip MCP load in `all` |
| `M4L_SKIP_VALIDATE=1` | Skip spec validation before build |
| `M4L_BUILD_ADV=1` | Generate/deploy `.adv` with `all` |
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
