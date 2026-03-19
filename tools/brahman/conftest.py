"""conftest.py — pytest fixtures for vyakarana integration tests.

One socket connection is opened per test session and shared across all tests.
Set VYAKARANA_SOCKET env var or pass --socket on the CLI to override the path.

Start the server before running:
    cd vyakarana && ./_build/default/bin/vyakarana.exe --quiet-startup --socket /tmp/vy.sock ../brahman &

Then run tests:
    cd vyakarana/tests && ../../.venv/bin/pytest
    or: cd vyakarana/tests && pytest            # if venv is activated

TEST RESULT CACHE
-----------------
Every test's queries and responses are recorded as JSON in:
    .pytest_cache/vyakarana/<test-node-id>.json

On failure the cache contains:
  - sentences sent to anuvada-ganana / vy.ask
  - server responses and elapsed_ms
  - what was expected vs what was got
  - the full exception message

This feeds directly into the analysis pipeline:
    python3 tools/analyze_tantras.py   # reads the cache
    python3 tools/analyze_pipeline.py  # cross-references failures with tantras

Format:
    {
      "test":     "test_file.py::test_name",
      "outcome":  "passed" | "failed" | "error" | "xfailed" | "xpassed",
      "calls":    [{"method": "eval|ask|walk", "input": "...", "output": ...,
                    "elapsed_ms": N, "error": null|"..."}],
      "failure":  {"expected": "...", "got": "...", "message": "..."},
      "duration": N.NN
    }
"""

import json
import os
import sys
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

# ensure vy.py is importable from tools/brahman/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vy import Client, DEFAULT_SOCKET

# fixed cache directory — always writes to tools/.pytest_cache/vyakarana/
# regardless of where pytest is invoked from
_BRAHMAN_DIR = Path(__file__).parent
_FIXED_CACHE = _BRAHMAN_DIR / ".pytest_cache" / "vyakarana"


# ── options ───────────────────────────────────────────────────────────────────


def pytest_addoption(parser):
    parser.addoption(
        "--socket",
        default=None,
        help="Path to vyakarana Unix socket (default: $VYAKARANA_SOCKET or /tmp/vy.sock)",
    )
    parser.addoption(
        "--no-cache",
        action="store_true",
        default=False,
        help="Disable test result caching",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "xfail_known: mark test as a known failure (feature not yet implemented)",
    )


# ── recording client wrapper ──────────────────────────────────────────────────


class RecordingClient:
    """
    Wraps Client to record every query/response pair.
    The test fixture swaps this in transparently — all test code uses vy.eval()
    etc. exactly as before. The recording is attached to the current test node
    via the _current_calls list, which conftest resets per test.
    """

    def __init__(self, client: Client):
        self._client = client
        self._calls: list[dict] = []  # reset per test by the fixture

    # ── delegate every Client method, recording as we go ─────────────────────

    def eval(self, expr: str) -> Any:
        t0 = time.monotonic()
        error = None
        result = None
        try:
            result = self._client.eval(expr)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append(
                {
                    "method": "eval",
                    "input": expr,
                    "output": result,
                    "elapsed_ms": int((time.monotonic() - t0) * 1000),
                    "error": error,
                }
            )
        return result

    def elapsed_ms(self, expr: str) -> tuple[Any, int]:
        t0 = time.monotonic()
        error = None
        result, ms = None, 0
        try:
            result, ms = self._client.elapsed_ms(expr)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append(
                {
                    "method": "elapsed_ms",
                    "input": expr,
                    "output": result,
                    "elapsed_ms": ms,
                    "error": error,
                }
            )
        return result, ms

    def ask(self, question: str, session_id: str = "test") -> str:
        t0 = time.monotonic()
        error = None
        result = None
        try:
            result = self._client.ask(question, session_id=session_id)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append(
                {
                    "method": "ask",
                    "input": question,
                    "session_id": session_id,
                    "output": result,
                    "elapsed_ms": int((time.monotonic() - t0) * 1000),
                    "error": error,
                }
            )
        return result

    def walk(self, node: str, relation: str) -> list:
        t0 = time.monotonic()
        error = None
        result = None
        try:
            result = self._client.walk(node, relation)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append(
                {
                    "method": "walk",
                    "input": f'{node} "{relation}"',
                    "output": result,
                    "elapsed_ms": int((time.monotonic() - t0) * 1000),
                    "error": error,
                }
            )
        return result

    def walk_in(self, node: str, relation: str) -> list:
        t0 = time.monotonic()
        error = None
        result = None
        try:
            result = self._client.walk_in(node, relation)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append(
                {
                    "method": "walk_in",
                    "input": f'{node} "{relation}"',
                    "output": result,
                    "elapsed_ms": int((time.monotonic() - t0) * 1000),
                    "error": error,
                }
            )
        return result

    # ── delegate everything else unchanged ────────────────────────────────────

    def __getattr__(self, name):
        return getattr(self._client, name)


# ── cache directory ───────────────────────────────────────────────────────────


def _cache_dir(config=None) -> Path:
    d = _FIXED_CACHE
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_node_id(node_id: str) -> str:
    """Convert test node id to a safe filename."""
    return (
        node_id.replace("/", "__")
        .replace("::", "__")
        .replace("[", "_")
        .replace("]", "")
    )


# ── fixtures ──────────────────────────────────────────────────────────────────

# The underlying Client — one per session, shared
_raw_client: Client | None = None
_recorder: RecordingClient | None = None


@pytest.fixture(scope="session")
def _vy_session(request) -> Generator[Client, None, None]:
    global _raw_client, _recorder
    socket_path = request.config.getoption("--socket") or DEFAULT_SOCKET
    _raw_client = Client(socket_path)
    _recorder = RecordingClient(_raw_client)
    yield _raw_client
    _raw_client.close()


@pytest.fixture
def vy(request, _vy_session) -> Generator[RecordingClient, None, None]:
    """
    Per-test vyakarana client fixture.
    Records every eval/ask/walk call for the cache.
    Passes through to the session-scoped raw client.
    """
    assert _recorder is not None
    _recorder._calls = []  # fresh call log for this test
    t0 = time.monotonic()
    yield _recorder
    duration = time.monotonic() - t0

    # write cache unless --no-cache
    if not request.config.getoption("--no-cache", default=False):
        _write_cache(request, _recorder._calls, duration)


# ── cache writer ──────────────────────────────────────────────────────────────


def _write_cache(request, calls: list[dict], duration: float) -> None:
    """Write the test result JSON to .pytest_cache/vyakarana/."""
    node_id = request.node.nodeid
    outcome = "unknown"

    # get outcome from the report (available after the test body runs)
    rep = getattr(request.node, "_last_outcome", None)
    if rep:
        outcome = rep

    xfail_meta = getattr(request.node, "_xfail_meta", None)
    entry: dict = {
        "test": node_id,
        "outcome": outcome,
        "calls": calls,
        "failure": None,
        "duration": round(duration, 3),
    }
    if xfail_meta:
        entry["xfail"] = xfail_meta

    cache_dir = _cache_dir(request.config)
    cache_file = cache_dir / (_safe_node_id(node_id) + ".json")
    try:
        cache_file.write_text(json.dumps(entry, indent=2, default=str))
    except Exception:
        pass  # never break tests due to cache write failure


# ── hook: capture outcome and failure details ─────────────────────────────────


_GATE_KEYWORDS = {
    # structural gaps — checked in order, first match wins
    "sthita-viveka": "sthita-viveka: multi-slot entity assignment",
    "relative-velocity": "relative-velocity: kosha concept missing",
    "dvandva": "dvandva: per-entity instance-map",
    "session_gap2": "session_gap2: prathama/shashthi across turns",
    "session gap2": "session_gap2: prathama/shashthi across turns",
    "prathama/shashthi": "session_gap2: prathama/shashthi across turns",
    "prathama-vibhakti": "session_gap2: prathama/shashthi across turns",
    "pratibimba": "pratibimba: gated on Gap 2",
    "simulation scene": "pratibimba: gated on Gap 2",
    "gravitational-force": "p8f_gravity: G + r² composition",
    "gravitational force": "p8f_gravity: G + r² composition",
    "expression graph": "p8f_gravity: G + r² composition",
    "bound-vals": "inverse-math: bound-vals / invert-math path",
    "invert-math": "inverse-math: bound-vals / invert-math path",
    "inverse": "inverse-math: bound-vals / invert-math path",
    "viraam boundary": "viraam: has-intent lost across period",
    "viraam": "viraam: has-intent lost across period",
    "syllogism": "logic_nyaya: P8d anumana not built",
    "anumana": "logic_nyaya: P8d anumana not built",
    "transitive": "logic_nyaya: P8d anumana not built",
    "modus-ponens": "logic_nyaya: P8d anumana not built",
    "compute-then-compare": "viveka: compute-then-compare not built",
    "which has more": "viveka: compute-then-compare not built",
    "proportional": "viveka: proportional reasoning",
    "count addition": "arithmetic: plain count not in pipeline",
    "count subtraction": "arithmetic: plain count not in pipeline",
    "plain count": "arithmetic: plain count not in pipeline",
    "distance = speed": "arithmetic: plain count not in pipeline",
    "area =": "arithmetic: plain count not in pipeline",
    "rectangle": "arithmetic: plain count not in pipeline",
    "coulomb": "kosha: missing concept node",
    "moves at": "kosha: missing concept node",
    "motion verb": "kosha: missing concept node",
    "period-mantra": "kosha: missing concept node",
    "m/s compound": "unit_rate: m/s compound unit",
    "gap 1": "unit_rate: m/s compound unit",
    "gap 2": "session_gap2: prathama/shashthi across turns",
    "rashi-anuvada bridge": "dvandva: per-entity instance-map",
    "p8b": "dvandva: per-entity instance-map",
    "article": "parsing: article before entity name",
    "the'": "parsing: article before entity name",
    "natural phrasing": "parsing: natural phrasing not handled",
    "from rest": "parsing: natural phrasing not handled",
}


def _xfail_info(item) -> dict:
    """Extract xfail marker metadata: reason, strict, file, line, gate."""
    marker = item.get_closest_marker("xfail")
    if not marker:
        return {}
    reason = marker.kwargs.get("reason", "") or (marker.args[0] if marker.args else "")
    strict = marker.kwargs.get("strict", False)

    # derive gate from keyword matching against the reason string
    reason_lower = reason.lower()
    gate = ""
    for keyword, group in _GATE_KEYWORDS.items():
        if keyword.lower() in reason_lower:
            gate = group
            break
    if not gate:
        # fall back to test file name
        gate = f"other:{item.fspath.basename.replace('.py', '')}"

    return {
        "reason": reason,
        "strict": strict,
        "gate": gate,
        "file": str(item.fspath),
        "line": item.function.__code__.co_firstlineno,
    }


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture pass/fail/xfail/xpass outcome and failure message into the cache."""
    outcome = yield
    rep = outcome.get_result()

    cache_dir = _FIXED_CACHE
    cache_file = cache_dir / (_safe_node_id(item.nodeid) + ".json")

    if rep.when == "call":
        # xpassed: strict xfail that now passes — record as xpassed
        if rep.passed and hasattr(rep, "wasxfail"):
            item._last_outcome = "xpassed"
            item._xfail_meta = _xfail_info(item)
            return

        # xfailed: test failed as expected
        if rep.skipped and hasattr(rep, "wasxfail"):
            item._last_outcome = "xfailed"
            item._xfail_meta = _xfail_info(item)
            return

        # normal pass
        item._last_outcome = rep.outcome  # "passed" | "failed" | "error"

        # on failure: extract what was expected vs what was got
        if rep.failed and _recorder is not None:
            failure_info = _extract_failure(rep)
            if cache_file.exists():
                try:
                    entry = json.loads(cache_file.read_text())
                    entry["outcome"] = "failed"
                    entry["failure"] = failure_info
                    cache_file.write_text(json.dumps(entry, indent=2, default=str))
                except Exception:
                    pass

    elif rep.when == "setup":
        if rep.skipped:
            # setup-phase xfail (e.g. condition=True xfail)
            item._last_outcome = (
                "xfailed" if getattr(rep, "wasxfail", False) else "skipped"
            )
            if item._last_outcome == "xfailed":
                item._xfail_meta = _xfail_info(item)


def _extract_failure(rep) -> dict:
    """Pull the expected/got/message from a pytest report."""
    msg = str(rep.longrepr) if rep.longrepr else ""

    # try to extract "expected X in Y" / "AssertionError: expected=... got=..."
    expected = ""
    got = ""

    import re

    # pattern: expected '15' in '...'
    m = re.search(r"expected[:\s]+['\"]?([^'\"]+)['\"]?\s+in\s+['\"]?(.{0,120})", msg)
    if m:
        expected = m.group(1).strip()
        got = m.group(2).strip()
    else:
        # pattern: assert "X" in result
        m2 = re.search(r'assert\s+["\'](.+?)["\']\s+in\s+(\w+)', msg)
        if m2:
            expected = m2.group(1)

    # last eval/ask call = the one that caused the failure
    last_call = None
    if _recorder and _recorder._calls:
        last_call = _recorder._calls[-1]

    return {
        "expected": expected,
        "got": got,
        "message": msg[:500],
        "last_call": last_call,
    }


# ── summary writer: runs once at end of session ───────────────────────────────


def pytest_sessionfinish(session, exitstatus):
    """
    Write a summary JSON after all tests complete.
    .pytest_cache/vyakarana/summary.json

    Format:
      {
        "total": N, "passed": N, "failed": N, "xfailed": N, "xpassed": N,
        "failed_tests": [
          {
            "test": "...", "failure": {...}, "sentences": ["..."],
            "expected": "...", "got": "..."
          }
        ],
        "xfail_tests": [...],
        "slow_tests": [{"test": "...", "duration": N, "calls": N}]
      }
    """
    try:
        cache_dir = _FIXED_CACHE
        if not cache_dir.exists():
            return

        entries = []
        for f in sorted(cache_dir.glob("*.json")):
            if f.name == "summary.json":
                continue
            try:
                entries.append(json.loads(f.read_text()))
            except Exception:
                pass

        counts: dict[str, int] = {
            "passed": 0,
            "failed": 0,
            "error": 0,
            "xfailed": 0,
            "xpassed": 0,
            "skipped": 0,
            "unknown": 0,
        }
        for e in entries:
            k = e.get("outcome", "unknown")
            counts[k] = counts.get(k, 0) + 1

        failed_tests = []
        for e in entries:
            if e.get("outcome") in ("failed", "error"):
                # extract all sentences sent in this test
                sentences = [
                    c["input"]
                    for c in e.get("calls", [])
                    if c.get("method") in ("ask", "eval")
                    and (
                        "anuvada-ganana" in c.get("input", "")
                        or c.get("method") == "ask"
                    )
                ]
                failure = e.get("failure") or {}
                failed_tests.append(
                    {
                        "test": e["test"],
                        "failure": failure,
                        "sentences": sentences,
                        "expected": failure.get("expected", ""),
                        "got": failure.get("got", ""),
                        "calls": len(e.get("calls", [])),
                        "duration": e.get("duration", 0),
                    }
                )

        xfail_tests = [
            {
                "test": e["test"],
                "duration": e.get("duration", 0),
                "reason": (e.get("xfail") or {}).get("reason", ""),
                "gate": (e.get("xfail") or {}).get("gate", ""),
                "strict": (e.get("xfail") or {}).get("strict", False),
                "file": (e.get("xfail") or {}).get("file", ""),
                "line": (e.get("xfail") or {}).get("line", 0),
            }
            for e in entries
            if e.get("outcome") == "xfailed"
        ]
        xpass_tests = [
            {
                "test": e["test"],
                "duration": e.get("duration", 0),
                "reason": (e.get("xfail") or {}).get("reason", ""),
                "file": (e.get("xfail") or {}).get("file", ""),
                "line": (e.get("xfail") or {}).get("line", 0),
            }
            for e in entries
            if e.get("outcome") == "xpassed"
        ]

        slow_tests = sorted(
            [
                {
                    "test": e["test"],
                    "duration": e.get("duration", 0),
                    "calls": len(e.get("calls", [])),
                }
                for e in entries
                if e.get("duration", 0) > 0.5
            ],
            key=lambda x: x["duration"],
            reverse=True,
        )[:20]

        summary = {
            "total": len(entries),
            "passed": counts["passed"],
            "failed": counts["failed"] + counts["error"],
            "xfailed": counts["xfailed"],
            "xpassed": counts["xpassed"],
            "skipped": counts["skipped"],
            "failed_tests": failed_tests,
            "xfail_tests": xfail_tests[:10],
            "xpass_tests": xpass_tests,
            "slow_tests": slow_tests,
        }

        (cache_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, default=str)
        )
    except Exception:
        pass  # never break the test run
