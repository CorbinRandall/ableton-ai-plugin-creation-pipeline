---
name: m4l-device-builder
description: >
  Build, iterate, and deploy custom Max for Live devices for Ableton Live from plain-English
  descriptions. Use this skill whenever the user wants to create, build, modify, tweak, or
  deploy a Max for Live device, Ableton effect, Ableton instrument, audio effect, MIDI effect,
  or M4L plugin. Also trigger when the user mentions "build me a plugin", "make an effect",
  "create a synth", "volume knob", "delay effect", "arpeggiator", or any request to make
  something that goes into Ableton Live — even if they don't say "Max for Live" explicitly.
  Use this skill for validating, deploying, verifying, or loading an existing .amxd device or
  spec JSON file. Also trigger when the user wants to change, fix, or improve an existing
  device they built with this pipeline.
---

# M4L Device Builder

Build Max for Live devices for Ableton Live from plain-English descriptions. The pipeline
takes a JSON spec, validates it, builds an `.amxd` file, deploys it to the Ableton User
Library, and loads it on a new track in Live — all without opening Max.

## Locating the pipeline

The pipeline repo may or may not be the current working directory. Find it by checking:

1. Current working directory — look for `tooling/m4l_pipeline.py`
2. `~/Documents/ableton-ai-plugin-creation-pipeline/`

Store the path as `PIPELINE` for all commands below. All Python commands use
`$PIPELINE/venv/bin/python`. If the repo is not found, tell the user to clone it and
run `./run` first.

## Hard rules

These rules apply to every build, every iteration, no exceptions:

1. **Always use `all`, never `build` alone.** The command is
   `m4l_pipeline.py all spec.json --with-adv`. The `all` subcommand builds, deploys,
   AND loads the device on a new track in Ableton. The `build` subcommand only writes
   a file — the user would have to drag it into Ableton manually, which defeats the
   purpose.

2. **Always pass `--with-adv`.** This generates the `.adv` preset file that registers
   parameters in Live. Without it, knobs/dials may not appear in Live's device view.

3. **Every change creates a new patch version.** Default bump: **1.1 → 1.2 → 1.3**
   (same major line). Each version gets its own directory under `projects/` with
   `spec.json`, `VERSION.txt`, and the `.amxd`. Never overwrite a previous version.
   **Do not** jump to `2.x` unless the user explicitly asks — then add **`--bump-major`**
   to `m4l_pipeline.py all`. See `$PIPELINE/docs/VERSIONING.md`.

4. **Every version lands on a new track.** The pipeline creates a fresh track (MIDI or
   audio, matching `device_type`) and names it with the device name + version. The user
   should never drag a device from the browser — it appears automatically, ready to
   play.

5. **Only use `--no-live` when Ableton is closed.** If the user says Ableton is open,
   always load onto a track.

6. **Never say "confirmed working."** After automated checks pass (T3), say "ready for
   you to verify in Live." Only say "confirmed working" after the user has actually
   listened and confirmed it sounds right (T5).

7. **Use `projects/workspace/` for user devices.** Set `M4L_PROJECTS_PREFIX=workspace`
   so builds land in the gitignored sandbox. Never commit workspace contents.

## Device types

| Type | What it does | Track type | Example |
|------|-------------|------------|---------|
| `audio_effect` | Processes audio | Audio track | Volume knob, delay, EQ, compressor |
| `midi_effect` | Processes MIDI notes | MIDI track | Arpeggiator, chord generator |
| `instrument` | Generates audio from MIDI | MIDI track | Synth, sampler |

## Workflow

### 1. Understand what the user wants

If unclear, ask:
- What type? (audio effect, MIDI effect, instrument)
- What parameters/knobs? (name, range, default value)
- Any DSP behavior? (filtering, delay, modulation, gain staging)

### 2. Check for a matching recipe

Before building from scratch, check if a recipe is close:

```bash
ls $PIPELINE/examples/recipes/
```

Recipes: gain, tone_lowpass, saturator_drive_tone, delay_feedback, simple_lfo, midi_arp,
mono_synth, noise_gate. Each has `build.py` + `spec.json`. If one fits, copy and modify
its spec rather than starting from zero.

### 3. Create the spec

Use the Python DSL (recommended) or edit JSON directly.

**DSL example — audio effect with a Volume knob:**

```python
import sys, json
sys.path.insert(0, "$PIPELINE/tooling")
from spec_builder import Device, save_spec

dev = Device("VolumeKnob", "audio_effect", devicewidth=256)
ain = dev.audio_in()       # plugin~
aout = dev.audio_out()     # plugout~
knob = dev.dial("Volume", min=0, max=100, default=80)
dev.connect(ain, aout)     # audio path: plugin~ → plugout~
save_spec(dev, "my_spec.json")
```

**DSL methods:**
- `dev.audio_in()` / `dev.audio_out()` — plugin~ / plugout~ (audio effects need both)
- `dev.midi_in()` / `dev.midi_out()` — midiin / midiout (MIDI effects need both)
- `dev.dial(name, min=, max=, default=)` — live.dial parameter knob
- `dev.toggle(name, default=)` — live.toggle on/off switch
- `dev.obj(text)` — any Max object by text (e.g. `dev.obj("*~ 0.5")`)
- `dev.multiply_signal()` — `*~` object
- `dev.sig()` — `sig~` object
- `dev.connect(src_id, dst_id, src_outlet=0, dst_inlet=0)` — patch cord

**JSON approach:** copy from `$PIPELINE/examples/` and edit fields directly.

### 4. Validate

```bash
$PIPELINE/venv/bin/python $PIPELINE/scripts/validate_spec.py path/to/spec.json
```

Look for `SPEC_VALIDATE_OK`. Fix errors before building.

Common errors:
- Missing `plugin~` or `plugout~` for `audio_effect`
- Duplicate box IDs
- Patchline referencing unknown box ID
- Dial without `parameter_longname`

### 5. Build + deploy + load

```bash
M4L_PROJECTS_PREFIX=workspace $PIPELINE/venv/bin/python $PIPELINE/tooling/m4l_pipeline.py all path/to/spec.json --with-adv
```

This does everything in one shot:
- Validates the spec
- Builds the `.amxd` into `projects/workspace/<slug>/<Name X.Y>/`
- Builds the `.adv` preset
- Deploys both to User Library `Imported/`
- Creates a new track (audio or MIDI based on `device_type`)
- Loads the device on that track
- Names the track with the device name + version

The output includes `version`, `track_index`, and `load_result`. Report the version
and track to the user.

### 6. Verify

```bash
$PIPELINE/venv/bin/python $PIPELINE/scripts/m4l_verify.py \
  --spec path/to/spec.json --skip-build --expect-params ParamName1 ParamName2
```

Look for `M4L_VERIFY_OK`. Then say: **"Version X.Y is on track N — ready for you to
verify in Live."**

### 7. Iterate

When the user wants changes:

1. Modify the spec (edit JSON or regenerate via DSL)
2. Re-validate (`validate_spec.py`)
3. Re-run `m4l_pipeline.py all ... --with-adv` — patch-bumps the version (1.1 → 1.2)
   and loads on a fresh track. Add `--bump-major` only if the user wants a new major line (2.1).
4. Tell the user: "Version 1.2 is loaded on a new track — ready for you to verify"
5. Repeat until the user is happy

Each iteration is a new version, a new track, immediately audible. The user never
touches the browser.

## Other useful commands

| Task | Command |
|------|---------|
| Scaffold workspace plugin | `scripts/scaffold_plugin.py --name MyPlugin --type audio_effect` |
| Export .amxd → spec | `scripts/export_spec_from_amxd.py device.amxd -o spec.json` |
| Patch UI colors | `m4l_pipeline.py patch device.amxd --bgcolor 0,0,0,1` |
| SVG preview (no Live) | `tooling/spec_to_svg.py spec.json preview.svg` |
| Check MCP connection | `scripts/verify_setup.py --wait-mcp 120` |
| Confirm audio track support | `scripts/verify_setup.py --wait-mcp 120 --assert-create-audio-track` |
| Offline verify (no Live) | `m4l_pipeline.py verify spec.json` |

## Troubleshooting

- **"CreateDevice failed"**: MCP may lack `create_audio_track`. Run
  `scripts/install_remote_scripts.py`, fully quit + reopen Live, then
  `verify_setup.py --wait-mcp 120 --assert-create-audio-track`.
- **Generic Max error on audio effect**: Device was loaded on wrong track type.
  Ensure audio effects go on audio tracks (the pipeline handles this automatically
  with `all`).
- **Parameters not showing in Live**: Rebuild with `--with-adv`.
- **Old version still playing**: Each `all` run loads on a NEW track. Mute or delete
  old tracks to avoid confusion.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `M4L_PROJECTS_PREFIX=workspace` | Build into gitignored `projects/workspace/` |
| `M4L_SKIP_LIVE=1` | Skip Ableton loading (same as `--no-live`) |
| `M4L_BUILD_ADV=1` | Always generate .adv preset |
| `M4L_VERSION_BUMP=major` | Next `all` starts major line (e.g. 2.1); rare — prefer `--bump-major` |
| `ABLETON_HOME` | Override Ableton user folder location |
