# Reference `.amxd` (header donor)

Python **`tooling/m4l_pipeline.build_amxd`** does not synthesize an `.amxd` from zero: it clones the binary **header / subheader** from a donor device on disk, then swaps the JSON patcher body and rebuilds **`dlst`**.

The donor’s **presentation layout is not your UI** — only the wrapper shape is reused. For visible knobs in Live, each control in your spec needs **`presentation: 1`** and **`presentation_rect`** (see **[`M4L_FRONTEND_AND_BACKEND.md`](M4L_FRONTEND_AND_BACKEND.md)**).

## Default donor path

``${ABLETON_HOME}/User Library/Presets/MIDI Effects/Max MIDI Effect/Imported/Reference_Donor.amxd``

- **`ABLETON_HOME`** defaults to **`~/Music/Ableton`** (macOS) or **`~/Documents/Ableton`** (Windows).

You normally get this file when you purchase/import the **Reference Reference** M4L pack into your library. Other **mmmmmmeta**‑style MIDI effects may work only if they share the same on-disk wrapper shape — when in doubt, use the Reference device.

### Fresh machine / wiped User Library

1. Copy **`Reference_Donor.amxd`** from a backup Mac or from your old Ableton **`User Library/.../Imported/`** folder into the same **Imported/** path above, **or**
2. Point the tooling at **any accessible path**:

```bash
export M4L_REFERENCE_AMXD="$HOME/MyBackups/Reference_Donor.amxd"
./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py
```

`./bootstrap.sh` does **not** download this donor (third‑party commercial/pack-specific).

**Preflight:** `./venv/bin/python scripts/verify_setup.py --preflight` checks that this file exists whenever `tooling/m4l_pipeline.py` imports cleanly.

---

## Adding another device project under **`projects/`**

Use **`projects/Pipeline_Example/`** as the template: a **spec** JSON, a small **`build_*.py`** that imports **`m4l_pipeline`** from **`tooling/`**, and optionally a **`.code-workspace`** file so your editor opens **`tooling/`** and **`projects/<YourPlugin>/`** side by side.

**Recommended for anything you ship locally:** put the folder under **`projects/workspace/<YourPlugin>/`** and set **`M4L_PROJECTS_PREFIX=workspace`** so **`build_deploy_load`** writes version dirs under **`projects/workspace/`**, which is **gitignored** — **`git pull`** will not delete those trees and **`git status`** stays clean. See **`projects/workspace/README.md`**.

Layout pattern:

```text
<repo-root>/
  tooling/m4l_pipeline.py
  projects/workspace/<YourPlugin>/your_build.py   # with M4L_PROJECTS_PREFIX=workspace
```

The builder uses **`_DEST_MAP`** from **`m4l_pipeline`** and **`ABLETON_HOME`** — **no hard-coded user paths**. Helpers in **`scripts/m4l_verify.py`** target the tutorial device; extend them or verify manually in Live for your own device names.
