# Instructions for AI coding agents

Automated Max for Live **build + deploy + Live load** pipeline. Prefer **`./run`** over ad‑hoc shell recipes.

**Works in any agentic IDE** with shell access (Cursor, Claude Code, Copilot, Windsurf, Zed, terminal-only, …). **[`docs/AGENTIC_IDES.md`](docs/AGENTIC_IDES.md)** · **[`docs/CROSS_PLATFORM.md`](docs/CROSS_PLATFORM.md)** (macOS / Windows / Linux).

Human checklist: **[`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)**.

**AbletonMCP** (Live Control Surface, TCP 9877) is **not** the same as optional **IDE MCP server** configs (e.g. `~/.cursor/mcp.json`). This repo’s Python tools connect to Live directly.

---

## Step 2 — User says “run” (first time after clone)

**Ableton must be closed.** If Live might be open, ask them to **quit Live** (step 1) before continuing.

From the **repo root**:

| Platform | Command |
|----------|---------|
| **macOS / Linux** | `chmod +x run bootstrap.sh 2>/dev/null; ./run` |
| **Windows** | `powershell -ExecutionPolicy Bypass -File .\run.ps1` |

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

| Platform | Command |
|----------|---------|
| **macOS / Linux** | `./run --live` |
| **Windows** | `powershell -ExecutionPolicy Bypass -File .\run.ps1 -Live` |

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

**Smoke-test suggestion:** point them at the tracked example **`examples/simple_gain_audio_spec.json`** first (*“build and load SimpleGain from `examples/simple_gain_audio_spec.json` with `--with-adv`”*) — it is CI-validated (gain knob on an audio effect).

---

Then help them write a spec and run **`tooling/m4l_pipeline.py`** when they are ready:

1. **Scaffold** (optional): `./venv/bin/python scripts/scaffold_plugin.py --name MyPlugin --type midi_effect`
2. **Validate**: `./venv/bin/python scripts/validate_spec.py path/to/spec.json`
3. **Build + load**: `export M4L_PROJECTS_PREFIX=workspace` then `./venv/bin/python tooling/m4l_pipeline.py all path/to/spec.json`

Full tool list: **[`docs/AGENT_TOOLS.md`](docs/AGENT_TOOLS.md)**.

---

## Tools (quick reference)

| Intent | Command |
|--------|---------|
| Validate spec | `./venv/bin/python scripts/validate_spec.py spec.json` |
| Scaffold workspace | `./venv/bin/python scripts/scaffold_plugin.py --name X --type midi_effect` |
| Export `.amxd` → spec | `./venv/bin/python scripts/export_spec_from_amxd.py device.amxd -o spec.json` |
| Build + deploy + load | `./venv/bin/python tooling/m4l_pipeline.py all spec.json` |
| Offline verify | `./venv/bin/python tooling/m4l_pipeline.py verify spec.json` |
| Patch UI (Max-first) | `./venv/bin/python tooling/m4l_pipeline.py patch device.amxd --bgcolor 0,0,0,1` |
| Live verify (OSC + MCP) | `./venv/bin/python scripts/m4l_verify.py` |
| Verify helpers unit tests (no Live) | `./venv/bin/python scripts/test_verification_helpers.py` |
| Templates | [`tooling/templates/`](tooling/templates/) |

---

## Other flags

| Flag | When |
|------|------|
| **`--no-live`** | Same as default step 2 |
| **`--setup-only`** | Bootstrap + preflight only |
| **`m4l_pipeline all --with-adv`** | Also build/deploy `.adv` preset |
| **`m4l_pipeline all --skip-validate`** | Skip spec schema/UI validation |

## Do not

- **Open a pull request** unless the user explicitly asks.  
- Run **`--live`** before step 3 is confirmed (unless they clearly already finished Control Surfaces).  
- Skip step 3 instructions after step 2 — always guide them and wait for **continue**.  
- Commit under **`projects/`** except public tutorial sources.  
- Put **private plugin names** in tracked files — use **`projects/workspace/`**.  
- Put private plugin names in **branch names, tag names, PR titles, or commit message subjects** on this public repo.  
- Stage paths under **`projects/workspace/`** except **`projects/workspace/README.md`** (run **`scripts/install_workspace_pre_commit.py`** locally).  
- When documenting fixes learned from private work, use **bug-class descriptions** only in tracked files (see **`docs/TROUBLESHOOTING_M4L.md`**).  
- Tell the user an **`audio_effect`** is “loaded and working” in Live **without** either (a) **`scripts/m4l_verify.py`** / pipeline **`all`** succeeding **after** AbletonMCP exposes **`create_audio_track`**, or (b) the user confirming in Live. Agents **cannot see the Ableton UI** — after **`install_remote_scripts`**, remind them to **quit Live fully** before **`create_audio_track`** works.

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
| **`M4L_VERIFY_OK`** | `scripts/m4l_verify.py` completed (build/browser/load/**T2 alignment**/OSC **T3**) |
| **`DEVICE_SELFTEST_OK`** | Optional **T4** UDP self-test passed (`--require-selftest-udp-port`) |

Tier meanings and honest wording: **`docs/VERIFICATION_TIERS.md`**.
