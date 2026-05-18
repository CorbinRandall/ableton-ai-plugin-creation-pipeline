#!/usr/bin/env python3
"""Fail if tracked files under projects/ fall outside the public allowlist.

Personal plugin work must live under projects/workspace/ (gitignored) or stay
local only. This script uses path allowlists only — no secret names in the repo.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Paths allowed in git under projects/ (posix-style, relative to repo root).
ALLOWED_PREFIXES = (
    "projects/Pipeline_Example/build_pipeline_example.py",
    "projects/Pipeline_Example/pipeline_example_spec.json",
    "projects/Pipeline_Example/README.md",
    "projects/Pipeline_Example/Pipeline_Example + Tooling.code-workspace",
    "projects/workspace/README.md",
)


def _tracked_under_projects() -> list[str]:
    import subprocess

    out = subprocess.run(
        ["git", "ls-files", "projects"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def _is_allowed(path: str) -> bool:
    if path in ALLOWED_PREFIXES:
        return True
    # No other paths under projects/ may be tracked.
    return False


def main() -> int:
    tracked = _tracked_under_projects()
    bad = [p for p in tracked if not _is_allowed(p)]
    if bad:
        print("ERROR: tracked files under projects/ outside the public allowlist:", file=sys.stderr)
        for p in bad:
            print(f"  {p}", file=sys.stderr)
        print(
            "\nPersonal plugins belong in projects/workspace/ with M4L_PROJECTS_PREFIX=workspace "
            "(see docs/PRIVATE_PLUGINS.md).",
            file=sys.stderr,
        )
        return 1
    print(f"OK: projects/ allowlist ({len(tracked)} tracked path(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
