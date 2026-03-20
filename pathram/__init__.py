"""patra — Living documentation system for agent-x.

All documentation lives in structured state. Markdown and HTML are emitted views.

Usage:
    CLI:    python3 -m patra <command> [args...]
    Python: from pathram import discover, step_done, glance
"""

from pathram.data import load, ensure_data_dir, save
from pathram.store import (
    create_doc, create_entry, update_entry, update_tag,
    update_baseline, create_session, close_session, add_ref,
)
from pathram.query import search, by_tag, by_doc, by_type, steps, gaps, quirks
from pathram.emit import emit_md, emit_glance, emit_index, emit_report

# Module-level state (lazy-loaded)
_state = None


def _get_state():
    global _state
    if _state is None:
        ensure_data_dir()
        _state = load()
    return _state


def _reset():
    """Reset module state (for testing)."""
    global _state
    _state = None


# --- Convenience functions ---

def discover(text, session_id=None, doc="discoveries"):
    """Record a discovery."""
    state = _get_state()
    if doc not in state.doc_by_id:
        create_doc(state, doc, "Discoveries")
    return create_entry(state, doc, "discovery", text, session_id=session_id)


def step_done(step_id, note="", session_id=None):
    """Mark a step complete."""
    state = _get_state()
    entry = update_entry(state, step_id, meta={"status": "done"})
    if note:
        update_entry(state, step_id,
                     body=entry.get("body", "") + f"\n\n{note}")
    return entry


def step_add(title, doc="plan", after=None, session_id=None, status="pending"):
    """Add a plan step."""
    state = _get_state()
    if doc not in state.doc_by_id:
        create_doc(state, doc, "Plan")
    position = after + 0.5 if after else None
    return create_entry(state, doc, "step", title,
                        position=position, session_id=session_id,
                        meta={"status": status})


def note(text, note_type="quirk", doc="notes", session_id=None):
    """Record a quirk or note."""
    state = _get_state()
    if doc not in state.doc_by_id:
        create_doc(state, doc, "Notes")
    return create_entry(state, doc, note_type, text, session_id=session_id)


def glance():
    """Get compact summary string."""
    from pathram.bridge import Bridge
    state = _get_state()
    return emit_glance(state, Bridge())
