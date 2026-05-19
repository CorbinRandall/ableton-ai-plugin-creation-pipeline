# Live API + M4L patterns (short)

When a device uses **`live.path`**, **`live.object`**, or **`live.observer`**:

- **`live.path`** may return **`id 0`** if you query **before** Live finished init — use **`delay`** after **`loadbang`** (often ≥1000 ms) before **`path live_set`**.
- **`live.object`**: send the **object id** to **inlet 1**; send messages like **`set tempo 120`** to **inlet 0**. Mixing both on inlet 0 fails silently.
- **Session vs Arrangement**: **`/live/song/start_playing`** follows **Arrangement**; Session clip **`fire`** is often better for repeatable tests.
- **Stale `Imported/` copies**: after `python` build, confirm **`User Library/.../Max MIDI Effect/Imported/YourDevice`** matches the file you just built (timestamp).

Tutorial device: **`../projects/Pipeline_Example/`**. Core builder: **`../tooling/m4l_pipeline.py`**.

## AbletonMCP + Max Audio Effects (`audio_effect`)

- **New audio tracks** use MCP command **`create_audio_track`** (added by **`scripts/install_remote_scripts.py`** upstream patch).
- If Live was **open** when Remote Scripts were installed or patched, the running control surface may still be the **old** MCP → **`Unknown command: create_audio_track`**. **Quit Live completely and reopen** so the script reloads.
- Never load a Max **audio effect** on a **MIDI** track: Live often shows a broken device / generic Max error (e.g. “error 6”). The pipeline refuses to fall back to MIDI for **`device_type: audio_effect`** unless **`M4L_ALLOW_AUDIO_ON_MIDI=1`** (debug only).
- After restart, optional check: **`./venv/bin/python scripts/verify_setup.py --wait-mcp 120 --assert-create-audio-track`** (creates one empty audio track if successful — delete in Session View if you want it gone).
