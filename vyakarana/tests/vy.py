"""vy.py — thin client for the vyakarana Unix socket.

Provides the `Client` class used by all pytest tests via the `vy` fixture
in conftest.py.

Protocol: newline-delimited JSON over a Unix domain socket.
- `eval-json` command: server evaluates a tantra expression and returns
  the result as a native JSON value (not a string repr).

Usage in tests:
    def test_something(vy):
        result = vy.eval('lookup-word "mass"')   # returns parsed JSON
        assert result == "mass"

        g = vy.eval('build-question-graph "find force"')  # returns list of triples
        triples = {t[1]: t for t in g}
        assert "satya" in triples
"""

import json
import os
import socket
import time
from typing import Any

DEFAULT_SOCKET = os.environ.get("VYAKARANA_SOCKET", "/tmp/vyakarana.sock")


class VyakaranaError(Exception):
    """Raised when the server returns status=error."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class Client:
    """A persistent connection to a running vyakarana server.

    One instance is created per pytest session (via the session-scoped
    fixture in conftest.py) and reused across all tests.
    """

    def __init__(self, socket_path: str = DEFAULT_SOCKET):
        self._path = socket_path
        self._sock: socket.socket | None = None
        self._buf = b""
        self._connect()

    def _connect(self) -> None:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self._path)
        self._sock = s
        self._buf = b""

    def _reconnect(self) -> None:
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass
        self._connect()

    def _send(self, payload: dict) -> dict:
        assert self._sock is not None
        data = json.dumps(payload) + "\n"
        self._sock.sendall(data.encode())
        # read until we have a complete newline-delimited JSON line
        while b"\n" not in self._buf:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise EOFError("vyakarana server closed the connection")
            self._buf += chunk
        line, self._buf = self._buf.split(b"\n", 1)
        return json.loads(line.decode())

    def _send_with_retry(self, payload: dict) -> dict:
        try:
            return self._send(payload)
        except (EOFError, BrokenPipeError, ConnectionResetError, OSError):
            self._reconnect()
            return self._send(payload)

    # ── public API ───────────────────────────────────────────────────────────

    def eval(self, expr: str) -> Any:
        """Evaluate a tantra expression and return the result as a Python value.

        The server uses eval-json, so lists come back as Python lists,
        strings as str, numbers as int/float, bools as bool, null as None.

        Raises VyakaranaError if the server returns status=error.
        Raises AssertionError if the response is malformed.
        """
        resp = self._send_with_retry({"command": "eval-json", "expr": expr})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"),
                err.get("message", repr(resp)),
            )
        assert resp.get("status") == "ok", f"unexpected status in: {resp}"
        return resp["result"]

    def elapsed_ms(self, expr: str) -> tuple[Any, int]:
        """Like eval() but also returns the server-side elapsed_ms."""
        resp = self._send_with_retry({"command": "eval-json", "expr": expr})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"), err.get("message", repr(resp))
            )
        return resp["result"], resp.get("elapsed_ms", 0)

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    # ── graph helpers ────────────────────────────────────────────────────────

    @staticmethod
    def triples_by_pred(graph: list) -> dict[str, list]:
        """Index a graph (list of [s,p,o] triples) by predicate.

        Returns {predicate: [s, p, o]} — last triple wins on collision.
        """
        return {t[1]: t for t in graph if isinstance(t, list) and len(t) >= 2}

    @staticmethod
    def find_triple(
        graph: list,
        *,
        subj: str | None = None,
        pred: str | None = None,
        obj: str | None = None,
    ) -> list | None:
        """Return the first triple matching all supplied constraints, or None."""
        for t in graph:
            if not (isinstance(t, list) and len(t) >= 3):
                continue
            if subj is not None and t[0] != subj:
                continue
            if pred is not None and t[1] != pred:
                continue
            if obj is not None and t[2] != obj:
                continue
            return t
        return None

    @staticmethod
    def has_triple(
        graph: list,
        *,
        subj: str | None = None,
        pred: str | None = None,
        obj: str | None = None,
    ) -> bool:
        """True if any triple matches all supplied constraints."""
        return Client.find_triple(graph, subj=subj, pred=pred, obj=obj) is not None
