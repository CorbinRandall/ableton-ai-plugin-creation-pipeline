#!/usr/bin/env python3
"""
End-to-end Live verify: build (optional) → browser → load → OSC parameters.

Requires Ableton Live (macOS or Windows) with AbletonMCP + AbletonOSC enabled.
Host scripts run on macOS, Windows, or Linux; Live control requires a Live host OS.

Usage (repo root — use your venv Python when available):

  python scripts/m4l_verify.py
  python scripts/m4l_verify.py --spec projects/Pipeline_Example/pipeline_example_spec.json
  python scripts/m4l_verify.py --device-type audio_effect --device-name MyFx --skip-build
  python scripts/m4l_verify.py --selftest-default-port   # T4 on default template port 39129

See: docs/VERIFY_GUIDE.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_TOOLING = REPO_ROOT / "tooling"
_SCRIPT_DIR = Path(__file__).resolve().parent
for p in (_TOOLING, _SCRIPT_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from live_osc_helpers import (  # noqa: E402
    DEFAULT_SELFTEST_UDP_PORT,
    ableton_cmd,
    coerce_dict,
    expected_param_names_from_spec,
    osc_device_parameter_names,
    poll_browser_imported,
    udp_selftest_bind,
    udp_selftest_receive_until,
)
from m4l_pipeline import (  # noqa: E402
    _BROWSER_MAP,
    _create_new_track_for_device_type,
    assert_loaded_device_matches_spec,
    build_deploy_load,
    load_browser_item_by_browser_path,
)

DEFAULT_SPEC = REPO_ROOT / "projects" / "Pipeline_Example" / "pipeline_example_spec.json"


def _params_include(names: tuple[str, ...], expected: tuple[str, ...]) -> bool:
    """True if each expected string matches some parameter name (exact or substring)."""
    return all(any(exp == n or exp in n for n in names) for exp in expected)


def _missing_expected(names: tuple[str, ...], expected: tuple[str, ...]) -> list[str]:
    return [e for e in expected if not any(e == n or e in n for n in names)]


def _load_spec(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _browser_imported_parent(device_type: str) -> str:
    root = _BROWSER_MAP.get(device_type, _BROWSER_MAP["midi_effect"])
    return f"{root}/Imported"


def _build_and_deploy(spec: dict, *, spec_path: Path | None) -> tuple[str, str]:
    """Deploy from spec; return (device stem, device_type)."""
    name = spec.get("name", "Untitled")
    device_type = spec.get("device_type", "midi_effect")
    prev = os.environ.get("M4L_PROJECTS_PREFIX")
    try:
        if spec_path and "Pipeline_Example" in str(spec_path).replace("\\", "/"):
            os.environ.pop("M4L_PROJECTS_PREFIX", None)
        build_deploy_load(spec, None, skip_live=True, with_adv=True)
    finally:
        if prev is not None:
            os.environ["M4L_PROJECTS_PREFIX"] = prev
        elif spec_path and "Pipeline_Example" in str(spec_path).replace("\\", "/"):
            os.environ.pop("M4L_PROJECTS_PREFIX", None)
    return name, device_type


def _run_pipeline_example_builder() -> int:
    proj = REPO_ROOT / "projects" / "Pipeline_Example"
    sys.path.insert(0, str(proj))
    import build_pipeline_example as bpe  # noqa: E402

    return bpe.main(["--no-live"])


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--spec",
        type=Path,
        default=None,
        help=f"Device spec JSON (default: {DEFAULT_SPEC.relative_to(REPO_ROOT)})",
    )
    ap.add_argument(
        "--device-name",
        default=None,
        help="Deployed .amxd stem (default: spec name field)",
    )
    ap.add_argument(
        "--device-type",
        choices=("midi_effect", "audio_effect", "instrument"),
        default=None,
        help="Browser/deploy category (default: from spec or midi_effect)",
    )
    ap.add_argument(
        "--expect-params",
        default="",
        help="Comma-separated parameter name substrings (default: from spec or tutorial)",
    )
    ap.add_argument(
        "--build",
        choices=("auto", "pipeline_example"),
        default="auto",
        help="auto: build from --spec; pipeline_example: tutorial builder only",
    )
    ap.add_argument("--skip-build", action="store_true", help="Device must already be under Imported/")
    ap.add_argument(
        "--browser-poll-attempts",
        type=int,
        default=None,
        metavar="N",
        help="Override MCP browser poll retries (default: 5 if --skip-build else 12)",
    )
    ap.add_argument(
        "--browser-poll-delay",
        type=float,
        default=None,
        metavar="SEC",
        help="Seconds between browser polls (default: 0.35 if --skip-build else 1.0)",
    )
    ap.add_argument("--no-cleanup", action="store_true", help="Leave track/devices in place")
    ap.add_argument("--no-osc", action="store_true", help="MCP load only; skip OSC parameter checks")
    ap.add_argument(
        "--require-selftest-udp-port",
        type=int,
        default=None,
        metavar="PORT",
        help=(
            "T4: UDP port bound before load; expect Max ping containing 'm4l_selftest'. "
            f"Template default port is {DEFAULT_SELFTEST_UDP_PORT} (see --selftest-default-port)."
        ),
    )
    ap.add_argument(
        "--selftest-default-port",
        action="store_true",
        help=f"Shorthand for --require-selftest-udp-port {DEFAULT_SELFTEST_UDP_PORT} (must match template udpsend)",
    )
    ap.add_argument(
        "--print-mcp-device-health",
        action="store_true",
        help="After load, print get_device_health snapshot (requires MCP patch from install_remote_scripts.py)",
    )
    args = ap.parse_args()

    spec_path = args.spec or DEFAULT_SPEC
    spec: dict | None = None
    if spec_path.is_file():
        spec = _load_spec(spec_path)

    device_type = args.device_type or (spec.get("device_type") if spec else None) or "midi_effect"
    name = args.device_name or (spec.get("name") if spec else None) or "Pipeline_Example"

    if args.expect_params.strip():
        expected = tuple(s.strip() for s in args.expect_params.split(",") if s.strip())
    elif spec:
        expected = expected_param_names_from_spec(spec)
    elif name == "Pipeline_Example":
        expected = ("Rate", "Depth", "Active")
    else:
        expected = ()

    if not args.skip_build:
        if args.build == "pipeline_example":
            if not (REPO_ROOT / "projects" / "Pipeline_Example").is_dir():
                print("ERROR: Pipeline_Example project missing", file=sys.stderr)
                return 1
            rc = _run_pipeline_example_builder()
            if rc != 0:
                return rc
        elif spec:
            print(f"==> build_deploy_load (no Live) from {spec_path}")
            name, device_type = _build_and_deploy(spec, spec_path=spec_path)
        else:
            print(f"ERROR: --spec file not found: {spec_path}", file=sys.stderr)
            return 1

    parent = _browser_imported_parent(device_type)

    poll_attempts = (
        args.browser_poll_attempts if args.browser_poll_attempts is not None else (5 if args.skip_build else 12)
    )
    poll_delay = (
        args.browser_poll_delay if args.browser_poll_delay is not None else (0.35 if args.skip_build else 1.0)
    )

    selftest_port = args.require_selftest_udp_port
    if args.selftest_default_port:
        if selftest_port is not None:
            print(
                "ERROR: use only one of --selftest-default-port or --require-selftest-udp-port",
                file=sys.stderr,
            )
            return 1
        selftest_port = DEFAULT_SELFTEST_UDP_PORT

    selftest_sock = None
    if selftest_port is not None:
        try:
            selftest_sock = udp_selftest_bind(selftest_port)
        except OSError as e:
            print(
                f"ERROR: Cannot bind UDP 127.0.0.1:{selftest_port} for self-test: {e}",
                file=sys.stderr,
            )
            return 1

    try:
        ping = ableton_cmd("get_session_info", {})
        if ping.get("status") != "success":
            print(f"ERROR: get_session_info: {ping}", file=sys.stderr)
            return 1

        if not poll_browser_imported(parent, name, attempts=poll_attempts, delay=poll_delay):
            print(f"ERROR: '{name}' not found under {parent}", file=sys.stderr)
            return 1
        print(f"OK: browser lists '{name}' ({device_type})")

        try:
            track, track_kind = _create_new_track_for_device_type(device_type)
        except RuntimeError as e:
            print(f"ERROR: create track: {e}", file=sys.stderr)
            return 1
        print(f"OK: new {track_kind} track index {track}")

        load_path = f"{parent}/{name}"
        loaded = load_browser_item_by_browser_path(track, load_path)
        if loaded.get("status") != "success":
            print(f"ERROR: load {load_path!r}: {loaded}", file=sys.stderr)
            return 1
        print(f"OK: loaded onto track {track}")

        time.sleep(0.35)

        info = ableton_cmd("get_track_info", {"track_index": track})
        if info.get("status") != "success":
            print(f"ERROR: get_track_info: {info}", file=sys.stderr)
            return 1
        tinfo = coerce_dict(info.get("result"))
        devices = tinfo.get("devices", [])
        if not devices:
            print("ERROR: No devices on track after load", file=sys.stderr)
            return 1
        dev_index = devices[-1]["index"]
        dev_name = devices[-1].get("name", "")
        print(f"OK: device index {dev_index} name={dev_name!r}")

        try:
            assert_loaded_device_matches_spec(device_type, tinfo, track_kind=track_kind)
        except RuntimeError as e:
            print(f"ERROR: track/device alignment: {e}", file=sys.stderr)
            return 1

        if args.print_mcp_device_health:
            dh = ableton_cmd("get_device_health", {"track_index": track, "device_index": dev_index})
            if dh.get("status") == "success":
                print(f"OK: MCP device health: {dh.get('result')}")
            else:
                print(
                    f"NOTE: get_device_health failed (install MCP patch or restart Live?): {dh}",
                    file=sys.stderr,
                )

        if selftest_sock is not None:
            if not udp_selftest_receive_until(
                selftest_sock,
                b"m4l_selftest",
                time.monotonic() + 15.0,
            ):
                print(
                    "ERROR: T4 self-test — no UDP datagram containing b'm4l_selftest' "
                    f"on port {selftest_port} (see tooling/templates/midi_effect_selftest_ping.json)",
                    file=sys.stderr,
                )
                return 1
            print("DEVICE_SELFTEST_OK")

        if name not in dev_name and dev_name not in name:
            print(
                f"WARN: loaded name {dev_name!r} does not match expected {name!r}",
                file=sys.stderr,
            )

        if args.no_osc:
            print("NOTE: --no-osc: skipping parameter checks")
        else:
            # Max devices often register Live parameter tuples shortly after load — AbletonOSC
            # may only see "Device On" until initialization completes.
            deadline = time.monotonic() + 45.0
            names: tuple[str, ...] = ()
            while time.monotonic() < deadline:
                try:
                    names = osc_device_parameter_names(track, dev_index, wait=2.0)
                except Exception as e:
                    print(
                        f"ERROR: AbletonOSC failed: {e}\n"
                        "  Enable AbletonOSC in Live; ensure UDP 11001 is free.",
                        file=sys.stderr,
                    )
                    return 1
                if not expected or _params_include(names, expected):
                    break
                time.sleep(0.75)

            if expected:
                missing = _missing_expected(names, expected)
                if missing:
                    print(f"ERROR: Missing parameters {missing}; got {names}", file=sys.stderr)
                    return 1
                print(f"OK: OSC parameters include {expected}")
            else:
                print(f"NOTE: OSC parameter names ({len(names)}): {names[:16]}...")

        if not args.no_cleanup:
            try:
                clr = ableton_cmd("clear_devices_on_track", {"track_index": track})
                if clr.get("status") == "success":
                    print(f"OK: cleared devices on track {track}")
                else:
                    print(f"NOTE: clear_devices_on_track: {clr.get('message', clr)}")
            except Exception:
                print("NOTE: cleanup skipped")

        print("M4L_VERIFY_OK")
        return 0
    except OSError as e:
        print(
            f"ERROR: Cannot reach AbletonMCP at 127.0.0.1:9877: {e}\n"
            "  Quit/reopen Live; enable AbletonMCP under Preferences → Link / Tempo / MIDI.",
            file=sys.stderr,
        )
        return 1
    finally:
        if selftest_sock is not None:
            try:
                selftest_sock.close()
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
