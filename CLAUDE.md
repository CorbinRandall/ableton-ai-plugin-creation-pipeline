# Claude Code — project instructions

Follow **[`AGENTS.md`](AGENTS.md)** for onboarding steps 1–5 and **[`docs/AGENT_TOOLS.md`](docs/AGENT_TOOLS.md)** for shell commands.

## Hard rules — every build, every iteration

1. **ALWAYS use `m4l_pipeline.py all spec.json --with-adv`** — never `build` alone. `all` builds, deploys, AND loads the device on a new track in Ableton. `build` only writes a file — the user would have to drag it into Ableton manually.
2. **ALWAYS pass `--with-adv`** — generates the `.adv` preset so parameters appear in Live.
3. **Every change = new version.** The pipeline auto-increments (1.1 → 1.2 → 1.3). Never overwrite a previous version.
4. **Every version lands on a new track automatically.** The user never drags anything from the browser.
5. **Only use `--no-live` when Ableton is explicitly closed.**
6. **After automated checks (T3), say "ready for you to verify in Live"** — never "confirmed working" until the user confirms (T5).
7. **Use `M4L_PROJECTS_PREFIX=workspace`** for user devices — keeps them gitignored.
8. **Never commit `projects/workspace/`** contents or private plugin names in public branches.

## Setup flow

- First setup: **`./run`** (Ableton closed), then guide user through AbletonOSC + AbletonMCP, then **`./run --live`** after they say **Continue**.
- **AbletonMCP** in Live (Control Surface) is **not** the same as optional Claude Desktop MCP servers.
- Personal plugins: **`projects/workspace/`** — see **`docs/PRIVATE_PLUGINS.md`**.
- End-to-end Live check (after MCP + OSC): **`./venv/bin/python scripts/m4l_verify.py`** — see **`docs/VERIFY_GUIDE.md`**.

Other IDEs: **`docs/AGENTIC_IDES.md`**.
