"""
runner.py — pytest subprocess wrapper for targeted test execution.

Runs v2 tests via pytest subprocess, capturing output and parsing results.
All filtering (layer, gate, name, pattern) is translated to pytest -k / nodeids.

The runner finds the project venv's pytest automatically, or falls back to
whatever pytest is on PATH.
"""

import json
import os
import re
import subprocess
import sys
import time

from .paths import ROOT
from . import tests as test_meta

# ── paths ──────────────────────────────────────────────────────────────────────

BRAHMAN_DIR = os.path.join(ROOT, "tools", "brahman")
V2_DIR = os.path.join(BRAHMAN_DIR, "v2")
TESTS_DIR = BRAHMAN_DIR  # conftest.py lives here; run pytest from here
VENV_PYTEST = os.path.join(ROOT, ".venv", "bin", "pytest")


def _pytest_bin() -> str:
    if os.path.exists(VENV_PYTEST):
        return VENV_PYTEST
    return "pytest"


# ── result parsing ─────────────────────────────────────────────────────────────


def _parse_pytest_output(stdout: str, stderr: str, returncode: int) -> dict:
    """Parse pytest -q output into structured result dict."""
    lines = stdout.split("\n")

    passed = failed = errors = xfailed = xpassed = 0
    failed_tests: list[dict] = []
    error_tests: list[dict] = []

    # collect FAILED lines
    for line in lines:
        m = re.match(r"^FAILED (.+?) - (.+)$", line.strip())
        if m:
            failed_tests.append({"nodeid": m.group(1), "reason": m.group(2)})

    # collect ERROR lines
    for line in lines:
        m = re.match(r"^ERROR (.+?) - (.+)$", line.strip())
        if m:
            error_tests.append({"nodeid": m.group(1), "reason": m.group(2)})

    # summary line: "67 passed, 31 xfailed, 1 warning in 13.56s"
    summary_line = ""
    for line in reversed(lines):
        if "passed" in line or "failed" in line or "error" in line:
            summary_line = line.strip()
            break

    for m in re.finditer(
        r"(\d+)\s+(passed|failed|error|xfailed|xpassed|warning)", summary_line
    ):
        n, kind = int(m.group(1)), m.group(2)
        if kind == "passed":
            passed = n
        elif kind == "failed":
            failed = n
        elif kind == "error":
            errors = n
        elif kind == "xfailed":
            xfailed = n
        elif kind == "xpassed":
            xpassed = n

    # extract duration
    duration = 0.0
    dm = re.search(r"in\s+([\d.]+)s", summary_line)
    if dm:
        duration = float(dm.group(1))

    ok = returncode == 0 or (returncode == 1 and failed == 0 and errors == 0)

    return {
        "status": "ok" if ok else "failed",
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "xfailed": xfailed,
        "xpassed": xpassed,
        "duration": duration,
        "summary": summary_line,
        "failed_tests": failed_tests,
        "error_tests": error_tests,
        "stdout": stdout,
        "returncode": returncode,
    }


# ── run helpers ────────────────────────────────────────────────────────────────


def _build_pytest_args(
    layer: str | None = None,
    gate: str | None = None,
    name: str | None = None,
    pattern: str | None = None,
    socket_path: str = "/tmp/vy.sock",
    verbose: bool = False,
    no_cache: bool = True,
) -> list[str]:
    """Build pytest argv from filter parameters.

    Always uses paths relative to TESTS_DIR so conftest.py is found correctly.
    The subprocess cwd is set to TESTS_DIR in run().
    """
    # v2/ relative to TESTS_DIR
    target = "v2/"
    args = [
        _pytest_bin(),
        target,
        f"--socket={socket_path}",
    ]

    if no_cache:
        args.append("--no-cache")

    if verbose:
        args.append("-v")
    else:
        args.append("-q")

    # build -k expression from filters
    k_parts = []

    if name:
        # exact name or nodeid
        if name.startswith("test_"):
            k_parts.append(name)
        else:
            k_parts.append(f"test_{name}")

    if pattern and not name:
        k_parts.append(pattern)

    if layer:
        # map layer to file relative to TESTS_DIR: v2/test_evaluator.py
        layer_file = f"v2/test_{layer}.py"
        abs_layer_file = os.path.join(TESTS_DIR, layer_file)
        if os.path.exists(abs_layer_file):
            args[1] = layer_file
        else:
            k_parts.append(layer)

    if gate:
        # gate is in xfail_gate — we need to find test names matching this gate
        # from static metadata and pass them as -k
        all_tests = test_meta.load_all()
        gate_tests = test_meta.filter_tests(all_tests, gate=gate)
        if gate_tests:
            gate_names = " or ".join(t["name"] for t in gate_tests)
            k_parts.append(f"({gate_names})")

    if k_parts:
        args.extend(["-k", " and ".join(k_parts)])

    return args


def run(
    layer: str | None = None,
    gate: str | None = None,
    name: str | None = None,
    pattern: str | None = None,
    socket_path: str = "/tmp/vy.sock",
    verbose: bool = False,
    timeout: int = 120,
) -> dict:
    """Run tests and return structured result dict.

    Parameters
    ----------
    layer:      filter by layer (evaluator, graph, pipeline, answers, xfail)
    gate:       filter xfails by gate name (arithmetic, dvandva, ...)
    name:       run a single test by name
    pattern:    pytest -k expression / substring
    socket_path: path to vyakarana socket
    verbose:    -v output
    timeout:    seconds before giving up
    """
    args = _build_pytest_args(
        layer=layer,
        gate=gate,
        name=name,
        pattern=pattern,
        socket_path=socket_path,
        verbose=verbose,
    )

    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=TESTS_DIR,  # run from tests/ so conftest.py is found
        )
        elapsed = time.monotonic() - t0
        result = _parse_pytest_output(proc.stdout, proc.stderr, proc.returncode)
        result["elapsed"] = round(elapsed, 2)
        result["args"] = args[1:]  # omit pytest bin
        return result
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "error": f"tests timed out after {timeout}s",
            "args": args[1:],
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "error": f"pytest not found at {args[0]}",
            "args": args[1:],
        }


def run_single(name: str, socket_path: str = "/tmp/vy.sock") -> dict:
    """Run a single test by name. Convenience wrapper."""
    return run(name=name, socket_path=socket_path, verbose=True)


def run_layer(layer: str, socket_path: str = "/tmp/vy.sock") -> dict:
    """Run all tests in one layer."""
    return run(layer=layer, socket_path=socket_path)


def run_gate(gate: str, socket_path: str = "/tmp/vy.sock") -> dict:
    """Run all xfail tests for one gate."""
    return run(gate=gate, socket_path=socket_path)


def run_all(socket_path: str = "/tmp/vy.sock") -> dict:
    """Run all v2 tests."""
    return run(socket_path=socket_path)
