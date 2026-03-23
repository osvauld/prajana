"""temporal.py — Session/journal management, time queries, hours tracking."""

from pathram2.types import Node, _now
from pathram2.graph.crud import add_node, get_node, update_node, link
from pathram2.graph.walk import walk, walk_in, chain
from pathram2.graph.query import by_type, by_shabda, since


def session_start(store, title: str, id: str | None = None) -> Node:
    """Begin a new session. Auto-links to previous session via krama."""
    shabda = {"started": _now()}
    session = add_node(store, "session", title, shabda=shabda, id=id)

    # Find previous session and link via krama
    sessions = by_type(store, "session")
    # Sort by created_at, exclude current
    others = sorted(
        [s for s in sessions if s.id != session.id],
        key=lambda s: s.created_at,
    )
    if others:
        prev = others[-1]
        link(store, prev.id, session.id, "krama")

    return session


def session_end(store, session_id: str) -> Node:
    """Close a session. Computes hours from start time."""
    from datetime import datetime

    session = get_node(store, session_id)
    if session is None:
        raise KeyError(f"Session not found: {session_id}")

    ended = _now()
    started = session.shabda.get("started", session.created_at)

    try:
        t_start = datetime.fromisoformat(started)
        t_end = datetime.fromisoformat(ended)
        hours = round((t_end - t_start).total_seconds() / 3600, 2)
    except (ValueError, TypeError):
        hours = 0.0

    return update_node(store, session_id, shabda={
        "ended": ended,
        "hours": hours,
    }, tag="done")


def current_session(store) -> Node | None:
    """Find the most recent open session (no 'ended' in shabda)."""
    sessions = by_type(store, "session")
    open_sessions = [
        s for s in sessions
        if s.tag == "active" and "ended" not in s.shabda
    ]
    if not open_sessions:
        return None
    return max(open_sessions, key=lambda s: s.created_at)


def journal(store, n: int = 5) -> list[Node]:
    """Last N sessions, ordered by time (most recent first)."""
    sessions = by_type(store, "session")
    sessions.sort(key=lambda s: s.created_at, reverse=True)
    return sessions[:n]


def today(store) -> list[Node]:
    """All nodes created or updated today."""
    from datetime import datetime
    day_start = datetime.now().replace(hour=0, minute=0, second=0).isoformat(timespec="seconds")
    return since(store, day_start)


def hours_on(store, node_id: str) -> float:
    """Total hours from all sessions linked to a node (via janya edges)."""
    session_ids = walk_in(store, node_id, "janya")
    total = 0.0
    for sid in session_ids:
        session = get_node(store, sid)
        if session and "hours" in session.shabda:
            try:
                total += float(session.shabda["hours"])
            except (ValueError, TypeError):
                pass
    return total


def session_diff(store, session_id: str) -> dict:
    """What was produced in a session. Walks janya edges outward."""
    products = walk(store, session_id, "phala")
    nodes = []
    for pid in products:
        node = get_node(store, pid)
        if node:
            nodes.append(node)
    return {
        "session_id": session_id,
        "products": nodes,
        "count": len(nodes),
    }
