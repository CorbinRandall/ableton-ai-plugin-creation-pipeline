# Contributing

Thanks for helping improve this pipeline.

## Getting started

1. **Fork** the repository (or clone directly if you have write access).
2. Run **`./run`** (macOS/Linux) or **`.\run.ps1`** (Windows) from the repo root — or **`./bootstrap.sh`** when debugging install only.
3. Confirm **`M4L_RUN_OK`** (or **`./venv/bin/python scripts/verify_setup.py --preflight`** — donors + Remote Scripts; see **`docs/RUN.md`**).

### Spec validation

```bash
./venv/bin/python scripts/validate_spec.py projects/Pipeline_Example/pipeline_example_spec.json
```

### Readable diffs on `.amxd` (optional)

Contributors may use [Ableton maxdevtools](https://github.com/Ableton/maxdevtools) `maxdiff` for human-readable `git diff` on Max devices. Agent workflows use **spec JSON** and [`scripts/export_spec_from_amxd.py`](scripts/export_spec_from_amxd.py) instead.

## Pull requests

- Keep changes focused on one concern when possible.
- Python style: match surrounding files; **`python -m compileall -q scripts tooling projects`** should stay clean (same as CI).

## Do not commit

- **`venv/`** — local virtualenv (listed in **`.gitignore`**).
- **`.env`**, API keys, or licensed Ableton pack content you cannot redistribute.
- Large binaries unless they are clearly licensed for redistribution.
- **Personal plugin trees** under **`projects/workspace/`** — that directory is **gitignored by design** so **`git pull`** does not delete your work and you are not prompted to push local devices. See **`projects/workspace/README.md`**.

## Licensing

By contributing, you agree your contributions are under the same license as this repository (**MIT**, see **`LICENSE`**).
