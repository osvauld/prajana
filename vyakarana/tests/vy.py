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

        # attach a new tantra or .om file without restarting the server
        vy.attach("/abs/path/brahman/yantra/vishesa/rashi-anuvada.tantra")

        # --- debug helpers ---

        # inspect a single node (outgoing + incoming edges)
        node = vy.inspect("velocity")
        # node == {"name": "velocity", "satya": 0.9, "out_edges": [...], "in_edges": [...]}

        # list all loaded tantra names
        names = vy.list_tantras()   # ["avrti-refine", "rashi-viveka", ...]

        # all triples touching a node (as subj or obj)
        triples = vy.triples_of("velocity")   # [["velocity","sankhya","20."], ...]

        # run avrti-refine stage-by-stage and see graph after each step
        trace = vy.pipeline_trace("ball has mass m1 of 5 and velocity v1 of 20")
        # trace == [{"stage": "sandhi-kosha", "triples": [...]}, ...]

        # show mantra coverage: which mantras fire and why
        status = vy.mantra_status("ball has mass m1 of 5 and velocity v1 of 20")
        # status["bound_concepts"] == [["mass","5."],["velocity","20."]]  (after bridge)
        # status["mantras"]        == [["kinetic-energy-mantra", True, [...], []], ...]

        # bound-concepts shortcut (just the [concept, value] pairs from a graph)
        bc = vy.bound_concepts(g)   # [["mass","5."],["velocity","20."]]
"""

import json
import os
import socket
from typing import Any

DEFAULT_SOCKET = os.environ.get("VYAKARANA_SOCKET", "/tmp/vy.sock")


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

    def reload_all(self) -> dict:
        """Re-read all tantra files from disk into the live server index.

        Use this after editing an existing tantra to pick up the changes
        without restarting the server.  All tantra dirs from the original
        startup are rescanned; the index is fully rebuilt in place.

        Returns the parsed response dict with key:
            tantras_loaded — count of tantras now registered

        Example:
            # edit brahman/yantra/vibhakti/vibhakti-shashthi.tantra
            vy.reload_all()   # server picks up the change immediately
        """
        resp = self._send_with_retry({"command": "reload-all"})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"),
                err.get("message", repr(resp)),
            )
        assert resp.get("status") == "ok", f"unexpected status in: {resp}"
        return resp

    def inspect(self, name: str) -> dict:
        """Return one kosha node with both outgoing and incoming edges.

        Replaces the pattern of calling walk() + walk_in() separately.
        Returns a dict with keys: name, satya, out_edges, in_edges.

        Each edge is {"target": str, "relation": str} (out_edges) or
        {"source": str, "relation": str} (in_edges).

        Raises VyakaranaError if the node is not found.

            node = vy.inspect("velocity")
            # {"name": "velocity", "satya": 0.9,
            #  "out_edges": [{"target": "displacement", "relation": "kramanusara"}],
            #  "in_edges":  [{"source": "v1", "relation": "vishesa"}]}
        """
        resp = self._send_with_retry({"command": "inspect-node", "name": name})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"), err.get("message", repr(resp))
            )
        assert resp.get("status") == "ok", f"unexpected status: {resp}"
        return resp

    def list_tantras(self) -> list[str]:
        """Return the names of all currently loaded tantras (sorted).

        Use this to confirm that attach() or reload_all() registered a tantra.

            names = vy.list_tantras()
            assert "rashi-anuvada" in names
        """
        resp = self._send_with_retry({"command": "list-tantras"})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"), err.get("message", repr(resp))
            )
        assert resp.get("status") == "ok", f"unexpected status: {resp}"
        return resp.get("tantras", [])

    def triples_of(self, node: str) -> list[list]:
        """Return all triples where `node` appears as subject or object.

        More convenient than separate walk() + walk_in() calls when you want
        everything touching a node at once.

            ts = vy.triples_of("velocity")
            # [["velocity","sankhya","20."], ["v1","vishesa","velocity"], ...]
        """
        resp = self._send_with_retry({"command": "triples-of", "node": node})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"), err.get("message", repr(resp))
            )
        assert resp.get("status") == "ok", f"unexpected status: {resp}"
        return resp.get("triples", [])

    def pipeline_trace(self, sentence: str) -> list[dict]:
        """Run avrti-refine stage by stage and return the graph after each stage.

        Invaluable for debugging which pipeline stage added (or failed to add)
        a particular triple.

        Returns a list of dicts: [{"stage": str, "triples": list}, ...]
        Stages in order:
          build-question-graph → sandhi-kosha → sandhi-avastha →
          sandhi-bandhana → vibhakti-shashthi → vishesa-instance →
          rashi-viveka → vishesa-bandhana → sankhya-bandha

            trace = vy.pipeline_trace("ball has mass m1 of 5 and velocity v1 of 20")
            for step in trace:
                print(step["stage"], "→", len(step["triples"]), "triples")
        """
        resp = self._send_with_retry(
            {"command": "pipeline-trace", "sentence": sentence}
        )
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"), err.get("message", repr(resp))
            )
        assert resp.get("status") == "ok", f"unexpected status: {resp}"
        return resp.get("stages", [])

    def mantra_status(self, sentence: str) -> dict:
        """Show mantra coverage for a sentence — which mantras fire and why.

        Runs the full avrti-refine pipeline on the sentence, then for every
        loaded mantra reports which janya concepts are bound, which are missing,
        and whether it would fire.

        Returns a dict with keys:
            sentence        — echo of the input
            refined_graph   — list of triples after avrti-refine fixpoint
            bound_concepts  — list of [concept, value] pairs (from debug-bound-concepts)
            mantras         — list of [name, fires, covered, missing] per mantra
                              (from mantra-coverage tantra, if loaded)

        Example (before rashi-anuvada bridge):
            s = vy.mantra_status("ball has mass m1 of 5 and velocity v1 of 20")
            s["bound_concepts"]  # []  — rashi instances not yet propagated
            # kinetic-energy-mantra fires=False, missing=["mass","velocity"]

        Example (after bridge):
            s["bound_concepts"]  # [["mass","5."],["velocity","20."]]
            # kinetic-energy-mantra fires=True, covered=["mass","velocity"]
        """
        resp = self._send_with_retry({"command": "mantra-status", "sentence": sentence})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"), err.get("message", repr(resp))
            )
        assert resp.get("status") == "ok", f"unexpected status: {resp}"
        return resp

    def bound_concepts(self, graph: list) -> list[list]:
        """Extract [concept, value] pairs from a refined graph.

        Shortcut for calling debug-bound-concepts tantra via eval. Returns
        only nodes that have a sankhya triple — i.e. what derive-step sees
        as bound inputs.

            g = vy.eval('fixpoint (build-question-graph "ball has mass m1 of 5") avrti-refine')
            bc = vy.bound_concepts(g)   # [["m1", "5."]] before bridge
                                        # [["m1","5."],["mass","5."]] after bridge
        """
        result = self.eval(f"debug-bound-concepts {self._graph_to_expr(graph)}")
        if result is None:
            return []
        return result if isinstance(result, list) else []

    @staticmethod
    def _graph_to_expr(graph: list) -> str:
        """Serialise a graph (list of triples) back to a tantra-evaluable JSON literal."""
        import json

        return json.dumps(graph)

    def attach(self, path: str) -> dict:
        """Incrementally load a single .om or .tantra file into the live server.

        For .tantra files the new tantra is registered immediately — no server
        restart needed.  For .om files the node is joined into the graph and
        the CSR adjacency matrix is rebuilt.

        The path must be absolute and accessible by the server process.

        Returns the parsed response dict with keys:
            kind   — "tantra" or "om"
            name   — the tantra/node name that was registered

        Raises VyakaranaError on server errors (bad path, parse failure, etc).

        Example:
            vy.attach("/abs/path/brahman/yantra/vishesa/rashi-anuvada.tantra")
            vy.attach("/abs/path/brahman/sangati/prashna/new-signal.om")
        """
        resp = self._send_with_retry({"command": "attach", "path": path})
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(
                err.get("code", "UNKNOWN"),
                err.get("message", repr(resp)),
            )
        assert resp.get("status") == "ok", f"unexpected status in: {resp}"
        return resp

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
