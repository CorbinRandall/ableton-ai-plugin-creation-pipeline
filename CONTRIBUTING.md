# Contributing

Thanks for helping improve this pipeline.

## Getting started

1. **Fork** the repository (or clone directly if you have write access).
2. Run **`./bootstrap.sh`** (macOS/Linux) or **`bootstrap.ps1`** (Windows) so **`venv/`** and dependencies exist locally.
3. Run **`./venv/bin/python scripts/verify_setup.py --preflight`** — fix missing donor **`.amxd`** / Remote Scripts per **`docs/SETUP_AUTOMATED.md`**.

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
