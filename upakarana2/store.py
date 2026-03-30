"""store.py — Centralized LMDB store for upakarana2.

Single LMDB environment at upakarana2/data/upakarana.lmdb with two
namespaced APIs:

    store.usage.track(command, action=None)
    store.usage.track_miss(command, action=None, arg=None, error_type=None)
    store.usage.bump_session()
    store.usage.report() -> dict
    store.usage.never_used(all_commands) -> list

    store.tests.begin_run(partial=False) -> str
    store.tests.record_result(run_id, test_id, outcome, duration, gate, layer, calls, failure)
    store.tests.finalize_run(run_id, stats)
    store.tests.last_run_id() -> str | None
    store.tests.query_by_outcome(outcome, run_id=None) -> list
    store.tests.query_by_gate(gate, run_id=None) -> list
    store.tests.get_trace(test_id, run_id=None) -> dict | None
    store.tests.get_result(test_id, run_id=None) -> dict | None
    store.tests.get_run_summary(run_id=None) -> dict | None
    store.tests.load_run_entries(run_id=None) -> list
    store.tests.load_run_entries_with_traces(run_id=None) -> list
    store.tests.history(n=10) -> list

Sub-databases:
  usage_meta        — sessions, first_use
  usage_commands    — cmd_key → {count, first, last, misses}
  usage_miss_args   — cmd_key||arg → {count}
  usage_error_types — cmd_key||type → {count}
  store_meta        — last_run, prev_run, run_count
  runs              — run_id → {timestamp, partial, total, passed, failed, ...}
  results           — run_id||test_id → {outcome, duration, gate, layer, calls_count}
  traces            — run_id||test_id → {calls, failure}  (last 2 runs only)
  idx_outcome       — outcome||run_id||test_id → b""
  idx_gate          — gate||run_id||test_id → b""
"""

import time
from pathlib import Path

import lmdb
import msgpack

from upakarana2.paths import STORE_PATH

_TABLES = [
    "usage_meta", "usage_commands", "usage_miss_args", "usage_error_types",
    "store_meta", "runs", "results", "traces", "idx_outcome", "idx_gate",
]
_SEP = "||"


# ---------------------------------------------------------------------------
# Shared LMDB helpers
# ---------------------------------------------------------------------------

def _open_env():
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    env = lmdb.open(
        str(STORE_PATH),
        max_dbs=len(_TABLES),
        map_size=128 * 1024 * 1024,
        subdir=True,
    )
    dbs = {name: env.open_db(name.encode(), create=True) for name in _TABLES}
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


def _scan_prefix(env, db, prefix_str):
    """Return list of (suffix, unpacked_value) for all keys starting with prefix_str."""
    prefix = prefix_str.encode()
    results = []
    with env.begin(db=db) as txn:
        cursor = txn.cursor()
        if not cursor.set_range(prefix):
            return results
        for k, v in cursor:
            if not k.startswith(prefix):
                break
            suffix = k.decode()[len(prefix_str):]
            results.append((suffix, _unpack(v)))
    return results


# ---------------------------------------------------------------------------
# usage namespace
# ---------------------------------------------------------------------------

class _Usage:
    """Usage tracking API: store.usage.*"""

    def track(self, command, action=None):
        """Record one invocation of command [action]."""
        key = f"{command} {action}" if action else command
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        env, dbs = _open_env()
        try:
            with env.begin(write=True) as txn:
                if _get_meta(txn, dbs["usage_meta"], "first_use") is None:
                    _set_meta(txn, dbs["usage_meta"], "first_use", now)
                raw = txn.get(key.encode(), db=dbs["usage_commands"])
                entry = _unpack(raw) or {"count": 0, "first": now, "last": None, "misses": 0}
                entry["count"] += 1
                entry["last"] = now
                txn.put(key.encode(), _pack(entry), db=dbs["usage_commands"])
        finally:
            env.close()

    def track_miss(self, command, action=None, arg=None, error_type=None):
        """Record a no-match or error invocation."""
        key = f"{command} {action}" if action else command
        env, dbs = _open_env()
        try:
            with env.begin(write=True) as txn:
                raw = txn.get(key.encode(), db=dbs["usage_commands"])
                entry = _unpack(raw)
                if entry is None:
                    return
                entry["misses"] = entry.get("misses", 0) + 1
                txn.put(key.encode(), _pack(entry), db=dbs["usage_commands"])
                if arg:
                    mk = f"{key}{_SEP}{arg}".encode()
                    r = _unpack(txn.get(mk, db=dbs["usage_miss_args"]))
                    txn.put(mk, _pack({"count": (r["count"] if r else 0) + 1}),
                            db=dbs["usage_miss_args"])
                if error_type:
                    ek = f"{key}{_SEP}{error_type}".encode()
                    r = _unpack(txn.get(ek, db=dbs["usage_error_types"]))
                    txn.put(ek, _pack({"count": (r["count"] if r else 0) + 1}),
                            db=dbs["usage_error_types"])
        finally:
            env.close()

    def bump_session(self):
        """Increment session counter."""
        env, dbs = _open_env()
        try:
            with env.begin(write=True) as txn:
                n = _get_meta(txn, dbs["usage_meta"], "sessions") or 0
                _set_meta(txn, dbs["usage_meta"], "sessions", n + 1)
        finally:
            env.close()

    def report(self):
        """Return usage report dict."""
        env, dbs = _open_env()
        try:
            commands = {}
            with env.begin(db=dbs["usage_commands"]) as txn:
                cursor = txn.cursor()
                if cursor.first():
                    for k, v in cursor:
                        e = _unpack(v)
                        if e:
                            commands[k.decode()] = e

            with env.begin(db=dbs["usage_meta"]) as txn:
                sessions = _get_meta(txn, dbs["usage_meta"], "sessions") or 0
                first_use = _get_meta(txn, dbs["usage_meta"], "first_use")

            by_count = sorted(commands.items(), key=lambda x: -x[1]["count"])
            total_misses = sum(v.get("misses", 0) for v in commands.values())
            miss_commands = [(k, v) for k, v in by_count if v.get("misses", 0) > 0]

            misses_out = []
            for k, v in sorted(miss_commands, key=lambda x: -x[1]["misses"]):
                top_args = sorted(
                    _scan_prefix(env, dbs["usage_miss_args"], f"{k}{_SEP}"),
                    key=lambda x: -(x[1]["count"] if x[1] else 0)
                )[:10]
                error_types = sorted(
                    _scan_prefix(env, dbs["usage_error_types"], f"{k}{_SEP}"),
                    key=lambda x: -(x[1]["count"] if x[1] else 0)
                )
                misses_out.append({
                    "command": k, "misses": v["misses"], "count": v["count"],
                    "rate": round(v["misses"] / v["count"] * 100, 1) if v["count"] else 0,
                    "top_args": [(s, d["count"] if d else 0) for s, d in top_args],
                    "error_types": [(s, d["count"] if d else 0) for s, d in error_types],
                })

            return {
                "sessions": sessions,
                "first_use": first_use,
                "total_invocations": sum(v["count"] for v in commands.values()),
                "total_misses": total_misses,
                "unique_commands": len(commands),
                "top": [{"command": k, "count": v["count"], "last": v["last"]}
                        for k, v in by_count[:20]],
                "misses": misses_out,
                "all": {k: v["count"] for k, v in by_count},
            }
        finally:
            env.close()

    def never_used(self, all_commands):
        """Return commands from all_commands that have never been invoked."""
        env, dbs = _open_env()
        try:
            with env.begin(db=dbs["usage_commands"]) as txn:
                cursor = txn.cursor()
                used = set()
                if cursor.first():
                    for k, _ in cursor:
                        used.add(k.decode())
        finally:
            env.close()
        return sorted(set(all_commands) - used)


# ---------------------------------------------------------------------------
# tests namespace
# ---------------------------------------------------------------------------

def _layer_from_test_id(test_id):
    part = test_id.split("::")[0].split("/")[-1]
    return part.replace("test_", "").replace(".py", "") if part else "unknown"


def _prune_traces(env, dbs, keep_run_ids):
    """Delete trace entries whose run_id is not in keep_run_ids."""
    keep = set(keep_run_ids)
    to_delete = []
    with env.begin(db=dbs["traces"]) as txn:
        cursor = txn.cursor()
        if cursor.first():
            for k, _ in cursor:
                run_id = k.decode().split(_SEP)[0]
                if run_id not in keep:
                    to_delete.append(k)
    if to_delete:
        with env.begin(write=True, db=dbs["traces"]) as txn:
            for k in to_delete:
                txn.delete(k)


class _Tests:
    """Test result store API: store.tests.*"""

    def begin_run(self, partial=False) -> str:
        """Create a new run_id.

        partial=True: creates the run entry but does NOT rotate last_run/prev_run
        meta pointers. Use for targeted re-runs (--failed, --xfailed) so that
        last_run_id() keeps pointing to the last full suite run.
        """
        new_run_id = time.strftime("%Y%m%dT%H%M%S")
        env, dbs = _open_env()
        try:
            with env.begin(write=True) as txn:
                old_last = _get_meta(txn, dbs["store_meta"], "last_run")
                if not partial:
                    _set_meta(txn, dbs["store_meta"], "prev_run", old_last or "")
                    _set_meta(txn, dbs["store_meta"], "last_run", new_run_id)
                n = _get_meta(txn, dbs["store_meta"], "run_count") or 0
                _set_meta(txn, dbs["store_meta"], "run_count", n + 1)
                txn.put(
                    new_run_id.encode(),
                    _pack({"timestamp": new_run_id, "partial": partial, "total": 0,
                           "passed": 0, "failed": 0, "xfailed": 0,
                           "xpassed": 0, "skipped": 0}),
                    db=dbs["runs"],
                )
            keep = {r for r in [old_last, new_run_id] if r}
            _prune_traces(env, dbs, keep)
        finally:
            env.close()
        return new_run_id

    def record_result(self, run_id, test_id, outcome, duration, gate, layer, calls, failure):
        """Write compact result + index entries + full trace."""
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
            outcome_idx = f"{outcome}{_SEP}{run_id}{_SEP}{test_id}".encode()
            gate_idx = f"{gate or 'none'}{_SEP}{run_id}{_SEP}{test_id}".encode()
            with env.begin(write=True) as txn:
                txn.put(result_key, _pack(compact), db=dbs["results"])
                txn.put(outcome_idx, b"", db=dbs["idx_outcome"])
                txn.put(gate_idx, b"", db=dbs["idx_gate"])
                txn.put(result_key, _pack({"calls": calls or [], "failure": failure}),
                        db=dbs["traces"])
        finally:
            env.close()

    def finalize_run(self, run_id, stats: dict):
        """Write final summary counts into the run entry."""
        env, dbs = _open_env()
        try:
            with env.begin(write=True) as txn:
                existing = _unpack(txn.get(run_id.encode(), db=dbs["runs"])) or {}
                existing.update(stats)
                txn.put(run_id.encode(), _pack(existing), db=dbs["runs"])
        finally:
            env.close()

    def last_run_id(self) -> "str | None":
        """Return the most recent full-suite run_id."""
        env, dbs = _open_env()
        try:
            with env.begin(db=dbs["store_meta"]) as txn:
                return _get_meta(txn, dbs["store_meta"], "last_run") or None
        finally:
            env.close()

    def query_by_outcome(self, outcome, run_id=None) -> list:
        """Return test_ids with given outcome in run_id (defaults to last run)."""
        run_id = run_id or self.last_run_id()
        if not run_id:
            return []
        prefix = f"{outcome}{_SEP}{run_id}{_SEP}"
        env, dbs = _open_env()
        results = []
        try:
            with env.begin(db=dbs["idx_outcome"]) as txn:
                cursor = txn.cursor()
                pfx = prefix.encode()
                if not cursor.set_range(pfx):
                    return results
                for k, _ in cursor:
                    if not k.startswith(pfx):
                        break
                    results.append(k.decode()[len(prefix):])
        finally:
            env.close()
        return results

    def query_by_gate(self, gate, run_id=None) -> list:
        """Return test_ids with given gate in run_id (defaults to last run)."""
        run_id = run_id or self.last_run_id()
        if not run_id:
            return []
        prefix = f"{gate}{_SEP}{run_id}{_SEP}"
        env, dbs = _open_env()
        results = []
        try:
            with env.begin(db=dbs["idx_gate"]) as txn:
                cursor = txn.cursor()
                pfx = prefix.encode()
                if not cursor.set_range(pfx):
                    return results
                for k, _ in cursor:
                    if not k.startswith(pfx):
                        break
                    results.append(k.decode()[len(prefix):])
        finally:
            env.close()
        return results

    def get_trace(self, test_id, run_id=None) -> "dict | None":
        run_id = run_id or self.last_run_id()
        if not run_id:
            return None
        key = f"{run_id}{_SEP}{test_id}".encode()
        env, dbs = _open_env()
        try:
            with env.begin(db=dbs["traces"]) as txn:
                return _unpack(txn.get(key))
        finally:
            env.close()

    def get_result(self, test_id, run_id=None) -> "dict | None":
        run_id = run_id or self.last_run_id()
        if not run_id:
            return None
        key = f"{run_id}{_SEP}{test_id}".encode()
        env, dbs = _open_env()
        try:
            with env.begin(db=dbs["results"]) as txn:
                return _unpack(txn.get(key))
        finally:
            env.close()

    def get_run_summary(self, run_id=None) -> "dict | None":
        run_id = run_id or self.last_run_id()
        if not run_id:
            return None
        env, dbs = _open_env()
        try:
            with env.begin(db=dbs["runs"]) as txn:
                return _unpack(txn.get(run_id.encode()))
        finally:
            env.close()

    def load_run_entries(self, run_id=None) -> list:
        """Compact result entries for all tests in a run."""
        run_id = run_id or self.last_run_id()
        if not run_id:
            return []
        prefix = f"{run_id}{_SEP}"
        env, dbs = _open_env()
        entries = []
        try:
            with env.begin(db=dbs["results"]) as txn:
                cursor = txn.cursor()
                pfx = prefix.encode()
                if not cursor.set_range(pfx):
                    return entries
                for k, v in cursor:
                    if not k.startswith(pfx):
                        break
                    test_id = k.decode()[len(prefix):]
                    rec = _unpack(v) or {}
                    rec["test"] = test_id
                    entries.append(rec)
        finally:
            env.close()
        return entries

    def load_run_entries_with_traces(self, run_id=None) -> list:
        """Entries with full calls[] attached (for analysis and find_false_positives)."""
        run_id = run_id or self.last_run_id()
        if not run_id:
            return []
        entries = self.load_run_entries(run_id)
        prefix = f"{run_id}{_SEP}"
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

    def history(self, n=10) -> list:
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


# ---------------------------------------------------------------------------
# Module-level singletons — import as: from upakarana2 import store; store.usage.track(...)
# ---------------------------------------------------------------------------

usage = _Usage()
tests = _Tests()
