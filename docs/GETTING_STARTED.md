# Getting started

**Never coded before?** → **[`START_HERE.md`](START_HERE.md)** (plain language, AI does everything)

**Same pipeline whether you or the AI runs commands** — the agent is just the recommended interface for beginners.

Technical reference: **[`RUN.md`](RUN.md)** · Agent rules: **[`AGENTS.md`](../AGENTS.md)** · **By editor:** **[`AGENTIC_IDES.md`](AGENTIC_IDES.md)**

---

## Steps at a glance

| Step | Ableton | Who | What happens |
|------|---------|-----|----------------|
| **1** | **Closed** | You | **Quit Live** completely |
| **2** | **Closed** | **AI agent** (you say **“run”**) | Agent runs **`./run`** — first-time install |
| **3** | Open (you) | **Agent guides you** | You enable **AbletonOSC** + **AbletonMCP** in Live; reply **“continue”** |
| **4** | **Open** | **Agent** | Agent runs **`./run --live`** → tutorial device on a track |
| **5** | **Open** | **You + agent** | Describe your device in plain language; agent builds, tests, iterates |

You do **not** need to type terminal commands yourself. Say **“run”**, **“continue”**, and describe what you want.

---

## Before you start (once per computer)

| You need | Why |
|----------|-----|
| **Ableton Live** opened **at least once** | Creates User Library folders |
| **Suite**, or **Standard + Max for Live** | Lite/Intro cannot run M4L |
| **An agentic IDE** (Cursor, etc.) with this **folder** open | Agent runs setup for you |
| **Write access** to your Ableton User Library folder | Deploys devices there |
| **Network** (first time) | Downloads tools |

No API keys for the tutorial pipeline.

---

## Step 1 — Close Ableton

Quit Live completely (Cmd+Q on Mac — not only closing a set).

---

## Step 2 — Open project in your AI app, say “run”

1. Get the project folder ([`START_HERE.md`](START_HERE.md) — download ZIP or clone).
2. **Open the folder** in Cursor (or similar) — the whole folder, not a subfolder.
3. Tell the agent: **“Run”** or **“Run first-time setup.”**

Wait for **`M4L_RUN_OK`**. The agent should **not** run **`--live`** yet.

*(Developers may run `./run` manually — same result.)*

---

## Step 3 — Ableton Control Surfaces (agent guides you)

**The agent should not run terminal commands here.** It walks you through Live:

1. Quit/reopen Live  
2. **Preferences → Link / Tempo / MIDI**  
3. **Control Surface** row 1 → **AbletonOSC** (Input/Output blank)  
4. **Control Surface** row 2 → **AbletonMCP**  
5. Leave Live open  

Reply: **“Continue”** (or **“ready”**).

---

## Step 4 — Agent connects (`./run --live`)

After you confirm step 3, say **“continue”**. The agent runs **`./run --live`**.

Success: **`M4L_RUN_OK`** and **`M4L_PIPELINE_READY`** — tutorial device on a new track.

---

## Step 5 — Describe your plugin

Tell the agent what you want in plain language, e.g.:

> Build an audio effect with a volume knob 0–100 and load it on a track for me to try.

The agent validates, builds, deploys, loads, and can **iterate** when you report what you hear in Live.

Personal builds: **`projects/workspace/`** — see **[`PRIVATE_PLUGINS.md`](PRIVATE_PLUGINS.md)**.

---

## Flow diagram

```text
Step 1: Quit Ableton
       │
       ▼
Step 2: Open folder in AI app → "run" → ./run  (Live closed) → M4L_RUN_OK
       │
       ▼
Step 3: Agent explains OSC + MCP in Live → you: "continue"
       │
       ▼
Step 4: Agent → ./run --live  → M4L_PIPELINE_READY
       │
       ▼
Step 5: You describe device → agent builds, tests, reloads until you confirm in Live
```

---

## Short answers

| Question | Answer |
|----------|--------|
| Do I need to use the terminal? | **No** — the agent runs commands. |
| Same if I run commands myself? | **Yes** — identical pipeline. |
| Open Ableton before first “run”? | **No** |
| Who sets Control Surfaces? | **You**, guided by the agent |
| What after surfaces are on? | **“Continue”** |

---

## Troubleshooting

| Problem | Tell the agent |
|---------|----------------|
| `./run` fails | Paste the error |
| Live never connects | Redo step 3; both surfaces on; Live open |
| Empty tracks, no device | “Load [device] on a track and leave it with --no-cleanup” |

More: **[`SETUP_AUTOMATED.md`](SETUP_AUTOMATED.md)** · **[`TROUBLESHOOTING_M4L.md`](TROUBLESHOOTING_M4L.md)**
