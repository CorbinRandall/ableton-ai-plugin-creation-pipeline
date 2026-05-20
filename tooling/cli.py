"""Command-line interface for the M4L pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from amxd.builder import build_amxd
from deploy import build_deploy_load, deploy_artifact_for_device_type
from patch import _parse_rgba_csv, patch_amxd_field
from paths import WORKSPACE
from verify_offline import verify_spec_offline


def _cli():
    if len(sys.argv) < 2:
        import m4l_pipeline

        print(m4l_pipeline.__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "build":
        argv_tail = sys.argv[2:]
        skip_validate = "--skip-validate" in argv_tail
        filtered = [a for a in argv_tail if a != "--skip-validate"]
        if not filtered:
            print("usage: m4l_pipeline.py build <spec.json> [output.amxd] [--skip-validate]", file=sys.stderr)
            sys.exit(1)
        spec_path = Path(filtered[0])
        output = Path(filtered[1]) if len(filtered) > 1 else None
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        build_amxd(spec, output, skip_validate=skip_validate)
        out = output or (WORKSPACE / f"{spec.get('name', 'Untitled')}.amxd")
        print(
            "\nNOTE: No Ableton Live step ran. To deploy + insert on a NEW track (default):\n"
            f"  python3 {WORKSPACE / 'm4l_pipeline.py'} all {spec_path}\n"
            "Or deploy then load manually: deploy → load",
            file=sys.stderr,
        )

    elif cmd == "deploy":
        argv_tail = sys.argv[2:]
        imported = "--category-root" not in argv_tail
        filtered = [a for a in argv_tail if a != "--category-root"]
        if not filtered:
            print(
                "usage: m4l_pipeline.py deploy <path.amxd|.adv> [device_type] [--category-root]",
                file=sys.stderr,
            )
            sys.exit(1)
        artifact = Path(filtered[0])
        device_type = filtered[1] if len(filtered) > 1 else "midi_effect"
        deploy_artifact_for_device_type(artifact, device_type, imported=imported)

    elif cmd == "patch":
        argv_tail = sys.argv[2:]
        if not argv_tail:
            print(
                "usage: m4l_pipeline.py patch <file.amxd> [--bgcolor R,G,B,A] "
                "[--editing-bgcolor R,G,B,A] [--title-text TEXT] [--title-color R,G,B,A] "
                "[--in-place] [--allow-dlst-rebuild] [--deploy device_type]",
                file=sys.stderr,
            )
            sys.exit(1)
        amxd = Path(argv_tail[0])
        bgcolor = editing_bgcolor = title_text = title_color = None
        in_place = False
        allow_dlst_rebuild = False
        deploy_type: str | None = None
        i = 1
        while i < len(argv_tail):
            a = argv_tail[i]
            if a == "--bgcolor" and i + 1 < len(argv_tail):
                bgcolor = _parse_rgba_csv(argv_tail[i + 1])
                i += 2
            elif a == "--editing-bgcolor" and i + 1 < len(argv_tail):
                editing_bgcolor = _parse_rgba_csv(argv_tail[i + 1])
                i += 2
            elif a == "--title-text" and i + 1 < len(argv_tail):
                title_text = argv_tail[i + 1]
                i += 2
            elif a == "--title-color" and i + 1 < len(argv_tail):
                title_color = _parse_rgba_csv(argv_tail[i + 1])
                i += 2
            elif a == "--in-place":
                in_place = True
                i += 1
            elif a == "--allow-dlst-rebuild":
                allow_dlst_rebuild = True
                i += 1
            elif a == "--deploy" and i + 1 < len(argv_tail):
                deploy_type = argv_tail[i + 1]
                i += 2
            else:
                print(f"Unknown patch argument: {a}", file=sys.stderr)
                sys.exit(1)
        out = patch_amxd_field(
            amxd,
            bgcolor=bgcolor,
            editing_bgcolor=editing_bgcolor,
            title_text=title_text,
            title_color=title_color,
            in_place=in_place,
            allow_dlst_rebuild=allow_dlst_rebuild,
        )
        if deploy_type:
            deploy_artifact_for_device_type(out, deploy_type, imported=True)

    elif cmd == "diagnose":
        text = sys.stdin.read() if len(sys.argv) <= 2 else " ".join(sys.argv[2:])
        from diagnose import diagnose as _diagnose

        result = _diagnose(text)
        print(json.dumps(result, indent=2))

    elif cmd == "verify":
        argv_tail = sys.argv[2:]
        skip_validate = "--skip-validate" in argv_tail
        filtered = [a for a in argv_tail if a != "--skip-validate"]
        if not filtered:
            print("usage: m4l_pipeline.py verify <spec.json> [--skip-validate]", file=sys.stderr)
            sys.exit(1)
        spec = json.loads(Path(filtered[0]).read_text(encoding="utf-8"))
        result = verify_spec_offline(spec, skip_validate=skip_validate)
        print(json.dumps(result, indent=2))
        print("M4L_VERIFY_OFFLINE_OK")

    elif cmd == "load":
        from live.browser import load_device

        track = int(sys.argv[2])
        name = sys.argv[3]
        device_type = sys.argv[4] if len(sys.argv) > 4 else "midi_effect"
        load_device(track, name, device_type)

    elif cmd == "info":
        from live.tracks import get_track_info

        track = int(sys.argv[2])
        info = get_track_info(track)
        print(json.dumps(info, indent=2))

    elif cmd == "session":
        from live.tracks import get_session_info

        info = get_session_info()
        print(json.dumps(info, indent=2))

    elif cmd == "all":
        argv_tail = sys.argv[2:]
        skip_live = False
        skip_validate = False
        with_adv = False
        filtered: list[str] = []
        for a in argv_tail:
            if a in ("--no-live", "--skip-live"):
                skip_live = True
            elif a == "--skip-validate":
                skip_validate = True
            elif a == "--with-adv":
                with_adv = True
            else:
                filtered.append(a)
        if not filtered:
            print(
                "usage: m4l_pipeline.py all <spec.json> [track_index|new] "
                "[--no-live] [--skip-validate] [--with-adv]",
                file=sys.stderr,
            )
            sys.exit(1)
        spec_path = Path(filtered[0])
        track: int | None = None
        if len(filtered) > 1:
            raw = filtered[1].lower()
            if raw not in ("new", "auto", "-1"):
                track = int(filtered[1])
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        result = build_deploy_load(
            spec,
            track,
            skip_live=skip_live,
            skip_validate=skip_validate,
            with_adv=with_adv,
        )
        print(json.dumps(result, indent=2, default=str))
        if not skip_live:
            lr = result.get("load_result") or {}
            if lr.get("status") != "success":
                print(
                    "\nERROR: Device did not load in Live. Common fixes: Live running, "
                    "AbletonMCP control surface enabled (TCP 9877), browser finished indexing "
                    "— or use --no-live and load by hand.",
                    file=sys.stderr,
                )
                sys.exit(1)

    else:
        import m4l_pipeline

        print(f"Unknown command: {cmd}")
        print(m4l_pipeline.__doc__)
        sys.exit(1)
