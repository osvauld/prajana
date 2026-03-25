"""run.py — Pytest subprocess wrapper for targeted test execution."""

import os
import re
import subprocess

from upakarana.paths import ROOT, TESTS_DIR, VENV_PYTEST

_UPAKARANA_DIR = ROOT / "upakarana"


def _pytest_bin():
    if os.path.isfile(str(VENV_PYTEST)):
        return str(VENV_PYTEST)
    return "pytest"


def _build_args(layer=None, gate=None, name=None, pattern=None,
                path=None, last_failed=False, socket_path=None,
                verbose=False, timeout=120, parallel=None):
    args = [_pytest_bin(), str(TESTS_DIR)]
    if parallel:
        args.extend(["-n", str(parallel)])
    if socket_path:
        args.extend(["--socket", socket_path])
    if verbose:
        args.append("-v")
    if last_failed:
        args.append("--lf")
    if layer:
        args.extend(["-k", layer])
    if gate:
        args.extend(["-k", gate])
    if name:
        args.extend(["-k", name])
    if pattern:
        args.extend(["-k", pattern])
    if path:
        args[-1] = path  # replace TESTS_DIR with specific path
    return args


def _parse_output(stdout, stderr, returncode):
    result = {
        "returncode": returncode,
        "passed": 0, "failed": 0, "errors": 0,
        "xfailed": 0, "xpassed": 0, "duration": "",
    }
    for line in (stdout + stderr).split("\n"):
        line = line.strip()
        m = re.search(r"(\d+) passed", line)
        if m:
            result["passed"] = int(m.group(1))
        m = re.search(r"(\d+) failed", line)
        if m:
            result["failed"] = int(m.group(1))
        m = re.search(r"(\d+) error", line)
        if m:
            result["errors"] = int(m.group(1))
        m = re.search(r"(\d+) xfailed", line)
        if m:
            result["xfailed"] = int(m.group(1))
        m = re.search(r"(\d+) xpassed", line)
        if m:
            result["xpassed"] = int(m.group(1))
        m = re.search(r"in ([\d.]+)s", line)
        if m:
            result["duration"] = m.group(1) + "s"
    return result


def run(**kwargs):
    """Run pytest with filters. Returns result dict."""
    timeout = kwargs.pop("timeout", 120)
    args = _build_args(**kwargs)
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                              cwd=str(_UPAKARANA_DIR))
        result = _parse_output(proc.stdout, proc.stderr, proc.returncode)
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        return result
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "error": "timeout", "passed": 0, "failed": 0}
