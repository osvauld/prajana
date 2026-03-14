"""vy.py — thin client for the vyakarana Unix socket.

Provides the `Client` class used by all pytest tests via the `vy` fixture
in conftest.py.

Protocol: newline-delimited JSON over a Unix domain socket.
- `eval-json` command: server evaluates a tantra expression and returns
  the result as a native JSON value (not a string repr).
- `question` command: send a natural-language question with a session_id,
  returns answer_text (used by test_session.py via vy.ask()).

Usage in tests:
    def test_something(vy):
        result = vy.eval('lookup-word "mass"')   # returns parsed JSON
        assert result == "mass"

        g = vy.eval('build-question-graph "find force"')  # returns list of triples
        assert vy.has_triple(g, subj="force", pred="satya")

        # walk the kosha graph
        units = vy.walk("mass", "matra")          # ["kilogram"]
        owners = vy.walk_in("kilogram", "matra")  # ["mass"]

        # numeric comparison with float tolerance
        assert vy.approx_eq(result, 5.0)

        # session questions
        answer = vy.ask("what is force", session_id="s1")
"""

import json
import os
import socket
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

    def ask(self, question: str, session_id: str = "test") -> str:
        """Send a natural-language question and return the answer_text.

        Uses the `question` socket command (not eval-json).  The session_id
        groups turns: the server accumulates turn history per id and resets
        on `end-session`.

        Returns the answer_text string (may be empty if the question contains
        only unknown words).  Raises VyakaranaError on server errors.
        """
        # NOTE: the question command is the catch-all (| _) in socket.ml.
        # Do NOT include "command": "question" — the simple JSON scanner in
        # json_string_field searches for the literal string "question" and
        # finds it in the command *value* first, returning None.
        # Omitting "command" lets it fall through to | _ correctly.
        resp = self._send_with_retry({"question": question, "session_id": session_id})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"),
                err.get("message", repr(resp)),
            )
        assert resp.get("status") == "ok", f"unexpected status in: {resp}"
        return resp.get("answer_text", "")

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

    @staticmethod
    def all_triples(
        graph: list,
        *,
        subj: str | None = None,
        pred: str | None = None,
        obj: str | None = None,
    ) -> list[list]:
        """Return all triples matching the supplied constraints.

        Unlike find_triple (which returns the first match), this returns every
        match.  Useful when checking that a predicate appears multiple times
        (e.g. both ball-A and ball-B have prathama-vibhakti) or that a stale
        triple was removed (assert all_triples(...) == []).
        """
        results = []
        for t in graph:
            if not (isinstance(t, list) and len(t) >= 3):
                continue
            if subj is not None and t[0] != subj:
                continue
            if pred is not None and t[1] != pred:
                continue
            if obj is not None and t[2] != obj:
                continue
            results.append(t)
        return results

    # ── numeric helpers ──────────────────────────────────────────────────────

    @staticmethod
    def approx_eq(a: Any, b: float, tol: float = 1e-3) -> bool:
        """True if numeric values a and b are within tol of each other.

        Handles the case where a arrives as a string from the server (e.g.
        sankhya object values like "5." or "10.0") by attempting float
        conversion first.

            assert vy.approx_eq(triple[2], 5.0)
            assert vy.approx_eq("10.", 10.0)
        """
        try:
            return abs(float(a) - float(b)) < tol
        except (TypeError, ValueError):
            return False

    # ── kosha walk helpers ───────────────────────────────────────────────────

    def walk(self, node: str, rel: str) -> list[str]:
        """Walk outgoing edges of `node` along `rel` in the kosha graph.

        Equivalent to the tantra:
            walked = walk "mass" "matra"
            names  = map walked (fn n -> to-string n)

        Returns a list of node-name strings (may be empty if no such edge
        exists or the node is unknown).

            units = vy.walk("mass", "matra")          # ["kilogram"]
            deps  = vy.walk("velocity", "kramanusara") # ["displacement", ...]
        """
        result = self.eval(f'walk "{node}" "{rel}"')
        if result is None:
            return []
        # val_to_json serialises graph nodes via as_string → plain strings
        return [str(n) for n in result] if isinstance(result, list) else []

    def walk_in(self, node: str, rel: str) -> list[str]:
        """Walk incoming edges to `node` along `rel` (reverse direction).

        Equivalent to the tantra:
            owns = walk-in "kilogram" "matra"
            names = map owns (fn n -> to-string n)

        Returns a list of node-name strings.

            owners = vy.walk_in("kilogram", "matra")  # ["mass"]
            props  = vy.walk_in("ball-A", "shashthi-vibhakti")  # ["mass", ...]
        """
        result = self.eval(f'walk-in "{node}" "{rel}"')
        if result is None:
            return []
        return [str(n) for n in result] if isinstance(result, list) else []
