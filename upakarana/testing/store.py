"""store.py — LMDB-backed test result store.

Tables:
  meta        — "last_run", "prev_run" → {v: run_id}; "run_count" → {v: N}
  runs        — {run_id} → {timestamp, total, passed, failed, xfailed, xpassed, skipped}
  results     — {run_id}||{test_id} → {outcome, duration, gate, layer, calls_count}
  traces      — {run_id}||{test_id} → {calls, failure}  (last 2 runs only)
  idx_outcome — {outcome}||{run_id}||{test_id} → b""
  idx_gate    — {gate}||{run_id}||{test_id} → b""

Trace retention: exactly 2 runs. begin_run() prunes any traces whose run_id
is not in {old last_run, new run_id} before writing the new run's traces.
"""

import time
from pathlib import Path

import lmdb
import msgpack

from upakarana.paths import TESTS_STORE_DIR

TABLES = ["meta", "runs", "results", "traces", "idx_outcome", "idx_gate"]
_SEP = "||"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _open_env():
    TESTS_STORE_DIR.mkdir(parents=True, exist_ok=True)
    env = lmdb.open(
        str(TESTS_STORE_DIR),
        max_dbs=len(TABLES),
        map_size=64 * 1024 * 1024,
        subdir=True,
    )
    dbs = {name: env.open_db(name.encode(), create=True) for name in TABLES}
    return env, dbs


def _pack(value):
    return msgpack.packb(value, use_bin_type=True)


def _unpack(raw):
    if raw is None:
        return None
    return msgpack.unpackb(raw, raw=False)


def _get_meta(txn, db, key):
    raw = txn.get(key.encode(), db=db)
    r = _unpack(raw)
    return r["v"] if r else None


def _set_meta(txn, db, key, value):
    txn.put(key.encode(), _pack({"v": value}), db=db)


def _layer_from_test_id(test_id):
    """Extract layer name from pytest nodeid. e.g. tests/test_arithmetic.py::foo → arithmetic"""
    part = test_id.split("::")[0].split("/")[-1]
    return part.replace("test_", "").replace(".py", "") if part else "unknown"


def _prune_traces(env, dbs, keep_run_ids):
    """Delete all traces entries whose run_id prefix is not in keep_run_ids."""
    keep = set(keep_run_ids)
    to_delete = []
    with env.begin(db=dbs["traces"]) as txn:
        cursor = txn.cursor()
        if cursor.first():
            for k, _ in cursor:
                key_str = k.decode()
                run_id = key_str.split(_SEP)[0]
                if run_id not in keep:
                    to_delete.append(k)
    if to_delete:
        with env.begin(write=True, db=dbs["traces"]) as txn:
            for k in to_delete:
                txn.delete(k)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def begin_run(partial=False) -> str:
    """Create new run_id and return it.

    partial=True: the run_id is created for trace storage but last_run/prev_run
    meta pointers are NOT rotated. Use this for targeted re-runs (--failed,
    --xfailed) so that last_run_id() keeps pointing to the last full suite run.
    """
    new_run_id = time.strftime("%Y%m%dT%H%M%S")
    env, dbs = _open_env()
    try:
        with env.begin(write=True) as txn:
            old_last = _get_meta(txn, dbs["meta"], "last_run")
            if not partial:
                _set_meta(txn, dbs["meta"], "prev_run", old_last or "")
                _set_meta(txn, dbs["meta"], "last_run", new_run_id)
            n = _get_meta(txn, dbs["meta"], "run_count") or 0
            _set_meta(txn, dbs["meta"], "run_count", n + 1)
            txn.put(
                new_run_id.encode(),
                _pack({"timestamp": new_run_id, "partial": partial, "total": 0,
                       "passed": 0, "failed": 0, "xfailed": 0,
                       "xpassed": 0, "skipped": 0}),
                db=dbs["runs"],
            )
        # Prune traces: keep old_last (prev) and new_run_id (current)
        keep = {r for r in [old_last, new_run_id] if r}
        _prune_traces(env, dbs, keep)
    finally:
        env.close()
    return new_run_id


def record_result(run_id, test_id, outcome, duration, gate, layer, calls, failure):
    """Write compact result + indexes. Write full trace only for current run."""
    env, dbs = _open_env()
    try:
        result_key = f"{run_id}{_SEP}{test_id}".encode()
        compact = {
            "outcome": outcome,
            "duration": round(duration, 3),
            "gate": gate or "",
            "layer": layer or _layer_from_test_id(test_id),
            "calls_count": len(calls) if calls else 0,
        }
        outcome_idx_key = f"{outcome}{_SEP}{run_id}{_SEP}{test_id}".encode()
        gate_idx_key = f"{gate or 'none'}{_SEP}{run_id}{_SEP}{test_id}".encode()

        with env.begin(write=True) as txn:
            txn.put(result_key, _pack(compact), db=dbs["results"])
            txn.put(outcome_idx_key, b"", db=dbs["idx_outcome"])
            txn.put(gate_idx_key, b"", db=dbs["idx_gate"])
            # Always write trace (run_id is always current — prune handles cleanup)
            trace = {"calls": calls or [], "failure": failure}
            txn.put(result_key, _pack(trace), db=dbs["traces"])
    finally:
        env.close()


def finalize_run(run_id, stats: dict):
    """Write final run summary counts."""
    env, dbs = _open_env()
    try:
        with env.begin(write=True) as txn:
            existing_raw = txn.get(run_id.encode(), db=dbs["runs"])
            existing = _unpack(existing_raw) or {}
            existing.update(stats)
            txn.put(run_id.encode(), _pack(existing), db=dbs["runs"])
    finally:
        env.close()


def last_run_id() -> str | None:
    """Return the most recent run_id."""
    env, dbs = _open_env()
    try:
        with env.begin(db=dbs["meta"]) as txn:
            return _get_meta(txn, dbs["meta"], "last_run") or None
    finally:
        env.close()


def query_by_outcome(outcome, run_id=None) -> list:
    """Return list of test_ids with given outcome in run_id (defaults to last run)."""
    run_id = run_id or last_run_id()
    if not run_id:
        return []
    prefix = f"{outcome}{_SEP}{run_id}{_SEP}".encode()
    results = []
    env, dbs = _open_env()
    try:
        with env.begin(db=dbs["idx_outcome"]) as txn:
            cursor = txn.cursor()
            if not cursor.set_range(prefix):
                return results
            for k, _ in cursor:
                if not k.startswith(prefix):
                    break
                # key = outcome||run_id||test_id — extract test_id
                test_id = k.decode()[len(outcome) + len(_SEP) + len(run_id) + len(_SEP):]
                results.append(test_id)
    finally:
        env.close()
    return results


def query_by_gate(gate, run_id=None) -> list:
    """Return list of test_ids with given gate in run_id (defaults to last run)."""
    run_id = run_id or last_run_id()
    if not run_id:
        return []
    prefix = f"{gate}{_SEP}{run_id}{_SEP}".encode()
    results = []
    env, dbs = _open_env()
    try:
        with env.begin(db=dbs["idx_gate"]) as txn:
            cursor = txn.cursor()
            if not cursor.set_range(prefix):
                return results
            for k, _ in cursor:
                if not k.startswith(prefix):
                    break
                test_id = k.decode()[len(gate) + len(_SEP) + len(run_id) + len(_SEP):]
                results.append(test_id)
    finally:
        env.close()
    return results


def get_trace(test_id, run_id=None) -> dict | None:
    """Return full call trace for test_id from run_id (defaults to last run)."""
    run_id = run_id or last_run_id()
    if not run_id:
        return None
    key = f"{run_id}{_SEP}{test_id}".encode()
    env, dbs = _open_env()
    try:
        with env.begin(db=dbs["traces"]) as txn:
            return _unpack(txn.get(key))
    finally:
        env.close()


def get_result(test_id, run_id=None) -> dict | None:
    """Return compact result record for test_id from run_id (defaults to last run)."""
    run_id = run_id or last_run_id()
    if not run_id:
        return None
    key = f"{run_id}{_SEP}{test_id}".encode()
    env, dbs = _open_env()
    try:
        with env.begin(db=dbs["results"]) as txn:
            return _unpack(txn.get(key))
    finally:
        env.close()


def get_run_summary(run_id=None) -> dict | None:
    """Return run summary dict for run_id (defaults to last run)."""
    run_id = run_id or last_run_id()
    if not run_id:
        return None
    env, dbs = _open_env()
    try:
        with env.begin(db=dbs["runs"]) as txn:
            return _unpack(txn.get(run_id.encode()))
    finally:
        env.close()


def load_run_entries(run_id=None) -> list:
    """Return list of result entry dicts for a run (compact + outcome/gate/layer).
    Used by cache.py analysis functions."""
    run_id = run_id or last_run_id()
    if not run_id:
        return []
    prefix = f"{run_id}{_SEP}".encode()
    env, dbs = _open_env()
    entries = []
    try:
        with env.begin(db=dbs["results"]) as txn:
            cursor = txn.cursor()
            if not cursor.set_range(prefix):
                return entries
            for k, v in cursor:
                if not k.startswith(prefix):
                    break
                test_id = k.decode()[len(run_id) + len(_SEP):]
                rec = _unpack(v) or {}
                rec["test"] = test_id
                # Attach trace data if available (calls for timing analysis)
                entries.append(rec)
    finally:
        env.close()
    return entries


def load_run_entries_with_traces(run_id=None) -> list:
    """Return entries with full calls[] attached (for slowest_calls analysis)."""
    run_id = run_id or last_run_id()
    if not run_id:
        return []
    entries = load_run_entries(run_id)
    env, dbs = _open_env()
    try:
        with env.begin(db=dbs["traces"]) as txn:
            for e in entries:
                key = f"{run_id}{_SEP}{e['test']}".encode()
                trace = _unpack(txn.get(key))
                if trace:
                    e["calls"] = trace.get("calls", [])
                    e["failure"] = trace.get("failure")
                else:
                    e.setdefault("calls", [])
                    e.setdefault("failure", None)
    finally:
        env.close()
    return entries


def history(n=10) -> list:
    """Return last n run summaries, newest first."""
    env, dbs = _open_env()
    summaries = []
    try:
        with env.begin(db=dbs["runs"]) as txn:
            cursor = txn.cursor()
            if cursor.last():
                while True:
                    k, v = cursor.item()
                    rec = _unpack(v) or {}
                    rec["run_id"] = k.decode()
                    summaries.append(rec)
                    if len(summaries) >= n or not cursor.prev():
                        break
    finally:
        env.close()
    return summaries
