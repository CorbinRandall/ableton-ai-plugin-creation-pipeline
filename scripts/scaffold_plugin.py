#!/usr/bin/env python3
"""Scaffold a personal plugin under projects/workspace/ from a spec template.

Usage:

  ./venv/bin/python scripts/scaffold_plugin.py --name HumanTempo --type midi_effect
  python scripts/scaffold_plugin.py --name MyFx --type audio_effect --template audio_effect_stub
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_TEMPLATES = _REPO / "tooling" / "templates"

_TYPE_TO_TEMPLATE = {
    "midi_effect": "midi_effect_pass_through",
    "audio_effect": "audio_effect_stub",
    "instrument": "instrument_stub",
}


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", name.strip())
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        raise ValueError("name must contain at least one letter or digit")
    return s


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="Plugin name (PascalCase or words; used for spec name field)")
    ap.add_argument(
        "--type",
        required=True,
        choices=sorted(_TYPE_TO_TEMPLATE),
        help="device_type for the template",
    )
    ap.add_argument(
        "--template",
        help="Template basename without .json (default: from --type)",
    )
    ap.add_argument(
        "--workspace",
        action="store_true",
        default=True,
        help="Write under projects/workspace/ (default)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print paths only, do not write files",
    )
    args = ap.parse_args(argv)

    slug = _slug(args.name)
    template_key = args.template or _TYPE_TO_TEMPLATE[args.type]
    template_path = _TEMPLATES / f"{template_key}.json"
    if not template_path.is_file():
        print(f"ERROR: template not found: {template_path}", file=sys.stderr)
        return 1

    spec = json.loads(template_path.read_text(encoding="utf-8"))
    spec["name"] = re.sub(r"\s+", "", args.name.replace(" ", ""))
    if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", spec["name"]):
        print(
            "ERROR: --name must yield a valid spec name (letter first, alphanumeric/underscore)",
            file=sys.stderr,
        )
        return 1
    spec["device_type"] = args.type
    spec["description"] = f"{spec['name']} — scaffolded from {template_key}"

    if args.workspace:
        project_dir = _REPO / "projects" / "workspace" / slug
    else:
        project_dir = _REPO / "projects" / slug

    spec_path = project_dir / f"{slug.lower()}_spec.json"
    build_script = project_dir / f"build_{slug.lower()}.py"
    readme = project_dir / "README.md"

    build_py = f'''#!/usr/bin/env python3
"""Build + deploy + load **{spec["name"]}** (workspace sandbox)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_TOOLING = Path(__file__).resolve().parent.parent.parent / "tooling"
sys.path.insert(0, str(_TOOLING))
from m4l_pipeline import build_deploy_load  # noqa: E402

_HERE = Path(__file__).resolve().parent
_SPEC = _HERE / "{spec_path.name}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-live", action="store_true")
    ap.add_argument("--track", type=int, default=None)
    ap.add_argument("--with-adv", action="store_true")
    args = ap.parse_args()
    spec = json.loads(_SPEC.read_text(encoding="utf-8"))
    os.environ.setdefault("M4L_PROJECTS_PREFIX", "workspace")
    build_deploy_load(
        spec,
        args.track,
        skip_live=args.no_live,
        with_adv=args.with_adv,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

    readme_md = f"""# {spec["name"]} (workspace)

Personal sandbox — **gitignored**. See [`docs/PRIVATE_PLUGINS.md`](../../docs/PRIVATE_PLUGINS.md).

## Build

From repo root (Live + AbletonMCP for load):

```bash
export M4L_PROJECTS_PREFIX=workspace
./venv/bin/python projects/workspace/{slug}/build_{slug.lower()}.py
```

Artifacts-only:

```bash
./venv/bin/python projects/workspace/{slug}/build_{slug.lower()}.py --no-live
```

Validate spec (use venv Python — see docs/CROSS_PLATFORM.md):

```bash
python scripts/validate_spec.py projects/workspace/{slug}/{spec_path.name}
```

## Quick UI tweak (Max-first)

After editing presentation in Max, or to change background/title without rebuilding the graph:

```bash
./venv/bin/python tooling/m4l_pipeline.py patch path/to/device.amxd --bgcolor 0,0,0,1 --deploy {args.type}
```

See [`docs/TROUBLESHOOTING_M4L.md`](../../docs/TROUBLESHOOTING_M4L.md).
"""

    if args.dry_run:
        print(f"Would create:\\n  {spec_path}\\n  {build_script}\\n  {readme}")
        return 0

    if project_dir.exists() and any(project_dir.iterdir()):
        print(f"ERROR: project dir not empty: {project_dir}", file=sys.stderr)
        return 1

    project_dir.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    build_script.write_text(build_py, encoding="utf-8")
    build_script.chmod(0o755)
    readme.write_text(readme_md, encoding="utf-8")

    print(f"SCAFFOLD_OK {project_dir}")
    print(f"  spec:   {spec_path}")
    print(f"  build:  {build_script}")
    print("  Next: edit spec, validate, then build with Live open.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
