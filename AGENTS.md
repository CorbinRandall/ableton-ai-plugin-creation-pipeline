# Instructions for AI coding agents

Automated Max for Live **build + deploy + Live load** pipeline. Prefer **`./run`** over ad-hoc shell recipes.

**Works in any agentic IDE** with shell access. Details: [`docs/AGENTIC_IDES.md`](docs/AGENTIC_IDES.md) · [`docs/CROSS_PLATFORM.md`](docs/CROSS_PLATFORM.md).

Human checklist: [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md).

**Two MCPs:** **AbletonMCP** = Live Control Surface (TCP 9877, required for `./run --live`). **IDE MCP servers** (Cursor `~/.cursor/mcp.json`, etc.) = optional — this repo also ships **`tooling/m4l_mcp_server.py`**.

---

## Onboarding (steps 1–5)

1. User quits Live → you run **`./run`** → wait for **`M4L_RUN_OK`**.
2. Guide Control Surfaces (AbletonOSC + AbletonMCP) → wait for **Continue**.
3. Run **`./run --live`** → wait for **`M4L_PIPELINE_READY`**.
4. Acknowledge success; ask MIDI effect / audio effect / instrument — or suggest **`examples/simple_gain_audio_spec.json`**.
5. Validate → build → load via **`tooling/m4l_pipeline.py`**, or compose with **`tooling/spec_builder.py`** / **`examples/recipes/`**.

Full step 3 wording, tool table, markers, ports: **[`docs/AGENT_REFERENCE.md`](docs/AGENT_REFERENCE.md)**.

Pipeline v2 plan (DSL, MCP, recipes): **[`docs/AGENT_IMPLEMENTATION_PLAN.md`](docs/AGENT_IMPLEMENTATION_PLAN.md)**.

---

## Must do

- Use **`./run`** for first setup; **`./run --live`** only after Control Surfaces are enabled.
- Put personal plugins in **`projects/workspace/`** (gitignored).
- After T3, say **“ready for you to verify in Live”** — not **“confirmed working”** until human T5 ack ([`docs/VERIFICATION_TIERS.md`](docs/VERIFICATION_TIERS.md)).

## Never do

- Open a PR unless the user asks.
- Commit **`projects/workspace/`** contents or private plugin names in public branch/PR/commit text.
- Run **`--live`** before step 3 is confirmed (unless user says surfaces are already on).
- Claim an **`audio_effect`** works without **`m4l_verify.py`** T3+ or user confirmation in Live.

---

Everything else — flags, diagnose, `--json`, privacy guards, troubleshooting — lives in **`docs/AGENT_REFERENCE.md`**, **`docs/AGENT_TOOLS.md`**, and **`docs/PRIVATE_PLUGINS.md`**.
