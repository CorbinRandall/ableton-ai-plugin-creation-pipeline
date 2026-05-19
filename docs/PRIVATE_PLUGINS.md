# Keeping personal Max for Live work out of this public repo

This repository is **public**. Anything you build for yourself (commercial devices, unreleased specs, private `.amxd` files) must **never** be committed here.

The guardrails below use **generic paths and allowlists only**. They do **not** name your plugins, and you should **not** add your plugin names to `.gitignore`, CI config, or docs in this repo — that would still publish the name.

## Recommended workflow

1. **Route all personal builds through the gitignored sandbox**

   ```bash
   export M4L_PROJECTS_PREFIX=workspace
   ```

   Put your project under `projects/workspace/<YourPlugin>/` (spec, `build_*.py`, version folders, `.amxd` artifacts). That entire tree is **gitignored** except `projects/workspace/README.md`.

2. **Keep a coding-only clone** (optional)

   Use this repo on a machine without Ableton for Python/spec work. Use a **separate clone or machine** with Live for load/deploy tests so fewer secrets sit in one tree.

3. **Never commit under `projects/` except the tutorial**

   Tracked paths are intentionally tiny:

   - `projects/Pipeline_Example/` — tutorial sources only (not version build folders)
   - `projects/workspace/README.md` — explains the sandbox

   CI runs `scripts/check_projects_allowlist.py` to enforce that.

## If you built without `M4L_PROJECTS_PREFIX=workspace`

The pipeline may have created `projects/<SomeSlug>/` at the repo root. Those folders are **ignored by git** (see `.gitignore`) but you should still:

- Move the tree into `projects/workspace/` when possible, or delete local copies you do not need.
- Run `git status` before every commit; do not `git add projects/` blindly.

## Machine-only exclusions (names stay off GitHub)

For extra safety, add paths **only on your machine** (not committed):

**Per-clone** (this repository only):

```bash
# Edit .git/info/exclude — never pushed to GitHub
echo 'projects/your-private-slug/' >> .git/info/exclude
```

**Global** (all repos on your Mac):

```bash
git config --global core.excludesfile ~/.gitignore_global
# Add lines to ~/.gitignore_global — never in this repo
```

Use your real folder slug locally; do not commit that file to the public repo.

## What not to do

| Do not | Why |
|--------|-----|
| Put your plugin name in `.gitignore` / CI / docs here | The name would still appear in public git history |
| Commit `projects/workspace/` contents | The folder is ignored on purpose — use `git add -f` only if you know you are publishing |
| Commit version folders like `projects/Pipeline_Example/Pipeline_Example 1.2/` | Build artifacts; already gitignored for the tutorial |
| Mention unreleased devices in commit messages or PR titles on this repo | Messages are public forever |

## Preflight on a coding-only machine

```bash
./venv/bin/python scripts/verify_setup.py --preflight --skip-import-check
./venv/bin/python scripts/check_projects_allowlist.py
./venv/bin/python projects/Pipeline_Example/build_pipeline_example.py --no-live
```

Remote Script / Ableton checks may fail without Live; donor + allowlist checks should pass.

## Agentic IDE sessions (Cursor, Claude, Copilot, …)

If you use an AI coding assistant in this repo, keep **private device names and specs** in:

- `projects/workspace/` (gitignored), or
- A **separate private repository**, or
- Local rules under your user config — not in tracked files here.
