"""storage.py — LMDB persistence layer.

Thin wrapper over lmdb providing named tables (sub-databases),
msgpack serialization, and prefix scans. All graph state lives here.
"""

import lmdb
import msgpack
from pathlib import Path

# Default database path
DEFAULT_PATH = Path(__file__).parent / "data" / "pathram.lmdb"

# Named sub-databases
TABLES = [
    "nodes",          # id → Node dict
    "edges",          # edge_key → Edge dict
    "idx_type",       # type:id → b""  (prefix scan by type)
    "idx_tag",        # tag:id → b""
    "idx_edges_out",  # source:edge_key → b""
    "idx_edges_in",   # target:edge_key → b""
    "idx_edges_rel",  # relation:edge_key → b""
    "idx_time",       # created_at:id → b""
]


class Storage:
    """LMDB-backed key-value store with named tables."""

    def __init__(self, path: str | Path | None = None, max_dbs: int = 16,
                 map_size: int = 100 * 1024 * 1024):
        self.path = Path(path) if path else DEFAULT_PATH
        self.path.mkdir(parents=True, exist_ok=True)
        self.env = lmdb.open(
            str(self.path),
            max_dbs=max_dbs,
            map_size=map_size,
            subdir=True,
        )
        self._dbs = {}
        for name in TABLES:
            self._dbs[name] = self.env.open_db(name.encode(), create=True)

    def _db(self, table: str):
        return self._dbs[table]

    # --- Core operations ---

    def put(self, table: str, key: str, value: dict | None = None):
        """Store a key-value pair. If value is None, stores empty bytes (for indexes)."""
        with self.env.begin(write=True, db=self._db(table)) as txn:
            k = key.encode()
            v = msgpack.packb(value, use_bin_type=True) if value is not None else b""
            txn.put(k, v)

    def get(self, table: str, key: str) -> dict | None:
        """Retrieve a value by key. Returns None if not found."""
        with self.env.begin(db=self._db(table)) as txn:
            raw = txn.get(key.encode())
            if raw is None:
                return None
            if raw == b"":
                return {}
            return msgpack.unpackb(raw, raw=False)

    def delete(self, table: str, key: str) -> bool:
        """Delete a key. Returns True if it existed."""
        with self.env.begin(write=True, db=self._db(table)) as txn:
            return txn.delete(key.encode())

    def exists(self, table: str, key: str) -> bool:
        """Check if a key exists."""
        with self.env.begin(db=self._db(table)) as txn:
            return txn.get(key.encode()) is not None

    # --- Scan operations ---

    def scan(self, table: str, prefix: str = "") -> list[str]:
        """Return all keys in a table matching a prefix."""
        keys = []
        prefix_bytes = prefix.encode()
        with self.env.begin(db=self._db(table)) as txn:
            cursor = txn.cursor()
            if prefix:
                if not cursor.set_range(prefix_bytes):
                    return keys
            else:
                if not cursor.first():
                    return keys
            for k, _ in cursor:
                if prefix and not k.startswith(prefix_bytes):
                    break
                keys.append(k.decode())
        return keys

    def scan_values(self, table: str, prefix: str = "") -> list[dict]:
        """Return all values in a table matching a prefix."""
        values = []
        prefix_bytes = prefix.encode()
        with self.env.begin(db=self._db(table)) as txn:
            cursor = txn.cursor()
            if prefix:
                if not cursor.set_range(prefix_bytes):
                    return values
            else:
                if not cursor.first():
                    return values
            for k, v in cursor:
                if prefix and not k.startswith(prefix_bytes):
                    break
                if v and v != b"":
                    values.append(msgpack.unpackb(v, raw=False))
        return values

    def keys(self, table: str) -> list[str]:
        """Return all keys in a table."""
        return self.scan(table)

    def count(self, table: str) -> int:
        """Count entries in a table."""
        with self.env.begin(db=self._db(table)) as txn:
            return txn.stat()["entries"]

    # --- Batch operations ---

    def put_batch(self, table: str, items: list[tuple[str, dict | None]]):
        """Store multiple key-value pairs in a single transaction."""
        db = self._db(table)
        with self.env.begin(write=True, db=db) as txn:
            for key, value in items:
                k = key.encode()
                v = msgpack.packb(value, use_bin_type=True) if value is not None else b""
                txn.put(k, v)

    def delete_batch(self, table: str, keys: list[str]):
        """Delete multiple keys in a single transaction."""
        db = self._db(table)
        with self.env.begin(write=True, db=db) as txn:
            for key in keys:
                txn.delete(key.encode())

    # --- Lifecycle ---

    def close(self):
        """Close the environment."""
        self.env.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
