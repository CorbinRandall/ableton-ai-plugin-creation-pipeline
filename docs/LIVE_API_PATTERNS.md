# Live API + M4L patterns (short)

When a device uses **`live.path`**, **`live.object`**, or **`live.observer`**:

- **`live.path`** may return **`id 0`** if you query **before** Live finished init — use **`delay`** after **`loadbang`** (often ≥1000 ms) before **`path live_set`**.
- **`live.object`**: send the **object id** to **inlet 1**; send messages like **`set tempo 120`** to **inlet 0**. Mixing both on inlet 0 fails silently.
- **Session vs Arrangement**: **`/live/song/start_playing`** follows **Arrangement**; Session clip **`fire`** is often better for repeatable tests.
- **Stale `Imported/` copies**: after `python` build, confirm **`User Library/.../Max MIDI Effect/Imported/YourDevice`** matches the file you just built (timestamp).

Tutorial device: **`../projects/Pipeline_Example/`**. Core builder: **`../tooling/m4l_pipeline.py`**.
