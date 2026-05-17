# GitHub repository metadata (public checklist)

Use this when configuring **[github.com/CorbinRandall/ableton-plugin-pipeline](https://github.com/CorbinRandall/ableton-plugin-pipeline)** (or a fork you intend to publish).

## Visibility → Public

1. Open the repo on GitHub → **Settings**.
2. Scroll to **Danger zone** → **Change repository visibility**.
3. Choose **Public** and confirm.

*(No GitHub CLI required.)*

## “About” sidebar (right-hand side on the repo home page)

Click **⚙️** (gear) next to **About** and set:

**Description** (short, ≤350 characters):

```
Bootstrap + Python pipeline for Max for Live: JSON spec → .amxd → Ableton User Library → load on a new track via AbletonMCP; AbletonOSC checks; macOS/Windows. Needs Live Suite or Standard+M4L.
```

**Website** (optional): leave blank, or point to this README’s documentation tree (there is no separate docs site).

**Topics** (suggested tags for discovery):

```
ableton-live
max-for-live
amxd
python
abletonmcp
abletonosc
music-production
automation
cursor
```

## Releases

Optional: tag **`v1.0.0`** (or **`v0.1.0`**) when you want a snapshot — **Release notes** can summarize bootstrap + **`verify_setup.py`** + tutorial **`Pipeline_Example`**.

## Creating a *new* empty repo (alternative flow)

If you ever recreate the remote from scratch:

| Setting | Choose |
|---------|--------|
| **Visibility** | **Public** |
| **Add README** | **Off** *(this repo ships `README.md`.)* |
| **Add .gitignore** | **No** *(use included `.gitignore`.)* |
| **Add license** | **No** *(use included `LICENSE`.)* |

Then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

For **this** canonical tree, **`origin`** is expected to be **`https://github.com/CorbinRandall/ableton-plugin-pipeline.git`**.
