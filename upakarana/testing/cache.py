"""cache.py — Pytest result cache analysis.

Reads .pytest_cache/vyakarana/ entries written by conftest.py.
"""

import json
import os
from collections import defaultdict
from pathlib import Path

from upakarana.paths import TESTS_DIR
from upakarana.testing.gates import gate_from_reason

DEFAULT_CACHE = TESTS_DIR / ".pytest_cache" / "vyakarana"


def load(cache_dir=None):
    """Load cache entries. Returns (summary_dict, entries_list)."""
    d = Path(cache_dir) if cache_dir else DEFAULT_CACHE
    if not d.exists():
        return {}, []

    summary = {}
    summary_path = d / "summary.json"
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text())
        except Exception:
            pass

    entries = []
    for f in sorted(d.iterdir()):
        if f.suffix == ".json" and f.name != "summary.json":
            try:
                entries.append(json.loads(f.read_text()))
            except Exception:
                pass

    return summary, entries


def by_outcome(entries):
    """Group entries by outcome (passed/failed/xfailed/xpassed)."""
    groups = defaultdict(list)
    for e in entries:
        groups[e.get("outcome", "unknown")].append(e)
    return dict(groups)


def failed(entries):
    return [e for e in entries if e.get("outcome") in ("failed", "error")]


def xfailed(entries):
    return [e for e in entries if e.get("outcome") in ("xfailed", "skipped")]


def passed(entries):
    return [e for e in entries if e.get("outcome") == "passed"]


def by_gate(entries):
    """Group xfailed entries by gate."""
    groups = defaultdict(list)
    for e in entries:
        if e.get("outcome") in ("xfailed", "skipped"):
            reason = e.get("xfail_reason", "")
            gate = gate_from_reason(reason)
            groups[gate].append(e)
    return dict(groups)


def slowest_calls(entries, top_n=10):
    """Slowest individual calls across all tests."""
    all_calls = []
    for e in entries:
        for call in e.get("calls", []):
            all_calls.append({
                "test": e.get("test", "?"),
                "method": call.get("method", "?"),
                "input": call.get("input", "")[:80],
                "elapsed_ms": call.get("elapsed_ms", 0),
            })
    all_calls.sort(key=lambda c: -c["elapsed_ms"])
    return all_calls[:top_n]


def summarize(entries):
    """Full summary dict."""
    outcomes = by_outcome(entries)
    gates = by_gate(entries)
    return {
        "total": len(entries),
        "passed": len(outcomes.get("passed", [])),
        "failed": len(outcomes.get("failed", [])),
        "xfailed": len(outcomes.get("xfailed", [])),
        "xpassed": len(outcomes.get("xpassed", [])),
        "gates": {k: len(v) for k, v in sorted(gates.items())},
    }
