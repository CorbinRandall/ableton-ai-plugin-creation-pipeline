# Agent reference — tools, markers, ports, privacy

Full detail moved from [`AGENTS.md`](../AGENTS.md). Read that file first for the imperative onboarding contract.

## Step 3 — Ableton setup (Control Surfaces)

1. Quit Ableton completely, then reopen.
2. **Preferences → Link / Tempo / MIDI**
3. Control Surface row 1 → **AbletonOSC** (Input/Output: None)
4. Control Surface row 2 → **AbletonMCP**
5. Leave Live open; reply **Continue** / **Ready**

## Step 5 — After pipeline ready

Suggest smoke-test: `examples/simple_gain_audio_spec.json` with `--with-adv`.

Build flow:

1. `./venv/bin/python scripts/scaffold_plugin.py --name MyPlugin --type midi_effect` (optional)
2. `./venv/bin/python scripts/validate_spec.py path/to/spec.json`
3. `./venv/bin/python tooling/m4l_pipeline.py all path/to/spec.json`

Or use **`tooling/spec_builder.py`** + **`examples/recipes/`** — see [`AGENT_IMPLEMENTATION_PLAN.md`](AGENT_IMPLEMENTATION_PLAN.md).

## Tool table

| Intent | Command |
|--------|---------|
| DSL compose | `tooling/spec_builder.py` or `examples/recipes/*/build.py` |
| Validate spec | `./venv/bin/python scripts/validate_spec.py spec.json` |
| UI preview (SVG) | `./venv/bin/python tooling/spec_to_svg.py spec.json -o preview.svg` |
| Scaffold workspace | `./venv/bin/python scripts/scaffold_plugin.py --name X --type midi_effect` |
| Export `.amxd` → spec | `./venv/bin/python scripts/export_spec_from_amxd.py device.amxd -o spec.json` |
| Build + deploy + load | `./venv/bin/python tooling/m4l_pipeline.py all spec.json` |
| Offline verify | `./venv/bin/python tooling/m4l_pipeline.py verify spec.json` |
| Patch UI | `./venv/bin/python tooling/m4l_pipeline.py patch device.amxd --bgcolor 0,0,0,1` |
| Diagnose errors | `echo "error text" \| ./venv/bin/python tooling/m4l_pipeline.py diagnose` |
| Live verify | `./venv/bin/python scripts/m4l_verify.py` |
| Pipeline MCP server | `./venv/bin/python tooling/m4l_mcp_server.py` (optional IDE MCP) |

Add **`--json`** to supported scripts for machine-readable stdout (one JSON object only; markers print without `--json`).

## Pipeline MCP server (optional IDE MCP)

**AbletonMCP** (Live Control Surface, TCP 9877) is **not** the same as this server.

Example Cursor / Claude Desktop config:

```json
{
  "mcpServers": {
    "m4l-pipeline": {
      "command": "/abs/path/to/repo/venv/bin/python",
      "args": ["/abs/path/to/repo/tooling/m4l_mcp_server.py"]
    }
  }
}
```

Requires `pip install 'mcp>=1.2.0'`.

## Other flags

| Flag | When |
|------|------|
| `all --no-live` | Build + deploy only |
| `all --with-adv` | Also build/deploy `.adv` preset |
| `all --skip-validate` | Skip spec validation |

## Do not

- Open a PR unless the user asks.
- Run `--live` before Control Surfaces are confirmed.
- Commit under `projects/` except tutorial sources.
- Put private plugin names in tracked files — use `projects/workspace/`.
- Put private names in branch/PR/commit subjects on this public repo.
- Claim audio devices “confirmed working” without `m4l_verify.py` T3+ or human T5 ack.

## Key paths

| Path | Role |
|------|------|
| `./run` | First-time setup (Ableton closed) |
| `./run --live` | Connect after Control Surfaces |
| `tooling/m4l_pipeline.py` | Build, deploy, load CLI |
| `tooling/spec_builder.py` | DSL for specs |
| `examples/recipes/` | Named device patterns |
| `projects/workspace/` | Gitignored personal plugins |

## Ports

| Component | Port |
|-----------|------|
| AbletonOSC | UDP 11000 |
| AbletonMCP | TCP 9877 |

## Markers

| Marker | Meaning |
|--------|---------|
| `M4L_RUN_OK` | `./run` finished |
| `M4L_PIPELINE_READY` | Live connected |
| `SPEC_VALIDATE_OK` | Spec passed |
| `M4L_VERIFY_OK` | Live verify T2/T3 |
| `M4L_VERIFY_OFFLINE_OK` | Offline build verify |
| `SCHEMA_NEGATIVES_OK` | Bad-spec tests |
| `SPEC_BUILDER_OK` | DSL self-test |
| `RECIPE_BUILD_OK` | Recipe spec written |
| `SPEC_SVG_OK` | SVG preview |
| `DEVICE_SELFTEST_OK` | T4 UDP self-test |

Tier honesty: [`VERIFICATION_TIERS.md`](VERIFICATION_TIERS.md).
