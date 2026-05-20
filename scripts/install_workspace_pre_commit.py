#!/usr/bin/env python3
"""Install a local pre-commit hook that blocks staging projects/workspace/*."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / ".git" / "hooks" / "pre-commit"
CHECK = REPO_ROOT / "scripts" / "check_workspace_not_staged.py"


def main() -> int:
    if not (REPO_ROOT / ".git").is_dir():
        print("ERROR: not a git repository", flush=True)
        return 1
    if not CHECK.is_file():
        print(f"ERROR: missing {CHECK}", flush=True)
        return 1

    script = f"""#!/bin/sh
# Installed by scripts/install_workspace_pre_commit.py — local only, not tracked.
exec "{CHECK}" "$@"
"""
    HOOK.write_text(script, encoding="utf-8")
    HOOK.chmod(0o755)
    print(f"Installed pre-commit hook → {HOOK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
