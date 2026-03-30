"""usage.py — LMDB-backed command usage tracker for pathram2.

Separate from the main pathram.lmdb so tracking writes never block graph writes.
"""

import lmdb
import msgpack
from datetime import datetime
from pathlib import Path

USAGE_PATH = Path(__file__).parent / "data" / "usage.lmdb"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _open(path=None, readonly=False):
    db_path = Path(path) if path else USAGE_PATH
    db_path.mkdir(parents=True, exist_ok=True)
    return lmdb.open(
        str(db_path),
        max_dbs=2,
        map_size=10 * 1024 * 1024,
        subdir=True,
        readonly=readonly,
    )


def track(command: str, path=None):
    """Record one invocation of a pathram2 command."""
    try:
        env = _open(path)
        db = env.open_db(b"commands", create=True)
        with env.begin(write=True, db=db) as txn:
            k = command.encode()
            raw = txn.get(k)
            if raw:
                entry = msgpack.unpackb(raw, raw=False)
            else:
                entry = {"count": 0, "first": _now(), "last": ""}
            entry["count"] += 1
            entry["last"] = _now()
            txn.put(k, msgpack.packb(entry, use_bin_type=True))
        env.close()
    except Exception:
        pass  # never let tracking break the CLI


def report(path=None) -> list[dict]:
    """Return all command counts sorted by frequency."""
    try:
        env = _open(path)
        db = env.open_db(b"commands", create=True)
        results = []
        with env.begin(db=db) as txn:
            cursor = txn.cursor()
            if cursor.first():
                for k, v in cursor:
                    entry = msgpack.unpackb(v, raw=False)
                    results.append({"command": k.decode(), **entry})
        env.close()
        results.sort(key=lambda x: -x["count"])
        return results
    except Exception:
        return []


def reset(path=None):
    """Wipe all usage data."""
    import shutil
    db_path = Path(path) if path else USAGE_PATH
    if db_path.exists():
        shutil.rmtree(db_path)
