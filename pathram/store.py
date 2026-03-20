"""store.py — Write operations for patra state.

Every mutation appends to the ops log, updates in-memory state,
and marks the affected collections dirty for saving.
"""

from pathram.data import now_iso, save


def _next_id(state, doc_id, type_prefix):
    """Generate next entry ID within a doc."""
    existing = [e["id"] for e in state.entries if e.get("doc_id") == doc_id]
    n = len(existing) + 1
    return f"{doc_id}.{type_prefix}-{n}"


def _log_op(state, op, entry_id, details=None):
    """Append to ops log."""
    state.ops.append({
        "op": op,
        "entry_id": entry_id,
        "at": now_iso(),
        "details": details,
    })
    state.mark_dirty("ops")


# --- Documents ---

def create_doc(state, doc_id, title, position=None, tag="active", data_dir=None):
    """Create a document container."""
    if position is None:
        positions = [d.get("position", 0) for d in state.docs]
        position = max(positions) + 1 if positions else 1.0

    doc = {
        "id": doc_id,
        "title": title,
        "tag": tag,
        "position": float(position),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    state.docs.append(doc)
    state.doc_by_id[doc_id] = doc
    state.by_doc[doc_id] = []
    _log_op(state, "create_doc", doc_id, {"title": title})
    state.mark_dirty("docs")
    save(state, data_dir)
    return doc


# --- Entries ---

def create_entry(state, doc_id, entry_type, title, body="",
                 tag="active", position=None, level=2,
                 session_id=None, meta=None, entry_id=None, data_dir=None):
    """Create a content entry within a document."""
    if entry_id is None:
        entry_id = _next_id(state, doc_id, entry_type)

    if position is None:
        doc_entries = state.by_doc.get(doc_id, [])
        if doc_entries:
            position = max(e.get("position", 0) for e in doc_entries) + 1.0
        else:
            position = 1.0

    entry = {
        "id": entry_id,
        "doc_id": doc_id,
        "type": entry_type,
        "title": title,
        "body": body,
        "tag": tag,
        "tag_pointer": None,
        "position": float(position),
        "level": level,
        "session_id": session_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "meta": meta or {},
    }
    state.entries.append(entry)
    state._index_entry(entry)
    # Re-sort doc entries
    if doc_id in state.by_doc:
        state.by_doc[doc_id].sort(key=lambda e: e.get("position", 0))

    _log_op(state, "create_entry", entry_id, {"type": entry_type, "title": title})
    state.mark_dirty("entries")
    save(state, data_dir)
    return entry


def update_entry(state, entry_id, body=None, title=None, tag=None,
                 meta=None, position=None, session_id=None, data_dir=None):
    """Update fields on an existing entry."""
    entry = state.by_id.get(entry_id)
    if not entry:
        raise KeyError(f"Entry not found: {entry_id}")

    if body is not None:
        entry["body"] = body
    if title is not None:
        entry["title"] = title
    if tag is not None:
        entry["tag"] = tag
    if meta is not None:
        entry["meta"].update(meta)
    if position is not None:
        entry["position"] = float(position)
    if session_id is not None:
        entry["session_id"] = session_id

    entry["updated_at"] = now_iso()
    state._reindex_entry(entry)

    _log_op(state, "update_entry", entry_id,
            {"fields": [k for k in ["body", "title", "tag", "meta", "position"]
                        if locals().get(k) is not None]})
    state.mark_dirty("entries")
    save(state, data_dir)
    return entry


def update_tag(state, entry_id, tag, pointer=None, data_dir=None):
    """Change an entry's lifecycle tag, optionally with pointer."""
    entry = state.by_id.get(entry_id)
    if not entry:
        raise KeyError(f"Entry not found: {entry_id}")

    old_tag = entry.get("tag")
    entry["tag"] = tag
    entry["tag_pointer"] = pointer
    entry["updated_at"] = now_iso()
    state._reindex_entry(entry)

    _log_op(state, "update_tag", entry_id,
            {"old": old_tag, "new": tag, "pointer": pointer})
    state.mark_dirty("entries")
    save(state, data_dir)
    return entry


# --- Baselines ---

def update_baseline(state, passed, xfailed, failed, session_id=None, data_dir=None):
    """Record a new baseline snapshot."""
    baseline = {
        "passed": int(passed),
        "xfailed": int(xfailed),
        "failed": int(failed),
        "session_id": session_id,
        "at": now_iso(),
    }
    state.baselines.append(baseline)
    _log_op(state, "update_baseline", "baseline",
            {"passed": passed, "xfailed": xfailed, "failed": failed})
    state.mark_dirty("baselines")
    save(state, data_dir)
    return baseline


# --- Sessions ---

def create_session(state, title, session_id=None, data_dir=None):
    """Start a new session."""
    if session_id is None:
        existing = [s.get("id", 0) for s in state.sessions]
        session_id = max(existing) + 1 if existing else 1

    session = {
        "id": session_id,
        "title": title,
        "started_at": now_iso(),
        "ended_at": None,
        "baseline_start": None,
        "baseline_end": None,
    }
    # Capture current baseline
    if state.baselines:
        latest = state.baselines[-1]
        session["baseline_start"] = {
            "passed": latest["passed"],
            "xfailed": latest["xfailed"],
            "failed": latest["failed"],
        }

    state.sessions.append(session)
    _log_op(state, "create_session", f"session-{session_id}", {"title": title})
    state.mark_dirty("sessions")
    save(state, data_dir)
    return session


def close_session(state, session_id, baseline_end=None, data_dir=None):
    """End a session."""
    session = None
    for s in state.sessions:
        if s["id"] == session_id:
            session = s
            break
    if not session:
        raise KeyError(f"Session not found: {session_id}")

    session["ended_at"] = now_iso()
    if baseline_end:
        session["baseline_end"] = baseline_end
    elif state.baselines:
        latest = state.baselines[-1]
        session["baseline_end"] = {
            "passed": latest["passed"],
            "xfailed": latest["xfailed"],
            "failed": latest["failed"],
        }

    _log_op(state, "close_session", f"session-{session_id}")
    state.mark_dirty("sessions")
    save(state, data_dir)
    return session


# --- Cross-references ---

def add_ref(state, from_id, to_id, ref_type="link", data_dir=None):
    """Add a cross-reference between entries or to external targets."""
    ref = {
        "from_id": from_id,
        "to_id": to_id,
        "ref_type": ref_type,
        "created_at": now_iso(),
    }
    state.refs.append(ref)
    state.ref_from[from_id].append(ref)
    state.ref_to[to_id].append(ref)

    _log_op(state, "add_ref", from_id, {"to": to_id, "type": ref_type})
    state.mark_dirty("refs")
    save(state, data_dir)
    return ref
