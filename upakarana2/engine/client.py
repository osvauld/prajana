"""client.py — Socket client for the vyakarana OCaml server.

Protocol: newline-delimited JSON over Unix domain socket.
"""

import json
import os
import socket
from typing import Any

DEFAULT_SOCKET = os.environ.get("VYAKARANA_SOCKET", "/tmp/vy.sock")


class VyakaranaError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class Client:
    """Persistent connection to a running vyakarana server."""

    def __init__(self, socket_path=DEFAULT_SOCKET):
        self._path = socket_path
        self._sock = None
        self._buf = b""
        self._connect()

    def _connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self._path)
        self._sock = s
        self._buf = b""

    def _reconnect(self):
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass
        self._connect()

    def _send(self, payload):
        data = json.dumps(payload) + "\n"
        self._sock.sendall(data.encode())
        while b"\n" not in self._buf:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise EOFError("server closed connection")
            self._buf += chunk
        line, self._buf = self._buf.split(b"\n", 1)
        return json.loads(line.decode())

    def _call(self, payload):
        try:
            return self._send(payload)
        except (EOFError, BrokenPipeError, ConnectionResetError, OSError):
            self._reconnect()
            return self._send(payload)

    def _check(self, resp):
        if resp.get("status") == "error":
            err = resp.get("error", {})
            raise VyakaranaError(err.get("code", "UNKNOWN"), err.get("message", repr(resp)))
        return resp

    # --- Core API ---

    def eval(self, expr: str) -> Any:
        """Evaluate a tantra expression, return result as Python value."""
        resp = self._check(self._call({"command": "eval-json", "expr": expr}))
        self._last_elapsed_us = resp.get("elapsed_us", 0)
        return resp["result"]

    def elapsed_us(self, expr: str) -> tuple[Any, int]:
        """Like eval() but also returns server-side elapsed_us."""
        resp = self._check(self._call({"command": "eval-json", "expr": expr}))
        return resp["result"], resp.get("elapsed_us", 0)

    def elapsed_ms(self, expr: str) -> tuple[Any, int]:
        """Like eval() but returns milliseconds (compat wrapper)."""
        result, us = self.elapsed_us(expr)
        return result, us // 1000

    def ask(self, question: str, session_id: str | None = None) -> str:
        """Send a question, return answer text."""
        import uuid
        sid = session_id or f"q-{uuid.uuid4().hex[:8]}"
        resp = self._check(self._call({"question": question, "session_id": sid}))
        self._last_elapsed_us = resp.get("elapsed_us", 0)
        return resp.get("answer_text", "")

    def close(self):
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    # --- Server management ---

    def reload_all(self) -> dict:
        """Re-read all tantra files from disk."""
        return self._check(self._call({"command": "reload-all"}))

    def attach(self, path: str) -> dict:
        """Load a single .om5 or .tantra4 file into the live server."""
        return self._check(self._call({"command": "attach", "path": path}))

    # --- Graph inspection ---

    def inspect(self, name: str) -> dict:
        """Node with outgoing + incoming edges."""
        return self._check(self._call({"command": "inspect-node", "name": name}))

    def list_tantras(self) -> list[str]:
        """All loaded tantra names."""
        resp = self._check(self._call({"command": "list-tantras"}))
        return resp.get("tantras", [])

    def triples_of(self, node: str) -> list[list]:
        """All triples touching a node."""
        resp = self._check(self._call({"command": "triples-of", "node": node}))
        return resp.get("triples", [])

    def walk(self, node: str, rel: str) -> list[str]:
        """Outgoing edges along relation."""
        result = self.eval(f'walk "{node}" "{rel}"')
        return [str(n) for n in result] if isinstance(result, list) else []

    def walk_in(self, node: str, rel: str) -> list[str]:
        """Incoming edges along relation."""
        result = self.eval(f'walk-in "{node}" "{rel}"')
        return [str(n) for n in result] if isinstance(result, list) else []

    def pipeline_trace(self, sentence: str) -> list[dict]:
        """Stage-by-stage avrti-refine trace."""
        resp = self._check(self._call({"command": "pipeline-trace", "sentence": sentence}))
        return resp.get("stages", [])

    def mantra_status(self, sentence: str) -> dict:
        """Mantra coverage for a sentence."""
        return self._check(self._call({"command": "mantra-status", "sentence": sentence}))

    def bound_concepts(self, graph: list) -> list[list]:
        """Extract [concept, value] pairs from a refined graph."""
        result = self.eval(f"debug-bound-concepts {json.dumps(graph)}")
        return result if isinstance(result, list) else []

    # --- Graph edit API ---

    def _edit(self, command, **kwargs):
        return self._check(self._call({"command": command, **kwargs}))

    def create_node(self, path, layer, name, edges=None, comments=None):
        """Create a new om5 node.

        edges: dict of {relation: [targets]} e.g. {"swarupa": ["velocity"], "sthita": ["kona"]}
        comments: list of comment strings (written as ; lines above the node)
        """
        return self._edit("create-node", path=path, layer=layer, name=name,
                          edges=edges or {}, comments=comments or [])

    def delete_node(self, name):
        return self._edit("delete-node", name=name)

    def add_edge(self, source, target, relation):
        return self._edit("add-edge", source=source, target=target, relation=relation)

    def remove_edge(self, source, target, relation):
        return self._edit("remove-edge", source=source, target=target, relation=relation)

    def set_shabda(self, name, shabda):
        return self._edit("set-shabda", name=name, shabda=shabda)

    def add_sloka(self, name, sloka):
        return self._edit("add-sloka", name=name, sloka=sloka)

    def remove_sloka(self, name, sloka):
        return self._edit("remove-sloka", name=name, sloka=sloka)

    def write_tantra(self, path, source):
        return self._edit("write-tantra", path=path, source=source)

    # --- Pipeline helpers ---

    def bqg(self, sentence):
        """Build question graph + avrti-refine fixpoint."""
        return self.eval(f'fixpoint (build-question-graph "{sentence}") avrti-refine')

    def answer(self, sentence):
        """Full anuvada-ganana pipeline."""
        return str(self.eval(f'anuvada-ganana "{sentence}"'))

    def raw_bqg(self, sentence):
        """Build question graph without refinement."""
        return self.eval(f'build-question-graph "{sentence}"')

    # --- Static graph helpers ---

    @staticmethod
    def find_triple(graph, *, subj=None, pred=None, obj=None):
        for t in graph:
            if not (isinstance(t, list) and len(t) >= 3):
                continue
            if subj and t[0] != subj:
                continue
            if pred and t[1] != pred:
                continue
            if obj and t[2] != obj:
                continue
            return t
        return None

    @staticmethod
    def has_triple(graph, *, subj=None, pred=None, obj=None):
        return Client.find_triple(graph, subj=subj, pred=pred, obj=obj) is not None

    @staticmethod
    def all_triples(graph, *, subj=None, pred=None, obj=None):
        return [t for t in graph if isinstance(t, list) and len(t) >= 3
                and (subj is None or t[0] == subj)
                and (pred is None or t[1] == pred)
                and (obj is None or t[2] == obj)]

    @staticmethod
    def subjects(graph, *, pred):
        return [t[0] for t in graph if isinstance(t, list) and len(t) >= 2 and t[1] == pred]

    @staticmethod
    def objects(graph, *, pred):
        return [t[2] for t in graph if isinstance(t, list) and len(t) >= 3 and t[1] == pred]

    @staticmethod
    def triple_map(graph, *, pred):
        return {t[0]: t[2] for t in graph if isinstance(t, list) and len(t) >= 3 and t[1] == pred}

    @staticmethod
    def sig(graph):
        return [t for t in graph if isinstance(t, list) and len(t) >= 2
                and t[1] not in ("kosha-janya", "ppr")]

    @staticmethod
    def approx_eq(a, b, tol=1e-3):
        try:
            return abs(float(a) - float(b)) < tol
        except (TypeError, ValueError):
            return False

    @staticmethod
    def tl(graph):
        return json.dumps(graph)

    @staticmethod
    def strand(answer, name):
        lower = answer.lower()
        parts = lower.split(name)
        if len(parts) < 2:
            return ""
        # find the position in the original string
        pos = lower.rfind(name)
        tail = answer[pos + len(name):]
        lower_tail = tail.lower()
        for boundary in ("we have", "we seek", "we know", "we see", "we find"):
            if boundary != name and boundary in lower_tail:
                tail = tail[:lower_tail.index(boundary)]
                break
        return tail

    @staticmethod
    def strands(answer):
        result = {}
        lower = answer.lower()
        for name in ("we have", "we seek", "we know", "we see", "we find"):
            if name in lower:
                result[name] = Client.strand(answer, name)
        return result
