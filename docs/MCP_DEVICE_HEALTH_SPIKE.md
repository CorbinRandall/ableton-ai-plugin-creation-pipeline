# AbletonMCP `get_device_health` spike

## Goal

Stock AbletonMCP exposes a **small fixed command set**. This repo adds an optional **`get_device_health`** command via **`scripts/install_remote_scripts.py`** so callers can fetch a **Live Object Model snapshot** for one device without opening the Max editor.

**Important:** Live’s LOM does **not** expose Max’s red error banner, DSP overload meters, or “sounds correct.” This command is a **diagnostic aid** (T2-adjacent), not a substitute for **T4** self-tests or **T5** human rack confirmation. See [`VERIFICATION_TIERS.md`](VERIFICATION_TIERS.md).

## Install / refresh patch

Re-run the installer (or MCP-only patch mode). Live must **fully quit and reopen** after the script file changes.

```bash
./venv/bin/python scripts/install_remote_scripts.py
# or: ./venv/bin/python scripts/install_remote_scripts.py --patch-mcp-only
```

## Wire protocol

JSON over MCP TCP (same as other commands), port **9877**:

```json
{"type": "get_device_health", "params": {"track_index": 0, "device_index": 0}}
```

Success payload (shape varies slightly by Live version):

```json
{
  "status": "success",
  "result": {
    "track_index": 0,
    "device_index": 0,
    "name": "MyDevice",
    "class_name": "MxDeviceAudioEffect",
    "type": "audio_effect",
    "parameter_count": 12,
    "class_display_name": "...",
    "can_have_chains": false,
    "can_have_drum_pads": false
  }
}
```

Optional fields are populated only when the attribute exists on the Live **`Device`** object for your Live version.

## Pipeline integration

- **`scripts/m4l_verify.py`** accepts **`--print-mcp-device-health`** to log the snapshot after load (non-fatal if an older MCP without the patch returns “Unknown command”).
- **`tooling/m4l_pipeline.assert_loaded_device_matches_spec`** remains the primary **T2** guardrail for wrong track/device class.

## Further experiments

If you fork AbletonMCP locally, you can extend `_get_device_health` to include safe `dir(device)` sampling behind a debug flag. Any property named like “error” should be validated **per Live major.minor** before relying on it in CI.
