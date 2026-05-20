# Scrubbing private names from git history

If a **private plugin name** or path under `projects/workspace/` was ever committed to this **public** repository, removing it from the latest commit is not enough — the name remains in **git history**, **PR titles**, **branch names**, and **forks**.

## Before you scrub

- **Assume anything pushed to GitHub is public forever** unless the repo is private and you control all forks.
- Prefer **preventing** leaks: see [`PRIVATE_PLUGINS.md`](PRIVATE_PLUGINS.md) and install the local pre-commit hook:

  ```bash
  ./venv/bin/python scripts/install_workspace_pre_commit.py
  ```

## If a name already landed in commits

1. **Stop** adding more references in tracked files, commit messages, PR titles, or branch names.
2. Use **[`git filter-repo`](https://github.com/newren/git-filter-repo)** or **[BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)** to rewrite history locally.
3. **Force-push** only if you understand that collaborators must re-clone; **open PRs and forks keep old history**.
4. For high-sensitivity work, consider a **fresh public repo** and retire the leaked one.

## What this repo does not scrub automatically

| Location | In repo? |
|----------|----------|
| `projects/workspace/*` (contents) | Gitignored |
| `.cursor/agent-transcripts/` | Gitignored (if present locally) |
| Your machine `.git/info/exclude` | Never pushed |
| Commit messages / PR titles | **Public** — edit manually before merge |

## Agents

When fixing pipeline bugs learned from a private project, describe the **bug class** only (device-class deploy mismatch, appversion stamp, etc.) — not private plugin names — in tracked docs and commit messages.
