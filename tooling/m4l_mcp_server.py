#!/usr/bin/env python3
"""M4L pipeline MCP server (stdio).

Run with:

  python tooling/m4l_mcp_server.py            # raw stdio
  mcp dev tooling/m4l_mcp_server.py             # interactive (requires mcp package)

Tools expose validate/build/deploy/load/diagnose so MCP-capable agents
can drive the pipeline without shell parsing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tooling"))
sys.path.insert(0, str(REPO / "scripts"))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    sys.stderr.write("mcp package not installed. pip install 'mcp>=1.2.0'\n")
    sys.exit(2)

from spec_validate import validate_spec as _validate_spec  # noqa: E402
import spec_builder  # noqa: E402
from m4l_pipeline import (  # noqa: E402
    build_amxd,
    build_deploy_load,
    deploy_artifact_for_device_type,
)
from spec_to_svg import render as _render_svg  # noqa: E402
from diagnose import diagnose as _diagnose  # noqa: E402

mcp = FastMCP("m4l-pipeline")

RECIPES_DIR = REPO / "examples" / "recipes"


@mcp.tool()
def list_recipes() -> dict:
    """List all built-in device recipes."""
    items = []
    for d in sorted(RECIPES_DIR.glob("*/")):
        readme = d / "README.md"
        desc = readme.read_text(encoding="utf-8").splitlines()[0] if readme.exists() else d.name
        spec_path = d / "spec.json"
        device_type = "?"
        if spec_path.exists():
            device_type = json.loads(spec_path.read_text(encoding="utf-8")).get("device_type", "?")
        items.append({"slug": d.name, "type": device_type, "description": desc})
    return {"recipes": items}


@mcp.tool()
def read_recipe_spec(slug: str) -> dict:
    """Return the spec dict for a named recipe (must be built first)."""
    spec_path = RECIPES_DIR / slug / "spec.json"
    if not spec_path.exists():
        return {
            "error": f"recipe {slug!r} has no spec.json — run examples/recipes/{slug}/build.py"
        }
    return {"spec": json.loads(spec_path.read_text(encoding="utf-8"))}


@mcp.tool()
def compose_spec_from_dsl(python_source: str) -> dict:
    """Evaluate spec_builder code; must assign `device = audio_effect(...)` (or similar)."""
    ns = {
        "audio_effect": spec_builder.audio_effect,
        "midi_effect": spec_builder.midi_effect,
        "instrument": spec_builder.instrument,
        "Device": spec_builder.Device,
        "json": json,
    }
    exec(python_source, ns)
    dev = ns.get("device")
    if not isinstance(dev, spec_builder.Device):
        return {"error": "snippet must assign `device = audio_effect(...)` etc."}
    return {"spec": dev.to_dict()}


@mcp.tool()
def validate_spec(spec: dict) -> dict:
    errors, warnings = _validate_spec(spec)
    return {"errors": errors, "warnings": warnings, "ok": not errors}


@mcp.tool()
def spec_to_svg(spec: dict) -> dict:
    return {"svg": _render_svg(spec)}


@mcp.tool()
def build_amxd_tool(spec: dict, out_path: str | None = None) -> dict:
    out = Path(out_path) if out_path else None
    built = build_amxd(spec, out)
    return {"amxd_path": str(built)}


@mcp.tool()
def deploy(amxd_path: str, device_type: str) -> dict:
    deployed = deploy_artifact_for_device_type(
        Path(amxd_path), device_type, imported=True
    )
    return {"deployed_paths": [str(p) for p in deployed]}


@mcp.tool()
def load_in_live(spec: dict, with_adv: bool = False) -> dict:
    result = build_deploy_load(spec, None, skip_live=False, with_adv=with_adv)
    return result


@mcp.tool()
def diagnose(error_text: str) -> dict:
    """Match known error patterns to recommended fixes."""
    return _diagnose(error_text)


if __name__ == "__main__":
    mcp.run()
