# Handoff — `docs/simple-gain-readme` (2026-05-19)

Snapshot of a debugging session using a SimpleGain knob as a test probe for the pipeline. **The SimpleGain plugin itself is throwaway** (under `projects/SimpleGain/`, gitignored). The goal is finding and fixing pipeline bugs that surface during a clean "build → deploy → verify" of an audio_effect spec.

## Where we left off

Awaiting an Ableton Live restart to pick up a patch to the **bundled** AbletonMCP. Once restarted, run:

```
./venv/bin/python scripts/m4l_verify.py \
  --spec "projects/SimpleGain/SimpleGain 1.5/spec.json" \
  --skip-build --device-type audio_effect \
  --device-name SimpleGain --expect-params Gain
```

If T2/T3 pass cleanly, the pipeline fixes below are validated end-to-end.

## Pipeline bugs found

### 1. `build_amxd` dropped required donor fields — **FIXED in this branch**

`tooling/m4l_pipeline.py:build_amxd` started from `ref_root.get("patcher", {})`. But `_extract_amxd_parts` returns the patcher dict *directly* as `ref_root` (not wrapped in `{"patcher": ...}`), so `.get("patcher", {})` always returned `{}`. The built `.amxd` was missing `fileversion: 1` and `classnamespace: "box"`, which Max requires — the symptom is `createdevice` returning **error 6: device file broken**.

Fix: `patch = deepcopy(ref_root)` (full donor patcher as base — spec content overrides boxes/lines/etc. downstream).

Affects: any device built from a spec via `build_amxd`. The Pipeline_Example tutorial MIDI device probably loaded *despite* this bug because Max is more lenient about MIDI patchers; audio_effect was the canary.

### 2. `scripts/install_remote_scripts.py` only patches User Library AbletonMCP — **NOT FIXED**

Ableton Live 12 ships AbletonMCP bundled inside the app at:

```
/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts/AbletonMCP/
```

The bundled version takes precedence over `~/Music/Ableton/User Library/Remote Scripts/AbletonMCP/`. The bundled version lacks `create_audio_track`, so `m4l_verify` fails with `Unknown command: create_audio_track` even after `install_remote_scripts.py` reports success.

Patched manually on this Mac (edits to bundled `__init__.py`: added `create_audio_track` to the dispatch tuple/if-chain and added `_create_audio_track` method right above `_create_midi_track`). The bundled version *already* searches `user_library` in `_find_browser_item_by_uri`, so that patch isn't needed for the bundled file.

**Pipeline fix needed**: `install_remote_scripts.py` should detect the bundled path (via `abc.find_installed_live_app_bundles()`, which it already calls for logging) and apply `patch_abletonmcp_create_audio_track` to it too. The existing patch function's pattern matcher needs to handle the bundled file's slightly different layout — current tuple-match string is `"create_midi_track", "set_track_name",` on a single line, but bundled splits it across two lines (`"create_midi_track", "set_track_name",\n` then `"create_clip"...`). Either loosen the matcher or add a second pattern.

This is the same fix that has to be reapplied on each new Mac, after every Live update that restores the bundle, so it's worth automating.

## Continuing on a different Mac

1. `git clone` and `git checkout docs/simple-gain-readme`.
2. `./run` (creates venv, installs deps).
3. Set up AbletonOSC + AbletonMCP control surfaces in Live preferences.
4. **Patch the bundled AbletonMCP** (see bug 2 above) — until `install_remote_scripts.py` is fixed, this is manual. The exact edits to apply are visible in git history via `git log -p -- scripts/install_remote_scripts.py` plus the bundled-file edits described in bug 2.
5. Run the verify command at the top of this doc.

`projects/SimpleGain/` won't come across (gitignored). Recreate the spec or rebuild from the README example.

## Take-aways for the pipeline (deploy after green verify)

- [ ] Commit the `build_amxd` fix (`tooling/m4l_pipeline.py`).
- [ ] Extend `install_remote_scripts.py` to patch the bundled AbletonMCP when present.
- [ ] Add a regression check: assert `fileversion`/`classnamespace` are present in any built `.amxd` (could go in `validate_spec.py` post-build or `test_verification_helpers.py`).
- [ ] Document Live 12's bundled AbletonMCP behavior in `docs/SETUP_AUTOMATED.md` so future users aren't surprised.
- [ ] Delete `HANDOFF.md` and this branch once the above ship to main.
