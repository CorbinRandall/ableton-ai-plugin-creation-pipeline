# Agentic IDEs — setup by editor

**Total beginners:** [`START_HERE.md`](START_HERE.md) — chat with the AI only; it runs setup.

This repo works with **any agentic coding environment** that can run terminal commands in the project folder. You do **not** need a specific IDE or IDE MCP server to build Max for Live devices.

**Same pipeline** whether the human types commands or the agent does — beginners should **never** need the terminal.

**Shared contract:** [`AGENTS.md`](../AGENTS.md) · **Commands:** [`AGENT_TOOLS.md`](AGENT_TOOLS.md) · **OS notes:** [`CROSS_PLATFORM.md`](CROSS_PLATFORM.md)

---

## Two different “MCP” meanings

| Name | What it is | Required? |
|------|------------|-----------|
| **AbletonMCP** (Remote Script) | Ableton **Control Surface** in Live; TCP **9877** | **Yes** for `./run --live` |
| **IDE MCP servers** | Optional extras in some editors’ global config | **No** for this pipeline |

Python tools talk to **AbletonMCP in Live** directly.

---

## What every IDE needs (same everywhere)

1. Open the **repository root** (folder containing `run`, `AGENTS.md`, `tooling/`).
2. Give the agent **terminal / shell** access.
3. Say **“run”** → agent runs **`./run`** (macOS/Linux) or **`.\run.ps1`** (Windows). **Quit Ableton** first.
4. After **`M4L_RUN_OK`**, complete step 3 in Live → reply **“continue”** → **`./run --live`**.
5. Use [`AGENT_TOOLS.md`](AGENT_TOOLS.md) for validate / scaffold / build.

**Prompts:** `Run`, `Continue`, `Run ./run --live`, `Validate my spec`.

---

## Optional per-editor pointers

These files **duplicate nothing** — they point agents at `AGENTS.md`.

| Editor | Extra file (optional) |
|--------|------------------------|
| **Any** | [`AGENTS.md`](../AGENTS.md) |
| **Cursor** | [`.cursor/rules/m4l-pipeline.mdc`](../.cursor/rules/m4l-pipeline.mdc) |
| **Claude Code** | [`CLAUDE.md`](../CLAUDE.md) |
| **GitHub Copilot** | [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) |
| **Windsurf, Zed, Continue, Cody, …** | Paste: “Follow `AGENTS.md` and run `./run` from repo root.” |

### Cursor (optional)

- Open **repo root**; rules load from `.cursor/rules/`.
- Approve terminal for `./run` or `.\run.ps1`.
- Do **not** confuse **Cursor MCP settings** with **AbletonMCP** in Live.

### Claude Code (optional)

- [`CLAUDE.md`](../CLAUDE.md) at repo root.

### GitHub Copilot (optional)

- [`.github/copilot-instructions.md`](../.github/copilot-instructions.md).

### Terminal only

No IDE required — see [`CROSS_PLATFORM.md`](CROSS_PLATFORM.md).

---

## What we do not ship

- No required IDE MCP manifest — but `tooling/m4l_mcp_server.py` is a ready-to-wire stdio server with build + Live control tools (see [`AGENT_TOOLS.md`](AGENT_TOOLS.md)).
- No editor-specific lock-in for build/deploy.
- Optional automation: [`examples/sdk-run-setup/`](../examples/sdk-run-setup/) (shell + optional Cursor SDK).
