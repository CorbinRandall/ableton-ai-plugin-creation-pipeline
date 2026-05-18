# Instructions for AI coding agents

Automated Max for Live **build + deploy + Live load** pipeline. Prefer **`./run`** over ad‑hoc shell recipes.

Human checklist: **[`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)**.

---

## Step 2 — User says “run” (first time after clone)

**Ableton must be closed.** If Live might be open, ask them to **quit Live** (step 1) before continuing.

From the **repo root**:

```bash
chmod +x run bootstrap.sh 2>/dev/null || true
./run
```

Windows: `powershell -ExecutionPolicy Bypass -File .\run.ps1`

Wait for **`M4L_RUN_OK`**. Do **not** pass **`--live`** yet.

---

## Step 3 — Guide Ableton setup (required after step 2)

**Do not run terminal commands.** Send instructions like this (adapt wording, keep the same facts):

---

**Step 3 — Enable control in Ableton (about 2 minutes)**

Setup on disk is done. Next you configure Live once:

1. **Quit Ableton completely**, then **reopen** it.  
2. Open **Preferences → Link / Tempo / MIDI** (or **Link, Tempo & MIDI**).  
3. **Control Surface** (first row) → **AbletonOSC**  
   - **Input** and **Output**: leave **None** / blank.  
4. **Control Surface** (second row) → **AbletonMCP**  
5. **Leave Live open** with both surfaces enabled.

When **AbletonOSC** and **AbletonMCP** are on and Live is still running, reply:

**`Continue`** (or **`Ready`** / **`OSC and MCP are set`**)

I will connect the pipeline and load the tutorial device on a new track.

---

**Wait** for that confirmation before step 4. If they already had surfaces enabled and Live is open, you may proceed when they say so explicitly.

---

## Step 4 — User says “continue” / “ready” / surfaces done

Run:

```bash
./run --live
```

Windows: `powershell -ExecutionPolicy Bypass -File .\run.ps1 -Live`

Wait for **`M4L_RUN_OK`** and **`M4L_PIPELINE_READY`**.

---

## Step 5 — Pipeline ready (required after step 4)

**Do not** jump straight into building without acknowledging success. Say something like:

---

**Pipeline connected**

Ableton is linked (OSC + MCP), and the tutorial Max for Live device is on a track in Live.

**What would you like to build next?** Tell me the type of device:

- **MIDI effect** (`midi_effect`)  
- **Audio effect** (`audio_effect`)  
- **Instrument** (`instrument`)  

Describe the plugin in plain language (controls, sound, workflow). Personal projects go in **`projects/workspace/`** — see **[`docs/PRIVATE_PLUGINS.md`](docs/PRIVATE_PLUGINS.md)**.

---

Then help them write a spec and run **`tooling/m4l_pipeline.py`** when they are ready.

---

## Other flags

| Flag | When |
|------|------|
| **`--no-live`** | Same as default step 2 |
| **`--setup-only`** | Bootstrap + preflight only |

## Do not

- **Open a pull request** unless the user explicitly asks.  
- Run **`--live`** before step 3 is confirmed (unless they clearly already finished Control Surfaces).  
- Skip step 3 instructions after step 2 — always guide them and wait for **continue**.  
- Commit under **`projects/`** except public tutorial sources.  
- Put **private plugin names** in tracked files — use **`projects/workspace/`**.

## Key paths

| Path | Role |
|------|------|
| **`./run`** | Step 2 (Ableton closed) |
| **`./run --live`** | Step 4 |
| **`tooling/m4l_pipeline.py`** | Spec → `.amxd`, deploy, load |
| **`projects/workspace/`** | Gitignored personal plugins |

## Ports

| Component | Port |
|-----------|------|
| **AbletonOSC** | UDP 11000 |
| **AbletonMCP** | TCP **9877** |

## Markers (grep)

| Marker | Meaning |
|--------|---------|
| **`M4L_RUN_OK`** | Step 2 or 4 command finished successfully |
| **`M4L_PIPELINE_READY`** | Step 4 complete — Live connected, tutorial loaded |
