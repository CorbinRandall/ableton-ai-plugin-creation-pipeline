# Agent implementation plan — pipeline v2 (DSL \+ MCP \+ tightened schema \+ recipes)

**Audience:** an agent (or a developer) implementing the audit recommendations from a fresh context. Read this top-to-bottom once, then work section-by-section.

**Goal:** turn this repo from "AI writes raw Max patcher JSON and prays" into "AI describes a device in plain language, a thin DSL generates a validated spec, an MCP server builds and loads it in Live."

**Do not** change the existing public CLI surface (`tooling/m4l_pipeline.py {build,deploy,patch,verify,load,all}`), the marker contract (`M4L_RUN_OK`, `SPEC_VALIDATE_OK`, `M4L_PIPELINE_READY`, `M4L_VERIFY_OK`, `DEVICE_SELFTEST_OK`, `M4L_AUDIO_MCP_OK`, `M4L_PARAM_SWEEP_OK`, `M4L_VERIFY_OFFLINE_OK`), the verification-tier honesty wording in `docs/VERIFICATION_TIERS.md`, or the privacy guards under `projects/workspace/`. Everything new is additive.

---

## Table of contents

1. Mission and success criteria  
2. Current architecture in one page  
3. What must not regress (preserve list)  
4. Branch / commit / PR plan  
5. Order of operations (dependency graph)  
6. Change 1 — Tighten `spec.schema.json` \+ validator  
7. Change 2 — Build `tooling/spec_builder.py` DSL  
8. Change 3 — Recipe library under `examples/recipes/`  
9. Change 4 — `tooling/spec_to_svg.py` (preview without Live)  
10. Change 5 — `--json` mode on every CLI script  
11. Change 6 — `tooling/m4l_mcp_server.py` (proper MCP server)  
12. Change 7 — `m4l_pipeline.py diagnose` subcommand  
13. Change 8 — Split `m4l_pipeline.py` into modules  
14. Change 9 — Trim `AGENTS.md` to imperative contract  
15. Change 10 — `scripts/m4l_audio_smoke.py` (stretch)  
16. Tests \+ acceptance criteria per change  
17. Live (T2/T3) verification protocol  
18. PR checklist \+ commit messages  
19. Failure modes and recovery  
20. Test commands cheat sheet

---

## 1\. Mission and success criteria

**Success looks like this end-to-end conversation:**

User: "Build me an audio effect with a Drive knob 0–10 (default 5\) and a Tone knob 0–100 (default 50)."

Agent: calls `compose_spec` MCP tool with a recipe \+ overrides, calls `validate_spec`, calls `spec_to_svg`, shows preview, user approves, agent calls `build_and_load`.

Agent: "Ready for you to verify in Live. T3 passed (OSC sees `Drive`, `Tone`)."

**Concrete success criteria for this PR:**

- `examples/recipes/` has at least 5 recipes that build, validate, deploy, and reach **T3** (OSC parameter check) on a real Mac/PC with Live \+ AbletonMCP \+ AbletonOSC.  
- `tooling/spec_builder.py` can produce every existing example (SimpleGain, VolumeKnob) byte-identically (after a `json.dumps(sort_keys=True)` normalization).  
- `tooling/spec.schema.json` rejects ≥ 5 hand-crafted bad specs in `tests/specs/bad/`.  
- `tooling/m4l_mcp_server.py` starts under `python -m mcp` or `mcp dev`, advertises ≥ 6 tools, and one round-trip `validate_spec → build_amxd → deploy → load_in_live` works against a running Live.  
- All existing `scripts/test_*.py` still pass.  
- `scripts/m4l_verify.py` still emits `M4L_VERIFY_OK` for `examples/simple_gain_audio_spec.json` and `examples/volume_knob_audio_spec.json`.  
- `.github/workflows/sanity.yml` (T0 CI) still passes.

---

## 2\. Current architecture in one page

spec.json ─► validate\_spec.py ─► m4l\_pipeline.py build  ─► .amxd

                                          │

                                          ▼

                                  deploy → User Library/Imported/

                                          │

                                          ▼

                                  AbletonMCP load (TCP 9877\)

                                          │

                                          ▼

                                  AbletonOSC params check (UDP 11000\)

                                          │

                                          ▼

                                  T3 pass → "ready to verify in Live"

**Key files (do not break their public API):**

| Path | Purpose |
| :---- | :---- |
| `tooling/m4l_pipeline.py` | Monolith: build, deploy, .adv, MCP socket, browser-path, track creation, CLI |
| `tooling/spec.schema.json` | JSON Schema (draft 2020-12), currently loose |
| `tooling/spec_validate.py` | JSON Schema \+ UI \+ layout checks |
| `tooling/donors/{midi_effect,audio_effect,instrument}.amxd` | Binary donor headers (do not regenerate casually) |
| `tooling/templates/*.json` | Stub specs used by `scaffold_plugin.py` |
| `scripts/validate_spec.py`, `scripts/scaffold_plugin.py`, `scripts/export_spec_from_amxd.py`, `scripts/m4l_verify.py`, `scripts/verify_setup.py` | Agent-facing entry points; each prints a marker on success |
| `scripts/install_remote_scripts.py` | Installs AbletonOSC \+ AbletonMCP \+ patches `create_audio_track` and `get_device_health` |
| `run` / `run.ps1` | Two-phase setup driver |
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules/*.mdc` | All point at `AGENTS.md` as canonical |
| `docs/VERIFICATION_TIERS.md` | T0–T5 ladder, agent honesty rules |

**The `.amxd` binary format (from `HANDOFF.md`):**

Bytes 0–31: 32-byte binary header

  \[0:4\]   "ampf" magic

  \[4:8\]   version (LE u32, \= 4\)

  \[8:12\]  device-type marker ("aaaa"/"mmmm"/"iiii")

  \[12:16\] "meta" tag

  \[16:20\] meta size (LE u32, \= 4\)

  \[20:24\] meta value (LE u32, 0 in blanks)

  \[24:28\] "ptch" tag

  \[28:32\] section\_size (LE u32) \= len(JSON)

Bytes 32+:    Raw JSON ({"patcher": {...}}); inner patcher must carry donor's

              fileversion, classnamespace, and project.amxdtype.

**Two MCPs trap (recurring confusion in this repo):**

- **AbletonMCP** \= Live Control Surface, TCP 9877\. Required for `./run --live`. Lives in Live → Preferences → Link/Tempo/MIDI.  
- **IDE MCP servers** (Claude Desktop, Cursor `~/.cursor/mcp.json`, etc.) \= optional. **This PR adds one of these** at `tooling/m4l_mcp_server.py` so agents can call pipeline tools without shell.

---

## 3\. What must not regress (preserve list)

1. `tooling/m4l_pipeline.py {build,deploy,patch,verify,load,all,info,session}` accept the exact same argv they accept today.  
2. All marker strings still appear on success.  
3. `tooling/spec.schema.json` `$id` and `title` are stable.  
4. `tooling/donors/*.amxd` bytes are unchanged (donor identity is a foot-gun — touch only with explicit human OK).  
5. `docs/VERIFICATION_TIERS.md` wording for "ready for you to verify in Live" vs "confirmed working" stays exactly as is.  
6. `projects/workspace/` allowlist \+ pre-commit hook are unchanged.  
7. No new dependencies in `requirements.txt` without listing them in PR body. New deps acceptable for this PR: `mcp` (Anthropic MCP Python SDK) for change 6 only — and it must be lazy-imported so the rest of the pipeline still runs without it.

---

## 4\. Branch / commit / PR plan

**Branch:** `feat/pipeline-v2-dsl-mcp-recipes`

**Strategy:** one branch, one PR, **ten commits** (one per change below). Keep commits clean — squash only at merge if reviewer asks.

**Commit messages (template):**

feat(\<area\>): \<imperative summary\>

\<2–4 line body: what changed, why, what's tested\>

Refs: docs/AGENT\_IMPLEMENTATION\_PLAN.md §\<N\>

Example for change 1:

feat(schema): tighten spec.schema.json with conditional rules

Adds if/then/else rules: live.dial requires parameter\_longname when

parameter\_enable=1; patchline endpoints must reference an existing

box id and an outlet \< numoutlets. Promotes the unknown-id warning

to an error.

Refs: docs/AGENT\_IMPLEMENTATION\_PLAN.md §6

**PR title:** `Pipeline v2: DSL, MCP server, tightened schema, recipe library`

**PR body skeleton:** see §18.

---

## 5\. Order of operations (dependency graph)

Strict order; each step is independently testable.

1\. schema tightening \+ bad-spec test corpus    (independent)

2\. spec\_builder DSL                            (depends on 1\)

3\. recipes library                             (depends on 2\)

4\. spec\_to\_svg                                 (independent)

5\. \--json mode on existing scripts             (independent)

6\. MCP server                                  (depends on 1, 2, 4, 5\)

7\. diagnose subcommand                         (independent)

8\. m4l\_pipeline.py module split                (do last; mechanical)

9\. AGENTS.md trim                              (do last; doc-only)

10\. audio smoke (stretch)                      (optional)

Run the offline tests (§16) after every change. Run §17 once at the end before opening the PR.

---

## 6\. Change 1 — Tighten `spec.schema.json` \+ validator

### Files to modify

- `tooling/spec.schema.json` — add conditional rules.  
- `tooling/spec_validate.py` — promote unknown-id reference to an error, add outlet-bounds check.  
- `tests/specs/bad/` — new directory with ≥ 5 hand-crafted bad specs that must each fail validation.  
- `scripts/test_schema_negatives.py` — new test runner.

### Updated `spec.schema.json` (replace whole file)

{

  "$schema": "https://json-schema.org/draft/2020-12/schema",

  "$id": "https://github.com/CorbinRandall/ableton-ai-plugin-creation-pipeline/tooling/spec.schema.json",

  "title": "Max for Live device spec",

  "type": "object",

  "additionalProperties": true,

  "required": \["name", "device\_type", "boxes", "lines"\],

  "properties": {

    "name": { "type": "string", "minLength": 1, "pattern": "^\[A-Za-z\]\[A-Za-z0-9\_\]\*$" },

    "description": { "type": "string" },

    "device\_type": { "type": "string", "enum": \["midi\_effect", "audio\_effect", "instrument"\] },

    "devicewidth": { "type": "number", "minimum": 40 },

    "openinpresentation": { "type": "integer", "enum": \[0, 1\] },

    "bgcolor": { "type": "array", "minItems": 3, "maxItems": 4, "items": { "type": "number" } },

    "parameters": { "type": "object" },

    "boxes": { "type": "array", "minItems": 1, "items": { "$ref": "\#/$defs/boxEntry" } },

    "lines": { "type": "array", "items": { "$ref": "\#/$defs/lineEntry" } }

  },

  "$defs": {

    "boxEntry": {

      "type": "object",

      "required": \["box"\],

      "properties": {

        "box": {

          "type": "object",

          "required": \["maxclass"\],

          "properties": {

            "id": { "type": "string" },

            "maxclass": { "type": "string", "minLength": 1 },

            "numinlets": { "type": "integer", "minimum": 0 },

            "numoutlets": { "type": "integer", "minimum": 0 },

            "patching\_rect": { "type": "array", "minItems": 4, "maxItems": 4, "items": { "type": "number" } },

            "presentation\_rect": { "type": "array", "minItems": 4, "maxItems": 4, "items": { "type": "number" } },

            "presentation": { "type": "integer", "enum": \[0, 1\] },

            "parameter\_enable": { "type": "integer", "enum": \[0, 1\] }

          },

          "allOf": \[

            {

              "if": {

                "properties": { "maxclass": { "enum": \["live.dial", "live.slider", "live.numbox", "live.toggle", "live.menu", "live.tab"\] } },

                "required": \["maxclass"\]

              },

              "then": {

                "properties": {

                  "parameter\_enable": { "const": 1 },

                  "saved\_attribute\_attributes": {

                    "type": "object",

                    "required": \["valueof"\],

                    "properties": {

                      "valueof": {

                        "type": "object",

                        "required": \["parameter\_longname", "parameter\_shortname", "parameter\_type"\]

                      }

                    }

                  }

                },

                "required": \["parameter\_enable", "saved\_attribute\_attributes"\]

              }

            }

          \]

        }

      }

    },

    "lineEntry": {

      "type": "object",

      "required": \["patchline"\],

      "properties": {

        "patchline": {

          "type": "object",

          "required": \["source", "destination"\],

          "properties": {

            "source": { "type": "array", "minItems": 2, "maxItems": 2, "items": \[{ "type": "string" }, { "type": "integer", "minimum": 0 }\] },

            "destination": { "type": "array", "minItems": 2, "maxItems": 2, "items": \[{ "type": "string" }, { "type": "integer", "minimum": 0 }\] }

          }

        }

      }

    }

  }

}

### `spec_validate.py` deltas

In `validate_structure`, replace the "warnings.append(...references unknown id...)" with `errors.append(...)` and add an outlet-bounds check:

\# Build id → numoutlets / numinlets map

box\_outlets: dict\[str, int\] \= {}

box\_inlets: dict\[str, int\] \= {}

for entry in spec.get("boxes") or \[\]:

    b \= entry.get("box") or {}

    bid \= b.get("id")

    if bid:

        box\_outlets\[bid\] \= int(b.get("numoutlets", 0\) or 0\)

        box\_inlets\[bid\] \= int(b.get("numinlets", 0\) or 0\)

for i, entry in enumerate(spec.get("lines") or \[\]):

    pl \= entry.get("patchline") or {}

    for role, lookup in (("source", box\_outlets), ("destination", box\_inlets)):

        end \= pl.get(role)

        if not end or len(end) \< 2:

            errors.append(f"lines\[{i}\].patchline.{role}: must be \[id, index\]")

            continue

        ref, idx \= end\[0\], end\[1\]

        if ref not in box\_ids:

            errors.append(f"lines\[{i}\].patchline.{role}: unknown id {ref\!r}")

        elif isinstance(idx, int) and idx \>= lookup.get(ref, 0\) \> 0:

            errors.append(f"lines\[{i}\].patchline.{role}: outlet/inlet {idx} out of range for {ref\!r} (has {lookup\[ref\]})")

### Bad-spec corpus (`tests/specs/bad/`)

Create one JSON file per failure mode. Each must fail validation. Minimum five — add more if you find more bug classes. Naming: `<failure>.json`.

| File | Bug it represents |
| :---- | :---- |
| `dial_without_parameter_longname.json` | `live.dial` with `parameter_enable: 1` but no `valueof.parameter_longname` |
| `patchline_unknown_id.json` | `patchline.source = ["obj-doesntexist", 0]` |
| `patchline_outlet_out_of_range.json` | source outlet index ≥ numoutlets |
| `audio_effect_missing_plugout.json` | `device_type: audio_effect` with no `plugout~`/`out` |
| `duplicate_box_id.json` | two boxes with same `id` |

Existing `tests/specs/midi_effect_missing_io.json` should already cover the device-type-IO check; keep it.

### Test runner — `scripts/test_schema_negatives.py`

\#\!/usr/bin/env python3

"""Run validate\_spec against tests/specs/bad/\*.json; assert each fails."""

from \_\_future\_\_ import annotations

import json, sys

from pathlib import Path

REPO \= Path(\_\_file\_\_).resolve().parent.parent

sys.path.insert(0, str(REPO / "tooling"))

from spec\_validate import validate\_spec

bad\_dir \= REPO / "tests" / "specs" / "bad"

failures \= \[\]

for spec\_path in sorted(bad\_dir.glob("\*.json")):

    spec \= json.loads(spec\_path.read\_text())

    errors, \_ \= validate\_spec(spec, check\_ui=True, include\_layout=False)

    if not errors:

        failures.append(spec\_path.name)

        print(f"FAIL: {spec\_path.name} should have failed validation but passed", file=sys.stderr)

    else:

        print(f"OK:   {spec\_path.name} → {len(errors)} error(s)")

if failures:

    print(f"\\n{len(failures)} bad spec(s) passed validation unexpectedly", file=sys.stderr)

    sys.exit(1)

print("SCHEMA\_NEGATIVES\_OK")

### Acceptance for change 1

- `./venv/bin/python scripts/test_schema_negatives.py` prints `SCHEMA_NEGATIVES_OK`.  
- `./venv/bin/python scripts/validate_spec.py examples/simple_gain_audio_spec.json` still prints `SPEC_VALIDATE_OK`.  
- `./venv/bin/python scripts/validate_spec.py examples/volume_knob_audio_spec.json` still prints `SPEC_VALIDATE_OK`.

---

## 7\. Change 2 — `tooling/spec_builder.py` DSL

A small Python library that produces validated spec dicts. The agent uses this instead of writing JSON.

### Design rules

- No new dependencies.  
- Every public function returns a dict that `validate_spec` accepts without warnings.  
- Auto-assigns `id` (`obj-1`, `obj-2`, …) when caller doesn't specify.  
- Auto-assigns `patching_rect` on a grid when caller doesn't specify.  
- Auto-assigns `presentation_rect` for UI controls on a separate presentation grid.  
- All `live.*` UI controls get `textcolor` defaulted to the same value `_apply_live_ui_contrast` uses.

### Public API (full skeleton)

\# tooling/spec\_builder.py

"""High-level DSL for composing Max for Live device specs.

Produces dicts identical in shape to examples/\*.json — same JSON the rest of

the pipeline already consumes. Use save\_spec() to write to disk.

"""

from \_\_future\_\_ import annotations

from copy import deepcopy

from pathlib import Path

import json

\_TEXTCOLOR\_DEFAULT \= \[0.811764705882353, 0.811764705882353, 0.827450980392157, 1.0\]

class Device:

    def \_\_init\_\_(self, name: str, device\_type: str, \*, description: str \= "", devicewidth: float \= 200.0):

        self.spec: dict \= {

            "name": name,

            "description": description,

            "device\_type": device\_type,

            "devicewidth": devicewidth,

            "openinpresentation": 1,

            "boxes": \[\],

            "lines": \[\],

        }

        self.\_next\_id \= 1

        self.\_patch\_y \= 30

        self.\_pres\_x \= 20

        self.\_pres\_y \= 40

    def \_new\_id(self) \-\> str:

        i \= self.\_next\_id

        self.\_next\_id \+= 1

        return f"obj-{i}"

    def \_patch\_rect(self, w=80, h=22) \-\> list\[float\]:

        rect \= \[30.0, float(self.\_patch\_y), float(w), float(h)\]

        self.\_patch\_y \+= h \+ 8

        return rect

    def \_pres\_rect(self, w=41, h=48) \-\> list\[float\]:

        rect \= \[float(self.\_pres\_x), float(self.\_pres\_y), float(w), float(h)\]

        self.\_pres\_x \+= w \+ 16

        return rect

    \# \--- I/O boxes \---

    def audio\_in(self) \-\> str:

        return self.\_add({"maxclass": "plugin\~", "numinlets": 1, "numoutlets": 1, "outlettype": \["signal"\]}, w=80)

    def audio\_out(self) \-\> str:

        return self.\_add({"maxclass": "plugout\~", "numinlets": 1, "numoutlets": 0}, w=80)

    def midi\_in(self) \-\> str:

        return self.\_add({"maxclass": "midiin", "numinlets": 1, "numoutlets": 1, "outlettype": \[""\]}, w=80)

    def midi\_out(self) \-\> str:

        return self.\_add({"maxclass": "midiout", "numinlets": 1, "numoutlets": 0}, w=80)

    \# \--- UI parameters \---

    def dial(self, longname: str, \*, min: float \= 0, max: float \= 1, default: float \= 0,

             shortname: str | None \= None, unitstyle: int \= 0\) \-\> str:

        box \= {

            "maxclass": "live.dial",

            "numinlets": 1, "numoutlets": 2, "outlettype": \["", "float"\],

            "parameter\_enable": 1,

            "presentation": 1,

            "presentation\_rect": self.\_pres\_rect(),

            "textcolor": list(\_TEXTCOLOR\_DEFAULT),

            "showname": 1, "shownumber": 1,

            "saved\_attribute\_attributes": {

                "valueof": {

                    "parameter\_longname": longname,

                    "parameter\_shortname": shortname or longname,

                    "parameter\_type": 0,

                    "parameter\_mmin": float(min),

                    "parameter\_mmax": float(max),

                    "parameter\_initial\_enable": 1,

                    "parameter\_initial": \[float(default)\],

                    "parameter\_unitstyle": unitstyle,

                },

            },

        }

        return self.\_add(box, w=41, h=48)

    def toggle(self, longname: str, \*, default: int \= 0, shortname: str | None \= None) \-\> str:

        box \= {

            "maxclass": "live.toggle",

            "numinlets": 1, "numoutlets": 1, "outlettype": \[""\],

            "parameter\_enable": 1,

            "presentation": 1,

            "presentation\_rect": self.\_pres\_rect(w=20, h=20),

            "textcolor": list(\_TEXTCOLOR\_DEFAULT),

            "saved\_attribute\_attributes": {

                "valueof": {

                    "parameter\_longname": longname,

                    "parameter\_shortname": shortname or longname,

                    "parameter\_type": 1,

                    "parameter\_initial\_enable": 1,

                    "parameter\_initial": \[float(default)\],

                },

            },

        }

        return self.\_add(box, w=20, h=20)

    \# \--- DSP / message boxes \---

    def obj(self, text: str, \*, numinlets: int \= 1, numoutlets: int \= 1, outlettype=None) \-\> str:

        return self.\_add({"maxclass": "newobj", "text": text,

                          "numinlets": numinlets, "numoutlets": numoutlets,

                          "outlettype": outlettype or \["float"\]}, w=max(40, len(text) \* 7))

    def multiply\_signal(self) \-\> str:

        return self.\_add({"maxclass": "\*\~", "numinlets": 2, "numoutlets": 1, "outlettype": \["signal"\]}, w=37)

    def sig(self) \-\> str:

        return self.\_add({"maxclass": "sig\~", "numinlets": 1, "numoutlets": 1, "outlettype": \["signal"\]}, w=37)

    \# \--- Connections \---

    def connect(self, src: str, dst: str, \*, src\_outlet: int \= 0, dst\_inlet: int \= 0\) \-\> None:

        self.spec\["lines"\].append({

            "patchline": {"source": \[src, src\_outlet\], "destination": \[dst, dst\_inlet\]}

        })

    \# \--- Internals \---

    def \_add(self, box: dict, \*, w: int \= 80, h: int \= 22\) \-\> str:

        bid \= self.\_new\_id()

        full \= {"id": bid, \*\*box}

        full.setdefault("patching\_rect", self.\_patch\_rect(w, h))

        self.spec\["boxes"\].append({"box": full})

        return bid

    def to\_dict(self) \-\> dict:

        return deepcopy(self.spec)

def audio\_effect(name: str, \*\*kw) \-\> Device:

    return Device(name, "audio\_effect", \*\*kw)

def midi\_effect(name: str, \*\*kw) \-\> Device:

    return Device(name, "midi\_effect", \*\*kw)

def instrument(name: str, \*\*kw) \-\> Device:

    return Device(name, "instrument", \*\*kw)

def save\_spec(device: Device | dict, path: str | Path) \-\> Path:

    p \= Path(path)

    p.parent.mkdir(parents=True, exist\_ok=True)

    spec \= device.to\_dict() if isinstance(device, Device) else device

    p.write\_text(json.dumps(spec, indent=2, ensure\_ascii=False) \+ "\\n", encoding="utf-8")

    return p

### Self-test — `scripts/test_spec_builder.py`

\#\!/usr/bin/env python3

"""Build the existing examples via spec\_builder; validate via validate\_spec."""

from \_\_future\_\_ import annotations

import json, sys

from pathlib import Path

REPO \= Path(\_\_file\_\_).resolve().parent.parent

sys.path.insert(0, str(REPO / "tooling"))

from spec\_builder import audio\_effect

from spec\_validate import validate\_spec

def build\_simple\_gain():

    d \= audio\_effect("SimpleGain", description="One Gain dial — dry pass-through (plugin\~ → plugout\~).", devicewidth=220.0)

    in\_ \= d.audio\_in()

    out \= d.audio\_out()

    d.dial("Gain", min=0, max=100, default=100, unitstyle=1)

    d.connect(in\_, out)

    return d.to\_dict()

def build\_volume\_knob():

    d \= audio\_effect("VolumeKnob", description="Volume dial scales audio via \*\~.", devicewidth=200.0)

    in\_ \= d.audio\_in()

    mul \= d.multiply\_signal()

    s \= d.sig()

    scale \= d.obj("\* 0.01", outlettype=\["float"\])

    out \= d.audio\_out()

    dial \= d.dial("Volume", min=0, max=100, default=100, unitstyle=1)

    d.connect(in\_, mul, dst\_inlet=0)

    d.connect(s, mul, dst\_inlet=1)

    d.connect(mul, out)

    d.connect(dial, scale, src\_outlet=1)

    d.connect(scale, s)

    return d.to\_dict()

def main() \-\> int:

    ok \= True

    for fn in (build\_simple\_gain, build\_volume\_knob):

        spec \= fn()

        errs, warns \= validate\_spec(spec)

        print(f"{spec\['name'\]}: {len(errs)} err / {len(warns)} warn")

        for e in errs:

            print(f"  ERROR: {e}")

            ok \= False

    if ok:

        print("SPEC\_BUILDER\_OK")

        return 0

    return 1

if \_\_name\_\_ \== "\_\_main\_\_":

    raise SystemExit(main())

### Acceptance for change 2

- `./venv/bin/python scripts/test_spec_builder.py` prints `SPEC_BUILDER_OK`.  
- The two specs it builds validate with zero errors and zero non-trivial warnings.

---

## 8\. Change 3 — Recipe library under `examples/recipes/`

Each recipe is one Python file using `spec_builder` \+ one short README. Build all of them in CI (T0) and at least one in Live (T3) before merging.

### Recipes to ship (minimum 5; aim for 8\)

| Slug | Type | Description (one line) |
| :---- | :---- | :---- |
| `gain` | audio\_effect | One Gain dial 0–100% wired through `*~` (the audible upgrade of VolumeKnob) |
| `tone_lowpass` | audio\_effect | Tone knob → one-pole `lores~` cutoff (200–18000 Hz) |
| `saturator_drive_tone` | audio\_effect | Drive 0–10 into `tanh~`, then Tone lowpass; mix knob 0–100 |
| `delay_feedback` | audio\_effect | Time (1–2000 ms) \+ Feedback (0–95%) \+ Mix (0–100%) using `tapin~` / `tapout~` |
| `simple_lfo` | audio\_effect | `cycle~` LFO → scaled DC → `*~` tremolo (Rate, Depth) |
| `midi_arp` | midi\_effect | Note in → `arpeggio` style (Rate, Octaves) using `metro` \+ `iter` |
| `mono_synth` | instrument | One-voice `cycle~`/`saw~` with `live.dial` Pitch, ADSR |
| `noise_gate` | audio\_effect | Threshold \+ Attack \+ Release using `thresh~` / `live.gain~` |

### Per-recipe file layout

examples/recipes/

├── README.md                       \# index \+ how to build any recipe

├── gain/

│   ├── build.py                    \# uses spec\_builder; writes spec.json

│   └── README.md                   \# 5–10 lines: what it does, params, knobs

├── tone\_lowpass/

│   ├── build.py

│   └── README.md

└── ...

### `build.py` template

\#\!/usr/bin/env python3

"""Build the \<name\> recipe spec.json next to this file."""

from \_\_future\_\_ import annotations

import json, sys

from pathlib import Path

HERE \= Path(\_\_file\_\_).resolve().parent

REPO \= HERE.parent.parent.parent  \# examples/recipes/\<slug\>/build.py

sys.path.insert(0, str(REPO / "tooling"))

from spec\_builder import audio\_effect, save\_spec  \# or midi\_effect / instrument

def build():

    d \= audio\_effect("Gain", description="One Gain dial (0–100%) scaling audio via \*\~.")

    in\_ \= d.audio\_in()

    mul \= d.multiply\_signal()

    sig \= d.sig()

    scale \= d.obj("\* 0.01", outlettype=\["float"\])

    out \= d.audio\_out()

    dial \= d.dial("Gain", min=0, max=100, default=100, unitstyle=1)

    d.connect(in\_, mul, dst\_inlet=0)

    d.connect(sig, mul, dst\_inlet=1)

    d.connect(mul, out)

    d.connect(dial, scale, src\_outlet=1)

    d.connect(scale, sig)

    return d

if \_\_name\_\_ \== "\_\_main\_\_":

    spec\_path \= save\_spec(build(), HERE / "spec.json")

    print(f"WROTE {spec\_path}")

    print("RECIPE\_BUILD\_OK")

### `examples/recipes/README.md`

A table of recipes \+ this command:

\# Build every recipe spec, validate it, build the .amxd offline

for d in examples/recipes/\*/; do

  ./venv/bin/python "$d/build.py"

  ./venv/bin/python scripts/validate\_spec.py "$d/spec.json"

  ./venv/bin/python tooling/m4l\_pipeline.py build "$d/spec.json" "/tmp/$(basename $d).amxd"

done

### Acceptance for change 3

- For each recipe: `build.py` prints `RECIPE_BUILD_OK`; `validate_spec.py` prints `SPEC_VALIDATE_OK`; `m4l_pipeline.py build` succeeds.  
- At least three recipes pass `scripts/m4l_verify.py --spec <recipe>/spec.json --expect-params <param>` with `M4L_VERIFY_OK` on a real Mac/PC.

---

## 9\. Change 4 — `tooling/spec_to_svg.py`

Render presentation rects as labeled SVG so agents can preview UI without Live.

### Code

\#\!/usr/bin/env python3

"""Render a spec's presentation layer to SVG (preview without Live).

Usage:

  ./venv/bin/python tooling/spec\_to\_svg.py spec.json \[-o preview.svg\]

"""

from \_\_future\_\_ import annotations

import argparse, json, sys

from pathlib import Path

PAD \= 8

H\_DEFAULT \= 200

LABEL\_MAP \= {

    "live.dial": ("dial", "\#e0a020"),

    "live.toggle": ("toggle", "\#20a0e0"),

    "live.slider": ("slider", "\#20e0a0"),

    "live.numbox": ("numbox", "\#e02080"),

    "live.menu": ("menu", "\#a020e0"),

    "live.tab": ("tab", "\#20e020"),

    "comment": ("text", "\#cccccc"),

}

def label\_for(box: dict) \-\> str:

    saa \= box.get("saved\_attribute\_attributes", {}).get("valueof", {})

    return saa.get("parameter\_longname") or box.get("text") or box.get("maxclass", "")

def render(spec: dict) \-\> str:

    width \= float(spec.get("devicewidth", 200))

    pres\_boxes \= \[\]

    for entry in spec.get("boxes", \[\]):

        b \= entry.get("box", {})

        if b.get("presentation") \!= 1:

            continue

        rect \= b.get("presentation\_rect")

        if not rect:

            continue

        pres\_boxes.append(b)

    if not pres\_boxes:

        height \= H\_DEFAULT

    else:

        height \= max(r\["presentation\_rect"\]\[1\] \+ r\["presentation\_rect"\]\[3\] for r in pres\_boxes) \+ PAD \* 4

    parts \= \[

        f'\<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}"\>',

        f'\<rect x="0" y="0" width="{width}" height="{height}" fill="\#2a2a2a"/\>',

        f'\<text x="{PAD}" y="{PAD \+ 10}" font-family="sans-serif" font-size="11" fill="\#ddd"\>{spec.get("name", "Untitled")} ({spec.get("device\_type", "?")})\</text\>',

    \]

    for b in pres\_boxes:

        x, y, w, h \= b\["presentation\_rect"\]

        y\_shifted \= y \+ 24  \# leave room for title

        mc \= b.get("maxclass", "")

        \_, color \= LABEL\_MAP.get(mc, ("box", "\#888"))

        label \= label\_for(b)

        parts.append(f'\<rect x="{x}" y="{y\_shifted}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.25" stroke="{color}" stroke-width="1"/\>')

        parts.append(f'\<text x="{x \+ 2}" y="{y\_shifted \+ h \+ 11}" font-family="sans-serif" font-size="10" fill="\#ccc"\>{label}\</text\>')

    parts.append('\</svg\>')

    return "\\n".join(parts)

def main(argv: list\[str\] | None \= None) \-\> int:

    ap \= argparse.ArgumentParser(description=\_\_doc\_\_)

    ap.add\_argument("spec", type=Path)

    ap.add\_argument("-o", "--out", type=Path, default=None)

    args \= ap.parse\_args(argv)

    spec \= json.loads(args.spec.read\_text())

    svg \= render(spec)

    if args.out:

        args.out.write\_text(svg, encoding="utf-8")

        print(f"WROTE {args.out}")

    else:

        sys.stdout.write(svg)

    print("\\nSPEC\_SVG\_OK")

    return 0

if \_\_name\_\_ \== "\_\_main\_\_":

    raise SystemExit(main())

### Acceptance for change 4

- `./venv/bin/python tooling/spec_to_svg.py examples/simple_gain_audio_spec.json -o /tmp/sg.svg` writes a non-empty SVG; opens in a browser; shows one labeled box "Gain".  
- Same for `volume_knob_audio_spec.json` (one box "Volume").

---

## 10\. Change 5 — `--json` mode on every CLI script

For each script that already prints a marker, add `--json`. When set, exit code stays the same, but stdout becomes one JSON object on the last line (after any human-readable logs).

### Pattern (apply to all listed scripts)

import json as \_json

def \_emit\_json(payload: dict, \*, ok: bool) \-\> None:

    payload.setdefault("ok", ok)

    sys.stdout.write(\_json.dumps(payload) \+ "\\n")

Scripts to update: `scripts/validate_spec.py`, `scripts/check_spec_ui.py`, `scripts/check_spec_layout.py`, `scripts/scaffold_plugin.py`, `scripts/export_spec_from_amxd.py`, `scripts/m4l_verify.py`, `scripts/verify_setup.py`, `tooling/m4l_pipeline.py` (every subcommand).

### Example for `validate_spec.py`

ap.add\_argument("--json", action="store\_true", help="Emit one JSON object on stdout (last line)")

\# ... after running validation:

if args.json:

    \_emit\_json({"errors": errors, "warnings": warnings, "spec": str(args.spec)}, ok=not errors)

\# always also print the marker so existing graders keep working

if not errors:

    print("SPEC\_VALIDATE\_OK", args.spec.name)

### Acceptance for change 5

- `./venv/bin/python scripts/validate_spec.py examples/simple_gain_audio_spec.json --json | tail -1 | python -c "import json,sys; d=json.loads(sys.stdin.read()); assert d['ok']"`  
- Marker grep still works without `--json`.

---

## 11\. Change 6 — `tooling/m4l_mcp_server.py` (proper MCP server)

A stdio MCP server (Anthropic Python SDK) that exposes pipeline functions as tools.

### Dependency

Add to `requirements.txt` only when this change lands:

mcp\>=1.2.0

Lazy-import so other tools still work if `mcp` isn't installed.

### Tools to expose

| Tool | Args | Returns |
| :---- | :---- | :---- |
| `list_recipes` | (none) | `{recipes: [{slug, type, description}]}` |
| `read_recipe_spec` | `slug` | `{spec: <dict>}` |
| `compose_spec_from_dsl` | `python_source` (DSL snippet using spec\_builder) | `{spec: <dict>}` — runs the snippet in a sandboxed namespace |
| `validate_spec` | `spec` (dict) | `{errors, warnings, ok}` |
| `spec_to_svg` | `spec` (dict) | `{svg: <string>}` |
| `build_amxd` | `spec`, `out_path?` | `{amxd_path}` |
| `deploy` | `amxd_path`, `device_type` | `{deployed_path}` |
| `load_in_live` | `spec`, `with_adv?` | `{track_index, load_result}` |
| `verify_in_live` | `spec`, `expect_params?` | `{tier, params_seen}` |
| `diagnose` | `error_text` | `{matches: [{pattern, fix}]}` |

### Skeleton

\#\!/usr/bin/env python3

"""M4L pipeline MCP server (stdio).

Run with:

  uv run mcp dev tooling/m4l\_mcp\_server.py    \# interactive

  python tooling/m4l\_mcp\_server.py            \# raw stdio

Tools expose validate/build/deploy/load/diagnose so any MCP-capable agent

can drive the pipeline without shell parsing.

"""

from \_\_future\_\_ import annotations

import json, sys, importlib

from pathlib import Path

REPO \= Path(\_\_file\_\_).resolve().parent.parent

sys.path.insert(0, str(REPO / "tooling"))

sys.path.insert(0, str(REPO / "scripts"))

try:

    from mcp.server.fastmcp import FastMCP

except ImportError:

    sys.stderr.write("mcp package not installed. pip install mcp\>=1.2.0\\n")

    sys.exit(2)

from spec\_validate import validate\_spec as \_validate\_spec

from spec\_builder import Device, save\_spec  \# noqa: F401  (used by DSL eval)

import spec\_builder

from m4l\_pipeline import build\_amxd, deploy\_artifact\_for\_device\_type, build\_deploy\_load

from spec\_to\_svg import render as \_render\_svg

mcp \= FastMCP("m4l-pipeline")

RECIPES\_DIR \= REPO / "examples" / "recipes"

@mcp.tool()

def list\_recipes() \-\> dict:

    """List all built-in device recipes."""

    items \= \[\]

    for d in sorted(RECIPES\_DIR.glob("\*/")):

        readme \= (d / "README.md")

        desc \= readme.read\_text(encoding="utf-8").splitlines()\[0\] if readme.exists() else d.name

        spec\_path \= d / "spec.json"

        device\_type \= "?"

        if spec\_path.exists():

            device\_type \= json.loads(spec\_path.read\_text()).get("device\_type", "?")

        items.append({"slug": d.name, "type": device\_type, "description": desc})

    return {"recipes": items}

@mcp.tool()

def read\_recipe\_spec(slug: str) \-\> dict:

    """Return the spec dict for a named recipe (must be built first)."""

    spec\_path \= RECIPES\_DIR / slug / "spec.json"

    if not spec\_path.exists():

        return {"error": f"recipe {slug\!r} has no spec.json — run examples/recipes/{slug}/build.py"}

    return {"spec": json.loads(spec\_path.read\_text())}

@mcp.tool()

def compose\_spec\_from\_dsl(python\_source: str) \-\> dict:

    """Evaluate a snippet of spec\_builder code; must define \`device \= audio\_effect(...)\` (or similar).

    Only spec\_builder names \+ json are exposed. No file I/O.

    """

    ns \= {"audio\_effect": spec\_builder.audio\_effect,

          "midi\_effect": spec\_builder.midi\_effect,

          "instrument": spec\_builder.instrument,

          "Device": spec\_builder.Device,

          "json": json}

    exec(python\_source, ns)

    dev \= ns.get("device")

    if not isinstance(dev, spec\_builder.Device):

        return {"error": "snippet must assign \`device \= audio\_effect(...)\` etc."}

    return {"spec": dev.to\_dict()}

@mcp.tool()

def validate\_spec(spec: dict) \-\> dict:

    errors, warnings \= \_validate\_spec(spec)

    return {"errors": errors, "warnings": warnings, "ok": not errors}

@mcp.tool()

def spec\_to\_svg(spec: dict) \-\> dict:

    return {"svg": \_render\_svg(spec)}

@mcp.tool()

def build\_amxd\_tool(spec: dict, out\_path: str | None \= None) \-\> dict:

    out \= Path(out\_path) if out\_path else None

    built \= build\_amxd(spec, out)

    return {"amxd\_path": str(built)}

@mcp.tool()

def deploy(amxd\_path: str, device\_type: str) \-\> dict:

    deployed \= deploy\_artifact\_for\_device\_type(Path(amxd\_path), device\_type, imported=True)

    return {"deployed\_paths": \[str(p) for p in deployed\]}

@mcp.tool()

def load\_in\_live(spec: dict, with\_adv: bool \= False) \-\> dict:

    result \= build\_deploy\_load(spec, None, skip\_live=False, with\_adv=with\_adv)

    return result

@mcp.tool()

def diagnose(error\_text: str) \-\> dict:

    """Match known error patterns to recommended fixes."""

    from diagnose import diagnose as \_d   \# change 7

    return \_d(error\_text)

if \_\_name\_\_ \== "\_\_main\_\_":

    mcp.run()

### Claude Desktop / Cursor wiring (document, do not auto-write)

In `docs/AGENT_TOOLS.md` add a section "Pipeline MCP server (optional)" with:

{

  "mcpServers": {

    "m4l-pipeline": {

      "command": "/abs/path/to/repo/venv/bin/python",

      "args": \["/abs/path/to/repo/tooling/m4l\_mcp\_server.py"\]

    }

  }

}

### Acceptance for change 6

- `./venv/bin/python tooling/m4l_mcp_server.py` runs without crashing (it'll block waiting for stdio — that's fine, ^C exits).  
- `./venv/bin/python -c "from mcp.server.fastmcp import FastMCP"` succeeds (package installed).  
- Manual MCP client test (use `mcp dev` or a small Python client): `list_recipes` returns ≥ 5 items; `validate_spec` on `examples/simple_gain_audio_spec.json` returns `ok: true`.

---

## 12\. Change 7 — `m4l_pipeline.py diagnose` subcommand

Maps known error text to recommended fixes. Used by both CLI and MCP server.

### New file — `tooling/diagnose.py`

"""Pattern-match Max/AbletonMCP error text to recommended fixes."""

from \_\_future\_\_ import annotations

import re

PATTERNS: list\[tuple\[str, str\]\] \= \[

    (r"createdevice.\*error 6", "Donor/header bytes wrong. Confirm tooling/donors/\<type\>.amxd device-type marker (8–11: aaaa/mmmm/iiii). See HANDOFF.md bugs 1B, 2."),

    (r"does not contain a Max patch of type 'Max MIDI Effect'", "Audio-type donor used for a MIDI build. Confirm tooling/donors/midi\_effect.amxd has 'mmmm' marker."),

    (r"Unknown command.\*create\_audio\_track", "AbletonMCP not patched. Run scripts/install\_remote\_scripts.py then FULLY QUIT and reopen Live."),

    (r"Unknown command.\*get\_device\_health", "MCP patch missing get\_device\_health. Same fix as create\_audio\_track."),

    (r"Timed out.\*9877", "AbletonMCP control surface not enabled. In Live → Preferences → Link/Tempo/MIDI → Control Surface: AbletonMCP. Then quit \+ reopen."),

    (r"AbletonOSC.\*not responding", "AbletonOSC control surface not enabled (UDP 11000). Enable in Live preferences."),

    (r"no presentation UI boxes found", "Spec has parameters but no presentation\_rect. Use spec\_builder which auto-sets these, or add presentation:1 \+ presentation\_rect on each control."),

    (r"parameter\_longname.\*missing|required.\*parameter\_longname", "live.dial/toggle/slider missing parameter\_longname in saved\_attribute\_attributes.valueof. Use spec\_builder.dial(...) which sets it."),

    (r"duplicate box id", "Two boxes share the same id. spec\_builder auto-assigns unique ids."),

    (r"references unknown id", "patchline source/destination references a box id that doesn't exist. Check the connect() args."),

\]

def diagnose(error\_text: str) \-\> dict:

    matches \= \[\]

    for pattern, fix in PATTERNS:

        if re.search(pattern, error\_text, re.IGNORECASE):

            matches.append({"pattern": pattern, "fix": fix})

    return {"matches": matches, "n": len(matches)}

if \_\_name\_\_ \== "\_\_main\_\_":

    import sys, json

    text \= sys.stdin.read()

    print(json.dumps(diagnose(text), indent=2))

### Wire into `m4l_pipeline.py` `_cli()`

Add a new `elif cmd == "diagnose":` branch that reads stdin (or argv) and prints the diagnosis JSON. Document in `docs/AGENT_TOOLS.md`.

### Acceptance for change 7

- `echo "createdevice error 6" | ./venv/bin/python tooling/m4l_pipeline.py diagnose` prints a JSON match with the donor fix.  
- ≥ 8 unique patterns in `PATTERNS`.

---

## 13\. Change 8 — Split `m4l_pipeline.py` into modules

Mechanical refactor. Keep the same public API by re-exporting from `tooling/m4l_pipeline.py`.

### Target layout

tooling/

├── m4l\_pipeline.py        \# thin shim: re-exports \+ CLI

├── amxd/

│   ├── \_\_init\_\_.py

│   ├── binary.py          \# \_amxd\_json\_starts\_at\_32, \_decode\_amxd\_json\_at, \_extract\_amxd\_parts, \_pack\_amxd

│   ├── builder.py         \# build\_amxd, \_ensure\_presentation\_boxes, \_apply\_live\_ui\_contrast, \_resolve\_appversion

│   └── adv.py             \# build\_adv, deploy\_adv

├── live/

│   ├── \_\_init\_\_.py

│   ├── mcp\_client.py      \# \_ableton\_cmd, \_coerce\_dict, \_normalize\_browser\_leaf

│   ├── browser.py         \# load\_browser\_item\_by\_browser\_path, \_wait\_load\_browser\_imported

│   └── tracks.py          \# \_create\_midi\_track\_index, \_create\_audio\_track\_index, \_create\_new\_track\_for\_device\_type, get\_track\_info, get\_session\_info, set\_tempo

├── deploy.py              \# deploy\_artifact\_for\_device\_type, deploy\_amxd, \_user\_lib\_presets, \_dest\_dir, \_browser\_root, \_LazyDestMap, \_LazyBrowserMap, sidecar helpers

├── patch.py               \# patch\_amxd\_field and helpers

├── verify\_offline.py      \# verify\_spec\_offline \+ \_lint\_amxd\_dlst

├── spec\_builder.py        \# change 2

├── spec\_validate.py       \# existing

├── spec.schema.json       \# existing

└── spec\_to\_svg.py         \# change 4

### Refactor rules

- Keep `tooling/m4l_pipeline.py` as a 60–100 line shim that re-exports every public name today (`build_amxd`, `build_deploy_load`, `deploy_artifact_for_device_type`, `load_browser_item_by_browser_path`, `_BROWSER_MAP`, `_create_new_track_for_device_type`, `assert_loaded_device_matches_spec`, `patch_amxd_field`, `verify_spec_offline`, `plugin_projects_base`, `reference_amxd_path`, …) so that `scripts/m4l_verify.py`'s existing imports (`from m4l_pipeline import …`) keep working unchanged.  
- Move the `_cli()` function into `tooling/cli.py` or keep at bottom of `m4l_pipeline.py`.  
- Run `scripts/test_m4l_pipeline_deploy.py` and `scripts/test_verification_helpers.py` after the move — they MUST still pass.

### Acceptance for change 8

- `./venv/bin/python scripts/test_m4l_pipeline_deploy.py` exits 0\.  
- `./venv/bin/python scripts/test_verification_helpers.py` exits 0\.  
- `./venv/bin/python -c "from m4l_pipeline import build_amxd, deploy_artifact_for_device_type, build_deploy_load, load_browser_item_by_browser_path, _BROWSER_MAP, _create_new_track_for_device_type, assert_loaded_device_matches_spec"` works.  
- `wc -l tooling/m4l_pipeline.py` reports \< 200 lines.

---

## 14\. Change 9 — Trim `AGENTS.md`

Reduce to ≤ 60 lines. Move tool table, "Do not" list, full step 3 instructions, ports table, marker table into `docs/AGENT_REFERENCE.md` (new). Keep at top of `AGENTS.md`:

- One-paragraph "what this repo does"  
- Steps 1–5 in five lines  
- "Two MCPs" one-liner (AbletonMCP vs IDE MCP)  
- Three "must do" bullets, three "never do" bullets  
- Pointer to `docs/AGENT_REFERENCE.md` for everything else

### Acceptance for change 9

- `wc -l AGENTS.md` \< 70\.  
- New file `docs/AGENT_REFERENCE.md` contains the moved content; every link in the repo that pointed at sections in `AGENTS.md` still resolves.

---

## 15\. Change 10 — `scripts/m4l_audio_smoke.py` (stretch — optional this PR)

Render a test signal through the device offline via AbletonOSC; check RMS difference vs dry. Skip if blocked.

Outline (no full code; document as a stub):

1. Insert dry sine wave clip on the test track.  
2. Render 1–2 seconds to a temp WAV via OSC `/live/set/render` (if supported in user's Live version).  
3. Compare with a reference WAV via simple RMS / FFT.  
4. Print `M4L_AUDIO_SMOKE_OK` on pass.

Acceptance: stub script with a real argparse interface that prints a clear "not yet implemented; manual smoke test required" message and exits with a documented exit code. Full implementation is a separate PR.

---

## 16\. Tests \+ acceptance criteria per change

Run after every change:

./venv/bin/python scripts/validate\_spec.py examples/simple\_gain\_audio\_spec.json

./venv/bin/python scripts/validate\_spec.py examples/volume\_knob\_audio\_spec.json

./venv/bin/python tooling/m4l\_pipeline.py build examples/simple\_gain\_audio\_spec.json /tmp/sg.amxd

./venv/bin/python tooling/m4l\_pipeline.py build examples/volume\_knob\_audio\_spec.json /tmp/vk.amxd

./venv/bin/python scripts/test\_m4l\_pipeline\_deploy.py

./venv/bin/python scripts/test\_verification\_helpers.py

./venv/bin/python scripts/check\_donor\_consistency.py

./venv/bin/python scripts/check\_workspace\_not\_staged.py

New tests (run from the change that introduces them onward):

./venv/bin/python scripts/test\_schema\_negatives.py      \# change 1

./venv/bin/python scripts/test\_spec\_builder.py          \# change 2

for d in examples/recipes/\*/; do "$d/build.py"; done    \# change 3

./venv/bin/python tooling/spec\_to\_svg.py examples/simple\_gain\_audio\_spec.json \-o /tmp/sg.svg  \# change 4

echo "createdevice error 6" | ./venv/bin/python tooling/m4l\_pipeline.py diagnose  \# change 7

Every command above must exit 0 before opening the PR.

---

## 17\. Live (T2/T3) verification protocol

**Only run once after all other changes are merged-locally.** Requires a Mac/PC with Live 12 Suite (or Standard \+ M4L) \+ AbletonOSC \+ AbletonMCP enabled.

\# Step 1: confirm AbletonMCP exposes create\_audio\_track (quit/reopen Live if needed)

./venv/bin/python scripts/verify\_setup.py \--wait-mcp 120 \--assert-create-audio-track

\# Step 2: SimpleGain T3

./venv/bin/python scripts/m4l\_verify.py \--spec examples/simple\_gain\_audio\_spec.json \--expect-params Gain

\# Step 3: VolumeKnob T3

./venv/bin/python scripts/m4l\_verify.py \--spec examples/volume\_knob\_audio\_spec.json \--expect-params Volume

\# Step 4: at least three recipes T3

./venv/bin/python examples/recipes/gain/build.py

./venv/bin/python scripts/m4l\_verify.py \--spec examples/recipes/gain/spec.json \--expect-params Gain

./venv/bin/python examples/recipes/tone\_lowpass/build.py

./venv/bin/python scripts/m4l\_verify.py \--spec examples/recipes/tone\_lowpass/spec.json \--expect-params Tone

./venv/bin/python examples/recipes/saturator\_drive\_tone/build.py

./venv/bin/python scripts/m4l\_verify.py \--spec examples/recipes/saturator\_drive\_tone/spec.json \--expect-params Drive \--expect-params Tone

\# Step 5: MCP server smoke (in a second terminal, with mcp installed)

./venv/bin/python tooling/m4l\_mcp\_server.py \< /dev/null   \# should start and wait; ^C exits cleanly

Each `m4l_verify.py` invocation must print `M4L_VERIFY_OK`. If any fail, pipe stderr into `tooling/m4l_pipeline.py diagnose` and follow the recommended fix.

**Honesty rule:** after T3 passes, the agent may say **"ready for you to verify in Live"**. The agent may NOT say **"confirmed working"** until the human responds with a T5 ack or until you've added a T4 self-test ping (see `tooling/templates/midi_effect_selftest_ping.json`).

---

## 18\. PR checklist \+ commit messages

Branch: `feat/pipeline-v2-dsl-mcp-recipes`.

Commit list (each is its own commit; build cleanly):

1. `feat(schema): tighten spec.schema.json with conditional rules`  
2. `feat(spec_builder): add tooling/spec_builder.py DSL`  
3. `feat(recipes): add examples/recipes/ library (8 recipes)`  
4. `feat(preview): add tooling/spec_to_svg.py`  
5. `feat(cli): add --json mode to validate/build/deploy/verify scripts`  
6. `feat(mcp): add tooling/m4l_mcp_server.py + mcp dep`  
7. `feat(diagnose): add tooling/diagnose.py + m4l_pipeline.py diagnose`  
8. `refactor(tooling): split m4l_pipeline.py into amxd/, live/, deploy.py, patch.py`  
9. `docs(agents): trim AGENTS.md, move detail into docs/AGENT_REFERENCE.md`  
10. `chore(audio): stub scripts/m4l_audio_smoke.py for future PR`

### PR body skeleton

\#\# Pipeline v2 — DSL, MCP server, tightened schema, recipe library

Closes the gap between "AI writes raw Max patcher JSON" and "AI describes a

device in plain language and a thin DSL emits validated spec."

\#\#\# What's new

\- \*\*\`tooling/spec\_builder.py\`\*\* — Python DSL for composing specs; auto-IDs,

  auto-layout, conditional required fields enforced.

\- \*\*\`tooling/spec.schema.json\`\*\* tightened — \`live.dial\` etc. must carry

  \`parameter\_longname\`; patchlines must reference real ids & valid outlets.

\- \*\*\`examples/recipes/\`\*\* — 8 named patterns (gain, tone\_lowpass,

  saturator\_drive\_tone, delay\_feedback, simple\_lfo, midi\_arp, mono\_synth,

  noise\_gate). Three reach T3 in Live.

\- \*\*\`tooling/m4l\_mcp\_server.py\`\*\* — proper MCP server exposing validate,

  build, deploy, load, diagnose; usable from Claude Desktop / Cursor.

\- \*\*\`tooling/spec\_to\_svg.py\`\*\* — preview presentation layer without Live.

\- \*\*\`--json\` output\*\* on every script for parse-safe agent consumption.

\- \*\*\`m4l\_pipeline.py diagnose\`\*\* — error pattern → fix table.

\- \*\*\`m4l\_pipeline.py\` split\*\* into \`amxd/\`, \`live/\`, \`deploy.py\`, etc.;

  public API preserved via shim.

\- \*\*\`AGENTS.md\` trimmed\*\* to imperative contract; details in

  \`docs/AGENT\_REFERENCE.md\`.

\#\#\# What's preserved

\- Marker contract (\`M4L\_RUN\_OK\`, \`SPEC\_VALIDATE\_OK\`, \`M4L\_PIPELINE\_READY\`,

  \`M4L\_VERIFY\_OK\`, …).

\- CLI argv compatibility for \`m4l\_pipeline.py {build,deploy,patch,verify,

  load,all}\`.

\- Donor \`.amxd\` files (untouched).

\- T0–T5 honesty wording.

\- \`projects/workspace/\` allowlist \+ pre-commit guards.

\#\#\# Tests

T0 (offline): all \`scripts/test\_\*.py\` \+ \`scripts/test\_schema\_negatives.py\` \+

\`scripts/test\_spec\_builder.py\` pass. T2/T3: SimpleGain, VolumeKnob, and three

recipes reach \`M4L\_VERIFY\_OK\` on a Mac with Live 12 Suite \+ AbletonOSC \+

AbletonMCP enabled.

\#\#\# Dependencies

\- New: \`mcp\>=1.2.0\` (lazy-imported; only required for \`m4l\_mcp\_server.py\`).

---

## 19\. Failure modes and recovery

| Symptom | Recovery |
| :---- | :---- |
| `createdevice error 6` on every device | Donor regression. Run `scripts/check_donor_consistency.py`. If it fails, restore donors from `git show main:tooling/donors/<type>.amxd > tooling/donors/<type>.amxd`. |
| `validate_spec` accepts something that fails in Max | Add the failure case to `tests/specs/bad/` and tighten the schema. |
| `m4l_mcp_server.py` can't import `mcp` | `./venv/bin/pip install 'mcp>=1.2.0'`. Document in PR body. |
| `m4l_verify.py` times out on TCP 9877 | AbletonMCP not enabled in Live's Control Surface row. User must enable, then **quit and reopen Live** if `install_remote_scripts.py` was just run. |
| `M4L_VERIFY_OK` never appears for a recipe | Pipe `m4l_verify.py` stderr to `tooling/m4l_pipeline.py diagnose`; follow the fix. Most likely: missing presentation rect, or audio\_effect on a MIDI track. |
| Module split breaks `scripts/m4l_verify.py` imports | Confirm `tooling/m4l_pipeline.py` re-exports every symbol on `from m4l_pipeline import ...` lines (grep the scripts). |
| `--json` mode prints extra lines before the JSON | Agents expect JSON on the **last** line. Tail-1 parse. |
| A recipe's `build.py` produces a spec that fails T3 | Reduce to the minimal working pattern (refer to `examples/simple_gain_audio_spec.json` proven path); refine after T3 passes. |

---

## 20\. Test commands cheat sheet

\# \=== T0 — offline (no Live required) \===

./venv/bin/python scripts/validate\_spec.py examples/simple\_gain\_audio\_spec.json

./venv/bin/python scripts/validate\_spec.py examples/volume\_knob\_audio\_spec.json

./venv/bin/python tooling/m4l\_pipeline.py build examples/simple\_gain\_audio\_spec.json /tmp/sg.amxd

./venv/bin/python tooling/m4l\_pipeline.py verify examples/simple\_gain\_audio\_spec.json

./venv/bin/python scripts/check\_donor\_consistency.py

./venv/bin/python scripts/check\_workspace\_not\_staged.py

./venv/bin/python scripts/test\_m4l\_pipeline\_deploy.py

./venv/bin/python scripts/test\_verification\_helpers.py

./venv/bin/python scripts/test\_schema\_negatives.py        \# change 1

./venv/bin/python scripts/test\_spec\_builder.py            \# change 2

for d in examples/recipes/\*/; do ./venv/bin/python "$d/build.py"; done   \# change 3

./venv/bin/python tooling/spec\_to\_svg.py examples/simple\_gain\_audio\_spec.json \-o /tmp/sg.svg    \# change 4

echo "createdevice error 6" | ./venv/bin/python tooling/m4l\_pipeline.py diagnose       \# change 7

\# \=== T1 — Ableton install on disk (no Live running) \===

./venv/bin/python scripts/verify\_setup.py \--preflight

\# \=== T2/T3 — Live running \+ AbletonMCP \+ AbletonOSC enabled \===

./venv/bin/python scripts/verify\_setup.py \--wait-mcp 120 \--assert-create-audio-track

./venv/bin/python scripts/m4l\_verify.py \--spec examples/simple\_gain\_audio\_spec.json \--expect-params Gain

./venv/bin/python scripts/m4l\_verify.py \--spec examples/volume\_knob\_audio\_spec.json \--expect-params Volume

./venv/bin/python scripts/m4l\_verify.py \--spec examples/recipes/gain/spec.json \--expect-params Gain

./venv/bin/python scripts/m4l\_verify.py \--spec examples/recipes/tone\_lowpass/spec.json \--expect-params Tone

./venv/bin/python scripts/m4l\_verify.py \--spec examples/recipes/saturator\_drive\_tone/spec.json \--expect-params Drive \--expect-params Tone

\# \=== MCP server (manual) \===

./venv/bin/python tooling/m4l\_mcp\_server.py    \# ^C to exit

---

## Appendix A — Style / honesty rules the agent must respect

1. Never claim "confirmed working" before T5 (or a real T4 self-test pass).  
2. Never commit anything under `projects/workspace/` except `README.md`.  
3. Never put private plugin names in branch names, tag names, PR titles, or commit subjects.  
4. Never modify `tooling/donors/*.amxd` without explicit human approval.  
5. Never break the marker contract (`M4L_VERIFY_OK`, `SPEC_VALIDATE_OK`, etc.) — `--json` is additive.  
6. Always quit Live fully after `scripts/install_remote_scripts.py` runs (the bundled MCP cache loads at startup).  
7. When in doubt about a Max attribute, copy from `examples/simple_gain_audio_spec.json` — it is the canary path that's known to work.

---

## Appendix B — Glossary

- **`.amxd`** — Max for Live device file. Binary header \+ JSON `{"patcher": ...}` payload.  
- **AbletonMCP** — Live Control Surface (Remote Script). TCP 9877\. Required for load \+ audio track creation.  
- **AbletonOSC** — Live Control Surface for parameter introspection. UDP 11000\.  
- **Donor** — a known-good `.amxd` whose binary header (especially `device-type marker` bytes 8–11 and inner-patcher `amxdtype`) we copy.  
- **Imported/** — the User Library subfolder where the pipeline deploys (so Live's browser indexes it).  
- **T0–T5** — verification tiers. T0 offline build, T3 OSC parameter check, T5 human-confirmed rack.  
- **Spec** — the JSON dict (today hand-written; with this PR, often produced by `spec_builder`) that drives `build_amxd`.

---

**End of plan.** A small agent executing this top-to-bottom, running the T0 tests after each commit and the T2/T3 protocol once at the end, should land a green PR.  
