# Handoff — `docs/simple-gain-readme` (2026-05-19, updated same day)

SimpleGain audio_effect used as a canary to find pipeline bugs.
**`M4L_VERIFY_OK` achieved on second Mac** — all T1–T3 tiers pass. Fixes are in this branch.

## Status

All pipeline bugs found and fixed. Ready to merge to main after:

- [ ] `install_remote_scripts.py`: patch bundled AbletonMCP when present (see bug 4 below — not needed on this Mac, still worth shipping)
- [ ] Delete this file and merge

---

## Bugs found and fixed this session

### Bug 1 — `build_amxd` dropped donor fields (original HANDOFF fix was incomplete)

**Root cause A** (was the stated fix): `ref_root.get("patcher", {})` returned `{}` because
`_extract_amxd_parts` returns the inner patcher dict directly, not `{"patcher": ...}`.
Fix: `patch = deepcopy(ref_root)`.

**Root cause B** (found this session): Even with fix A, builds still failed with error 6.
`_pack_amxd` wrote: `header(32) + subheader(16) + JSON + dlst`.
The "subheader" was actually the first 16 bytes of the donor's JSON, with bytes 44–47
corrupted by `struct.pack_into` writing `content_size` into them.
Max reads JSON from byte 32 and hit those corrupted bytes immediately.

The official `.amxd` format is simply `header(32) + JSON`. No binary subheader, no dlst.
Fix: rewrote `_pack_amxd` to emit `header + JSON` only; removed `_build_dlst` (dead code).

### Bug 2 — Wrong donors (new)

`tooling/donors/midi_effect.amxd` and `audio_effect.amxd` were identical files.
Both had header bytes 8–11 = `0x61616161` ("aaaa") — the Audio Effect type marker.
Max uses those bytes as the device-type discriminator:

| bytes 8–11 | ASCII | device type     |
|------------|-------|-----------------|
| `61616161` | aaaa  | Audio Effect    |
| `6d6d6d6d` | mmmm  | MIDI Effect     |
| `69696969` | iiii  | Instrument      |

Using the audio-type header for MIDI builds caused "does not contain a Max patch of
type 'Max MIDI Effect'". Using it for audio builds still caused error 6 (combined with bug 1B).

Fix: replaced all three donors with the official blank templates from:
`/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/Misc/Max Devices/`

### Bug 3 — `amxdtype` in project dict was hardcoded to "mmmm" (new)

`build_amxd` overwrote the project dict with `amxdtype: 1835887981` (`0x6D6D6D6D`, "mmmm")
for every device type. The patcher-level `amxdtype` should match the donor's value
(audio = `0x61616161`, midi = `0x6D6D6D6D`, instrument = `0x69696969`).

Fix: `donor_amxdtype = ref_root.get("project", {}).get("amxdtype", ...)` and use that.

### Bug 4 — `install_remote_scripts.py` only patches User Library AbletonMCP (pre-existing, unfixed)

Ableton Live 12 ships AbletonMCP bundled at:
`/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts/AbletonMCP/`

The bundled version takes precedence over the User Library version. The bundled version lacks
`create_audio_track`. **Not an issue on the Mac where this was debugged** (no bundled AbletonMCP
present — only User Library). Fix still worth shipping for other machines and Live updates.

Fix needed: `install_remote_scripts.py` should detect and patch the bundled path too.
The existing `patch_abletonmcp_create_audio_track` pattern matcher needs to handle the
bundled file's multi-line tuple layout (see original HANDOFF for details).

---

## How to verify on a new Mac

```bash
git clone https://github.com/CorbinRandall/ableton-ai-plugin-creation-pipeline
cd ableton-ai-plugin-creation-pipeline
git checkout docs/simple-gain-readme

# Ableton MUST be closed for this step
./run

# Open Ableton, enable AbletonOSC + AbletonMCP in Preferences → Link/Tempo/MIDI
# Then:
mkdir -p "projects/SimpleGain/SimpleGain 1.0"
cp examples/simple_gain_audio_spec.json "projects/SimpleGain/SimpleGain 1.0/spec.json"

./venv/bin/python scripts/m4l_verify.py \
  --spec "projects/SimpleGain/SimpleGain 1.0/spec.json" \
  --device-type audio_effect --device-name SimpleGain --expect-params Gain
```

Expected: `M4L_VERIFY_OK`

---

## Key facts deduced about the .amxd format

The official Ableton `.amxd` binary format (confirmed by diffing against
`/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/Misc/Max Devices/`):

```
Bytes 0–31:   32-byte binary header
  [0:4]   "ampf" magic
  [4:8]   version (LE u32, = 4)
  [8:12]  device type marker ("aaaa"/"mmmm"/"iiii")
  [12:16] "meta" tag
  [16:20] meta size (LE u32, = 4)
  [20:24] meta value (LE u32, = 0 in official blanks)
  [24:28] "ptch" tag
  [28:32] section_size (LE u32) = len(JSON bytes)

Bytes 32+:    Raw JSON — the complete {"patcher": {...}} dict
              No binary subheader. No dlst. Just JSON.
```

Max reads JSON from byte 32. `section_size` at header[28:32] is the byte count of the JSON.
The inner patcher dict (at ~byte 48 in tab-indented official files) carries `fileversion`,
`classnamespace`, and `project.amxdtype` — all must match the donor's values.
