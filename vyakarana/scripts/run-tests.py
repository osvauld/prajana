#!/usr/bin/env python3
"""run-tests.py — fast tantra test runner over a live vyakarana socket.

Connects to an already-running vyakarana server (Unix domain socket),
sends {"command":"eval","expr":"<test-name>"} for each test-*.tantra file,
collects results and reports pass/fail with timing.

Usage:
  python3 scripts/run-tests.py [--socket PATH] [suite ...]

  --socket PATH   path to the vyakarana Unix domain socket
                  (default: /tmp/vyakarana.sock, or $VYAKARANA_SOCKET)

  suite ...       optional suite name(s) to filter (e.g. avrti bqg match)
                  omit to run all suites

Examples:
  python3 scripts/run-tests.py
  python3 scripts/run-tests.py avrti
  python3 scripts/run-tests.py avrti match --socket /tmp/vy.sock

Exit code: 0 if all pass, 1 if any fail or on connection error.
"""

import json
import os
import socket
import sys
import time
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
TESTS_DIR = PROJECT_DIR.parent / "brahman" / "yantra" / "tests"

DEFAULT_SOCKET = os.environ.get("VYAKARANA_SOCKET", "/tmp/vyakarana.sock")

# ── socket helpers ────────────────────────────────────────────────────────────


def connect(socket_path: str) -> socket.socket:
    """Open a Unix domain socket connection to vyakarana."""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(socket_path)
    except FileNotFoundError:
        print(f"error: socket not found: {socket_path}", file=sys.stderr)
        print(
            "  is vyakarana running? start with: ./vyakarana --socket <path>",
            file=sys.stderr,
        )
        sys.exit(1)
    except ConnectionRefusedError:
        print(f"error: connection refused: {socket_path}", file=sys.stderr)
        sys.exit(1)
    return sock


def send_eval(sock: socket.socket, expr: str) -> dict:
    """Send one eval command and read the newline-delimited JSON response."""
    req = json.dumps({"command": "eval", "expr": expr}) + "\n"
    sock.sendall(req.encode())
    # read until newline
    buf = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise EOFError("server closed connection")
        buf += chunk
        if b"\n" in buf:
            line, _ = buf.split(b"\n", 1)
            return json.loads(line.decode())


# ── test discovery ────────────────────────────────────────────────────────────


def find_tests(suites: list[str]) -> list[Path]:
    """Return sorted list of test-*.tantra paths for the requested suites."""
    if not TESTS_DIR.exists():
        print(f"error: tests directory not found: {TESTS_DIR}", file=sys.stderr)
        sys.exit(1)
    if suites:
        paths = []
        for suite in suites:
            suite_dir = TESTS_DIR / suite
            if not suite_dir.exists():
                print(f"warning: suite not found: {suite_dir}", file=sys.stderr)
                continue
            paths.extend(sorted(suite_dir.glob("test-*.tantra")))
    else:
        paths = sorted(TESTS_DIR.rglob("test-*.tantra"))
    return paths


# ── runner ────────────────────────────────────────────────────────────────────

PASS_MARK = "\033[32mPASS\033[0m"
FAIL_MARK = "\033[31mFAIL\033[0m"


def run_tests(socket_path: str, suites: list[str]) -> int:
    """Run all tests. Returns exit code (0 = all pass, 1 = any fail)."""
    tests = find_tests(suites)
    if not tests:
        print("no tests found.")
        return 0

    sock = connect(socket_path)

    # group by suite (parent dir name) for display
    suite_results: dict[str, list[tuple[str, bool, str, int]]] = {}
    # (name, passed, result, elapsed_ms)

    total_pass = 0
    total_fail = 0
    failures: list[str] = []

    current_suite = None

    for path in tests:
        suite = path.parent.name
        name = path.stem  # e.g. test-avrti-fixpoint

        if suite != current_suite:
            current_suite = suite
            print(f"\n  [{suite}]")

        t0 = time.monotonic()
        try:
            resp = send_eval(sock, name)
        except Exception as exc:
            # reconnect on dropped connection
            try:
                sock.close()
            except Exception:
                pass
            print(f"  connection lost: {exc}  (reconnecting…)", file=sys.stderr)
            sock = connect(socket_path)
            try:
                resp = send_eval(sock, name)
            except Exception as exc2:
                resp = {
                    "status": "error",
                    "result": str(exc2),
                    "passed": False,
                    "elapsed_ms": 0,
                }
        elapsed = int((time.monotonic() - t0) * 1000)

        passed = resp.get("passed", False)
        result_val = resp.get("result", "")
        status = resp.get("status", "")
        elapsed_ms = resp.get("elapsed_ms", elapsed)

        if status == "error":
            passed = False
            result_val = (
                resp.get("error", {}).get("message", result_val)
                if isinstance(resp.get("error"), dict)
                else result_val
            )

        mark = PASS_MARK if passed else FAIL_MARK
        timing = f"{elapsed_ms}ms"

        if passed:
            print(f"  [{mark}] {name}  ({timing})")
            total_pass += 1
        else:
            print(f"  [{mark}] {name}  got: {result_val!r}  ({timing})")
            total_fail += 1
            failures.append(name)

        suite_results.setdefault(suite, []).append(
            (name, passed, result_val, elapsed_ms)
        )

    sock.close()

    # summary
    print(f"\nResults: {total_pass} passed, {total_fail} failed.")
    if failures:
        print("Failed:")
        for f in failures:
            print(f"  - {f}")
        return 1
    else:
        print("All tests passed.")
        return 0


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    args = sys.argv[1:]
    suites = []
    socket_path = DEFAULT_SOCKET

    i = 0
    while i < len(args):
        if args[i] == "--socket" and i + 1 < len(args):
            socket_path = args[i + 1]
            i += 2
        elif args[i].startswith("--socket="):
            socket_path = args[i].split("=", 1)[1]
            i += 1
        elif args[i].startswith("--"):
            print(f"unknown option: {args[i]}", file=sys.stderr)
            sys.exit(1)
        else:
            suites.append(args[i])
            i += 1

    sys.exit(run_tests(socket_path, suites))


if __name__ == "__main__":
    main()
