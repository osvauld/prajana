"""server.py — Vyakarana OCaml server lifecycle management.

Start, stop, health-check, ensure running.
"""

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from upakarana.paths import ROOT, BRAHMAN, BRAHMAN2

DEFAULT_SOCKET = os.environ.get("VYAKARANA_SOCKET", "/tmp/vy.sock")
DEFAULT_BINARY = str(ROOT / "vyakarana" / "_build" / "default" / "bin" / "vyakarana.exe")
PID_FILE = Path("/tmp/vy.pid")


def find_binary():
    """Find the vyakarana binary. Returns path or None."""
    if os.path.isfile(DEFAULT_BINARY) and os.access(DEFAULT_BINARY, os.X_OK):
        return DEFAULT_BINARY
    alt = str(ROOT / "vyakarana" / "_build" / "install" / "default" / "bin" / "vyakarana")
    if os.path.isfile(alt) and os.access(alt, os.X_OK):
        return alt
    return None


def health(socket_path=DEFAULT_SOCKET, timeout=2.0):
    """True if the server responds to a ping."""
    if not os.path.exists(socket_path):
        return False
    try:
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


def start(socket_path=DEFAULT_SOCKET, brahman_dir=None, binary=None,
          quiet=True, background=False):
    """Start a vyakarana server. Returns Popen or None if already running."""
    if health(socket_path):
        return None

    binary = binary or find_binary()
    if not binary:
        print("[vyakarana] binary not found. Run 'dune build' in vyakarana/",
              file=sys.stderr)
        return None

    if os.path.exists(socket_path):
        os.unlink(socket_path)

    cmd = [binary, "--socket", socket_path]
    if quiet:
        cmd.append("--quiet-startup")
    cmd.append(str(brahman_dir or BRAHMAN2))

    stderr_target = subprocess.DEVNULL if quiet else None
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=stderr_target)

    try:
        PID_FILE.write_text(str(proc.pid))
    except Exception:
        pass

    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        if health(socket_path, timeout=1.0):
            print(f"[vyakarana] ready on {socket_path} (pid {proc.pid})",
                  file=sys.stderr)
            if background:
                return proc
            try:
                proc.wait()
            except KeyboardInterrupt:
                stop(socket_path)
            return proc
        if proc.poll() is not None:
            print(f"[vyakarana] exited with code {proc.returncode}",
                  file=sys.stderr)
            return None
        time.sleep(0.3)

    print("[vyakarana] did not become ready within 15s", file=sys.stderr)
    proc.kill()
    return None


def stop(socket_path=DEFAULT_SOCKET):
    """Stop the server. Returns True if stopped."""
    pid = _read_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(20):
                try:
                    os.kill(pid, 0)
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
    _cleanup(socket_path)
    return False


def ensure(socket_path=DEFAULT_SOCKET, **kwargs):
    """Ensure server is running. Returns socket path."""
    if health(socket_path):
        return socket_path
    proc = start(socket_path=socket_path, background=True, **kwargs)
    if proc is None and not health(socket_path):
        raise RuntimeError(f"Could not start vyakarana on {socket_path}")
    return socket_path


def status(socket_path=DEFAULT_SOCKET):
    """Server status dict."""
    alive = health(socket_path)
    result = {
        "running": alive,
        "socket": socket_path,
        "pid": _read_pid(),
        "binary": find_binary(),
    }
    if alive:
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


def reload(socket_path=DEFAULT_SOCKET):
    """Tell server to reload tantras. Returns response or None."""
    if not health(socket_path):
        return None
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
    except Exception:
        pass
    return None


def _read_pid():
    try:
        return int(PID_FILE.read_text().strip())
    except Exception:
        return None


def _cleanup(socket_path):
    try:
        if os.path.exists(socket_path):
            os.unlink(socket_path)
    except Exception:
        pass
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass
