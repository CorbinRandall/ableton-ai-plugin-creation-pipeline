# Roadmap

Phased improvements for the M4L pipeline.

## Architecture

```mermaid
flowchart LR
  Spec[spec.json]
  Validate[validate_spec]
  Build[build_amxd]
  Deploy[User Library]
  MCP[AbletonMCP]
  Spec --> Validate --> Build --> Deploy --> MCP
```

M4L devices are **Max patchers** inside **`.amxd`**, running only in **Ableton Live** (macOS/Windows). Host Python tooling runs on **macOS, Windows, or Linux**.

## Phase 1 — Agent ergonomics (done)

| Item | Status |
|------|--------|
| Spec schema + `validate_spec.py` | Done |
| Templates + `scaffold_plugin.py` | Done |
| `export_spec_from_amxd.py` | Done |
| `AGENT_TOOLS.md`, `AGENTIC_IDES.md`, multi-editor pointers | Done |
| `build_adv`, pinned OSC/MCP archives | Done |

## Phase 2 — Quality loop (done)

| Item | Status |
|------|--------|
| Generalized `m4l_verify.py` (`--spec`, `--device-type`) | Done |
| `live_osc_helpers.py` + `m4l_parameter_sweep.py` | Done |
| `check_spec_layout.py` (presentation overlap) | Done |
| [`AUDIO_SMOKE_TEST.md`](AUDIO_SMOKE_TEST.md) (manual) | Done |

**CI:** No Live on GitHub Actions — validate + `build` only. Full verify on a Mac/PC with Ableton.

## Phase 3 — Automation (done / optional use)

| Item | Status |
|------|--------|
| [`examples/sdk-run-setup/`](../examples/sdk-run-setup/) shell wrappers | Done |
| Optional Cursor SDK script (`run-setup.mjs`) | Done (optional) |
| [Ableton maxdevtools](https://github.com/Ableton/maxdevtools) | Documented in CONTRIBUTING |
| Self-hosted Live runner | Out of scope |

## Cross-cutting

| Doc | Purpose |
|-----|---------|
| [`CROSS_PLATFORM.md`](CROSS_PLATFORM.md) | macOS / Windows / Linux + any agentic IDE |
| [`AGENTIC_IDES.md`](AGENTIC_IDES.md) | Editor-specific optional notes |

## Can vs cannot

| Can | Cannot |
|-----|--------|
| Spec-first build from JSON | Headless Max.app Save As |
| Export `.amxd` → spec | Edit open device patch via MCP |
| MCP load + OSC on Mac/PC | Live on Linux |
| Any agentic IDE with shell | Guaranteed audio QA in CI |

## Upstream

| Repo | Install |
|------|---------|
| [ideoforms/AbletonOSC](https://github.com/ideoforms/AbletonOSC) | Pinned ZIP — `ableton_bootstrap_common.py` |
| [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) | Pinned ZIP + local patches |

Override: `BOOTSTRAP_ABLETON_OSC_ARCHIVE` / `BOOTSTRAP_ABLETON_MCP_ARCHIVE`.
