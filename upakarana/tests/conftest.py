"""conftest.py — pytest fixtures for upakarana integration tests.

Uses upakarana.engine.client directly (no tools/ dependency).
Records every eval/ask/walk call into .pytest_cache/vyakarana/.
One socket connection per session, shared across all tests.
"""

import json
import os
import re
import sys
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from upakarana.engine.client import Client, DEFAULT_SOCKET
from upakarana.testing.gates import gate_from_reason, description_from_reason

_CACHE_DIR = Path(__file__).parent / ".pytest_cache" / "vyakarana"


# ── options ────────────────────────────────────────────────────────────────────


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


# ── recording client ───────────────────────────────────────────────────────────


class RecordingClient:
    """Wraps Client to record every query/response pair per test."""

    def __init__(self, client: Client):
        self._client = client
        self._calls: list[dict] = []

    def _server_us(self) -> int:
        """Server-side elapsed_us from last call (excludes queue wait)."""
        return getattr(self._client, "_last_elapsed_us", 0)

    def eval(self, expr: str) -> Any:
        error = None
        result = None
        try:
            result = self._client.eval(expr)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append({
                "method": "eval", "input": expr, "output": result,
                "elapsed_us": self._server_us(), "error": error,
            })
        return result

    def ask(self, question: str, session_id: str = "test") -> str:
        error = None
        result = None
        try:
            result = self._client.ask(question, session_id=session_id)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append({
                "method": "ask", "input": question, "session_id": session_id,
                "output": result, "elapsed_us": self._server_us(),
                "error": error,
            })
        return result

    def walk(self, node: str, relation: str) -> list:
        error = None
        result = None
        try:
            result = self._client.walk(node, relation)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append({
                "method": "walk", "input": f'{node} "{relation}"', "output": result,
                "elapsed_us": self._server_us(), "error": error,
            })
        return result

    def walk_in(self, node: str, relation: str) -> list:
        error = None
        result = None
        try:
            result = self._client.walk_in(node, relation)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append({
                "method": "walk_in", "input": f'{node} "{relation}"', "output": result,
                "elapsed_us": self._server_us(), "error": error,
            })
        return result

    def answer(self, sentence: str) -> str:
        error = None
        result = None
        try:
            result = self._client.answer(sentence)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append({
                "method": "answer", "input": sentence, "output": result,
                "elapsed_us": self._server_us(), "error": error,
            })
        return result

    def bqg(self, sentence: str) -> Any:
        error = None
        result = None
        try:
            result = self._client.bqg(sentence)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append({
                "method": "bqg", "input": sentence, "output": result,
                "elapsed_us": self._server_us(), "error": error,
            })
        return result

    def raw_bqg(self, sentence: str) -> Any:
        error = None
        result = None
        try:
            result = self._client.raw_bqg(sentence)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append({
                "method": "raw_bqg", "input": sentence, "output": result,
                "elapsed_us": self._server_us(), "error": error,
            })
        return result

    def elapsed_us(self, expr: str) -> tuple[Any, int]:
        error = None
        result, us = None, 0
        try:
            result, us = self._client.elapsed_us(expr)
        except Exception as e:
            error = str(e)
            raise
        finally:
            self._calls.append({
                "method": "elapsed_us", "input": expr, "output": result,
                "elapsed_us": us, "error": error,
            })
        return result, us

    def elapsed_ms(self, expr: str) -> tuple[Any, int]:
        result, us = self.elapsed_us(expr)
        return result, us // 1000

    def __getattr__(self, name):
        return getattr(self._client, name)


# ── cache helpers ──────────────────────────────────────────────────────────────


def _cache_dir() -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR


def _safe_node_id(node_id: str) -> str:
    return (
        node_id.replace("/", "__").replace("::", "__")
        .replace("[", "_").replace("]", "")
    )


# ── fixtures ───────────────────────────────────────────────────────────────────

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
    assert _recorder is not None
    _recorder._calls = []
    t0 = time.monotonic()
    yield _recorder
    duration = time.monotonic() - t0
    if not request.config.getoption("--no-cache", default=False):
        _write_cache(request, _recorder._calls, duration)


# ── cache writer ───────────────────────────────────────────────────────────────


def _write_cache(request, calls: list[dict], duration: float) -> None:
    node_id = request.node.nodeid
    outcome = getattr(request.node, "_last_outcome", "unknown")
    xfail_meta = getattr(request.node, "_xfail_meta", None)
    entry = {
        "test": node_id, "outcome": outcome, "calls": calls,
        "failure": None, "duration": round(duration, 3),
    }
    if xfail_meta:
        entry["xfail"] = xfail_meta
    cache_file = _cache_dir() / (_safe_node_id(node_id) + ".json")
    try:
        cache_file.write_text(json.dumps(entry, indent=2, default=str))
    except Exception:
        pass


# ── hook: capture outcome ──────────────────────────────────────────────────────


def _xfail_info(item) -> dict:
    marker = item.get_closest_marker("xfail")
    if not marker:
        return {}
    reason = marker.kwargs.get("reason", "") or (marker.args[0] if marker.args else "")
    strict = marker.kwargs.get("strict", False)
    gate = description_from_reason(reason)
    if not gate:
        gate = f"other:{item.fspath.basename.replace('.py', '')}"
    return {
        "reason": reason, "strict": strict, "gate": gate,
        "file": str(item.fspath), "line": item.function.__code__.co_firstlineno,
    }


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    cache_file = _CACHE_DIR / (_safe_node_id(item.nodeid) + ".json")

    if rep.when == "call":
        if rep.passed and hasattr(rep, "wasxfail"):
            item._last_outcome = "xpassed"
            item._xfail_meta = _xfail_info(item)
            return
        if rep.skipped and hasattr(rep, "wasxfail"):
            item._last_outcome = "xfailed"
            item._xfail_meta = _xfail_info(item)
            return
        item._last_outcome = rep.outcome
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
            item._last_outcome = (
                "xfailed" if getattr(rep, "wasxfail", False) else "skipped"
            )
            if item._last_outcome == "xfailed":
                item._xfail_meta = _xfail_info(item)


def _extract_failure(rep) -> dict:
    msg = str(rep.longrepr) if rep.longrepr else ""
    expected, got = "", ""
    m = re.search(r"expected[:\s]+['\"]?([^'\"]+)['\"]?\s+in\s+['\"]?(.{0,120})", msg)
    if m:
        expected = m.group(1).strip()
        got = m.group(2).strip()
    else:
        m2 = re.search(r'assert\s+["\'](.+?)["\']\s+in\s+(\w+)', msg)
        if m2:
            expected = m2.group(1)
    last_call = _recorder._calls[-1] if _recorder and _recorder._calls else None
    return {
        "expected": expected, "got": got,
        "message": msg[:500], "last_call": last_call,
    }


# ── session summary ────────────────────────────────────────────────────────────


def pytest_sessionstart(session):
    """Wipe stale cache entries so only current-run results remain."""
    try:
        if _CACHE_DIR.exists():
            for f in _CACHE_DIR.glob("*.json"):
                f.unlink()
    except Exception:
        pass


def pytest_sessionfinish(session, exitstatus):
    try:
        cache_dir = _CACHE_DIR
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

        counts = {k: 0 for k in ("passed", "failed", "error", "xfailed", "xpassed", "skipped", "unknown")}
        for e in entries:
            k = e.get("outcome", "unknown")
            counts[k] = counts.get(k, 0) + 1

        failed_tests = [
            {
                "test": e["test"],
                "failure": e.get("failure") or {},
                "calls": len(e.get("calls", [])),
                "duration": e.get("duration", 0),
            }
            for e in entries if e.get("outcome") in ("failed", "error")
        ]

        summary = {
            "total": len(entries),
            "passed": counts["passed"],
            "failed": counts["failed"] + counts["error"],
            "xfailed": counts["xfailed"],
            "xpassed": counts["xpassed"],
            "skipped": counts["skipped"],
            "failed_tests": failed_tests,
            "slow_tests": sorted(
                [{"test": e["test"], "duration": e.get("duration", 0)}
                 for e in entries if e.get("duration", 0) > 0.5],
                key=lambda x: x["duration"], reverse=True
            )[:20],
        }
        (cache_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    except Exception:
        pass
