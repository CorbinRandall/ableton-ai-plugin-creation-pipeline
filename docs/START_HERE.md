# Start here — never coded before?

This guide is for **music people**, not programmers. You do **not** need to know GitHub, terminals, or what an “IDE” is. You **chat with an AI assistant** (in an app like **Cursor**), and **it runs the setup for you**.

---

## What this project does (30 seconds)

You describe a **Max for Live** device in normal words — for example:

> “Make an audio effect with a volume knob from 0 to 100.”

The pipeline **checks** your idea, **builds** the device file, **puts it in Ableton’s browser**, and **loads it on a track** so you can hear it and tweak it.

The same steps run whether **you** click things or **the AI** runs them. There is **no special “beginner architecture”** — the AI is just the easiest way to drive the same tools.

---

## Words we use (quick glossary)

| Word | Plain English |
|------|----------------|
| **Repo / project folder** | The folder you downloaded from GitHub — your copy of this toolkit on your computer. |
| **IDE / editor** | An app where you talk to AI and it can run setup — e.g. **Cursor**, Claude Code, VS Code with Copilot. Think: *chat app + project folder*. |
| **Agent / AI assistant** | The chat side of that app. You type in English; it runs commands for you. |
| **Terminal** | A text window where commands run. **You don’t have to use it** — the agent does. |
| **Max for Live (M4L)** | The part of Ableton that runs custom devices. You need **Live Suite**, or **Standard + the M4L add-on**. |
| **Pipeline** | The automated path: your description → device file → Ableton User Library → new track. |
| **Verify / test** | The pipeline checks “did the file build?”, “did Ableton load it?”, “does the knob show up?” — then **you** listen and decide if it *sounds* right. |

---

## What you need on your computer

| Need | Why |
|------|-----|
| **Ableton Live** (Suite, or Standard + Max for Live) | To actually run the devices |
| **Internet** (first setup only) | Downloads helper tools once |
| **An AI coding app** (Cursor recommended) | So you never touch the terminal yourself |
| **This project folder** | Downloaded from GitHub (see below) |

You do **not** need a GitHub account to *use* the pipeline after you have the folder (only to download updates).

---

## One-time setup — you only talk to the AI

Open your AI app, open **this whole folder** as the project, open **Chat**, and follow these steps.

### Step 1 — Close Ableton

**Quit Ableton completely** (Mac: Cmd+Q — not just closing a song).

**Say to the AI:**

> I’m new. Quit Ableton is done. Please run the first-time setup.

*(Or simply: **“run”** — the AI knows the rest from this project.)*

The AI runs setup **while Live is closed**. Wait until it says something like **`M4L_RUN_OK`**. That can take a few minutes the first time.

---

### Step 2 — Turn on two switches in Ableton (the AI walks you through this)

The AI will **not** run scary commands here. It tells you what to click in Ableton. Summary:

1. **Quit Ableton**, then **open it again** (picks up new files from step 1).
2. **Live → Settings/Preferences → Link, Tempo & MIDI** (wording varies slightly by version).
3. **Control Surface** — first empty row → choose **AbletonOSC** (leave Input/Output blank).
4. **Control Surface** — second row → choose **AbletonMCP**.
5. **Leave Live open.**

**Say to the AI when done:**

> Continue — AbletonOSC and AbletonMCP are on and Live is still open.

*(Also works: **“ready”**, **“done”**.)*

---

### Step 3 — Connect everything

**Say to the AI:**

> Continue

It connects to Live and loads a **small tutorial device** on a new track. Success looks like: **`M4L_PIPELINE_READY`** in the AI’s output, and a new device on a track in Live.

If something fails, paste the error back to the AI — it can diagnose and tell you what to fix.

---

### Step 4 — You’re ready — describe your first device

**Say something like:**

> Build a simple audio effect with one volume knob, 0 to 100, and load it in Live so I can try it.

Or:

> Use the VolumeKnob example, build it, and leave it on a track for me to test.

The AI will validate, build, deploy, and load. When it’s done, look at **that track in Live** — not a pile of empty tracks from earlier tests.

**You confirm it works by:**

1. Seeing the device name and knob on the track (not a broken “Max Audio Effect” shell).
2. Playing audio on that track and turning the knob.
3. Telling the AI **“sounds good”** or **“volume doesn’t change — fix it.”**

That back-and-forth **is** the iteration loop — you don’t need to know command names.

---

## Daily workflow (after setup)

| You want… | Say to the AI… |
|-----------|----------------|
| A new effect | “Build a [describe it] audio effect and load it on a track.” |
| Change a knob range | “Change the Tone knob to go from 200 Hz to 18 kHz and rebuild.” |
| Try a preset pattern | “Build the gain recipe and load it in Live.” |
| Something broke | Paste the error, or: “Diagnose this: [error text]” |
| Leave device for you to hear | “Load it with --no-cleanup so it stays on the track.” |

Personal / secret plugins stay in a **private folder** on your machine (`projects/workspace/`) — nothing gets published unless you choose to.

---

## Agent vs doing it yourself

| | **You + AI (recommended)** | **You typing commands** |
|--|---------------------------|-------------------------|
| Same result? | **Yes** | **Yes** |
| Same files built? | **Yes** | **Yes** |
| Who runs `./run`, build, load? | AI | You (or a script) |
| Best for | Total beginners | Developers who prefer the terminal |

The architecture does **not** change. The AI is the **remote control** for the same pipeline.

---

## Pick an AI app (minimum fuss)

1. Install **[Cursor](https://cursor.com)** (free tier is fine to start).
2. **File → Open Folder** → select the folder you downloaded (the one that contains `run` and `README.md`).
3. Open **Chat** (usually a panel on the side).
4. Start with: **“I’m new. Read START_HERE and run first-time setup.”**

Other apps work the same way if they can run terminal commands in the folder: Claude Code, GitHub Copilot, Windsurf, etc. See [`AGENTIC_IDES.md`](AGENTIC_IDES.md).

---

## How to get the project folder (first time only)

**Option A — Download ZIP (no Git needed)**

1. Go to the project on GitHub.
2. Click **Code → Download ZIP**.
3. Unzip. Open **that folder** in Cursor.

**Option B — Git (if you already use it)**

Someone technical can `git clone` for you; you still only need to **open the folder in Cursor**.

---

## Troubleshooting in plain language

| Problem | What to tell the AI |
|---------|---------------------|
| “I only see empty audio tracks” | “Load VolumeKnob on one track and leave it there with --no-cleanup.” |
| Device says “broken” in Live | “Diagnose CreateDevice error 6” — usually wrong browser folder or needs Live restart. |
| AI can’t connect to Ableton | “Check AbletonMCP is enabled in Live and run verify setup.” |
| Knob visible but no sound change | “That’s a T5 check — help me wire the knob to actually change volume.” |

More: [`TROUBLESHOOTING_M4L.md`](TROUBLESHOOTING_M4L.md) (you can ask the AI to explain any section).

---

## What “testing” means here

1. **Automatic (AI runs this)** — Did the file build? Did Ableton load it? Does the knob name show up in Live’s controls?
2. **You (ears and eyes)** — Does it sound right? Does the UI look good? Would you use it in a set?

The AI should say **“ready for you to verify in Live”** after automatic checks — not **“it definitely works perfectly”** until you’ve tried it.

---

## Next docs (optional — or ask the AI to summarize)

| Doc | When |
|-----|------|
| [`GETTING_STARTED.md`](GETTING_STARTED.md) | Same steps, slightly more technical |
| [`AGENT_TOOLS.md`](AGENT_TOOLS.md) | Command list (for the AI, not you) |
| [`examples/recipes/`](examples/recipes/) | Ready-made device patterns |
| [`PRIVATE_PLUGINS.md`](PRIVATE_PLUGINS.md) | Keeping personal projects private |

**You never have to read those.** Asking the AI is enough.
