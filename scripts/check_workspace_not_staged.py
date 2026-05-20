#!/usr/bin/env python3
"""Block git commits that stage gitignored workspace plugin content."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWED = frozenset({"projects/workspace/README.md"})


def main() -> int:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if out.returncode != 0:
        print(out.stderr or out.stdout, file=sys.stderr)
        return out.returncode

    bad: list[str] = []
    for line in out.stdout.splitlines():
        path = line.strip().replace("\\", "/")
        if not path.startswith("projects/workspace/"):
            continue
        if path in ALLOWED:
            continue
        bad.append(path)

    if bad:
        print(
            "ERROR: staged paths under projects/workspace/ (private plugins must stay local):",
            file=sys.stderr,
        )
        for p in bad:
            print(f"  {p}", file=sys.stderr)
        print("See docs/PRIVATE_PLUGINS.md", file=sys.stderr)
        return 1

    print("OK: no private workspace paths staged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
