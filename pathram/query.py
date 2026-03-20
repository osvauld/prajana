"""query.py — Read operations for patra state.

All queries work on the in-memory State object.
Search uses regex. Everything is fast enough for <1000 entries.
"""

import re
from datetime import datetime, timedelta


def search(state, pattern):
    """Full-text regex search across all entry titles and bodies."""
    try:
        rx = re.compile(pattern, re.IGNORECASE)
    except re.error:
        rx = re.compile(re.escape(pattern), re.IGNORECASE)

    results = []
    for entry in state.entries:
        title_match = rx.search(entry.get("title", ""))
        body_match = rx.search(entry.get("body", ""))
        if title_match or body_match:
            results.append(entry)
    return results


def by_tag(state, tag):
    """All entries with the given lifecycle tag."""
    return list(state.by_tag.get(tag, []))


def by_session(state, session_id):
    """All entries created or modified in a session."""
    sid = int(session_id)
    return list(state.by_session.get(sid, []))


def by_type(state, entry_type):
    """All entries of a given type."""
    return list(state.by_type.get(entry_type, []))


def by_doc(state, doc_id):
    """All entries in a document, ordered by position."""
    return list(state.by_doc.get(doc_id, []))


def steps(state, status=None):
    """All plan steps, optionally filtered by status."""
    all_steps = state.by_type.get("step", [])
    if status:
        return [s for s in all_steps
                if s.get("meta", {}).get("status") == status]
    return list(all_steps)


def gaps(state):
    """All known data gaps."""
    return list(state.by_type.get("gap", []))


def quirks(state):
    """All recorded quirks/gotchas."""
    return list(state.by_type.get("quirk", []))


def stale(state, days):
    """Entries not updated in N days."""
    cutoff = datetime.now() - timedelta(days=int(days))
    results = []
    for entry in state.entries:
        updated = entry.get("updated_at", "")
        try:
            dt = datetime.fromisoformat(updated)
            if dt < cutoff:
                results.append(entry)
        except (ValueError, TypeError):
            results.append(entry)
    return results


def timeline(state, session_start=None, session_end=None):
    """Chronological events, optionally scoped to session range."""
    entries = state.entries
    if session_start is not None or session_end is not None:
        s_start = int(session_start) if session_start is not None else 0
        s_end = int(session_end) if session_end is not None else 999999
        entries = [e for e in entries
                   if e.get("session_id") is not None
                   and s_start <= e["session_id"] <= s_end]

    return sorted(entries, key=lambda e: e.get("created_at", ""))


def refs_for(state, entry_id):
    """Incoming and outgoing references for an entry."""
    outgoing = list(state.ref_from.get(entry_id, []))
    incoming = list(state.ref_to.get(entry_id, []))
    return {"outgoing": outgoing, "incoming": incoming}


def broken_refs(state):
    """Find refs pointing to non-existent patra entries."""
    broken = []
    for ref in state.refs:
        to_id = ref["to_id"]
        # Skip external refs (om:, tantra:, shabda:, ext:)
        if ":" in to_id:
            continue
        if to_id not in state.by_id:
            broken.append(ref)
    return broken


def topic(state, name, bridge=None):
    """Cross-source search: patra entries + om nodes + tantras + shabda."""
    result = {
        "entries": search(state, name),
        "om_nodes": [],
        "tantras": [],
        "shabda": [],
    }
    if bridge:
        result["om_nodes"] = bridge.search_om(name)
        result["tantras"] = bridge.search_tantras(name)
        result["shabda"] = bridge.search_shabda(name)
    return result


def glance(state, bridge=None):
    """Compact summary dict for LLM context."""
    # Latest baseline
    baseline = None
    if state.baselines:
        baseline = state.baselines[-1]

    # Next step
    next_steps = [s for s in state.by_type.get("step", [])
                  if s.get("meta", {}).get("status") == "next"]
    next_step = next_steps[0] if next_steps else None

    # Recent discoveries (last 5)
    discoveries = sorted(
        state.by_type.get("discovery", []),
        key=lambda e: e.get("created_at", ""),
        reverse=True
    )[:5]

    # Status rollup
    tag_counts = {}
    for tag, entries in state.by_tag.items():
        if entries:
            tag_counts[tag] = len(entries)

    # Live stats from bridge
    live = {}
    if bridge:
        live = bridge.live_stats()

    return {
        "baseline": baseline,
        "next_step": next_step,
        "recent_discoveries": discoveries,
        "tag_counts": tag_counts,
        "doc_count": len(state.docs),
        "entry_count": len(state.entries),
        "live": live,
    }
