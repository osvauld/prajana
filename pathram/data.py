"""data.py — JSON file storage + in-memory indexes for pathram.

All documentation state lives in pathram/data/*.json files.
On startup, everything is loaded into a State object with indexes.
On mutation, the affected JSON file is rewritten.
"""

import json
import re
from collections import defaultdict, OrderedDict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

COLLECTIONS = ["docs", "entries", "sessions", "baselines", "ops", "refs"]


class State:
    """In-memory documentation state with indexes."""

    def __init__(self):
        self.docs = []
        self.entries = []
        self.sessions = []
        self.baselines = []
        self.ops = []
        self.refs = []
        # Indexes
        self.by_id = {}          # entry id -> entry
        self.by_doc = {}         # doc id -> [entries] ordered by position
        self.by_tag = defaultdict(list)   # tag -> [entries]
        self.by_type = defaultdict(list)  # type -> [entries]
        self.by_session = defaultdict(list)  # session id -> [entries]
        self.doc_by_id = {}      # doc id -> doc
        self.ref_from = defaultdict(list)  # entry id -> [outgoing refs]
        self.ref_to = defaultdict(list)    # entry id -> [incoming refs]
        self._dirty = set()      # which collections need saving

    def rebuild_indexes(self):
        """Rebuild all indexes from raw data."""
        self.by_id.clear()
        self.by_doc.clear()
        self.by_tag.clear()
        self.by_type.clear()
        self.by_session.clear()
        self.doc_by_id.clear()
        self.ref_from.clear()
        self.ref_to.clear()

        for doc in self.docs:
            self.doc_by_id[doc["id"]] = doc
            self.by_doc[doc["id"]] = []

        for entry in self.entries:
            self._index_entry(entry)

        # Sort by_doc lists by position
        for doc_id in self.by_doc:
            self.by_doc[doc_id].sort(key=lambda e: e.get("position", 0))

        for ref in self.refs:
            self.ref_from[ref["from_id"]].append(ref)
            self.ref_to[ref["to_id"]].append(ref)

    def _index_entry(self, entry):
        """Add a single entry to all indexes."""
        eid = entry["id"]
        self.by_id[eid] = entry
        doc_id = entry.get("doc_id")
        if doc_id:
            if doc_id not in self.by_doc:
                self.by_doc[doc_id] = []
            self.by_doc[doc_id].append(entry)
        tag = entry.get("tag", "active")
        self.by_tag[tag].append(entry)
        etype = entry.get("type", "section")
        self.by_type[etype].append(entry)
        sid = entry.get("session_id")
        if sid is not None:
            self.by_session[sid].append(entry)

    def _reindex_entry(self, entry):
        """Remove entry from indexes and re-add it."""
        eid = entry["id"]
        # Remove from tag index
        for tag, lst in list(self.by_tag.items()):
            self.by_tag[tag] = [e for e in lst if e["id"] != eid]
        # Remove from type index
        for t, lst in list(self.by_type.items()):
            self.by_type[t] = [e for e in lst if e["id"] != eid]
        # Remove from session index
        for s, lst in list(self.by_session.items()):
            self.by_session[s] = [e for e in lst if e["id"] != eid]
        # Remove from doc index
        doc_id = entry.get("doc_id")
        if doc_id and doc_id in self.by_doc:
            self.by_doc[doc_id] = [e for e in self.by_doc[doc_id] if e["id"] != eid]
        # Re-add
        self.by_id[eid] = entry
        if doc_id and doc_id in self.by_doc:
            self.by_doc[doc_id].append(entry)
            self.by_doc[doc_id].sort(key=lambda e: e.get("position", 0))
        tag = entry.get("tag", "active")
        self.by_tag[tag].append(entry)
        etype = entry.get("type", "section")
        self.by_type[etype].append(entry)
        sid = entry.get("session_id")
        if sid is not None:
            self.by_session[sid].append(entry)

    def mark_dirty(self, *collections):
        self._dirty.update(collections)


def ensure_data_dir(data_dir=None):
    """Create data directory with empty JSON files if needed."""
    d = Path(data_dir) if data_dir else DATA_DIR
    d.mkdir(parents=True, exist_ok=True)
    for name in COLLECTIONS:
        p = d / f"{name}.json"
        if not p.exists():
            p.write_text("[]")
    return d


def load(data_dir=None):
    """Load all JSON files into a State object."""
    d = Path(data_dir) if data_dir else DATA_DIR
    state = State()

    for name in COLLECTIONS:
        p = d / f"{name}.json"
        if p.exists():
            try:
                data = json.loads(p.read_text())
            except (json.JSONDecodeError, OSError):
                data = []
            setattr(state, name, data)

    state.rebuild_indexes()
    return state


def save(state, data_dir=None):
    """Write dirty collections back to JSON files."""
    d = Path(data_dir) if data_dir else DATA_DIR
    d.mkdir(parents=True, exist_ok=True)

    to_save = state._dirty if state._dirty else set(COLLECTIONS)
    for name in to_save:
        p = d / f"{name}.json"
        data = getattr(state, name, [])
        p.write_text(json.dumps(data, indent=2, default=str) + "\n")

    state._dirty.clear()


def now_iso():
    """Current datetime as ISO string."""
    return datetime.now().isoformat(timespec="seconds")
