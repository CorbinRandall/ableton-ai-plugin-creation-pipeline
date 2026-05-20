#!/usr/bin/env python3
"""Fail when tooling/donors/*.amxd disagree on Max appversion.major."""

from __future__ import annotations

import argparse
import sys
from copy import deepcopy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLING = REPO_ROOT / "tooling"
if str(TOOLING) not in sys.path:
    sys.path.insert(0, str(TOOLING))

from m4l_pipeline import (  # noqa: E402
    _extract_amxd_parts,
    _patcher_dict_from_amxd_root,
    _repack_amxd_patched,
    reference_amxd_path,
)


def _donor_appversion(path: Path) -> dict:
    _h, _s, root, _t = _extract_amxd_parts(path.read_bytes())
    patcher = _patcher_dict_from_amxd_root(root)
    av = patcher.get("appversion")
    if not isinstance(av, dict):
        raise ValueError(f"{path.name}: missing appversion")
    return av


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--align-instrument",
        action="store_true",
        help="Copy midi_effect appversion onto instrument donor (offline JSON patch).",
    )
    args = ap.parse_args()

    types = ("midi_effect", "audio_effect", "instrument")
    versions: dict[str, dict] = {}
    for dt in types:
        path = reference_amxd_path(dt)
        if not path.is_file():
            print(f"ERROR: missing donor {path}", file=sys.stderr)
            return 1
        versions[dt] = _donor_appversion(path)

    majors = {dt: int(v.get("major", 0)) for dt, v in versions.items()}
    unique_majors = set(majors.values())
    if len(unique_majors) > 1:
        print("ERROR: donor appversion.major mismatch:", file=sys.stderr)
        for dt in types:
            av = versions[dt]
            print(
                f"  {dt}: {av.get('major')}.{av.get('minor')}.{av.get('revision')} ({reference_amxd_path(dt).name})",
                file=sys.stderr,
            )
        if args.align_instrument and majors.get("instrument") != majors.get("midi_effect"):
            inst_path = reference_amxd_path("instrument")
            data = inst_path.read_bytes()
            _h, _s, root, _t = _extract_amxd_parts(data)
            patcher = deepcopy(_patcher_dict_from_amxd_root(root))
            patcher["appversion"] = deepcopy(versions["midi_effect"])
            out = _repack_amxd_patched(
                data,
                patcher,
                device_name=inst_path.stem,
                allow_dlst_rebuild=True,
            )
            inst_path.write_bytes(out)
            print(f"Aligned instrument donor appversion → {inst_path}")
            majors["instrument"] = majors["midi_effect"]
            unique_majors = {majors["midi_effect"]}
        if len(unique_majors) > 1:
            return 1

    print(f"OK: donor appversion.major={next(iter(unique_majors))} for {len(types)} donors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
