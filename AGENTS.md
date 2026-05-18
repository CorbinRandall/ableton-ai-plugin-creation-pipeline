# Instructions for AI coding agents

This repository is an **automated Max for Live build + deploy + Live load** pipeline. Minimize manual steps: prefer **one entry command** over ad‑hoc shell recipes.

## When the user says “run” (or similar)

Phrases: **run**, **set up**, **bootstrap**, **get started**, **install MCP**, **wire up Ableton**.

**Do this from the repo root:**

```bash
chmod +x run bootstrap.sh 2>/dev/null || true
./run
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

- **Live open + load tutorial on a track:** `./run --live` (or `.\run.ps1 -Live`).
- **Build only, no Ableton:** `./run --no-live`.
- **Setup only:** `./run --setup-only`.

Wait for **`M4L_RUN_OK`** in the output. If missing, read stderr and **[`docs/RUN.md`](docs/RUN.md)** / **[`docs/SETUP_AUTOMATED.md`](docs/SETUP_AUTOMATED.md)**.

## Do not

- Run **`bootstrap.sh`** and five other commands when **`./run`** covers the same ground (unless a step failed and you are fixing one layer).
- Commit anything under **`projects/`** except the public tutorial sources (see **`scripts/check_projects_allowlist.py`**).
- Put **private / commercial plugin names** in **`.gitignore`**, docs, or CI in this public repo — use **`projects/workspace/`** locally (**[`docs/PRIVATE_PLUGINS.md`](docs/PRIVATE_PLUGINS.md)**).

## Key paths

| Path | Role |
|------|------|
| **`./run`** | Post-clone setup + verify + optional tutorial |
| **`tooling/m4l_pipeline.py`** | Spec → `.amxd`, deploy, MCP load |
| **`tooling/donors/*.amxd`** | In-repo header donors (no external pack) |
| **`projects/Pipeline_Example/`** | Public tutorial only |
| **`projects/workspace/`** | Gitignored personal plugins |

## Ableton MCP / OSC (after `./run`)

| Component | Port | Enable in Live |
|-----------|------|----------------|
| **AbletonOSC** | UDP 11000 / replies 11001 | Control Surface → AbletonOSC |
| **AbletonMCP** | TCP **9877** | Control Surface → AbletonMCP |

Scripts are installed under **`User Library/Remote Scripts/`** by bootstrap / **`./run`**.

## Common follow-ups

| User intent | Command |
|-------------|---------|
| Verify Live connection | `./venv/bin/python scripts/verify_setup.py --wait-mcp 120` |
| Build tutorial with Live load | `./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py` |
| Build custom spec | `./venv/bin/python tooling/m4l_pipeline.py all path/to/spec.json` |
| Personal plugin work | `export M4L_PROJECTS_PREFIX=workspace` — build under **`projects/workspace/`** |

## More documentation

- **[`docs/RUN.md`](docs/RUN.md)** — `./run` flags and behavior  
- **[`docs/AGENT_IDE_BEGINNER_GUIDE.md`](docs/AGENT_IDE_BEGINNER_GUIDE.md)** — human-oriented IDE walkthrough  
- **[`README.md`](README.md)** — overview and requirements  
