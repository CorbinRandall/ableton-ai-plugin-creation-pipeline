# Verification tiers (T0–T5)

Agents and CI tools **cannot see Ableton’s rack UI or Max’s in-device error banner**. Signals such as “MCP load succeeded” or “OSC lists parameter names” are **useful but not sufficient** for “the device sounds correct” or “Max interpreted the patch without DSP/UI failure.”

This repo uses explicit tiers so automation stays honest and humans know what was actually proven.

| Tier | Marker | What it proves | Typical tooling |
|------|--------|----------------|-----------------|
| **T0** | `SPEC_OK` / `BUILD_OK` | JSON/UI/layout/schema validity + `.amxd` bytes produced | `scripts/validate_spec.py`, `tooling/m4l_pipeline.py build` |
| **T1** | `MCP_PRECONDITION_OK` | AbletonMCP present on disk; optional runtime proves **`create_audio_track`** | `scripts/verify_setup.py` (`--preflight`, `--assert-create-audio-track`) |
| **T2** | `MCP_LOAD_OK` | Browser listing + MCP load success **and** track kind / loaded device type align with `device_type` | `scripts/m4l_verify.py` (alignment step), `tooling/m4l_pipeline.build_deploy_load` |
| **T3** | `OSC_PARAMS_OK` | AbletonOSC sees expected parameter names after load | `scripts/m4l_verify.py` (default path) |
| **T4** | `DEVICE_SELFTEST_OK` | Max-side proof (e.g. **`loadmess` → UDP ping**) — patch executed, independent of OSC tuples | `--require-selftest-udp-port PORT`, or **`--selftest-default-port`** (port **`39129`**, same as [`midi_effect_selftest_ping.json`](../tooling/templates/midi_effect_selftest_ping.json)) |
| **T5** | `HUMAN_RACK_OK` | Human confirms rack is healthy (green device / no error banner / audition) | Verbal confirmation or **`scripts/capture_live_window.sh`** (macOS screenshot helper) |

## Agent-facing language

- After **T3** (or **T2** with `--no-osc`): say **“ready for you to verify in Live”**, not **“confirmed working.”**
- Say **“confirmed working”** only after **T5**, or after **T4** if your device implements a meaningful self-test and you trust it for that release.
- **GitHub `sanity` workflow** reaches **T0** (validate, compile, offline build) plus **`verify_setup.py --preflight --repo-only`** (python-osc import + pipeline donor `.amxd` files — no Ableton install required). It does **not** run Live or prove rack health — see [`.github/workflows/sanity.yml`](../.github/workflows/sanity.yml). Full **`verify_setup.py --preflight`** (without `--repo-only`) on a Mac/Windows machine with Ableton installed covers closer to **T1** (Remote Scripts + **`create_audio_track`** on disk).

## Automated checks (no Live)

```bash
./venv/bin/python scripts/test_verification_helpers.py
```

Covers **`assert_loaded_device_matches_spec`**, Effect Rack heuristic, and idempotent **`get_device_health`** MCP patch application against stubs.

## MCP device introspection spike (optional)

`scripts/install_remote_scripts.py` can patch AbletonMCP with **`get_device_health`** — a read-only LOM snapshot (name, class, heuristic type, parameter count, optional flags). **This is still not Max DSP health.** Details: [`docs/MCP_DEVICE_HEALTH_SPIKE.md`](MCP_DEVICE_HEALTH_SPIKE.md).

## Related

- [`VERIFY_GUIDE.md`](VERIFY_GUIDE.md) — `m4l_verify.py` usage  
- [`LIVE_API_PATTERNS.md`](LIVE_API_PATTERNS.md) — Live/Max gotchas  
- [`AUDIO_SMOKE_TEST.md`](AUDIO_SMOKE_TEST.md) — hearing checks  
