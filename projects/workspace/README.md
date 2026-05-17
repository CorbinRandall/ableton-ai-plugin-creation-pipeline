# `projects/workspace/` — local plugins (not in Git)

Put **your own** Max for Live projects here — one folder per plugin (spec JSON, `build_*.py`, notes, `versions/`, etc.).

## Why this exists

- **`git pull` / `git merge` never deletes untracked files.** Everything under **`workspace/`** is **gitignored**, so upstream updates **do not wipe** your trees.
- **`git status` stays clean** — you are not nudged to commit `.amxd` blobs or version folders unless you choose to.

The canonical **tutorial** stays in **`projects/Pipeline_Example/`** (tracked source only). Generated **`Pipeline_Example */`** folders there are **ignored** too.

Personal plugins (specs, **`build_*.py`**, **`versions/`**) stay **only** under **`workspace/`** — they never ship with this repo and **`git pull`** will not remove them.

### Private builders: deploy **and** load in Live

Match **`projects/Pipeline_Example/build_pipeline_example.py`**, which calls **`build_deploy_load(..., skip_live=...)`** with **`skip_live=False`** unless **`--no-live`**.

If you deploy **`.amxd`** files yourself then call **`tooling/m4l_pipeline.load_imported_device_new_track`**, default **`skip_live=False`** so AbletonMCP **creates a new track** (type follows **`device_type`**) and loads from **User Library → Imported/**. Opt out with **`--no-live`** / **`M4L_SKIP_LIVE=1`** for CI or headless builds — same contract as **`m4l_pipeline.py all`**.

## Recommended: route pipeline builds here

From the repo root (shell profile, **`.env`** loaded by your tooling, or inline):

```bash
export M4L_PROJECTS_PREFIX=workspace
```

Then **`tooling/m4l_pipeline.py`** / **`build_deploy_load`** create version folders **and**, unless you use **`all --no-live`** / **`M4L_SKIP_LIVE`**, **insert the device on a new Live track** via AbletonMCP (Live must be running with AbletonMCP enabled):

```text
projects/workspace/<PluginSlug>/<Plugin Name> 1.1/
```

instead of **`projects/<PluginSlug>/`** when the prefix is unset.

**Unset** `M4L_PROJECTS_PREFIX` when you want the default **`projects/<slug>/`** layout (rare if you keep personal work in this folder).

The tutorial script **`projects/Pipeline_Example/build_pipeline_example.py`** **forces** the tutorial path so it **always** writes under **`projects/Pipeline_Example/`**, even if `M4L_PROJECTS_PREFIX` is set.

## Sharing your work

This folder is ignored — **clone others do not get your plugins.** To publish:

- Push from a **fork** after selectively **`git add -f`** (not ideal), or  
- Move stable specs into a **separate repo**, or  
- Use **GitHub Releases** / artifact uploads for **`.amxd`** files.

Pick what matches how open you want the device to be.
