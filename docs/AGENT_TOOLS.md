# Agent tools — commands for any agentic IDE

Use these from the **repository root** after `./run` (step 2). Same commands in **Cursor, Claude Code, Copilot, Windsurf, terminal + agent**, etc.

**IDE setup:** [`AGENTIC_IDES.md`](AGENTIC_IDES.md) · **Agent behavior:** [`AGENTS.md`](../AGENTS.md)

## Ableton MCP vs IDE MCP

| | AbletonMCP | IDE MCP (optional) |
|---|------------|---------------------|
| **What** | Remote Script in **Live** Preferences | Extra servers in Cursor / Claude Desktop config |
| **Port** | TCP **9877** | Varies |
| **This repo** | **Required** for `./run --live` | **Not required** |

Do not tell users to install a Cursor MCP server package unless they want IDE features beyond this pipeline.

## Onboarding (human + agent)

| Step | Agent action |
|------|----------------|
| 1 | Remind user: **quit Ableton** |
| 2 | Run `./run` → `M4L_RUN_OK` |
| 3 | **No shell** — guide AbletonOSC + AbletonMCP; wait for **Continue** |
| 4 | Run `./run --live` → `M4L_PIPELINE_READY` |
| 5 | Ask what **midi_effect** / **audio_effect** / **instrument** to build |

Full copy: [`AGENTS.md`](../AGENTS.md) · [`GETTING_STARTED.md`](GETTING_STARTED.md)

## Tool table

| User intent | Command |
|-------------|---------|
| Validate spec (schema + UI) | `./venv/bin/python scripts/validate_spec.py path/to/spec.json` |
| UI-only check | `./venv/bin/python scripts/check_spec_ui.py path/to/spec.json` |
| Scaffold workspace plugin | `./venv/bin/python scripts/scaffold_plugin.py --name MyPlugin --type midi_effect` |
| Export Max save → spec | `./venv/bin/python scripts/export_spec_from_amxd.py device.amxd -o spec.json --device-type midi_effect` |
| Build `.amxd` only | `./venv/bin/python tooling/m4l_pipeline.py build spec.json [out.amxd]` |
| Build + deploy + load | `./venv/bin/python tooling/m4l_pipeline.py all spec.json` |
| Same, no Live | `... all spec.json --no-live` |
| Include `.adv` preset | `... all spec.json --with-adv` or `M4L_BUILD_ADV=1` |
| Skip validation | `... build spec.json --skip-validate` or `M4L_SKIP_VALIDATE=1` |
| Preflight stack | `./venv/bin/python scripts/verify_setup.py --preflight` |
| Wait for MCP | `./venv/bin/python scripts/verify_setup.py --wait-mcp 120` |
| Tutorial verify | `./venv/bin/python scripts/m4l_verify.py` |

## Markers (grep stdout)

| Marker | Meaning |
|--------|---------|
| `M4L_RUN_OK` | `./run` step finished |
| `M4L_PIPELINE_READY` | Live connected + tutorial loaded |
| `SPEC_VALIDATE_OK` | Spec passed schema + UI checks |
| `SPEC_UI_OK` | UI check only |
| `SCAFFOLD_OK` | Workspace project created |
| `EXPORT_SPEC_OK` | Export from `.amxd` done |

## Environment

| Variable | Purpose |
|----------|---------|
| `M4L_PROJECTS_PREFIX=workspace` | Builds under `projects/workspace/` |
| `M4L_SKIP_LIVE=1` | Skip MCP load in `all` |
| `M4L_SKIP_VALIDATE=1` | Skip spec validation before build |
| `M4L_BUILD_ADV=1` | Generate + deploy `.adv` with `all` |

## Templates

See [`tooling/templates/README.md`](../tooling/templates/README.md).

## Per-IDE config (optional)

| IDE | Auto-loaded instructions |
|-----|--------------------------|
| **Any** | [`AGENTS.md`](../AGENTS.md), this file |
| **Cursor** | [`.cursor/rules/m4l-pipeline.mdc`](../.cursor/rules/m4l-pipeline.mdc) |
| **Claude Code** | [`CLAUDE.md`](../CLAUDE.md) |
| **GitHub Copilot** | [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) |

See [`examples/README.md`](../examples/README.md). **Do not** overwrite `~/.cursor/mcp.json` from bootstrap.
