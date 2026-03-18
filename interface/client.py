"""
client.py — the canonical vyakarana socket client.

This is the absorbed form of vyakarana/tests/vy.py.
It lives in interface/ because it IS the interface —
not a test utility but the primary way anything speaks to the proof graph.

The same client is used by:
  - pytest tests (via conftest.py fixture)
  - tools/analyze_*.py (for live graph queries)
  - interface/bus.py (ProofGraphNode uses transport.py directly, but
    higher-level callers can use this Client)
  - interface/session.py (BusSession wraps this)
  - any script that needs to talk to the server

vyakarana/tests/vy.py re-exports from here so tests are unaffected.

PROTOCOL:
  Unix domain socket, newline-delimited JSON.
  One JSON object per line in each direction, no length prefix.
  The server dispatches on the "command" field.
  Exception: the question command has NO "command" field —
  the server catches it as the | _ case.

QUESTION COMMAND GOTCHA:
  Do NOT include "command": "question".
  The server's json_string_field scanner finds the literal string "question"
  in the value of "command": "question" and returns None, routing to error.
  Correct: {"question": "...", "session_id": "..."}
  Wrong:   {"command": "question", "question": "...", "session_id": "..."}
"""

import json
import os
import socket
from typing import Any

DEFAULT_SOCKET = os.environ.get("VYAKARANA_SOCKET", "/tmp/vy.sock")


class VyakaranaError(Exception):
    """Raised when the server returns status=error."""

    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


class Client:
    """
    Thin client for the vyakarana Unix socket.

    Keeps a single persistent connection and reconnects automatically on
    disconnect (BrokenPipe, ConnectionReset, EOFError).

    All public methods raise VyakaranaError on server-side errors.
    """

    def __init__(self, socket_path: str = DEFAULT_SOCKET):
        self._path = socket_path
        self._sock: socket.socket | None = None
        self._buf = b""
        self._connect()

    # ── connection management ─────────────────────────────────────────────────

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

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    # ── wire protocol ─────────────────────────────────────────────────────────

    def _send(self, payload: dict) -> dict:
        assert self._sock is not None
        data = json.dumps(payload) + "\n"
        self._sock.sendall(data.encode())
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

    # ── core evaluation ────────────────────────────────────────────────────────

    def eval(self, expr: str) -> Any:
        """
        Evaluate a tantra2 expression. Returns the result as a Python value.

        Lists come back as Python lists, strings as str, numbers as int/float,
        bools as bool, null as None.

            vy.eval('lookup-word "mass"')          # "mass"
            vy.eval('build-question-graph "ball has mass"')  # [[...], ...]
            vy.eval('match-mantra [...]')           # [...] or []
        """
        resp = self._send_with_retry({"command": "eval-json", "expr": expr})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"), err.get("message", repr(resp))
            )
        assert resp.get("status") == "ok", f"unexpected status: {resp}"
        return resp["result"]

    def elapsed_ms(self, expr: str) -> tuple[Any, int]:
        """Like eval() but also returns server-side elapsed_ms."""
        resp = self._send_with_retry({"command": "eval-json", "expr": expr})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"), err.get("message", repr(resp))
            )
        return resp["result"], resp.get("elapsed_ms", 0)

    def ask(self, question: str, session_id: str = "test") -> str:
        """
        Send a natural-language question. Returns answer_text string.

        IMPORTANT: no "command" key — server dispatches via | _ catch-all.

            answer = vy.ask("find kinetic energy given mass 5 velocity 10")
            answer = vy.ask("ball has mass 3", session_id="s1")
        """
        resp = self._send_with_retry({"question": question, "session_id": session_id})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"), err.get("message", repr(resp))
            )
        assert resp.get("status") == "ok", f"unexpected status: {resp}"
        return resp.get("answer_text", "")

    # ── session management ────────────────────────────────────────────────────

    def end_session(self, session_id: str) -> None:
        """Release session state from the server's session_store."""
        self._send_with_retry({"command": "end-session", "session_id": session_id})

    # ── kosha graph walks ─────────────────────────────────────────────────────

    def walk(self, node: str, relation: str) -> list:
        """
        Follow outgoing edges of type `relation` from `node`.

            vy.walk("mass", "matra")        # ["kilogram"]
            vy.walk("velocity", "kramanusara")  # ["displacement"]
        """
        return self.eval(f'walk "{node}" "{relation}"')

    def walk_in(self, node: str, relation: str) -> list:
        """
        Follow incoming edges of type `relation` to `node`.

            vy.walk_in("kilogram", "matra")  # ["mass", ...]
        """
        return self.eval(f'walk-in "{node}" "{relation}"')

    def node_satya(self, node: str) -> float:
        """Return the satya (certainty) score for a node. 0.0 if not found."""
        result = self.eval(f'node-satya "{node}"')
        try:
            return float(result)
        except (TypeError, ValueError):
            return 0.0

    # ── graph triple helpers ──────────────────────────────────────────────────

    @staticmethod
    def has_triple(
        graph: list,
        subj: str | None = None,
        pred: str | None = None,
        obj: str | None = None,
    ) -> bool:
        """True if graph contains at least one matching [s, p, o] triple."""
        for triple in graph:
            if not (isinstance(triple, list) and len(triple) == 3):
                continue
            s, p, o = triple
            if subj is not None and str(s) != subj:
                continue
            if pred is not None and str(p) != pred:
                continue
            if obj is not None and str(o) != obj:
                continue
            return True
        return False

    @staticmethod
    def find_triple(
        graph: list,
        subj: str | None = None,
        pred: str | None = None,
        obj: str | None = None,
    ) -> list | None:
        """Return the first matching triple, or None."""
        for triple in graph:
            if not (isinstance(triple, list) and len(triple) == 3):
                continue
            s, p, o = triple
            if subj is not None and str(s) != subj:
                continue
            if pred is not None and str(p) != pred:
                continue
            if obj is not None and str(o) != obj:
                continue
            return triple
        return None

    @staticmethod
    def all_triples(
        graph: list,
        subj: str | None = None,
        pred: str | None = None,
        obj: str | None = None,
    ) -> list:
        """Return all matching triples."""
        results = []
        for triple in graph:
            if not (isinstance(triple, list) and len(triple) == 3):
                continue
            s, p, o = triple
            if subj is not None and str(s) != subj:
                continue
            if pred is not None and str(p) != pred:
                continue
            if obj is not None and str(o) != obj:
                continue
            results.append(triple)
        return results

    @staticmethod
    def approx_eq(value: Any, expected: float, tol: float = 1e-6) -> bool:
        """
        Numeric comparison with tolerance.
        Server returns floats as strings like "5." or "250." — handles both.
        """
        try:
            return abs(float(value) - expected) <= tol
        except (TypeError, ValueError):
            return False

    # ── live server management ────────────────────────────────────────────────

    def reload_all(self) -> dict:
        """
        Re-read all tantra files from disk without restarting.
        Use after editing existing tantras.
        """
        resp = self._send_with_retry({"command": "reload-all"})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"), err.get("message", repr(resp))
            )
        assert resp.get("status") == "ok"
        return resp

    def attach(self, path: str) -> dict:
        """
        Live-load a single .tantra2 or .om file without restart.
        Path must be absolute.
        """
        resp = self._send_with_retry({"command": "attach", "path": path})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"), err.get("message", repr(resp))
            )
        assert resp.get("status") == "ok"
        return resp

    def dump_ast(self, path: str) -> dict | None:
        """
        Parse a .tantra2 file and return its AST as a dict.
        Used by tools/collect_data.py for structural analysis.
        """
        resp = self._send_with_retry({"command": "dump-ast", "path": path})
        if resp.get("status") == "ok":
            return resp.get("tantra")
        return None

    # ── debug commands ────────────────────────────────────────────────────────

    def inspect(self, name: str) -> dict:
        """
        Return one graph node with both outgoing and incoming edges.

            node = vy.inspect("velocity")
            # {"name": "velocity", "satya": 0.9,
            #  "out_edges": [...], "in_edges": [...]}
        """
        resp = self._send_with_retry({"command": "inspect-node", "name": name})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"), err.get("message", repr(resp))
            )
        assert resp.get("status") == "ok"
        return resp

    def list_tantras(self) -> list[str]:
        """Return names of all currently loaded tantras."""
        resp = self._send_with_retry({"command": "list-tantras"})
        if resp.get("status") == "error":
            return []
        return resp.get("tantras", [])

    def triples_of(self, node: str) -> list:
        """All triples where node appears as subject or object."""
        resp = self._send_with_retry({"command": "triples-of", "node": node})
        if resp.get("status") == "error":
            return []
        return resp.get("triples", [])

    def pipeline_trace(self, sentence: str) -> list[dict]:
        """
        Run avrti-refine step-by-step on a sentence.
        Returns [{stage, triples}, ...] for each avrti sub-tantra.

            trace = vy.pipeline_trace("ball has mass m1 of 5")
            for step in trace:
                print(step["stage"], "→", len(step["triples"]), "triples")
        """
        resp = self._send_with_retry(
            {"command": "pipeline-trace", "sentence": sentence}
        )
        if resp.get("status") == "error":
            return []
        return resp.get("stages", [])

    def mantra_status(self, sentence: str) -> dict:
        """
        Run the pipeline and report which mantras fire and why.
        Returns {refined_graph, bound_concepts, mantras}.

            s = vy.mantra_status("ball has mass m1 of 5 and velocity v1 of 20")
            # s["bound_concepts"]  → [["mass","5."], ["velocity","20."]]
            # s["mantras"]         → [["ke-mantra", True, ["mass","vel"], []], ...]
        """
        resp = self._send_with_retry({"command": "mantra-status", "sentence": sentence})
        if resp.get("status") == "error":
            return {}
        return resp

    def bound_concepts(self, graph: list) -> list:
        """
        Run debug-bound-concepts tantra on a pre-built graph.
        Returns [[concept, val], ...] pairs.
        """
        g_json = json.dumps(graph)
        result = self.eval(f"debug-bound-concepts {g_json}")
        return result if isinstance(result, list) else []
