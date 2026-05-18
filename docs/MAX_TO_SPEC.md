# Max-first workflow: `.amxd` → spec JSON

Use this when you build or edit a device in **Max** and want the pipeline (versioning, deploy, MCP load) to own the rest.

## Steps

1. In Max, finish the device and **Save** as `.amxd` (unfrozen recommended for git; see [Ableton maxdevtools](https://github.com/Ableton/maxdevtools) guidance on frozen devices).
2. Export to spec:

```bash
./venv/bin/python scripts/export_spec_from_amxd.py ~/path/to/MyDevice.amxd \
  -o projects/workspace/my_plugin/my_device_spec.json \
  --device-type midi_effect \
  --name MyDevice
```

3. Validate and build:

```bash
./venv/bin/python scripts/validate_spec.py projects/workspace/my_plugin/my_device_spec.json
export M4L_PROJECTS_PREFIX=workspace
./venv/bin/python tooling/m4l_pipeline.py all projects/workspace/my_plugin/my_device_spec.json
```

4. Let your IDE agent iterate on **spec JSON**; re-run `all` after changes.

## Limitations

| Topic | Note |
|-------|------|
| **Trailing embeds** | Export warns if the `.amxd` had bytes after the JSON section. **`build_amxd` drops them** — custom SVG/skins need a separate strategy. |
| **Dense UIs** | Presentation layout is easier to refine in Max once, then re-export. |
| **Live API objects** | `live.path` / timing patterns — see [`LIVE_API_PATTERNS.md`](LIVE_API_PATTERNS.md). |
| **Max app** | This repo does not drive Max headlessly; export runs on the saved file only. |

## Round-trip

```text
Max Save .amxd  →  export_spec_from_amxd.py  →  edit spec  →  m4l_pipeline build/all  →  Live
```

For readable `git diff` on `.amxd` in other projects, contributors may use **maxdevtools** `amxd_textconv.py` — that output is for humans, not this pipeline’s spec format.
