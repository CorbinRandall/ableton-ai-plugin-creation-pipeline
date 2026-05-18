# Examples

## Agentic IDEs (all editors)

Start with **[`docs/AGENTIC_IDES.md`](../docs/AGENTIC_IDES.md)** — Cursor, Claude Code, Copilot, Windsurf, terminal-only, etc.

This pipeline does **not** require a repo-bundled IDE MCP config. Agents run Python/shell from **[`docs/AGENT_TOOLS.md`](../docs/AGENT_TOOLS.md)**.

### Cursor-only

- Rules: [`.cursor/rules/m4l-pipeline.mdc`](../.cursor/rules/m4l-pipeline.mdc)
- Do **not** let bootstrap overwrite `~/.cursor/mcp.json` (see [`scripts/m4l_fresh_reset_backup_and_restore.md`](../scripts/m4l_fresh_reset_backup_and_restore.md))

### Claude Code

- [`CLAUDE.md`](../CLAUDE.md) at repo root

### GitHub Copilot

- [`.github/copilot-instructions.md`](../.github/copilot-instructions.md)

## Cursor SDK (Phase 3, optional)

A minimal `@cursor/sdk` runner that executes `./run` on a clone may be added under `sdk-run-setup/` later. See [`docs/ROADMAP.md`](../docs/ROADMAP.md). Not required for normal IDE agent use.
