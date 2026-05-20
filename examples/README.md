# Examples

## SimpleGain (first-build smoke test)

**[`simple_gain_audio_spec.json`](simple_gain_audio_spec.json)** — minimal **audio effect** with one **Gain** dial; audio path is **`plugin~` → `plugout~`** (same proven pattern as **`audio_effect_stub`**). The dial is a real Live parameter; add DSP in Max to affect volume. Validated and built in **[`.github/workflows/sanity.yml`](../.github/workflows/sanity.yml)**.

```bash
./venv/bin/python scripts/validate_spec.py examples/simple_gain_audio_spec.json
./venv/bin/python tooling/m4l_pipeline.py all examples/simple_gain_audio_spec.json --with-adv
```

See the **[README](../README.md)** “First device to build” section for context.

---

## Agentic IDEs + platforms

- **[`docs/AGENTIC_IDES.md`](../docs/AGENTIC_IDES.md)** — any editor  
- **[`docs/CROSS_PLATFORM.md`](../docs/CROSS_PLATFORM.md)** — macOS / Windows / Linux  
- **[`docs/AGENT_TOOLS.md`](../docs/AGENT_TOOLS.md)** — shell commands  

Agents run Python/shell directly — no repo-bundled IDE MCP config required.

## sdk-run-setup (optional automation)

**[`sdk-run-setup/`](sdk-run-setup/)** — wrappers that call `./run` or `run.ps1` from CI or scripts. Optional Node + Cursor SDK example; not required.

## Optional editor pointer files

| Editor | File |
|--------|------|
| Any | [`AGENTS.md`](../AGENTS.md) |
| Cursor | [`.cursor/rules/m4l-pipeline.mdc`](../.cursor/rules/m4l-pipeline.mdc) |
| Claude Code | [`CLAUDE.md`](../CLAUDE.md) |
| GitHub Copilot | [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) |

Do **not** overwrite personal IDE config from bootstrap — see [`scripts/m4l_fresh_reset_backup_and_restore.md`](../scripts/m4l_fresh_reset_backup_and_restore.md).
