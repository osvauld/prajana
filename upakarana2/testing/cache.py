"""cache.py — Test result cache analysis.

Reads from the LMDB store (testing/store.py). Analysis functions operate on
entry lists and are storage-format agnostic — they receive plain dicts.
"""

from collections import defaultdict

from upakarana2.testing.gates import gate_from_reason


def load(run_id=None):
    """Load entries from LMDB store. Returns (summary_dict, entries_list).

    entries_list contains compact records with calls[] attached from traces
    for timing analysis. Falls back to empty if store has no data yet.
    """
    from upakarana2.testing.store import (
        get_run_summary, load_run_entries_with_traces, last_run_id
    )
    rid = run_id or last_run_id()
    if not rid:
        return {}, []
    summary = get_run_summary(rid) or {}
    entries = load_run_entries_with_traces(rid)
    return summary, entries


def history(n=10):
    """Return last n run summaries, newest first."""
    from upakarana2.testing.store import history as store_history
    return store_history(n)


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
            gate = e.get("gate") or gate_from_reason(e.get("xfail_reason", ""))
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
                "elapsed_us": call.get("elapsed_us", call.get("elapsed_ms", 0) * 1000),
            })
    all_calls.sort(key=lambda c: -c["elapsed_us"])
    return all_calls[:top_n]


def slowest_tests(entries, top_n=20):
    """Slowest tests by wall-clock duration."""
    timed = []
    for e in entries:
        dur = e.get("duration", 0)
        call_us = sum(c.get("elapsed_us", c.get("elapsed_ms", 0) * 1000) for c in e.get("calls", []))
        timed.append({
            "test": e.get("test", "?"),
            "duration_s": round(dur, 3),
            "call_us": call_us,
            "calls": len(e.get("calls", [])),
            "outcome": e.get("outcome", "?"),
        })
    timed.sort(key=lambda t: -t["duration_s"])
    return timed[:top_n]


def timing_by_layer(entries):
    """Aggregate timing by test layer (file)."""
    layers = defaultdict(lambda: {"duration_s": 0, "count": 0, "call_us": 0})
    for e in entries:
        layer = e.get("layer") or "unknown"
        layers[layer]["duration_s"] += e.get("duration", 0)
        layers[layer]["count"] += 1
        layers[layer]["call_us"] += sum(
            c.get("elapsed_us", c.get("elapsed_ms", 0) * 1000)
            for c in e.get("calls", [])
        )
    return {k: {**v, "duration_s": round(v["duration_s"], 1)}
            for k, v in sorted(layers.items(), key=lambda x: -x[1]["duration_s"])}


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
