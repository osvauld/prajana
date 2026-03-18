"""
nodes/llm.py — LLMNode.

An LLM endpoint that returns structured triples.
The LLM is asked a precise structured question:
  "What is X (classified as: pada)? Return ONLY JSON triples."

Supports two transports:
  Unix socket — for local LLM proxies that speak the jnana-bus triple protocol
  HTTP        — for ollama-compatible APIs (llama3, mistral, etc.)

The LLM socket protocol (Unix):
  request:  {"command": "triples-for", "prompt": "..."}
  response: {"triples": [[s,e,o], ...], "confidence": 0.7}

The HTTP protocol (ollama):
  POST /api/generate {"model": "...", "prompt": "...", "stream": false}
  response: {"response": "[[...]]"}
"""

import os
import re
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import socket as socket_mod
from triples import BusResponse, Triple
from node_base import BusNode
from pada_viveka import PadaResult


class LLMNode(BusNode):
    """
    LLM knowledge source. High coverage, moderate confidence, higher latency.
    The LLM is asked a structured question and must return only triples.
    No prose. No explanation. Just [subject, edge, object] arrays.
    """

    name = "llm"
    priority = 70

    def __init__(
        self,
        sock_path: str | None = None,
        http_url: str | None = None,
        model: str = "llama3",
        timeout: float = 30.0,
    ):
        self._sock_path = sock_path
        self._http_url = http_url
        self.model = model
        self.timeout = timeout

        if sock_path:
            self.name = f"llm-socket"
        elif http_url:
            self.name = f"llm-http"

    def available(self) -> bool:
        if self._sock_path:
            return os.path.exists(self._sock_path)
        if self._http_url:
            try:
                import urllib.request

                probe = self._http_url.replace("/api/generate", "/api/tags")
                urllib.request.urlopen(probe, timeout=2)
                return True
            except Exception:
                return False
        return False

    def query(self, word: str, pada: PadaResult, context: dict) -> BusResponse:
        if not self.available():
            return BusResponse(self.name, word, pada.pada, [], 0.0, "llm not available")

        prompt = _build_prompt(word, pada, context)

        if self._sock_path:
            return self._via_socket(word, pada, prompt)
        if self._http_url:
            return self._via_http(word, pada, prompt)

        return BusResponse(
            self.name, word, pada.pada, [], 0.0, "no endpoint configured"
        )

    def _via_socket(self, word: str, pada: PadaResult, prompt: str) -> BusResponse:
        assert self._sock_path is not None
        try:
            with socket_mod.socket(socket_mod.AF_UNIX, socket_mod.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect(self._sock_path)
                s.sendall(
                    (
                        json.dumps({"command": "triples-for", "prompt": prompt}) + "\n"
                    ).encode()
                )
                data = b""
                while True:
                    chunk = s.recv(65536)
                    if not chunk:
                        break
                    data += chunk
                    try:
                        resp = json.loads(data.decode())
                        triples = _clean(resp.get("triples", []))
                        conf = float(resp.get("confidence", 0.6))
                        return BusResponse(self.name, word, pada.pada, triples, conf)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            return BusResponse(self.name, word, pada.pada, [], 0.0, str(e))
        return BusResponse(self.name, word, pada.pada, [], 0.0)

    def _via_http(self, word: str, pada: PadaResult, prompt: str) -> BusResponse:
        assert self._http_url is not None
        try:
            import urllib.request

            body = json.dumps(
                {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                }
            ).encode()
            req = urllib.request.Request(
                self._http_url,
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read())
                text = raw.get("response", "")
                m = re.search(r"\[[\s\S]*\]", text)
                if m:
                    triples = _clean(json.loads(m.group(0)))
                    return BusResponse(
                        self.name, word, pada.pada, triples, 0.65, "ollama"
                    )
        except Exception as e:
            return BusResponse(self.name, word, pada.pada, [], 0.0, str(e))
        return BusResponse(self.name, word, pada.pada, [], 0.0)


def _build_prompt(word: str, pada: PadaResult, context: dict) -> str:
    known = context.get("known_concepts", {})
    sentence = context.get("sentence", "")
    return (
        f'The word "{word}" (word-class: {pada.pada}) appears in: "{sentence}". '
        f"Already known: {json.dumps(known)}. "
        f"Return ONLY a JSON array of triples [[subject, edge, object], ...] "
        f'that express what "{word}" IS and what it relates to. '
        f"Use short lowercase hyphenated terms. No prose. No explanation. "
        f"Example output: "
        f'[["electron","satya","particle"],'
        f'["electron","rest-mass-energy","0.511"],'
        f'["electron","matra","MeV"]]'
    )


def _clean(raw: list) -> list[Triple]:
    """Filter to valid (s, e, o) triples of strings."""
    result = []
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) == 3:
            s, e, o = item
            result.append((str(s), str(e), str(o)))
    return result
