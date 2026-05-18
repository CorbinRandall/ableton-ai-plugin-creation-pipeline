# Device spec templates

Copy or scaffold from these JSON files. Run validation before build:

```bash
./venv/bin/python scripts/validate_spec.py path/to/spec.json
./venv/bin/python tooling/m4l_pipeline.py all path/to/spec.json
```

| Template | `device_type` | Use |
|----------|---------------|-----|
| `midi_effect_pass_through.json` | `midi_effect` | MIDI in → out + `live.*` controls |
| `audio_effect_stub.json` | `audio_effect` | `plugin~` / `plugout~` audio path |
| `instrument_stub.json` | `instrument` | `in` + `plugout~` stub |

Scaffold a workspace project:

```bash
./venv/bin/python scripts/scaffold_plugin.py --name MyPlugin --type midi_effect
```
