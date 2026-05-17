# Max for Live: frontend (UI) vs backend (patch) — and what this pipeline builds

If your device loads in Live, automation/OSC sees parameters, but the **device face is blank in Presentation mode**, you built the **backend** correctly and skipped (or omitted) the **frontend**. This repo’s Python pipeline historically focused on **graph + parameters + deploy + MCP load**; visible UI requires extra JSON fields that are easy to miss.

---

## Two views of the same device

Max for Live devices are Max patchers stored inside an **`.amxd`** file. Live shows the **Presentation** layer in the rack; **Edit** opens the full patcher.

| Layer | What it is | What you see in Live |
|--------|------------|----------------------|
| **Backend (patching / signal)** | `boxes`, `lines`, `midiin`/`midiout`, DSP, `live.*` logic, messages between objects | **Edit** mode (wires, objects) — not the rack face |
| **Frontend (presentation)** | Subset of boxes marked `presentation: 1` with `presentation_rect` positions | **Presentation** mode — knobs, buttons, labels in the device chain |

**Patching coordinates** (`patching_rect`) and **presentation coordinates** (`presentation_rect`) are **independent**. Objects can exist only in the patch (invisible in the rack) or only in presentation (rare), or both.

Cycling ’74 documents the box attributes [`presentation`](https://docs.cycling74.com/reference/live.dial) and [`presentation_rect`](https://docs.cycling74.com/reference/live.dial) on UI objects (e.g. `live.dial`, `live.toggle`).

---

## What is inside an `.amxd` (relevant to this repo)

`tooling/m4l_pipeline.build_amxd` does **not** compile Max from source. It:

1. Copies the **binary header** from a **donor** `.amxd` ([`REFERENCE_HEADER_AND_IMPORT.md`](REFERENCE_HEADER_AND_IMPORT.md)).
2. Replaces the **JSON** `patcher` document (boxes, lines, metadata).
3. Rebuilds the **`dlst`** index so Live can find parameters.

Optional **trailing bytes** after the JSON (embedded SVGs, images, extra resources from the donor) are **dropped** on purpose so the new device does not inherit another product’s artwork. Decorative assets are optional; **presentation flags on your own boxes are not optional** for a custom UI.

---

## Backend checklist (what the pipeline already targets)

These are enough for **MCP load**, **Live parameter automation**, and **`m4l_verify.py` OSC checks** — but **not** for a visible rack UI.

| Piece | Spec / code | Purpose |
|--------|-------------|---------|
| Device graph | `boxes`, `lines` | MIDI/audio routing, logic |
| Live parameters | `live.dial`, `live.toggle`, … with `parameter_enable: 1` and `saved_attribute_attributes.valueof` | Ableton mixer/automation/MCP |
| Device class | `device_type`: `midi_effect` \| `audio_effect` \| `instrument` | Deploy folder + MIDI vs audio track |
| Patcher metadata | `devicewidth`, `description`, `digest` / `name` | Rack width, browser text |
| Binary wrapper | Donor header + `dlst` | Live accepts the file |

**Verify backend without UI:** `./venv/bin/python scripts/m4l_verify.py` (OSC parameter names).

---

## Frontend checklist (what you must add for a visible UI)

| Piece | Where | Notes |
|--------|--------|------|
| `openinpresentation` | `patcher` (often inherited from donor) | `1` = Live opens Presentation, not Edit |
| `devicewidth` | spec `devicewidth` → `patcher.devicewidth` | Width of the device panel in Live (pixels) |
| `presentation: 1` | **each** UI box you want visible | Default is `0` (patch-only) |
| `presentation_rect` | same box: `[x, y, width, height]` | Position/size on the **device face** |
| Optional chrome | `bgcolor`, `editing_bgcolor`, `default_fontsize`, `comment`/`panel` in presentation | Match your design |
| **Readable labels** | `textcolor` on `live.dial` / `live.toggle` / `comment` | **Required** on dark faces — see [Label contrast](#label-contrast-textcolor) |
| Optional assets | Trailing binary resources in `.amxd` | Logos, custom SVG — **not** required for basic `live.*` controls |

### Label contrast (`textcolor`)

On a dark device background (`patcher.bgcolor` ≈ Live’s rack gray), **parameter names and values** come from each UI object’s **`textcolor`** attribute ([`live.dial` reference](https://docs.cycling74.com/reference/live.dial)). If you omit it:

- Knobs and arcs may still draw (theme accent colors).
- **“Rate” / “43.70” style text can match the background** and look invisible.

**Spec-first builds:** `build_amxd` calls **`_apply_live_ui_contrast`** and sets a light gray `textcolor` when missing (same RGBA as readable `comment` text in many factory devices):

```text
[0.811764705882353, 0.811764705882353, 0.827450980392157, 1.0]
```

**Max-first / theme-aware UIs:** use Live **dynamic colors** in Max (Inspector → Dynamic tab) so labels follow the active Live theme — then copy the saved JSON into your spec. See [Cycling ’74: Dynamic Colors](https://docs.cycling74.com/userguide/dynamic_colors/).

| Object | Attribute(s) for visible text |
|--------|-------------------------------|
| `live.dial` | `textcolor`, `showname`, `shownumber` |
| `live.toggle` | `textcolor` |
| `live.numbox` | `lcdcolor` (value), often `textcolor` |
| `comment` (in presentation) | `textcolor` |

**Check a spec before build:**

```bash
./venv/bin/python scripts/check_spec_ui.py projects/Pipeline_Example/pipeline_example_spec.json
```

### Minimal example (one dial)

```json
{
  "box": {
    "id": "obj-10",
    "maxclass": "live.dial",
    "parameter_enable": 1,
    "patching_rect": [30.0, 100.0, 41.0, 48.0],
    "presentation": 1,
    "presentation_rect": [20.0, 40.0, 41.0, 48.0],
    "textcolor": [0.811764705882353, 0.811764705882353, 0.827450980392157, 1.0],
    "showname": 1,
    "shownumber": 1,
    "saved_attribute_attributes": {
      "valueof": {
        "parameter_longname": "Rate",
        "parameter_shortname": "Rate",
        "parameter_type": 0,
        "parameter_mmin": 0.0,
        "parameter_mmax": 100.0
      }
    }
  }
}
```

Keep **`midiin` / `midiout` / `plugout~`** patch-only unless you intentionally want them on the face.

### Authoring workflows

1. **Max-first (recommended for real UIs)**  
   Build the device in Max → **Presentation** layout → Save → export or copy JSON from the saved `.amxd` into your spec (`boxes` / `lines`). Use the pipeline for **versioning, deploy, and MCP load**.

2. **Spec-first (tutorial / agents)**  
   Write `pipeline_*_spec.json` with both `patching_rect` and `presentation_rect`.  
   `build_amxd` can **auto-enable presentation** (`_ensure_presentation_boxes`) and **default `textcolor`** (`_apply_live_ui_contrast`) when omitted.

3. **Hybrid**  
   One-time UI in Max, then maintain parameters and deploy via Python.

---

## What existing repo docs covered (and what was missing)

| Doc | Covered | Did **not** clearly state |
|-----|---------|-------------------------|
| [`README.md`](../README.md) | Spec → `.amxd` → User Library → MCP | Presentation vs patching; blank UI symptom |
| [`AGENT_IDE_BEGINNER_GUIDE.md`](AGENT_IDE_BEGINNER_GUIDE.md) | Versions, deploy, MCP gotchas | UI layer requirements |
| [`REFERENCE_HEADER_AND_IMPORT.md`](REFERENCE_HEADER_AND_IMPORT.md) | Donor header, paths | Donor’s **presentation** is not your UI |
| [`projects/Pipeline_Example/README.md`](../projects/Pipeline_Example/README.md) | Build commands | Why tutorial face can be empty |
| [`LIVE_API_PATTERNS.md`](LIVE_API_PATTERNS.md) | `live.object` / OSC timing | Device JSON layout |
| `tooling/m4l_pipeline.py` comments | `devicewidth` as “presentation width” | Each box needs `presentation` + `presentation_rect` |

**Misleading comment (fixed in code):** `build_amxd` once said Live “handles gracefully” missing trailing resources — true for **not crashing**, false for **showing your UI**.

---

## Pipeline roadmap (for contributors)

Suggested additions to **`ableton-plugin-pipeline`**:

| Priority | Item | Benefit |
|----------|------|---------|
| Done | `_ensure_presentation_boxes` in `build_amxd` | Controls on device face when spec only has `patching_rect` |
| Done | `_apply_live_ui_contrast` + `scripts/check_spec_ui.py` | Readable labels on dark backgrounds |
| High | `build_deploy_load` optionally call `build_adv` | Richer Live device chain metadata (`.adv`) where needed |
| High | Preflight: warn if zero boxes have `presentation: 1` | Catch blank UI before Live |
| Medium | `scripts/export_spec_from_amxd.py` | Max → JSON spec for agents |
| Medium | Document trailing-resource embedding | Custom SVG / skins |
| Low | Presentation layout linter (overlapping rects) | QA for dense UIs |

---

## Quick diagnosis

| Symptom | Check |
|---------|--------|
| Blank device face, parameters work in Live / OSC | Boxes lack `presentation: 1` or `presentation_rect` |
| Knobs visible, **labels/values invisible** | Missing or dark `textcolor` on `live.dial` — rebuild with current `m4l_pipeline` or set explicitly |
| Blank face, no parameters | Backend: `parameter_enable`, donor `.amxd`, wrong `device_type` |
| UI in Edit, blank in Presentation | `openinpresentation` vs objects not in presentation layer |
| Wrong width / clipped UI | `devicewidth` and `presentation_rect` extents |
| Old UI after rebuild | Stale `Imported/` copy — compare file timestamp ([`LIVE_API_PATTERNS.md`](LIVE_API_PATTERNS.md)) |

---

## See also

- [`projects/Pipeline_Example/`](../projects/Pipeline_Example/) — tutorial spec (should include presentation fields after update)
- [`VERIFY_GUIDE.md`](VERIFY_GUIDE.md) — MCP + OSC verification (backend)
- [Ableton: Max for Live device presentation](https://help.ableton.com/hc/en-us/articles/209072909-Max-for-Live-device-presentation) — official UI mode overview
