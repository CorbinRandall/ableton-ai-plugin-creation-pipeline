# Instructions for AI coding agents

Automated Max for Live **build + deploy + Live load** pipeline. Prefer **`./run`** over ad-hoc shell recipes.

**Default audience:** **total beginners** who use the agent for **everything** — they do not open a terminal, know Git, or read command docs. **You** run `./run` when they say **“run”**. Same tools, same architecture — you are their interface.

**Point humans here:** [`docs/START_HERE.md`](docs/START_HERE.md)

**Works in any agentic IDE** with shell access. Details: [`docs/AGENTIC_IDES.md`](docs/AGENTIC_IDES.md) · [`docs/CROSS_PLATFORM.md`](docs/CROSS_PLATFORM.md).

Human checklist: [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md).

**Two MCPs:** **AbletonMCP** = Live Control Surface (TCP 9877, required for `./run --live`). **IDE MCP servers** (Cursor `~/.cursor/mcp.json`, etc.) = optional — this repo also ships **`tooling/m4l_mcp_server.py`** (build + deploy + full Live control).

---

## Onboarding (steps 1–5)

1. User quits Live → **you** run **`./run`** when they say **“run”** → wait for **`M4L_RUN_OK`**. Do not ask them to type commands.
2. Guide Control Surfaces in plain language (no jargon) → wait for **Continue**.
3. Run **`./run --live`** → wait for **`M4L_PIPELINE_READY`**.
4. Acknowledge success; ask what they want in **plain language** (MIDI effect / audio effect / instrument) — or suggest a simple example like a volume knob.
5. Build, verify, load, **iterate** based on what they report from Live. Say **“ready for you to verify in Live”** after automated checks — not **“confirmed working”** until they confirm (T5).

Full step 3 wording, tool table, markers, ports: **[`docs/AGENT_REFERENCE.md`](docs/AGENT_REFERENCE.md)**.

Pipeline v2 plan (DSL, MCP, recipes): **[`docs/AGENT_IMPLEMENTATION_PLAN.md`](docs/AGENT_IMPLEMENTATION_PLAN.md)**.

---

## Hard rules — every build, every iteration

1. **ALWAYS use `m4l_pipeline.py all spec.json --with-adv`** — never `build` alone. `all` builds, deploys, AND loads the device on a new track in Ableton. `build` only writes a file — the user would have to drag it into Ableton manually.
2. **ALWAYS pass `--with-adv`** — generates the `.adv` preset so parameters appear in Live.
3. **Every change = new patch version.** Default bump is **minor/patch** on the same major line (1.1 → 1.2 → 1.3). **Never** jump to `2.x` unless the user asks or you pass **`--bump-major`** — see [`docs/VERSIONING.md`](docs/VERSIONING.md). Never overwrite a previous version folder.
4. **Every version lands on a new track automatically.** The user never drags anything from the browser.
5. **Only use `--no-live` when Ableton is explicitly closed.**
6. **Use `M4L_PROJECTS_PREFIX=workspace`** for user devices — keeps them gitignored.

## Must do

- Use **`./run`** for first setup; **`./run --live`** only after Control Surfaces are enabled.
- Put personal plugins in **`projects/workspace/`** (gitignored).
- After T3, say **”ready for you to verify in Live”** — not **”confirmed working”** until human T5 ack ([`docs/VERIFICATION_TIERS.md`](docs/VERIFICATION_TIERS.md)).

## Never do

- Open a PR unless the user asks.
- Commit **`projects/workspace/`** contents or private plugin names in public branch/PR/commit text.
- Run **`--live`** before step 3 is confirmed (unless user says surfaces are already on).
- Claim an **`audio_effect`** works without **`m4l_verify.py`** T3+ or user confirmation in Live.
- Use `m4l_pipeline.py build` instead of `all` — `build` alone skips deploy and Live loading.
- Run `all` without `--with-adv` — parameters won't register in Live without the preset.
- Bump to `2.x` without user direction or `--bump-major` — default is patch (`1.2` → `1.3`). See [`docs/VERSIONING.md`](docs/VERSIONING.md).

---

## MCP server — AI-native Live control (optional)

When **`tooling/m4l_mcp_server.py`** is wired as an IDE MCP server (see **[`docs/AGENT_TOOLS.md`](docs/AGENT_TOOLS.md)**), you have direct tool calls for the full pipeline:

- **Orient:** `live_session_state()` → all tracks, devices, tempo
- **Build + load + verify:** `live_build_and_verify(spec)` → one call, returns track index + params
- **Inspect:** `live_track_devices(track_index)` → param names/values/ranges
- **Tweak:** `live_set_param(track, device, "Gain", -6.0)`
- **Transport:** `live_transport("play"/"stop"/"set_tempo", bpm=120)`
- **Clips:** `live_create_midi_clip(track, slot, notes)` · `live_fire_clip(track, slot)`
- **Cleanup:** `live_delete_track(index)` · `live_rename_track(index, "name")`

Config template (absolute paths, inside editor's MCP settings):

````json
{
  "mcpServers": {
    "m4l-pipeline": {
      "command": "/abs/path/to/repo/venv/bin/python",
      "args": ["/abs/path/to/repo/tooling/m4l_mcp_server.py"],
      "env": { "M4L_PROJECTS_PREFIX": "workspace" }
    }
  }
}
````

Requires `pip install 'mcp>=1.2.0'` (already in `requirements.txt`). Full tool list: **[`docs/AGENT_TOOLS.md`](docs/AGENT_TOOLS.md)**.

---

Everything else — flags, diagnose, `--json`, privacy guards, troubleshooting — lives in **`docs/AGENT_REFERENCE.md`**, **`docs/AGENT_TOOLS.md`**, and **`docs/PRIVATE_PLUGINS.md`**.
