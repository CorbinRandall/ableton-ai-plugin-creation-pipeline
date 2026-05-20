# First-time setup — use the AI for everything

**→ Main guide for total beginners: [`START_HERE.md`](START_HERE.md)**

You do **not** need GitHub jargon, a terminal, or coding experience. Open this project in **Cursor** (or similar), chat with the AI, and say **“run”** then **“continue”**.

The pipeline is the **same** whether the AI or a developer runs the commands — the AI is just the easiest remote control.

**Checklist:** [`GETTING_STARTED.md`](GETTING_STARTED.md) · **By app:** [`AGENTIC_IDES.md`](AGENTIC_IDES.md)

---

## The five things you say

| When | Say this |
|------|----------|
| First time, Live **closed** | **“Run”** or **“Run first-time setup”** |
| After clicking OSC + MCP in Live | **“Continue”** |
| Ready to make a device | **“Build [describe it] and load it on a track for me to test”** |
| Something broke | Paste the error, or **“Diagnose this”** |
| It works / doesn’t work | **“Sounds good”** or **“The knob doesn’t change volume — fix and reload”** |

That’s the whole loop: **setup once → describe → AI builds & tests → you listen → AI iterates**.

---

## Cursor (recommended for noobs)

1. Install [Cursor](https://cursor.com).
2. **File → Open Folder** → the downloaded project folder (contains `README.md` and `run`).
3. Open **Chat**.
4. First message: **“I’m new. Follow START_HERE and run setup.”**
5. When Cursor asks to run terminal commands, **Allow** — that’s the AI doing step 2 for you.

Rules for the AI load automatically from this project — you don’t configure anything.

---

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Opened a subfolder only | Open the **top-level** project folder |
| Confused Cursor settings with Ableton | **AbletonMCP** is enabled **inside Ableton**, not in Cursor |
| Skipped “continue” after Live setup | Finish both Control Surfaces, then say **continue** |
| Expected magic without Live open | Keep Ableton running from step 3 onward |

---

## After setup

Ask for devices in normal words. Examples:

- *“Simple gain knob on an audio track.”*
- *“MIDI effect that messes with tempo slightly.”*
- *“Use the gain recipe and leave it on a track.”*

See [`examples/recipes/`](../examples/recipes/) — or ask the AI *“what recipes do we have?”*
