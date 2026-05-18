# First-time setup with an AI coding assistant (Cursor / similar)

**Quit Ableton → clone → “run” → agent guides Live setup → “continue” → pipeline ready → describe your plugin.**

**Full checklist:** **[`GETTING_STARTED.md`](GETTING_STARTED.md)**

---

## Steps

| Step | Ableton | Who |
|------|---------|-----|
| **1** | **Closed** | You quit Live |
| **2** | **Closed** | You clone + **“Run”**; agent runs **`./run`** |
| **3** | Open (you) | **Agent** explains OSC/MCP; you say **“continue”** when done |
| **4** | **Open** | Agent runs **`./run --live`** |
| **5** | **Open** | Agent confirms **pipeline ready**; asks what **`.amxd`** you want |

---

## Step 1 — Close Ableton

Quit Live fully before step 2.

---

## Step 2 — Clone and “run”

1. Clone → open **repo root** in the IDE.  
2. Say **“Run”**.  
3. Wait for **`M4L_RUN_OK`**.

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

The agent should celebrate the connected pipeline and ask what device type you want (**MIDI effect**, **audio effect**, **instrument**).

Use **`projects/workspace/`** for personal work — **[`PRIVATE_PLUGINS.md`](PRIVATE_PLUGINS.md)**.

---

## Cursor tips

- Open the **repo root**.  
- **“Run”** → later **“Continue”** → then describe your plugin.  
- No passwords needed for the tutorial.
