#!/usr/bin/env python3
"""Post-bootstrap health checks: MCP socket + AbletonOSC /live/test round-trip."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import ableton_bootstrap_common as abc  # noqa: E402

_ABLETON_HOST = "127.0.0.1"
_MCP_PORT = 9877
_OSC_SND = (_ABLETON_HOST, 11000)
_OSC_RECV = (_ABLETON_HOST, 11001)


def _poll_tcp(port: int, retries: float, interval: float) -> bool:
    deadline = time.monotonic() + retries
    while time.monotonic() < deadline:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect((_ABLETON_HOST, port))
            s.close()
            return True
        except OSError:
            time.sleep(interval)
    return False


def _ableton_cmd(cmd_type: str, params: dict, timeout: float = 25.0) -> dict:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((_ABLETON_HOST, _MCP_PORT))
    s.sendall(json.dumps({"type": cmd_type, "params": params}).encode())
    chunks: list[bytes] = []
    while True:
        chunk = s.recv(32768)
        if not chunk:
            break
        chunks.append(chunk)
        try:
            json.loads(b"".join(chunks))
            break
        except json.JSONDecodeError:
            continue
        except UnicodeDecodeError:
            continue
    s.close()
    if not chunks:
        raise RuntimeError("No reply from AbletonMCP.")
    return json.loads(b"".join(chunks))


def _live_test_udp(wait: float = 8.0) -> bool:
    from pythonosc import udp_client

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(wait)
    sock.bind(_OSC_RECV)
    try:
        client = udp_client.SimpleUDPClient(*_OSC_SND)
        client.send_message("/live/test", [])
        sock.recvfrom(65536)
        return True
    except TimeoutError:
        return False
    finally:
        sock.close()


_APPS_FALLBACK = ("Ableton Live 12 Suite", "Ableton Live 12 Standard", "Ableton Live 11 Suite")


def _guess_open_app_candidates() -> list[str]:
    return [p.stem for p in abc.find_installed_live_app_bundles()] + list(_APPS_FALLBACK)


def launch_ableton_macos() -> bool:
    if sys.platform != "darwin":
        print("WARN: --launch-ableton supports macOS only.")
        return False
    exe = shutil.which("open")
    if not exe:
        return False
    for stem in dict.fromkeys(_guess_open_app_candidates()):
        rc = subprocess.run([exe, "-a", stem], capture_output=True, text=True, check=False).returncode
        if rc == 0:
            print(f"Tried launching “{stem}” via open(1); wait until Live finishes loading.")
            return True
        # open -a exits 1 if app bundle name doesn't match exactly
    return False


def preflight(skip_imports: bool, *, repo_only: bool = False) -> int:
    ok = True
    rs = abc.user_library_remote_scripts()
    osc = rs / "AbletonOSC"
    mcp = rs / "AbletonMCP"

    print(f"[preflight] ABLETON_HOME={abc.ableton_home()}")
    print(f"[preflight] Remote Scripts folder: {rs}")
    print(f"[preflight] AbletonOSC path exists:           {osc.is_dir()} ({osc})")
    print(f"[preflight] AbletonMCP path exists:           {mcp.is_dir()} ({mcp})")

    ven = Path(os.environ.get("VIRTUAL_ENV", ""))
    if ven.is_dir():
        print(f"[preflight] VIRTUAL_ENV: {ven}")
    elif (REPO_ROOT / "venv").is_dir():
        print(f"[preflight] venv/: {REPO_ROOT / 'venv'}")

    if not skip_imports:
        try:
            import pythonosc  # noqa: F401

            print(f"[preflight] python-osc import OK ({pythonosc.__file__})")
        except ImportError:
            ok = False
            print("[preflight] FAIL: python-osc not installed (activate venv / pip install -r requirements.txt)")

    if repo_only:
        print(
            "[preflight] --repo-only: skipping Remote Scripts presence / MCP "
            "create_audio_track-on-disk checks (use full --preflight on a machine with Ableton installed)."
        )
    else:
        if not osc.is_dir() or not mcp.is_dir():
            ok = False
            print("[preflight] FAIL: Remote scripts missing — run bootstrap.sh")

        init_py = mcp / "__init__.py"
        if mcp.is_dir():
            if init_py.is_file():
                txt = init_py.read_text(encoding="utf-8", errors="replace")
                has_audio = (
                    "create_audio_track" in txt
                    and "_create_audio_track" in txt
                    and "def _create_audio_track" in txt
                )
                print(
                    f"[preflight] AbletonMCP create_audio_track patch present (on disk): {has_audio}"
                )
                if not has_audio:
                    ok = False
                    print(
                        "[preflight] FAIL: reinstall/patch AbletonMCP — "
                        "scripts/install_remote_scripts.py (needed for audio_effect devices)."
                    )
                has_health = "get_device_health" in txt and "def _get_device_health" in txt
                print(f"[preflight] AbletonMCP get_device_health patch present (optional): {has_health}")
                if not has_health:
                    print(
                        "[preflight] NOTE: optional get_device_health not found — "
                        "re-run scripts/install_remote_scripts.py for docs/MCP_DEVICE_HEALTH_SPIKE.md features."
                    )
            else:
                ok = False
                print(f"[preflight] FAIL: missing {init_py}")

    tooling_dir = REPO_ROOT / "tooling"
    if tooling_dir.is_dir():
        tpath = str(tooling_dir)
        inserted = tpath not in sys.path
        if inserted:
            sys.path.insert(0, tpath)
        try:
            from m4l_pipeline import reference_amxd_path  # noqa: E402

            # Check all three types
            for dt in ("midi_effect", "audio_effect", "instrument"):
                refp = reference_amxd_path(dt)
                exists = refp.is_file()
                print(f"[preflight] Pipeline donor ({dt}) exists: {exists} ({refp})")
                if not exists:
                    ok = False
                    print(
                        f"[preflight] FAIL: missing donor for {dt}. "
                        "Check tooling/donors/ or docs/REFERENCE_HEADER_AND_IMPORT.md"
                    )
        except Exception as exc:
            ok = False
            print(f"[preflight] FAIL: tooling/m4l_pipeline import error — {exc}")
        finally:
            if inserted and sys.path[:1] == [tpath]:
                sys.path.pop(0)

    donor_check = REPO_ROOT / "scripts" / "check_donor_consistency.py"
    if donor_check.is_file():
        import subprocess

        rc = subprocess.run(
            [sys.executable, str(donor_check)],
            cwd=REPO_ROOT,
            check=False,
        ).returncode
        if rc != 0:
            ok = False
            print("[preflight] FAIL: donor appversion consistency (see scripts/check_donor_consistency.py)")

    print("SETUP_PREFLIGHT_" + ("OK" if ok else "FAIL"))
    print(abc.MAX_FOR_LIVE_EDITION_NOTICE.strip())
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--preflight",
        action="store_true",
        help="Filesystem + imports only (no Ableton TCP/OSC). Exit 1 if installs missing.",
    )
    ap.add_argument(
        "--repo-only",
        action="store_true",
        help=(
            "With --preflight: skip User Library Remote Scripts checks — for CI or clones without "
            "Ableton installed; still validates python-osc + pipeline donor .amxd paths."
        ),
    )
    ap.add_argument(
        "--skip-import-check",
        action="store_true",
        help='With --preflight: do not verify "import pythonosc".',
    )
    ap.add_argument(
        "--wait-mcp",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="Before MCP checks: wait up to this many seconds for TCP 9877 (default off).",
    )
    ap.add_argument(
        "--launch-ableton",
        action="store_true",
        help="macOS only: try ``open -a`` on a guessed Live bundle before MCP checks.",
    )
    ap.add_argument(
        "--assert-create-audio-track",
        action="store_true",
        help=(
            "After MCP connects: send create_audio_track once. Fails if Live runs an old AbletonMCP "
            "(requires restart after install_remote_scripts). Creates one empty audio track on success."
        ),
    )
    args = ap.parse_args()

    if args.repo_only and not args.preflight:
        print("ERROR: --repo-only requires --preflight", file=sys.stderr)
        return 2

    if args.preflight:
        return preflight(skip_imports=args.skip_import_check, repo_only=args.repo_only)

    if args.launch_ableton and launch_ableton_macos():
        time.sleep(3.0)

    if args.wait_mcp > 0:
        print(f"[verify] Waiting for MCP on {_ABLETON_HOST}:{_MCP_PORT} (up to {args.wait_mcp}s)…")
        if not _poll_tcp(_MCP_PORT, args.wait_mcp, min(2.0, max(0.25, args.wait_mcp / 10))):
            print(
                "[verify] FAIL: MCP port closed. Quit Live completely, reopen, enable AbletonMCP "
                "(Remote Script loaded + selected in Preferences → Link / Tempo / MIDI)."
            )
            return 2

    try:
        pong = _ableton_cmd("get_session_info", {})
    except OSError:
        print(
            "[verify] FAIL: TCP connect refused (Ableton off or AbletonMCP not selected)."
        )
        return 2
    except Exception as e:
        print(f"[verify] FAIL: MCP handshake error — {e}")
        return 2

    status = pong.get("status")
    print(f"[verify] AbletonMCP get_session_info: status={status!r}")
    if status != "success":
        print(f"[verify] Full payload: {pong}")
        return 2

    if args.assert_create_audio_track:
        print("[verify] Probing create_audio_track (creates one audio track if OK)…")
        probe = _ableton_cmd("create_audio_track", {"index": -1})
        if probe.get("status") != "success":
            print(
                "[verify] FAIL: create_audio_track unavailable — Live is likely running an old "
                "AbletonMCP. Quit Live completely, reopen, then retry.\n"
                f"  Raw reply: {probe}",
                file=sys.stderr,
            )
            return 5
        inner = probe.get("result")
        if isinstance(inner, str):
            inner = json.loads(inner)
        idx = (inner or {}).get("index")
        print(
            f"[verify] create_audio_track OK (new audio track index={idx!r}). "
            "Delete the empty track in Live if you do not want it."
        )
        print("M4L_AUDIO_MCP_OK")

    try:
        if not _live_test_udp():
            print("[verify] FAIL: AbletonOSC /live/test timed out — select AbletonOSC Control Surface.")
            return 3
    except ImportError:
        print("[verify] FAIL: python-osc import failed — install pip requirements inside venv.")
        return 4

    print("[verify] MCP + AbletonOSC /live/test OK")
    print("M4L_SETUP_VERIFY_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
