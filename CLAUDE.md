# Claude Code — project instructions

Follow **[`AGENTS.md`](AGENTS.md)** for onboarding steps 1–5 and **[`docs/AGENT_TOOLS.md`](docs/AGENT_TOOLS.md)** for shell commands.

- First setup: **`./run`** (Ableton closed), then guide user through AbletonOSC + AbletonMCP, then **`./run --live`** after they say **Continue**.
- **AbletonMCP** in Live (Control Surface) is **not** the same as optional Claude Desktop MCP servers.
- Personal plugins: **`projects/workspace/`** — see **`docs/PRIVATE_PLUGINS.md`**.
- End-to-end Live check (after MCP + OSC): **`./venv/bin/python scripts/m4l_verify.py`** — builds with **`.adv`** under **`Imported/`** so OSC sees real parameters; see **`docs/VERIFY_GUIDE.md`**.

Other IDEs: **`docs/AGENTIC_IDES.md`**.
