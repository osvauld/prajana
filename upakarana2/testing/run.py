"""run.py — Pytest subprocess wrapper for targeted test execution."""

import contextlib
import os
import subprocess
import re
import time

from upakarana2.paths import ROOT, TESTS_DIR, VENV_PYTEST

_UPAKARANA_DIR = ROOT / "upakarana2"  # cwd for pytest; pyproject.toml here sets pythonpath


def _pytest_bin():
    if os.path.isfile(str(VENV_PYTEST)):
        return str(VENV_PYTEST)
    return "pytest"


def _build_args(nodeids=None, layer=None, gate=None, name=None, pattern=None,
                path=None, last_failed=False, socket_path=None,
                verbose=False, timeout=120, parallel=None):
    if nodeids:
        # Pass specific nodeids directly — exact matching, no -k substring risks
        args = [_pytest_bin()] + list(nodeids)
    else:
        args = [_pytest_bin(), str(TESTS_DIR)]
    if parallel:
        args.extend(["-n", str(parallel), "--dist=loadfile"])
    if socket_path:
        args.extend(["--socket", socket_path])
    if verbose:
        args.append("-v")
    if not nodeids:
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


@contextlib.contextmanager
def _parallel_servers(n):
    """Spawn N vyakarana instances on /tmp/vy-{i}.sock, yield, then kill them.

    Uses Popen directly (not server.start) to avoid clobbering /tmp/vy.pid,
    which would break the main server's stop/status commands.
    """
    from upakarana2.engine.server import find_binary, health
    from upakarana2.paths import BRAHMAN

    binary = find_binary()
    if not binary:
        raise RuntimeError("vyakarana binary not found — run 'dune build' in vyakarana/")

    sockets = [f"/tmp/vy-{i}.sock" for i in range(n)]
    procs = []

    # Clean up any stale sockets from previous crashed runs
    for sock in sockets:
        if os.path.exists(sock):
            os.unlink(sock)

    # Spawn all instances simultaneously
    for sock in sockets:
        proc = subprocess.Popen(
            [binary, "--socket", sock, "--quiet-startup", str(BRAHMAN)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        procs.append(proc)

    # Wait for all instances to be ready (health-check each socket)
    deadline = time.monotonic() + 30.0
    ready = [False] * n
    while time.monotonic() < deadline:
        for i, sock in enumerate(sockets):
            if not ready[i] and health(sock, timeout=1.0):
                ready[i] = True
        if all(ready):
            break
        time.sleep(0.3)

    not_ready = [sockets[i] for i, r in enumerate(ready) if not r]
    if not_ready:
        for proc in procs:
            try:
                proc.terminate()
            except Exception:
                pass
        raise RuntimeError(f"Parallel servers did not start within 30s: {not_ready}")

    print(f"[parallel] {n} vyakarana instances ready on {sockets}", flush=True)
    try:
        yield sockets
    finally:
        for proc in procs:
            try:
                proc.terminate()
            except Exception:
                pass
        for sock in sockets:
            try:
                if os.path.exists(sock):
                    os.unlink(sock)
            except Exception:
                pass
        print(f"[parallel] {n} instances stopped", flush=True)


def run(nodeids=None, **kwargs):
    """Run pytest with filters. Returns result dict."""
    timeout = kwargs.pop("timeout", 120)
    parallel = kwargs.get("parallel")

    # Resolve worker count for server spawning
    n_workers = None
    if parallel and parallel != "off":
        n_workers = os.cpu_count() or 4 if parallel == "auto" else int(parallel)

    args = _build_args(nodeids=nodeids, **kwargs)

    def _execute():
        try:
            proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                                  cwd=str(_UPAKARANA_DIR))
            result = _parse_output(proc.stdout, proc.stderr, proc.returncode)
            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            return result
        except subprocess.TimeoutExpired:
            return {"returncode": -1, "error": "timeout", "passed": 0, "failed": 0}

    if n_workers:
        with _parallel_servers(n_workers):
            return _execute()
    else:
        return _execute()
