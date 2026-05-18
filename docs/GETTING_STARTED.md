# Getting started (humans) — clone to device on a Live track

Step-by-step with an **agentic IDE** (Cursor, Claude Code, Copilot, Windsurf, …) or on your own.

Technical reference: **[`RUN.md`](RUN.md)** · Agent rules: **[`AGENTS.md`](../AGENTS.md)** · **By editor:** **[`AGENTIC_IDES.md`](AGENTIC_IDES.md)**

---

## Steps at a glance

| Step | Ableton | Who | What happens |
|------|---------|-----|----------------|
| **1** | **Closed** | You | **Quit Live** completely |
| **2** | **Closed** | You + agent | **Clone** → open repo in IDE → say **“run”** → agent runs **`./run`** |
| **3** | Open (you) | **Agent guides you** | Agent walks you through **AbletonOSC** + **AbletonMCP**; you reply when ready |
| **4** | **Open** | Agent | You say **“continue”** (or similar) → agent runs **`./run --live`** |
| **5** | **Open** | Agent + you | **Pipeline connected** — agent asks what **`.amxd`** you want to build |

---

## Before you start (once per computer)

| You need | Why |
|----------|-----|
| **Ableton Live** opened **at least once** on this account | Creates `User Library` and prefs folders |
| **Suite**, or **Standard + Max for Live add-on** | Lite/Intro cannot run M4L devices |
| **Terminal permission** + write **`venv/`** in the repo | Bootstrap |
| **Write access** to `~/Music/Ableton` (macOS) or `~/Documents/Ableton` (Windows) | Remote Scripts + deploy |
| **Network** (first time) | Downloads tools and deps |

No API keys for the tutorial pipeline.

---

## Step 1 — Close Ableton

**Quit Live completely** (Cmd+Q on Mac — not only closing a set).

| App | Open? |
|-----|-------|
| **Ableton Live** | **No** |

---

## Step 2 — Clone, open in IDE, say “run”

| App | Open? |
|-----|-------|
| **Agentic IDE** (repo root) | Yes — [Cursor, Claude, Copilot, …](AGENTIC_IDES.md) |
| **Ableton Live** | **No** |

1. Clone the repository.  
2. **Open folder** in your editor → repo root (contains **`run`**, **`AGENTS.md`**).  
3. Tell the agent: **“Run”** or **“Run `./run` from the repo root.”**

Wait for **`M4L_RUN_OK`**. The agent should **not** run **`--live`** yet.

---

## Step 3 — Ableton Control Surfaces (agent guides you)

**The agent does not run commands in this step.** It should give you clear instructions, then wait.

### What the agent should tell you

1. **Quit Live completely**, then **reopen** it (picks up Remote Scripts from step 2).  
2. **Preferences → Link / Tempo / MIDI**  
3. **Control Surface** (first row) → **AbletonOSC** — Input / Output: **None** (blank).  
4. **Control Surface** (second row) → **AbletonMCP**  
5. **Leave Live open.**

### What you say when finished

Reply with something like:

> **Continue** — AbletonOSC and AbletonMCP are enabled and Live is open.

Other phrases work: **“ready”**, **“surfaces are set”**, **“OSC and MCP are on.”**

The agent should **wait** for that before step 4.

---

## Step 4 — Connect and load the tutorial (agent runs `--live`)

After you confirm step 3, tell the agent:

> **Continue**  
> or: **Run `./run --live`**

The agent runs **`./run --live`** with Live open. You should get a **new MIDI track** with the tutorial device — no Finder drag-and-drop.

Success: **`M4L_RUN_OK`** and **`M4L_PIPELINE_READY`** in the terminal.

---

## Step 5 — Pipeline ready — describe your plugin

When step 4 succeeds, the agent should say the **pipeline is connected** and ask what you want to build, for example:

> What type of Max for Live device do you want to create — **MIDI effect**, **audio effect**, or **instrument**?

Personal builds go under **`projects/workspace/`** (see **[`PRIVATE_PLUGINS.md`](PRIVATE_PLUGINS.md)**).

---

## Flow diagram

```text
Step 1: Quit Ableton
       │
       ▼
Step 2: Clone → IDE → "run" → ./run  (Live closed) → M4L_RUN_OK
       │
       ▼
Step 3: Agent explains OSC + MCP in Live → you: "continue" when done
       │
       ▼
Step 4: Agent → ./run --live  (Live open) → M4L_PIPELINE_READY
       │
       ▼
Step 5: Agent asks what .amxd you want → specs / workspace builds
```

---

## Step 5 — Build your plugin

After **`M4L_PIPELINE_READY`**, tell the agent the device type (**MIDI effect**, **audio effect**, **instrument**).

Typical commands (repo root):

```bash
./venv/bin/python scripts/scaffold_plugin.py --name MyPlugin --type midi_effect
./venv/bin/python scripts/validate_spec.py projects/workspace/my_plugin/my_plugin_spec.json
export M4L_PROJECTS_PREFIX=workspace
./venv/bin/python tooling/m4l_pipeline.py all projects/workspace/my_plugin/my_plugin_spec.json
```

See **[`AGENT_TOOLS.md`](AGENT_TOOLS.md)**, **[`MAX_TO_SPEC.md`](MAX_TO_SPEC.md)**, **[`PRIVATE_PLUGINS.md`](PRIVATE_PLUGINS.md)**.

---

## Short answers

| Question | Answer |
|----------|--------|
| **Open Ableton before first “run”?** | **No** — step 1 first, then step 2. |
| **Who sets Control Surfaces?** | **You**, guided by the agent in **step 3**. |
| **What do I say after surfaces are on?** | **“Continue”** (or **“ready”**) → step 4. |
| **Coding-only Mac?** | Stop after step 2; do 3–5 on a machine with Live. |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| **`./run`** fails on Python | Let bootstrap install Python |
| Live never connects | Redo step 3; confirm both surfaces; Live still open for step 4 |
| Port **9877** refused | **AbletonMCP** not selected, or Live not restarted after step 2 |

More: **[`SETUP_AUTOMATED.md`](SETUP_AUTOMATED.md)**.
