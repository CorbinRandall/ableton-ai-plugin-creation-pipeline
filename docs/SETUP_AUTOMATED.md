# Automated bootstrap (Ableton MCP + AbletonOSC)

**Fast path after clone:** run **`./run`** from the repo root ([**`RUN.md`**](RUN.md)). It calls the steps below, runs preflight, and optionally verifies Live. Use **`./bootstrap.sh`** directly only when debugging one layer.

This repo installs **AbletonOSC** (`ideoforms/AbletonOSC`, default branch `master` ZIP) and the **AbletonMCP remote script** (`ahujasid/ableton-mcp`, default branch `main` ZIP, folder `AbletonMCP_Remote_Script/` → **`AbletonMCP`**) into:

| OS | Folder |
|----|--------|
| macOS / Linux (default Ableton convention) | `$ABLETON_HOME/User Library/Remote Scripts/` |
| Windows (Ableton convention) | `%USERPROFILE%\Documents\Ableton\User Library\Remote Scripts\` |

Override the library root anytime with **`ABLETON_HOME`** (same variable as **`tooling/m4l_pipeline.py`**).

Pinned download URLs:

- **`BOOTSTRAP_ABLETON_OSC_ARCHIVE`** — default `…/ideoforms/AbletonOSC/archive/refs/heads/master.zip`
- **`BOOTSTRAP_ABLETON_MCP_ARCHIVE`** — default `…/ahujasid/ableton-mcp/archive/refs/heads/main.zip`

Caches land in **`.bootstrap_cache/`** inside the repo (gitignored unless you customize).

**AbletonMCP patch:** after extracting the remote script, **`install_remote_scripts.py`** adds TCP **`create_audio_track`** (stock ahujasid/ableton-mcp only had **`create_midi_track`**). The M4L pipeline needs this for **`device_type: "audio_effect"`** → new audio track. Already bootstrapped? Run `./venv/bin/python scripts/install_remote_scripts.py --patch-mcp-only` and restart Live.

This repo installs the **AbletonMCP *remote script*** that opens **TCP 9877 inside Live**. The tutorial Python tools (`m4l_pipeline.py`, `m4l_verify.py`) connect to that socket directly. They do **not** require optional **IDE MCP server** packages (Cursor `~/.cursor/mcp.json`, Claude Desktop MCP, etc.)—see **[`AGENTIC_IDES.md`](AGENTIC_IDES.md)**. Only add those if you want IDE features beyond this pipeline.

## Python 3.10+ (auto when missing)

- **macOS / Linux:** **`bootstrap.sh`** sources **`scripts/ensure_python.sh`**. If no suitable interpreter is on `PATH`, macOS runs **`brew install python@3.12`** when Homebrew is installed. Linux prints **`apt`** / **`dnf`** hints (no silent `sudo`).
- **Windows:** **`bootstrap.ps1`** dot-sources **`scripts/ensure_python.ps1`**, then **`winget install Python.Python.3.12`** when needed. Re-run bootstrap in a **new** PowerShell if `python` is not found immediately after install.

Override the bootstrap interpreter anytime with **`BOOTSTRAP_PYTHON`** / **`$env:BOOTSTRAP_PYTHON`**.

## Single command install

macOS / Linux:

```bash
chmod +x bootstrap.sh
./bootstrap.sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1
```

This creates **`venv/`**, installs **`requirements.txt`** (python-osc), downloads remote scripts (GitHub **ZIP** archives unpacked with Python’s **`zipfile`** — no separate `unzip` / `git` dependency), runs **`scripts/install_default_template.py`** unless **`M4L_SKIP_TEMPLATE=1`**, then **`scripts/configure_ableton.py`** (Options.txt block + printed MIDI instructions). **Bootstrap finishes by printing the same Max-for-Live edition summary** echoed from **`README.md`** (suite vs Standard vs Lite/Intro).

Use another Python:

```bash
BOOTSTRAP_PYTHON=/usr/local/bin/python3.11 ./bootstrap.sh
```

## Max for Live — bundled or separate?

Per [Ableton’s documentation](https://help.ableton.com/hc/en-us/articles/360000036850-Max-for-Live-bundled-in-Live):

- **Live Suite** — **Max for Live is included** with Ableton Live; it is installed together with Suite. You normally **do not** install Cycling ’74 **Max** as a separate app to use Max for Live or open the integrated editor (**Edit**).
- **Live Standard** — Max for Live is **not** included by default; you buy the **[Max for Live add‑on](https://help.ableton.com/hc/en-us/articles/206407124-Buying-Max-for-Live)** from Ableton.
- **Live Lite / Intro** — **Max for Live is not available** on these editions (Ableton KB: [Buying Max for Live](https://help.ableton.com/hc/en-us/articles/206407124-Buying-Max-for-Live)).
- **Optional** — Advanced users may install **standalone Max** from Cycling ’74 so Live uses an **[external Max build](https://help.ableton.com/hc/en-us/articles/209070309-Using-a-separate-Max-for-Live-installation)** (Preferences → paths). That is not required for the default Suite workflow.

**This repo** can **assemble `.amxd` files without launching Max**, but Ableton Live still needs a **Max‑for‑Live–capable** license (**Suite**, or **Standard + add‑on**) to **run** tutorial devices inside a Live set.

## Default Live Set (factory template)

**`scripts/install_default_template.py`** (invoked from **`bootstrap`**) copies Ableton’s factory **`DefaultLiveSet.als`** from the application bundle / **`Program Files\Ableton\…`** into **`$ABLETON_HOME/User Library/Templates/M4L Pipeline/m4l_pipeline_startup.als`**, then sets **`<DefaultTemplateSet …/>`** in each **`Library.cfg`** under **`Live x.x.x`** prefs (plaintext XML).

Quit Live first if **`Library.cfg`** might be locked. If no prefs folder exists yet, launch Live once, quit, then re-run **`install_default_template.py`** (or full bootstrap). Set **`M4L_SKIP_TEMPLATE=1`** to skip.


## Preferences limitation (manual step)

Ableton Live stores Control Surface selection in **`Preferences.cfg`**, which is **opaque / undocumented**. This repository **does not** edit it. After install you must:

1. **Quit Live completely** (not only close the window).
2. Relaunch Live.
3. Open **Preferences → Link / Tempo / MIDI**.
4. **Control Surface** → **AbletonOSC** (inputs/outputs blank). Status line should mention **port 11000**.
5. **Control Surface** (second slot / next row where shown) → **AbletonMCP** if needed for MCP (TCP **9877**).

`scripts/configure_ableton.py` can append Ableton-supported lines to **`Options.txt`** (guarded block) for each **`Live x.x.x`** prefs folder — use only documented flags.

## Verification

Preflight (**no Ableton running**):

```bash
./venv/bin/python scripts/verify_setup.py --preflight
```

Live health check (Ableton running with both surfaces loaded):

```bash
./venv/bin/python scripts/verify_setup.py --wait-mcp 120
```

macOS shortcut (tries **`open -a 'Ableton Live …'`**, then waits):

```bash
./venv/bin/python scripts/verify_setup.py --launch-ableton --wait-mcp 180
```

Then run the tutorial pipeline (**`docs/VERIFY_GUIDE.md`**):

```bash
./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py
./venv/bin/python scripts/m4l_verify.py
```

Ports used by this project:

| Service | Direction | Port |
|---------|-----------|------|
| AbletonOSC (send queries) | host → Live | UDP **11000** |
| AbletonOSC replies | Live → host | UDP **11001** |
| AbletonMCP | host ↔ Live | TCP **9877** |

## Troubleshooting

- **`verify_setup.py` MCP connect refused**: Live closed, AbletonMCP not selected as a Control Surface, or script version mismatch — re-run **`install_remote_scripts.py`**, restart Live.
- **`/live/test` timeouts**: AbletonOSC not selected, wrong Live version (**AbletonOSC requires Live 11+ per upstream**), or another process binding **11001**.
- **Wrong Ableton Library path**: Export **`ABLETON_HOME`** pointing at the folder **containing `User Library`**.
