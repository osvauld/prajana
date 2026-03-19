"""vyakarana.py — manage vyakarana OCaml server lifecycle.

Start, stop, reload, health-check, and pool multiple instances.
The tools package uses this to auto-start the server when needed.

Usage from CLI:
    python3 -m tools serve-vy              # start and block
    python3 -m tools serve-vy --background # start in background

Usage from Python:
    from tools.vyakarana import ensure, stop, health
    ensure()           # start if not running, return socket path
    stop()             # kill the server
    health()           # True if server responds to ping
"""

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from .paths import ROOT, BRAHMAN

# ── defaults ──────────────────────────────────────────────────────────────────

DEFAULT_SOCKET = os.environ.get("VYAKARANA_SOCKET", "/tmp/vy.sock")
DEFAULT_BINARY = os.path.join(
    ROOT, "vyakarana", "_build", "default", "bin", "vyakarana.exe"
)
PID_FILE = Path("/tmp/vy.pid")


# ── discovery ─────────────────────────────────────────────────────────────────


def find_binary() -> str | None:
    """Find the vyakarana binary. Returns path or None."""
    # prefer built binary
    if os.path.isfile(DEFAULT_BINARY) and os.access(DEFAULT_BINARY, os.X_OK):
        return DEFAULT_BINARY
    # try dune exec path
    alt = os.path.join(
        ROOT, "vyakarana", "_build", "install", "default", "bin", "vyakarana"
    )
    if os.path.isfile(alt) and os.access(alt, os.X_OK):
        return alt
    return None


# ── health check ──────────────────────────────────────────────────────────────


def health(socket_path: str = DEFAULT_SOCKET, timeout: float = 2.0) -> bool:
    """True if the vyakarana server responds to a ping on the socket."""
    if not os.path.exists(socket_path):
        return False
    try:
        import json

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(socket_path)
        sock.sendall(b'{"command":"list-tantras"}\n')
        data = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
            try:
                resp = json.loads(data.decode())
                sock.close()
                return resp.get("status") == "ok"
            except Exception:
                continue
        sock.close()
        return False
    except (ConnectionRefusedError, FileNotFoundError, OSError, TimeoutError):
        return False


# ── start ─────────────────────────────────────────────────────────────────────


def start(
    socket_path: str = DEFAULT_SOCKET,
    brahman_dir: str = BRAHMAN,
    binary: str | None = None,
    quiet: bool = True,
    background: bool = False,
) -> subprocess.Popen | None:
    """Start a vyakarana server instance.

    Returns the Popen object (background=False blocks until server is ready).
    Returns None if the server is already running.
    """
    if health(socket_path):
        return None  # already running

    binary = binary or find_binary()
    if not binary:
        print(
            f"[vyakarana] binary not found. Run 'dune build' in vyakarana/",
            file=sys.stderr,
        )
        return None

    # clean stale socket
    if os.path.exists(socket_path):
        os.unlink(socket_path)

    cmd = [binary, "--socket", socket_path]
    if quiet:
        cmd.append("--quiet-startup")
    cmd.append(brahman_dir)

    stderr_target = subprocess.DEVNULL if quiet else None
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=stderr_target)

    # write pid file
    try:
        PID_FILE.write_text(str(proc.pid))
    except Exception:
        pass

    # wait for socket to appear
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        if health(socket_path, timeout=1.0):
            print(
                f"[vyakarana] server ready on {socket_path} (pid {proc.pid})",
                file=sys.stderr,
            )
            if background:
                return proc
            # foreground: block until killed
            try:
                proc.wait()
            except KeyboardInterrupt:
                stop(socket_path)
            return proc
        # check if process died
        if proc.poll() is not None:
            print(
                f"[vyakarana] server exited with code {proc.returncode}",
                file=sys.stderr,
            )
            return None
        time.sleep(0.3)

    print(f"[vyakarana] server did not become ready within 15s", file=sys.stderr)
    proc.kill()
    return None


# ── stop ──────────────────────────────────────────────────────────────────────


def stop(socket_path: str = DEFAULT_SOCKET) -> bool:
    """Stop the vyakarana server. Returns True if stopped."""
    # try pid file first
    pid = _read_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            # wait for it to die
            for _ in range(20):
                try:
                    os.kill(pid, 0)  # check if alive
                    time.sleep(0.1)
                except ProcessLookupError:
                    break
            _cleanup(socket_path)
            print(f"[vyakarana] stopped (pid {pid})", file=sys.stderr)
            return True
        except ProcessLookupError:
            _cleanup(socket_path)
            return True
        except PermissionError:
            pass

    # fallback: find by socket
    _cleanup(socket_path)
    return False


def _read_pid() -> int | None:
    try:
        return int(PID_FILE.read_text().strip())
    except Exception:
        return None


def _cleanup(socket_path: str):
    try:
        if os.path.exists(socket_path):
            os.unlink(socket_path)
    except Exception:
        pass
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


# ── reload ────────────────────────────────────────────────────────────────────


def reload(socket_path: str = DEFAULT_SOCKET) -> dict | None:
    """Tell the running server to reload all tantras from disk.

    Returns the server response dict, or None if not running.
    """
    if not health(socket_path):
        return None
    import json

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        sock.connect(socket_path)
        sock.sendall(b'{"command":"reload-all"}\n')
        data = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
            try:
                resp = json.loads(data.decode())
                sock.close()
                return resp
            except Exception:
                continue
        sock.close()
        return None
    except Exception:
        return None


# ── ensure ────────────────────────────────────────────────────────────────────


def ensure(socket_path: str = DEFAULT_SOCKET, **kwargs) -> str:
    """Ensure a vyakarana server is running. Start one if needed.

    Returns the socket path. Raises RuntimeError if unable to start.
    """
    if health(socket_path):
        return socket_path

    proc = start(socket_path=socket_path, background=True, **kwargs)
    if proc is None and not health(socket_path):
        raise RuntimeError(f"Could not start vyakarana server on {socket_path}")
    return socket_path


# ── status ────────────────────────────────────────────────────────────────────


def status(socket_path: str = DEFAULT_SOCKET) -> dict:
    """Return server status info."""
    alive = health(socket_path)
    pid = _read_pid()
    result = {
        "running": alive,
        "socket": socket_path,
        "pid": pid,
        "binary": find_binary(),
    }
    if alive:
        # get tantra count
        import json

        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect(socket_path)
            sock.sendall(b'{"command":"list-tantras"}\n')
            data = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk
                try:
                    resp = json.loads(data.decode())
                    result["tantras"] = len(resp.get("tantras", []))
                    break
                except Exception:
                    continue
            sock.close()
        except Exception:
            pass
    return result
