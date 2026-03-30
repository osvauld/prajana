"""usage.py — Command usage tracking backed by LMDB.

Tables:
  meta        — "sessions" → {v: N}, "first_use" → {v: "timestamp"}
  commands    — cmd_key → {count, first, last, misses}
  miss_args   — "cmd_key||arg" → {count: N}
  error_types — "cmd_key||error_type" → {count: N}
"""

import time
from pathlib import Path

import lmdb
import msgpack

from upakarana.paths import ROOT

USAGE_DIR = ROOT / "upakarana" / "data" / "usage.lmdb"

TABLES = ["meta", "commands", "miss_args", "error_types"]
_SEP = "||"  # separator between cmd_key and arg in miss_args table


# ---------------------------------------------------------------------------
# Internal DB helpers
# ---------------------------------------------------------------------------

def _open_env():
    USAGE_DIR.mkdir(parents=True, exist_ok=True)
    env = lmdb.open(
        str(USAGE_DIR),
        max_dbs=len(TABLES),
        map_size=32 * 1024 * 1024,
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


def _get_cmd(txn, db, key):
    raw = txn.get(key.encode(), db=db)
    return _unpack(raw)


def _put_cmd(txn, db, key, entry):
    txn.put(key.encode(), _pack(entry), db=db)


def _get_miss_arg(txn, db, cmd_key, arg):
    k = f"{cmd_key}{_SEP}{arg}".encode()
    raw = txn.get(k, db=db)
    return _unpack(raw)


def _put_miss_arg(txn, db, cmd_key, arg, entry):
    k = f"{cmd_key}{_SEP}{arg}".encode()
    txn.put(k, _pack(entry), db=db)


def _scan_table_prefix(env, db, cmd_key):
    """Return list of (suffix, count) for all keys starting with cmd_key||."""
    prefix = f"{cmd_key}{_SEP}".encode()
    results = []
    with env.begin(db=db) as txn:
        cursor = txn.cursor()
        if not cursor.set_range(prefix):
            return results
        for k, v in cursor:
            if not k.startswith(prefix):
                break
            suffix = k.decode()[len(cmd_key) + len(_SEP):]
            entry = _unpack(v)
            results.append((suffix, entry["count"] if entry else 0))
    return results


def _scan_miss_args(env, db, cmd_key):
    return _scan_table_prefix(env, db, cmd_key)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def track(command, action=None):
    """Record one invocation of command [action]."""
    key = f"{command} {action}" if action else command
    now = time.strftime("%Y-%m-%dT%H:%M:%S")

    env, dbs = _open_env()
    try:
        with env.begin(write=True) as txn:
            if _get_meta(txn, dbs["meta"], "first_use") is None:
                _set_meta(txn, dbs["meta"], "first_use", now)

            entry = _get_cmd(txn, dbs["commands"], key)
            if entry is None:
                entry = {"count": 0, "first": now, "last": None, "misses": 0}
            entry["count"] += 1
            entry["last"] = now
            _put_cmd(txn, dbs["commands"], key, entry)
    finally:
        env.close()


def track_miss(command, action=None, arg=None, error_type=None):
    """Record a no-match or error invocation.

    arg        — the specific name/pattern/expression queried (stored in miss_args)
    error_type — the error code from VyakaranaError.code, if applicable (stored in error_types)
    """
    key = f"{command} {action}" if action else command

    env, dbs = _open_env()
    try:
        with env.begin(write=True) as txn:
            entry = _get_cmd(txn, dbs["commands"], key)
            if entry is None:
                return  # track() should have been called first
            entry["misses"] = entry.get("misses", 0) + 1
            _put_cmd(txn, dbs["commands"], key, entry)

            if arg:
                existing = _get_miss_arg(txn, dbs["miss_args"], key, arg)
                cnt = existing["count"] if existing else 0
                _put_miss_arg(txn, dbs["miss_args"], key, arg, {"count": cnt + 1})

            if error_type:
                et_key = f"{key}{_SEP}{error_type}".encode()
                raw = txn.get(et_key, db=dbs["error_types"])
                existing = _unpack(raw)
                cnt = existing["count"] if existing else 0
                txn.put(et_key, _pack({"count": cnt + 1}), db=dbs["error_types"])
    finally:
        env.close()


def bump_session():
    """Increment session counter."""
    env, dbs = _open_env()
    try:
        with env.begin(write=True) as txn:
            n = _get_meta(txn, dbs["meta"], "sessions") or 0
            _set_meta(txn, dbs["meta"], "sessions", n + 1)
    finally:
        env.close()


def report():
    """Return usage report dict."""
    env, dbs = _open_env()
    try:
        # Read all command entries
        commands = {}
        with env.begin(db=dbs["commands"]) as txn:
            cursor = txn.cursor()
            if cursor.first():
                for k, v in cursor:
                    entry = _unpack(v)
                    if entry:
                        commands[k.decode()] = entry

        with env.begin(db=dbs["meta"]) as txn:
            sessions = _get_meta(txn, dbs["meta"], "sessions") or 0
            first_use = _get_meta(txn, dbs["meta"], "first_use")

        by_count = sorted(commands.items(), key=lambda x: -x[1]["count"])
        total_misses = sum(v.get("misses", 0) for v in commands.values())
        miss_commands = [(k, v) for k, v in by_count if v.get("misses", 0) > 0]

        # Fetch top miss args + error types per command
        misses_out = []
        for k, v in sorted(miss_commands, key=lambda x: -x[1]["misses"]):
            top_args = sorted(
                _scan_table_prefix(env, dbs["miss_args"], k),
                key=lambda x: -x[1]
            )[:10]
            error_types = sorted(
                _scan_table_prefix(env, dbs["error_types"], k),
                key=lambda x: -x[1]
            )
            misses_out.append({
                "command": k,
                "misses": v["misses"],
                "count": v["count"],
                "rate": round(v["misses"] / v["count"] * 100, 1) if v["count"] else 0,
                "top_args": top_args,
                "error_types": error_types,
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


def never_used(all_commands):
    """Given a list of all possible commands, return those never invoked."""
    env, dbs = _open_env()
    try:
        with env.begin(db=dbs["commands"]) as txn:
            cursor = txn.cursor()
            used = set()
            if cursor.first():
                for k, _ in cursor:
                    used.add(k.decode())
    finally:
        env.close()
    return sorted(set(all_commands) - used)


