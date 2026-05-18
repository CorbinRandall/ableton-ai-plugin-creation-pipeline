# Agentic IDEs — setup by editor

This repo works with **any agentic coding environment** that can run terminal commands in the project folder. You do **not** need a special IDE plugin to build Max for Live devices.

**Shared agent contract:** [`AGENTS.md`](../AGENTS.md) · **Command reference:** [`AGENT_TOOLS.md`](AGENT_TOOLS.md) · **Human steps:** [`GETTING_STARTED.md`](GETTING_STARTED.md)

---

## Two different “MCP” meanings (read this once)

| Name | What it is | Required? |
|------|------------|-----------|
| **AbletonMCP** (Remote Script) | Ableton **Control Surface** in Live; TCP **9877** inside Live | **Yes** for `./run --live` and loading devices |
| **IDE MCP servers** | Optional extras in Cursor / Claude Desktop / etc. (`~/.cursor/mcp.json`, …) | **No** for this pipeline |

Python tools in this repo talk to **AbletonMCP in Live** directly. They do **not** require wiring the ahujasid **Cursor MCP server** package unless you want separate IDE features.

---

## What every IDE needs (same everywhere)

1. Open the **repository root** (folder containing `run`, `AGENTS.md`, `tooling/`).
2. Give the agent **terminal / shell** access.
3. Say **“run”** → agent runs **`./run`** (Ableton **quit** first).
4. After **`M4L_RUN_OK`**, complete step 3 in Live (surfaces), then **“continue”** → **`./run --live`**.
5. Use commands from [`AGENT_TOOLS.md`](AGENT_TOOLS.md) for validate / scaffold / build.

**Prompts that work in any IDE:** `Run`, `Continue`, `Run ./run --live`, `Validate my spec`, `Scaffold a midi effect called MyPlugin`.

---

## IDE-specific notes

### Cursor

| Item | Location |
|------|----------|
| Auto-loaded rules | [`.cursor/rules/m4l-pipeline.mdc`](../.cursor/rules/m4l-pipeline.mdc) |
| Agent instructions | [`AGENTS.md`](../AGENTS.md) (also read by other tools) |
| Optional global MCP | `~/.cursor/mcp.json` — **merge manually**; bootstrap must **not** overwrite it |

**Cursor tips:** Use **Agent** mode with the repo root open. Approve terminal runs for `./run`. See [`AGENT_IDE_BEGINNER_GUIDE.md`](AGENT_IDE_BEGINNER_GUIDE.md).

**Do not** confuse Cursor’s MCP settings with **AbletonMCP** in Live Preferences.

### Claude Code (CLI / desktop)

| Item | Location |
|------|----------|
| Project instructions | [`CLAUDE.md`](../CLAUDE.md) → points to `AGENTS.md` |
| Same terminal flow | `./run`, `./run --live`, `tooling/m4l_pipeline.py` |

### GitHub Copilot (VS Code, JetBrains, …)

| Item | Location |
|------|----------|
| Repo instructions | [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) |
| Open folder | Repo root in VS Code / compatible editor |

Use **Copilot Chat** with workspace context; ask it to run `./run` from the integrated terminal.

### Windsurf, Zed, Continue, Cody, etc.

No extra config required. Open the repo root, ensure the agent can execute shell commands, and reference **`AGENTS.md`** in chat if the tool does not auto-load it:

> Follow `AGENTS.md` in this repo. Run `./run` from the repo root.

### Terminal only (no agent IDE)

```bash
./run
# … configure Live …
./run --live
./venv/bin/python tooling/m4l_pipeline.py all path/to/spec.json
```

---

## Files agents may auto-discover

| File | Typical readers |
|------|-----------------|
| [`AGENTS.md`](../AGENTS.md) | Cursor, many agents, GitHub |
| [`CLAUDE.md`](../CLAUDE.md) | Claude Code |
| [`.cursor/rules/*.mdc`](../.cursor/rules/) | Cursor only |
| [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) | GitHub Copilot |

Content is intentionally **short pointers** to one source of truth (`AGENTS.md` + `AGENT_TOOLS.md`) so we do not maintain five diverging copies.

---

## What we do not ship per IDE

- No required **Cursor MCP server** manifest in this repo (avoids clobbering `~/.cursor/mcp.json`).
- No Windsurf / Zed proprietary config beyond universal docs.
- No Max application automation — see [`MAX_TO_SPEC.md`](MAX_TO_SPEC.md).

Optional automation examples (e.g. Cursor SDK) may appear under [`examples/`](../examples/) — still optional.
