"""runner.py — pytest subprocess wrapper for targeted test execution."""

import os
import re
import subprocess
import time

from .paths import HERE, V2_DIR, VENV_PYTEST
from . import tests as test_meta


def _pytest_bin() -> str:
    return VENV_PYTEST if os.path.exists(VENV_PYTEST) else "pytest"


def _parse_pytest_output(stdout: str, stderr: str, returncode: int) -> dict:
    lines = stdout.split("\n")
    passed = failed = errors = xfailed = xpassed = 0
    failed_tests = []
    error_tests = []

    for line in lines:
        m = re.match(r"^FAILED (.+?) - (.+)$", line.strip())
        if m:
            failed_tests.append({"nodeid": m.group(1), "reason": m.group(2)})
    for line in lines:
        m = re.match(r"^ERROR (.+?) - (.+)$", line.strip())
        if m:
            error_tests.append({"nodeid": m.group(1), "reason": m.group(2)})

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


def _build_pytest_args(
    layer=None,
    gate=None,
    name=None,
    pattern=None,
    socket_path="/tmp/vy.sock",
    verbose=False,
    no_cache=True,
):
    target = "v2/"
    args = [_pytest_bin(), target, f"--socket={socket_path}"]
    if no_cache:
        args.append("--no-cache")
    args.append("-v" if verbose else "-q")

    k_parts = []
    if name:
        k_parts.append(name if name.startswith("test_") else f"test_{name}")
    if pattern and not name:
        k_parts.append(pattern)
    if layer:
        layer_file = f"v2/test_{layer}.py"
        if os.path.exists(os.path.join(HERE, layer_file)):
            args[1] = layer_file
        else:
            k_parts.append(layer)
    if gate:
        all_tests = test_meta.load_all()
        gate_tests = test_meta.filter_tests(all_tests, gate=gate)
        if gate_tests:
            k_parts.append(f"({' or '.join(t['name'] for t in gate_tests)})")
    if k_parts:
        args.extend(["-k", " and ".join(k_parts)])
    return args


def run(
    layer=None,
    gate=None,
    name=None,
    pattern=None,
    socket_path="/tmp/vy.sock",
    verbose=False,
    timeout=120,
):
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
            cwd=HERE,
        )
        elapsed = time.monotonic() - t0
        result = _parse_pytest_output(proc.stdout, proc.stderr, proc.returncode)
        result["elapsed"] = round(elapsed, 2)
        result["args"] = args[1:]
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


def run_single(name, socket_path="/tmp/vy.sock"):
    return run(name=name, socket_path=socket_path, verbose=True)


def run_layer(layer, socket_path="/tmp/vy.sock"):
    return run(layer=layer, socket_path=socket_path)


def run_gate(gate, socket_path="/tmp/vy.sock"):
    return run(gate=gate, socket_path=socket_path)


def run_all(socket_path="/tmp/vy.sock"):
    return run(socket_path=socket_path)
