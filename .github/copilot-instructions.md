# Copilot instructions

When helping with this repository, follow **[`AGENTS.md`](../AGENTS.md)** and **[`docs/AGENT_TOOLS.md`](../docs/AGENT_TOOLS.md)**.

## Hard rules — every build, every iteration

1. **ALWAYS use `m4l_pipeline.py all spec.json --with-adv`** — never `build` alone. `all` builds, deploys, AND loads the device on a new track in Ableton.
2. **ALWAYS pass `--with-adv`** — generates the `.adv` preset so parameters appear in Live.
3. **Every change = new version.** The pipeline auto-increments (1.1 → 1.2 → 1.3). Never overwrite.
4. **Every version lands on a new track automatically.** The user never drags from the browser.
5. **Only use `--no-live` when Ableton is explicitly closed.**
6. **Use `M4L_PROJECTS_PREFIX=workspace`** for user devices.
7. **Say "ready for you to verify in Live"** after automated checks — never "confirmed working" until the user confirms.

## Setup

- Run **`./run`** from the repo root on first setup (Ableton quit).
- After user enables **AbletonOSC** and **AbletonMCP** in Live, run **`./run --live`**.
- Use **`./venv/bin/python scripts/validate_spec.py`** before building specs.
- **AbletonMCP** (Live Control Surface, port 9877) is required for Live load; it is separate from GitHub Copilot or IDE MCP products.

Human walkthrough: **[`docs/GETTING_STARTED.md`](../docs/GETTING_STARTED.md)** · All IDEs: **[`docs/AGENTIC_IDES.md`](../docs/AGENTIC_IDES.md)**.
