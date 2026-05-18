# First-time setup with an agentic IDE

**Quit Ableton → clone → “run” → agent guides Live setup → “continue” → pipeline ready → describe your plugin.**

Works the same in **Cursor, Claude Code, GitHub Copilot, Windsurf, Zed**, or any tool that can run terminal commands in the project folder.

**Full checklist:** [`GETTING_STARTED.md`](GETTING_STARTED.md) · **By editor:** [`AGENTIC_IDES.md`](AGENTIC_IDES.md) · **Commands:** [`AGENT_TOOLS.md`](AGENT_TOOLS.md)

---

## Steps

| Step | Ableton | Who |
|------|---------|-----|
| **1** | **Closed** | You quit Live |
| **2** | **Closed** | You clone + **“Run”**; agent runs **`./run`** |
| **3** | Open (you) | **Agent** explains OSC/MCP in Live; you say **“continue”** |
| **4** | **Open** | Agent runs **`./run --live`** |
| **5** | **Open** | Agent asks what **`.amxd`** you want |

---

## Step 1 — Close Ableton

Quit Live fully before step 2.

---

## Step 2 — Clone and “run”

1. Clone → open **repo root** in your editor (folder with **`run`** and **`AGENTS.md`**).  
2. Open the **agent / chat** panel (name varies by IDE).  
3. Say **“Run”** or **“Run `./run` from the repo root.”**  
4. Wait for **`M4L_RUN_OK`**.

---

## Step 3 — Agent guides Control Surfaces

The agent should **not** run terminal commands here. It walks you through:

- Quit/reopen Live  
- **Preferences → Link / Tempo / MIDI**  
- **AbletonOSC**, then **AbletonMCP** (I/O blank)  
- Keep Live open  

When finished, reply: **“Continue — OSC and MCP are enabled.”**

---

## Step 4 — Say “continue”

The agent runs **`./run --live`**. Tutorial device loads on a new track.

Look for **`M4L_PIPELINE_READY`**.

---

## Step 5 — Build your plugin

The agent should confirm the pipeline is connected and ask what device type you want.

Use **`projects/workspace/`** for personal work — [`PRIVATE_PLUGINS.md`](PRIVATE_PLUGINS.md).

---

## Tips by IDE

### Cursor

- **File → Open Folder** → repo root.  
- Rules load from [`.cursor/rules/m4l-pipeline.mdc`](../.cursor/rules/m4l-pipeline.mdc).  
- Approve terminal when the agent runs **`./run`**.

### Claude Code

- Open repo root; [`CLAUDE.md`](../CLAUDE.md) points to **`AGENTS.md`**.

### GitHub Copilot (VS Code, etc.)

- Open repo root; see [`.github/copilot-instructions.md`](../.github/copilot-instructions.md).  
- Use integrated terminal or let Copilot run commands.

### Other agents

Paste once if needed:

> Read `AGENTS.md` and run `./run` from the repo root. Ableton should be quit first.

---

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Opened a subfolder only (`projects/…`) | Open **repo root** |
| Confused **Cursor MCP** with **AbletonMCP** | Enable **AbletonMCP** in **Live** Preferences |
| Ran `--live` before Control Surfaces | Finish step 3, then **Continue** |

No passwords needed for the tutorial.
