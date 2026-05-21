# Plugin versioning (pipeline + agents)

Each successful **`m4l_pipeline.py all`** run creates a **new** version folder — it never overwrites a previous build.

## Default: patch bumps (stay on the same major line)

| Prior highest | Next (default) |
|---------------|----------------|
| *(none)* | `1.1` |
| `1.1` | `1.2` |
| `1.9` | `1.10` |
| `1.27` | `1.28` |

Folder layout:

```text
projects/workspace/<PluginSlug>/<Plugin Name> 1.28/
  spec.json
  VERSION.txt
  <Plugin Name>.amxd
```

Track names in Live use the same label (e.g. `VolumeKnob 1.28`).

**Agents:** treat every small spec/UI/DSP tweak as a **patch** bump. Do **not** jump to `2.x` because the build count is high or because you are on “version 20” of a dev iteration.

## Major bump: only when directed

Start a **new major line** (`1.x` → `2.1`) only when:

- The user explicitly asks (e.g. “ship v2”, “bump major”, “start version 2”), or
- You pass **`--bump-major`** on **`m4l_pipeline.py all`**, or
- **`M4L_VERSION_BUMP=major`** is set in the environment.

```bash
M4L_PROJECTS_PREFIX=workspace ./venv/bin/python tooling/m4l_pipeline.py all spec.json --with-adv --bump-major
```

Never invent `2.0` folders or `Human_Tempo_v2_*` filenames unless one of the above applies.

## Custom workspace builders (e.g. Human Tempo)

Scripts under **`projects/workspace/`** should use the same rules via **`tooling/paths.py`** (`compute_next_version`, `resolve_version_bump`) so archive filenames and **`VERSION.txt`** stay aligned with pipeline folders.

## What this is not

- **Max `appversion`** in the `.amxd` blob — donor stamp for Live compatibility; unrelated to product version folders.
- **Ad-hoc labels** (`vFinalv9`, `v22` layout codenames) — fine for experiments; do not replace semver folders unless the user wants a named snapshot.

See also: [`AGENT_TOOLS.md`](AGENT_TOOLS.md), [`m4l-device-builder/SKILL.md`](../m4l-device-builder/SKILL.md).
