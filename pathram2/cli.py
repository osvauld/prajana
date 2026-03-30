"""cli.py — CLI dispatch for pathram2."""

import argparse
import json
import sys

from pathram2.graph import Graph
from pathram2.types import RELATIONS, NODE_TYPES, TAGS


def _graph(args) -> Graph:
    path = getattr(args, "db", None)
    return Graph(path=path)


def _resolve(g: Graph, id_or_name: str) -> str | None:
    """Resolve slug or ID → confirmed node ID. Exits with error if not found."""
    nid = g.resolve(id_or_name)
    if nid is None:
        print(f"Not found: {id_or_name}", file=sys.stderr)
        g.close()
        sys.exit(1)
    return nid


def _print_node(node, verbose=False):
    status = node.shabda.get("status", "")
    name = node.shabda.get("name", "")
    status_badge = f" [{status}]" if status else ""
    tag_badge = f" ({node.tag})" if node.tag != "active" else ""
    name_badge = f" @{name}" if name else ""
    print(f"  {node.id:30s} {node.type:12s}{name_badge} {node.title}{status_badge}{tag_badge}")
    if verbose and node.body:
        for line in node.body.split("\n")[:5]:
            print(f"    {line}")


def _print_edge(edge):
    reason = edge.shabda.get("reason", "")
    extra = f"  # {reason}" if reason else ""
    print(f"  {edge.source} --{edge.relation}--> {edge.target}{extra}")


def _node_to_dict(node, edges=None) -> dict:
    d = node.to_dict()
    if edges is not None:
        d["edges"] = [
            {"source": e.source, "target": e.target,
             "relation": e.relation, "shabda": e.shabda}
            for e in edges
        ]
    return d


# --- Commands ---

def cmd_add(args):
    g = _graph(args)
    shabda = {}
    if args.status:
        shabda["status"] = args.status
    if args.name:
        shabda["name"] = args.name
    node = g.add(args.type, args.title, body=args.body or "",
                 tag=args.tag or "active", shabda=shabda, id=args.id or args.name)
    if args.parent:
        parent_id = g.resolve(args.parent) or args.parent
        g.link(node.id, parent_id, "sthita")
    if args.session:
        session_id = g.resolve(args.session) or args.session
        g.link(node.id, session_id, "janya")
    print(f"Created: {node.id}")
    g.close()


def cmd_show(args):
    g = _graph(args)
    nid = _resolve(g, args.node_id)
    node = g.get(nid)
    edges = g.edges_of(nid)
    if args.json_out:
        print(json.dumps(_node_to_dict(node, edges), indent=2))
        g.close()
        return
    print(f"# {node.title}")
    name = node.shabda.get("name", "")
    print(f"id: {node.id}  type: {node.type}  tag: {node.tag}" + (f"  name: @{name}" if name else ""))
    status = node.shabda.get("status", "")
    if status:
        print(f"status: {status}")
    other_shabda = {k: v for k, v in node.shabda.items() if k not in ("name", "status")}
    if other_shabda:
        print(f"shabda: {json.dumps(other_shabda)}")
    print(f"created: {node.created_at}  updated: {node.updated_at}")
    if node.body:
        print()
        print(node.body)
    if edges:
        print("\nEdges:")
        for e in edges:
            _print_edge(e)
    g.close()


def cmd_update(args):
    g = _graph(args)
    nid = _resolve(g, args.node_id)
    fields = {}
    if args.title:
        fields["title"] = args.title
    if args.body:
        fields["body"] = args.body
    if args.tag:
        fields["tag"] = args.tag
    shabda_updates = {}
    if args.status:
        shabda_updates["status"] = args.status
    if args.name:
        shabda_updates["name"] = args.name
    if shabda_updates:
        fields["shabda"] = shabda_updates
    node = g.update(nid, **fields)
    print(f"Updated: {node.id}")
    g.close()


def cmd_delete(args):
    g = _graph(args)
    nid = _resolve(g, args.node_id)
    g.delete(nid)
    print(f"Deleted: {nid}")
    g.close()


def cmd_link(args):
    g = _graph(args)
    src = g.resolve(args.source) or args.source
    tgt = g.resolve(args.target) or args.target
    shabda = {}
    if args.reason:
        shabda["reason"] = args.reason
    edge = g.link(src, tgt, args.relation, shabda=shabda)
    print(f"Linked: {edge.source} --{edge.relation}--> {edge.target}")
    g.close()


def cmd_unlink(args):
    g = _graph(args)
    src = g.resolve(args.source) or args.source
    tgt = g.resolve(args.target) or args.target
    g.unlink(src, tgt, args.relation)
    print(f"Unlinked: {src} -> {tgt}")
    g.close()


def cmd_walk(args):
    g = _graph(args)
    nid = _resolve(g, args.node_id)
    if args.incoming:
        targets = g.walk_in(nid, args.relation)
    else:
        targets = g.walk(nid, args.relation)
    if args.json_out:
        results = []
        for t in targets:
            node = g.get(t)
            results.append(node.to_dict() if node else {"id": t})
        print(json.dumps(results, indent=2))
        g.close()
        return
    for t in targets:
        node = g.get(t)
        if node:
            _print_node(node)
        else:
            print(f"  {t}")
    g.close()


def cmd_search(args):
    g = _graph(args)
    nodes = g.search(args.pattern)
    if args.json_out:
        print(json.dumps([n.to_dict() for n in nodes], indent=2))
        g.close()
        return
    print(f"Found {len(nodes)} nodes:")
    for n in nodes:
        _print_node(n)
    g.close()


def cmd_steps(args):
    g = _graph(args)
    q = g.q().type("step")
    if args.pending:
        q = q.shabda("status", "pending")
    elif args.done:
        q = q.shabda("status", "done")
    elif args.status:
        q = q.shabda("status", args.status)
    if args.tag:
        q = q.tag(args.tag)
    nodes = q.sort("created_at").load()
    if args.json_out:
        print(json.dumps([n.to_dict() for n in nodes], indent=2))
        g.close()
        return
    print(f"{len(nodes)} steps:")
    for n in nodes:
        _print_node(n, verbose=args.verbose)
    g.close()


def cmd_session_start(args):
    from pathram2.temporal import session_start
    g = _graph(args)
    session = session_start(g.store, args.title, id=args.id)
    print(f"Session started: {session.id}")
    g.close()


def cmd_session_end(args):
    from pathram2.temporal import session_end, current_session
    g = _graph(args)
    sid = args.session_id
    if not sid:
        cs = current_session(g.store)
        if not cs:
            print("No open session", file=sys.stderr)
            g.close()
            return
        sid = cs.id
    else:
        sid = g.resolve(sid) or sid
    session = session_end(g.store, sid)
    hours = session.shabda.get("hours", 0)
    print(f"Session ended: {session.id} ({hours}h)")
    g.close()


def cmd_journal(args):
    from pathram2.temporal import journal
    g = _graph(args)
    sessions = journal(g.store, n=args.n)
    if args.json_out:
        print(json.dumps([s.to_dict() for s in sessions], indent=2))
        g.close()
        return
    print(f"Last {len(sessions)} sessions:")
    for s in sessions:
        hours = s.shabda.get("hours", "?")
        ended = s.shabda.get("ended", "open")
        print(f"  {s.id:20s} {s.title:40s} {hours}h  {ended}")
    g.close()


def cmd_today(args):
    from pathram2.temporal import today
    g = _graph(args)
    nodes = today(g.store)
    if args.json_out:
        print(json.dumps([n.to_dict() for n in nodes], indent=2))
        g.close()
        return
    print(f"{len(nodes)} nodes today:")
    for n in nodes:
        _print_node(n)
    g.close()


def cmd_branch(args):
    from pathram2.branch import branch
    g = _graph(args)
    from_id = g.resolve(args.from_node) or args.from_node
    node = branch(g.store, from_id, args.reason, args.title)
    print(f"Branched: {node.id} (from {from_id})")
    g.close()


def cmd_return(args):
    from pathram2.branch import return_to
    from pathram2.temporal import current_session
    g = _graph(args)
    nid = g.resolve(args.node_id) or args.node_id
    sid = args.session_id
    if not sid:
        cs = current_session(g.store)
        if cs:
            sid = cs.id
    if sid:
        return_to(g.store, sid, nid)
        print(f"Returned to: {nid}")
    else:
        print("No session to mark return from", file=sys.stderr)
    g.close()


def cmd_branches(args):
    from pathram2.branch import open_branches
    g = _graph(args)
    branches = open_branches(g.store)
    if args.json_out:
        results = []
        for b in branches:
            results.append({
                "branch": b["branch"].to_dict() if b["branch"] else None,
                "origin": b["origin"].to_dict() if b["origin"] else None,
                "reason": b["reason"],
            })
        print(json.dumps(results, indent=2))
        g.close()
        return
    if not branches:
        print("No open branches.")
    else:
        print(f"{len(branches)} open branches:")
        for b in branches:
            br = b["branch"]
            orig = b["origin"]
            reason = b["reason"]
            print(f"  {br.id} (from {orig.id}): {reason}")
    g.close()


def cmd_tree(args):
    from pathram2.branch import branch_tree
    g = _graph(args)
    root = None
    if args.root:
        root = g.resolve(args.root) or args.root
    tree = branch_tree(g.store, root=root)
    _print_tree(tree, indent=0)
    g.close()


def _print_tree(tree, indent=0):
    if isinstance(tree, dict) and "id" in tree:
        prefix = "  " * indent
        tag = f" ({tree['tag']})" if tree.get("tag") and tree["tag"] != "active" else ""
        reason = f" -- {tree['reason']}" if tree.get("reason") else ""
        print(f"{prefix}{tree['id']}: {tree.get('title', '?')}{tag}{reason}")
        for b in tree.get("branches", []):
            _print_tree(b, indent + 1)
    elif isinstance(tree, dict):
        for k, v in tree.items():
            _print_tree(v, indent)


def cmd_merge(args):
    g = _graph(args)
    node_ids = [g.resolve(nid) or nid for nid in args.node_ids]
    node = g.merge(node_ids, args.into, args.title, body=args.body or "")
    print(f"Merged into: {node.id}")
    g.close()


def cmd_stale(args):
    g = _graph(args)
    nodes = g.stale(args.days)
    if args.json_out:
        print(json.dumps([n.to_dict() for n in nodes], indent=2))
        g.close()
        return
    print(f"{len(nodes)} nodes stale >{args.days} days:")
    for n in nodes:
        _print_node(n)
    g.close()


def cmd_abandoned(args):
    from pathram2.branch import abandoned
    g = _graph(args)
    nodes = abandoned(g.store, stale_days=args.days)
    if args.json_out:
        print(json.dumps([n.to_dict() for n in nodes], indent=2))
        g.close()
        return
    print(f"{len(nodes)} abandoned steps:")
    for n in nodes:
        _print_node(n)
    g.close()


def cmd_glance(args):
    from pathram2.branch import open_branches
    from pathram2.temporal import current_session, journal
    g = _graph(args)
    total = g.q().count()
    steps = g.q().type("step").count()
    done = g.q().type("step").shabda("status", "done").count()
    pending_nodes = g.q().type("step").shabda("status", "pending").load()
    sessions = g.q().type("session").count()
    discoveries = g.q().type("discovery").count()
    branches = open_branches(g.store)
    cs = current_session(g.store)
    recent = journal(g.store, n=3)

    if args.json_out:
        print(json.dumps({
            "total_nodes": total,
            "sessions": sessions,
            "discoveries": discoveries,
            "steps": {"total": steps, "done": done, "pending": len(pending_nodes)},
            "current_session": cs.to_dict() if cs else None,
            "open_branches": len(branches),
            "recent_sessions": [s.to_dict() for s in recent],
            "pending_steps": [n.to_dict() for n in pending_nodes],
        }, indent=2))
        g.close()
        return

    print("## pathram2 glance")
    print(f"Nodes: {total}  |  Sessions: {sessions}  |  Discoveries: {discoveries}")
    print(f"Steps: {steps} (done: {done}, pending: {len(pending_nodes)})")
    if cs:
        print(f"Current session: {cs.id} — {cs.title}")
    if branches:
        print(f"Open branches: {len(branches)}")
        for b in branches[:3]:
            print(f"  {b['branch'].id} (from {b['origin'].id}): {b['reason']}")
    if pending_nodes:
        print(f"Pending steps:")
        for n in pending_nodes[:5]:
            print(f"  {n.id}: {n.title}")
    g.close()


def cmd_context(args):
    """LLM startup dump: current session, open branches, pending steps, recent discoveries."""
    from pathram2.branch import open_branches
    from pathram2.temporal import current_session, journal
    from pathram2.graph.query import by_type
    g = _graph(args)

    cs = current_session(g.store)
    branches = open_branches(g.store)
    pending = g.q().type("step").shabda("status", "pending").sort("created_at").load()
    recent_sessions = journal(g.store, n=5)
    recent_discoveries = g.q().type("discovery").sort("created_at", reverse=True).limit(5).load()

    if args.json_out:
        print(json.dumps({
            "current_session": cs.to_dict() if cs else None,
            "open_branches": [
                {"branch_id": b["branch"].id, "branch_title": b["branch"].title,
                 "origin_id": b["origin"].id, "reason": b["reason"]}
                for b in branches
            ],
            "pending_steps": [{"id": n.id, "title": n.title, "body": n.body[:200]} for n in pending],
            "recent_sessions": [{"id": s.id, "title": s.title,
                                  "hours": s.shabda.get("hours", 0),
                                  "ended": s.shabda.get("ended", "open")} for s in recent_sessions],
            "recent_discoveries": [{"id": n.id, "title": n.title, "body": n.body[:300]} for n in recent_discoveries],
        }, indent=2))
        g.close()
        return

    print("## Context")
    print()
    if cs:
        print(f"Current session: {cs.id} — {cs.title}")
        print(f"  started: {cs.shabda.get('started', cs.created_at)}")
    else:
        print("No open session.")

    print()
    print(f"Open branches ({len(branches)}):")
    for b in branches:
        print(f"  {b['branch'].id} ← from {b['origin'].id}: {b['reason']}")

    print()
    print(f"Pending steps ({len(pending)}):")
    for n in pending:
        print(f"  {n.id}: {n.title}")

    print()
    print(f"Recent sessions:")
    for s in recent_sessions:
        ended = s.shabda.get("ended", "open")
        hours = s.shabda.get("hours", "?")
        print(f"  {s.id:20s} {s.title:50s} {hours}h  {ended}")

    print()
    print(f"Recent discoveries:")
    for n in recent_discoveries:
        print(f"  {n.id}: {n.title}")
        if n.body:
            print(f"    {n.body.splitlines()[0][:120]}")

    g.close()


def cmd_cleanup(args):
    """Workflow health check: open sessions, tangent branches, pending steps."""
    from pathram2.branch import open_branches
    from pathram2.temporal import current_session, journal
    from pathram2.graph.query import by_type
    from datetime import datetime

    g = _graph(args)

    def _age(ts: str) -> str:
        try:
            delta = datetime.now() - datetime.fromisoformat(ts)
            d = delta.days
            h = delta.seconds // 3600
            if d > 0:
                return f"{d}d ago"
            return f"{h}h ago"
        except Exception:
            return "?"

    # --- Sessions ---
    all_sessions = by_type(g.store, "session")
    open_sessions = [s for s in all_sessions if s.tag == "active" and "ended" not in s.shabda]
    open_sessions.sort(key=lambda s: s.shabda.get("started", s.created_at), reverse=True)
    cs = current_session(g.store)

    # --- Branches (tangents) ---
    branches = open_branches(g.store)

    # --- Pending steps ---
    pending = g.q().type("step").shabda("status", "pending").sort("created_at").load()

    # --- Steps missing status ---
    all_steps = g.q().type("step").load()
    no_status = [n for n in all_steps if "status" not in n.shabda]

    if args.json_out:
        print(json.dumps({
            "open_sessions": [s.to_dict() for s in open_sessions],
            "current_session": cs.to_dict() if cs else None,
            "open_branches": [
                {"branch_id": b["branch"].id, "branch_title": b["branch"].title,
                 "origin_id": b["origin"].id, "reason": b["reason"],
                 "age": _age(b["branch"].created_at)}
                for b in branches if b["branch"]
            ],
            "pending_steps": [n.to_dict() for n in pending],
            "steps_missing_status": [n.to_dict() for n in no_status],
        }, indent=2))
        g.close()
        return

    issues = 0

    # Sessions
    print("## Sessions")
    if not open_sessions:
        print("  No open session. Run: session-start \"<topic>\"")
        issues += 1
    elif len(open_sessions) == 1:
        s = open_sessions[0]
        started = s.shabda.get("started", s.created_at)
        print(f"  {s.id}: {s.title}  [{_age(started)}]  ✓")
    else:
        print(f"  {len(open_sessions)} open sessions (expected ≤1):")
        for s in open_sessions:
            started = s.shabda.get("started", s.created_at)
            marker = " [current]" if cs and s.id == cs.id else " [stale — close with: session-end " + s.id + "]"
            print(f"    {s.id:20s} {s.title:45s} {_age(started)}{marker}")
        issues += len(open_sessions) - 1

    # Branches / tangents
    print(f"\n## Open branches — tangents in flight ({len(branches)})")
    if not branches:
        print("  None.")
    else:
        for b in branches:
            br = b["branch"]
            orig = b["origin"]
            if not br or not orig:
                continue
            age = _age(br.updated_at)
            print(f"  {br.id:30s} ← {orig.id}")
            print(f"    reason: {b['reason']}")
            print(f"    last touched: {age}")
        issues += len(branches)

    # Pending steps
    print(f"\n## Pending steps ({len(pending)})")
    if not pending:
        print("  None.")
    else:
        for n in pending:
            age = _age(n.updated_at)
            print(f"  {n.id:30s} {n.title}  [{age}]")

    # Steps missing status
    if no_status:
        print(f"\n## Steps missing status field ({len(no_status)})")
        print("  These steps have no shabda.status — add: update <id> --status pending|done")
        for n in no_status[:10]:
            print(f"  {n.id:30s} {n.title}")
        if len(no_status) > 10:
            print(f"  ... and {len(no_status) - 10} more")
        issues += len(no_status)

    print(f"\n{'✓ Workflow clean' if issues == 0 else f'⚠ {issues} item(s) need attention'}")
    g.close()


def cmd_usage(args):
    """Show or reset pathram2 command usage statistics."""
    from pathram2.usage import report, reset

    if args.action == "reset":
        reset()
        print("Usage data reset.")
        return

    rows = report()
    if not rows:
        print("No usage data yet.")
        return

    if args.json_out:
        print(json.dumps(rows, indent=2))
        return

    total = sum(r["count"] for r in rows)
    print(f"pathram2 usage — {total} total calls, {len(rows)} distinct commands\n")
    print(f"  {'command':25s} {'count':>6}  {'last':20s}  first")
    print(f"  {'-'*25} {'-'*6}  {'-'*20}  {'-'*19}")
    for r in rows:
        print(f"  {r['command']:25s} {r['count']:>6}  {r['last']:20s}  {r['first']}")


def cmd_resolve(args):
    """Resolve a name slug or ID to a confirmed node ID."""
    g = _graph(args)
    nid = g.resolve(args.name)
    if nid:
        node = g.get(nid)
        if args.json_out:
            print(json.dumps({"id": nid, "title": node.title if node else None}, indent=2))
        else:
            print(f"{nid}" + (f"  ({node.title})" if node else ""))
    else:
        print(f"Not found: {args.name}", file=sys.stderr)
        g.close()
        sys.exit(1)
    g.close()


def cmd_query(args):
    """Run a composable query from CLI.

    Example: pathram2 query type=step tag=active shabda.status=pending sort=created_at limit=10
    """
    g = _graph(args)
    q = g.q()
    for expr in args.exprs:
        if "=" not in expr:
            continue
        key, val = expr.split("=", 1)
        if key == "type":
            q = q.type(val)
        elif key == "tag":
            q = q.tag(val)
        elif key.startswith("shabda."):
            sk = key.split(".", 1)[1]
            q = q.shabda(sk, val)
        elif key == "search":
            q = q.search(val)
        elif key == "since":
            q = q.since(val)
        elif key == "before":
            q = q.before(val)
        elif key == "stale":
            q = q.stale(int(val))
        elif key == "walk":
            q = q.walk(val)
        elif key == "walk_in":
            q = q.walk_in(val)
        elif key == "descendants":
            q = q.descendants(val)
        elif key == "ancestors":
            q = q.ancestors(val)
        elif key == "sort":
            q = q.sort(val)
        elif key == "rsort":
            q = q.sort(val, reverse=True)
        elif key == "limit":
            q = q.limit(int(val))
        elif key == "node":
            resolved = g.resolve(val) or val
            q = q.node(resolved)

    if args.json_out:
        nodes = q.load()
        print(json.dumps([n.to_dict() for n in nodes], indent=2))
    elif args.count_only:
        print(q.count())
    elif args.ids_only:
        for i in q.ids():
            print(i)
    else:
        nodes = q.load()
        print(f"{len(nodes)} results:")
        for n in nodes:
            _print_node(n, verbose=args.verbose)
    g.close()


def cmd_relations(args):
    print("Core visheshanam (10):")
    from pathram2.types import VISHESHANAM, EXTENSIONS
    for name, desc in VISHESHANAM.items():
        print(f"  {name:16s} {desc}")
    print("\nExtensions:")
    for name, desc in EXTENSIONS.items():
        print(f"  {name:16s} {desc}")


def cmd_types(args):
    print("Node types:")
    for name, desc in NODE_TYPES.items():
        print(f"  {name:14s} {desc}")
    print("\nTags:")
    for name, desc in TAGS.items():
        print(f"  {name:14s} {desc}")


# --- Parser ---

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pathram2", description="Graph-native knowledge tracker")
    p.add_argument("--db", help="LMDB database path")
    sub = p.add_subparsers(dest="command")

    # add
    s = sub.add_parser("add", help="Add a node")
    s.add_argument("type", choices=list(NODE_TYPES.keys()))
    s.add_argument("title")
    s.add_argument("--body", "-b")
    s.add_argument("--tag", "-t")
    s.add_argument("--id", help="Explicit node ID (use for stable references)")
    s.add_argument("--name", "-n", help="Slug for name-based lookup (stored in shabda.name; also used as ID if --id not set)")
    s.add_argument("--parent", "-p", help="Link via sthita to parent (ID or name)")
    s.add_argument("--session", "-s", help="Link via janya to session (ID or name)")
    s.add_argument("--status", help="Set shabda.status")

    # show
    s = sub.add_parser("show", help="Show a node")
    s.add_argument("node_id", help="Node ID or name slug")
    s.add_argument("--json", dest="json_out", action="store_true")

    # update
    s = sub.add_parser("update", help="Update a node")
    s.add_argument("node_id", help="Node ID or name slug")
    s.add_argument("--title")
    s.add_argument("--body", "-b")
    s.add_argument("--tag", "-t")
    s.add_argument("--status")
    s.add_argument("--name", "-n", help="Set or update name slug")

    # delete
    s = sub.add_parser("delete", help="Delete a node")
    s.add_argument("node_id", help="Node ID or name slug")

    # link
    s = sub.add_parser("link", help="Create an edge")
    s.add_argument("source", help="Source node ID or name")
    s.add_argument("target", help="Target node ID or name")
    s.add_argument("relation", choices=list(RELATIONS.keys()))
    s.add_argument("--reason", "-r")

    # unlink
    s = sub.add_parser("unlink", help="Remove an edge")
    s.add_argument("source", help="Source node ID or name")
    s.add_argument("target", help="Target node ID or name")
    s.add_argument("relation", nargs="?")

    # walk
    s = sub.add_parser("walk", help="Walk edges from a node")
    s.add_argument("node_id", help="Node ID or name slug")
    s.add_argument("relation")
    s.add_argument("--incoming", "-i", action="store_true")
    s.add_argument("--json", dest="json_out", action="store_true")

    # search
    s = sub.add_parser("search", help="Search nodes by pattern")
    s.add_argument("pattern")
    s.add_argument("--json", dest="json_out", action="store_true")

    # steps
    s = sub.add_parser("steps", help="List steps")
    s.add_argument("--status")
    s.add_argument("--pending", action="store_true", help="Show pending steps only")
    s.add_argument("--done", action="store_true", help="Show done steps only")
    s.add_argument("--tag")
    s.add_argument("--json", dest="json_out", action="store_true")
    s.add_argument("--verbose", "-v", action="store_true")

    # session-start
    s = sub.add_parser("session-start", help="Start a session")
    s.add_argument("title")
    s.add_argument("--id")

    # session-end
    s = sub.add_parser("session-end", help="End current session")
    s.add_argument("session_id", nargs="?", help="Session ID or name (default: current open session)")

    # journal
    s = sub.add_parser("journal", help="Show recent sessions")
    s.add_argument("-n", type=int, default=5)
    s.add_argument("--json", dest="json_out", action="store_true")

    # today
    s = sub.add_parser("today", help="Nodes touched today")
    s.add_argument("--json", dest="json_out", action="store_true")

    # branch
    s = sub.add_parser("branch", help="Branch from a node")
    s.add_argument("from_node", help="Origin node ID or name")
    s.add_argument("reason")
    s.add_argument("title")

    # return
    s = sub.add_parser("return", help="Mark return to original task")
    s.add_argument("node_id", help="Node ID or name")
    s.add_argument("--session-id")

    # branches
    s = sub.add_parser("branches", help="Show open branches")
    s.add_argument("--json", dest="json_out", action="store_true")

    # tree
    s = sub.add_parser("tree", help="Show branch DAG")
    s.add_argument("root", nargs="?", help="Root node ID or name")

    # merge
    s = sub.add_parser("merge", help="Consolidate nodes")
    s.add_argument("node_ids", nargs="+", help="Node IDs or names to merge")
    s.add_argument("--into", required=True, choices=list(NODE_TYPES.keys()))
    s.add_argument("--title", required=True)
    s.add_argument("--body", "-b")

    # stale
    s = sub.add_parser("stale", help="Show stale nodes")
    s.add_argument("days", type=int)
    s.add_argument("--json", dest="json_out", action="store_true")

    # abandoned
    s = sub.add_parser("abandoned", help="Show abandoned steps")
    s.add_argument("--days", type=int, default=7)
    s.add_argument("--json", dest="json_out", action="store_true")

    # glance
    s = sub.add_parser("glance", help="Quick summary")
    s.add_argument("--json", dest="json_out", action="store_true")

    # context
    s = sub.add_parser("context", help="LLM startup context dump")
    s.add_argument("--json", dest="json_out", action="store_true")

    # cleanup
    s = sub.add_parser("cleanup", help="Workflow health: open sessions, branches, pending steps")
    s.add_argument("--json", dest="json_out", action="store_true")

    # usage
    s = sub.add_parser("usage", help="Command usage statistics")
    s.add_argument("action", nargs="?", choices=["report", "reset"], default="report")
    s.add_argument("--json", dest="json_out", action="store_true")

    # resolve
    s = sub.add_parser("resolve", help="Resolve a name slug or ID to a node ID")
    s.add_argument("name", help="Slug or ID to resolve")
    s.add_argument("--json", dest="json_out", action="store_true")

    # query
    s = sub.add_parser("query", help="Composable query")
    s.add_argument("exprs", nargs="+", help="key=value filter expressions")
    s.add_argument("--json", dest="json_out", action="store_true")
    s.add_argument("--count", dest="count_only", action="store_true")
    s.add_argument("--ids", dest="ids_only", action="store_true")
    s.add_argument("--verbose", "-v", action="store_true")

    # relations
    sub.add_parser("relations", help="List all relation types")

    # types
    sub.add_parser("types", help="List node types and tags")

    return p


DISPATCH = {
    "add": cmd_add,
    "show": cmd_show,
    "update": cmd_update,
    "delete": cmd_delete,
    "link": cmd_link,
    "unlink": cmd_unlink,
    "walk": cmd_walk,
    "search": cmd_search,
    "steps": cmd_steps,
    "session-start": cmd_session_start,
    "session-end": cmd_session_end,
    "journal": cmd_journal,
    "today": cmd_today,
    "branch": cmd_branch,
    "return": cmd_return,
    "branches": cmd_branches,
    "tree": cmd_tree,
    "merge": cmd_merge,
    "stale": cmd_stale,
    "abandoned": cmd_abandoned,
    "glance": cmd_glance,
    "context": cmd_context,
    "cleanup": cmd_cleanup,
    "usage": cmd_usage,
    "resolve": cmd_resolve,
    "query": cmd_query,
    "relations": cmd_relations,
    "types": cmd_types,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    # Track usage in pathram2's own LMDB
    from pathram2.usage import track as _track
    _track(args.command)

    # Also track in upakarana2's shared store
    try:
        from upakarana2.store import store as _store2
        _store2.usage.track(f"pathram2 {args.command}", None)
    except Exception:
        pass

    handler = DISPATCH.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
