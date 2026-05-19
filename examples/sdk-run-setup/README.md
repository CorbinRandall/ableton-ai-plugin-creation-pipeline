# Optional automation: run setup from a script

**Not required** for normal use. Any agentic IDE can run **`./run`** directly (see [`docs/AGENTIC_IDES.md`](../../docs/AGENTIC_IDES.md)).

These examples help **CI or headless hosts** trigger the same bootstrap on **macOS, Windows, or Linux** (Live steps still need a Mac/PC with Ableton).

## Shell (all platforms)

From repo root:

| Platform | Command |
|----------|---------|
| macOS / Linux | `bash examples/sdk-run-setup/run.sh` |
| Windows | `powershell -ExecutionPolicy Bypass -File examples\sdk-run-setup\run.ps1` |

## Environment

| Variable | Purpose |
|----------|---------|
| `CURSOR_API_KEY` | Only for optional Node/Cursor SDK example below |
| `M4L_SKIP_TEMPLATE` | `1` to skip Live template install |

## Optional: Cursor SDK (Node)

If you use **Cursor’s** programmatic SDK and have Node 18+:

```bash
cd examples/sdk-run-setup
npm install
export CURSOR_API_KEY=your_key   # Windows: set CURSOR_API_KEY
node run-setup.mjs
```

That runs **`./run`** in the repo via a one-shot agent prompt — useful for experimentation, not for Ableton control (Live still needs a human/agent on a Live machine).

Other automation products can wrap the same shell commands without this package.
