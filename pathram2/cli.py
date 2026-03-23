"""cli.py — CLI dispatch for pathram2."""

import argparse
import json
import sys

from pathram2.graph import Graph
from pathram2.types import RELATIONS, NODE_TYPES, TAGS


def _graph(args) -> Graph:
    path = getattr(args, "db", None)
    return Graph(path=path)


def _print_node(node, verbose=False):
    status = node.shabda.get("status", "")
    status_badge = f" [{status}]" if status else ""
    tag_badge = f" ({node.tag})" if node.tag != "active" else ""
    print(f"  {node.id:30s} {node.type:12s} {node.title}{status_badge}{tag_badge}")
    if verbose and node.body:
        for line in node.body.split("\n")[:5]:
            print(f"    {line}")


def _print_edge(edge):
    reason = edge.shabda.get("reason", "")
    extra = f"  # {reason}" if reason else ""
    print(f"  {edge.source} --{edge.relation}--> {edge.target}{extra}")


# --- Commands ---

def cmd_add(args):
    g = _graph(args)
    shabda = {}
    if args.status:
        shabda["status"] = args.status
    node = g.add(args.type, args.title, body=args.body or "",
                 tag=args.tag or "active", shabda=shabda, id=args.id)
    if args.parent:
        g.link(node.id, args.parent, "sthita")
    if args.session:
        g.link(node.id, args.session, "janya")
    print(f"Created: {node.id}")
    g.close()


def cmd_show(args):
    g = _graph(args)
    node = g.get(args.node_id)
    if not node:
        print(f"Not found: {args.node_id}", file=sys.stderr)
        g.close()
        return
    print(f"# {node.title}")
    print(f"id: {node.id}  type: {node.type}  tag: {node.tag}")
    if node.shabda:
        print(f"shabda: {json.dumps(node.shabda)}")
    print(f"created: {node.created_at}  updated: {node.updated_at}")
    if node.body:
        print()
        print(node.body)
    edges = g.edges_of(node.id)
    if edges:
        print("\nEdges:")
        for e in edges:
            _print_edge(e)
    g.close()


def cmd_update(args):
    g = _graph(args)
    fields = {}
    if args.title:
        fields["title"] = args.title
    if args.body:
        fields["body"] = args.body
    if args.tag:
        fields["tag"] = args.tag
    if args.status:
        fields["shabda"] = {"status": args.status}
    node = g.update(args.node_id, **fields)
    print(f"Updated: {node.id}")
    g.close()


def cmd_delete(args):
    g = _graph(args)
    g.delete(args.node_id)
    print(f"Deleted: {args.node_id}")
    g.close()


def cmd_link(args):
    g = _graph(args)
    shabda = {}
    if args.reason:
        shabda["reason"] = args.reason
    edge = g.link(args.source, args.target, args.relation, shabda=shabda)
    print(f"Linked: {edge.source} --{edge.relation}--> {edge.target}")
    g.close()


def cmd_unlink(args):
    g = _graph(args)
    g.unlink(args.source, args.target, args.relation)
    print(f"Unlinked: {args.source} -> {args.target}")
    g.close()


def cmd_walk(args):
    g = _graph(args)
    if args.incoming:
        targets = g.walk_in(args.node_id, args.relation)
    else:
        targets = g.walk(args.node_id, args.relation)
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
    print(f"Found {len(nodes)} nodes:")
    for n in nodes:
        _print_node(n)
    g.close()


def cmd_steps(args):
    g = _graph(args)
    q = g.q().type("step")
    if args.status:
        q = q.shabda("status", args.status)
    if args.tag:
        q = q.tag(args.tag)
    nodes = q.sort("created_at").load()
    print(f"{len(nodes)} steps:")
    for n in nodes:
        _print_node(n)
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
    session = session_end(g.store, sid)
    hours = session.shabda.get("hours", 0)
    print(f"Session ended: {session.id} ({hours}h)")
    g.close()


def cmd_journal(args):
    from pathram2.temporal import journal
    g = _graph(args)
    sessions = journal(g.store, n=args.n)
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
    print(f"{len(nodes)} nodes today:")
    for n in nodes:
        _print_node(n)
    g.close()


def cmd_branch(args):
    from pathram2.branch import branch
    g = _graph(args)
    node = branch(g.store, args.from_node, args.reason, args.title)
    print(f"Branched: {node.id} (from {args.from_node})")
    g.close()


def cmd_return(args):
    from pathram2.branch import return_to
    from pathram2.temporal import current_session
    g = _graph(args)
    sid = args.session_id
    if not sid:
        cs = current_session(g.store)
        if cs:
            sid = cs.id
    if sid:
        return_to(g.store, sid, args.node_id)
        print(f"Returned to: {args.node_id}")
    else:
        print("No session to mark return from", file=sys.stderr)
    g.close()


def cmd_branches(args):
    from pathram2.branch import open_branches
    g = _graph(args)
    branches = open_branches(g.store)
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
    tree = branch_tree(g.store, root=args.root)
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
    node = g.merge(args.node_ids, args.into, args.title, body=args.body or "")
    print(f"Merged into: {node.id}")
    g.close()


def cmd_stale(args):
    g = _graph(args)
    nodes = g.stale(args.days)
    print(f"{len(nodes)} nodes stale >{args.days} days:")
    for n in nodes:
        _print_node(n)
    g.close()


def cmd_abandoned(args):
    from pathram2.branch import abandoned
    g = _graph(args)
    nodes = abandoned(g.store, stale_days=args.days)
    print(f"{len(nodes)} abandoned steps:")
    for n in nodes:
        _print_node(n)
    g.close()


def cmd_glance(args):
    g = _graph(args)
    total = g.q().count()
    steps = g.q().type("step").count()
    done = g.q().type("step").shabda("status", "done").count()
    pending = g.q().type("step").shabda("status", "pending").count()
    sessions = g.q().type("session").count()
    discoveries = g.q().type("discovery").count()

    from pathram2.branch import open_branches
    branches = open_branches(g.store)

    print("## pathram2 glance")
    print(f"Nodes: {total}  |  Sessions: {sessions}  |  Discoveries: {discoveries}")
    print(f"Steps: {steps} (done: {done}, pending: {pending})")
    if branches:
        print(f"Open branches: {len(branches)}")
        for b in branches[:3]:
            print(f"  {b['branch'].id} (from {b['origin'].id}): {b['reason']}")
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
            q = q.node(val)

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
    s.add_argument("--id")
    s.add_argument("--parent", "-p", help="Link via sthita to parent")
    s.add_argument("--session", "-s", help="Link via janya to session")
    s.add_argument("--status", help="Set shabda.status")

    # show
    s = sub.add_parser("show", help="Show a node")
    s.add_argument("node_id")

    # update
    s = sub.add_parser("update", help="Update a node")
    s.add_argument("node_id")
    s.add_argument("--title")
    s.add_argument("--body", "-b")
    s.add_argument("--tag", "-t")
    s.add_argument("--status")

    # delete
    s = sub.add_parser("delete", help="Delete a node")
    s.add_argument("node_id")

    # link
    s = sub.add_parser("link", help="Create an edge")
    s.add_argument("source")
    s.add_argument("target")
    s.add_argument("relation", choices=list(RELATIONS.keys()))
    s.add_argument("--reason", "-r")

    # unlink
    s = sub.add_parser("unlink", help="Remove an edge")
    s.add_argument("source")
    s.add_argument("target")
    s.add_argument("relation", nargs="?")

    # walk
    s = sub.add_parser("walk", help="Walk edges from a node")
    s.add_argument("node_id")
    s.add_argument("relation")
    s.add_argument("--incoming", "-i", action="store_true")

    # search
    s = sub.add_parser("search", help="Search nodes by pattern")
    s.add_argument("pattern")

    # steps
    s = sub.add_parser("steps", help="List steps")
    s.add_argument("--status")
    s.add_argument("--tag")

    # session-start
    s = sub.add_parser("session-start", help="Start a session")
    s.add_argument("title")
    s.add_argument("--id")

    # session-end
    s = sub.add_parser("session-end", help="End current session")
    s.add_argument("session_id", nargs="?")

    # journal
    s = sub.add_parser("journal", help="Show recent sessions")
    s.add_argument("-n", type=int, default=5)

    # today
    sub.add_parser("today", help="Nodes touched today")

    # branch
    s = sub.add_parser("branch", help="Branch from a node")
    s.add_argument("from_node")
    s.add_argument("reason")
    s.add_argument("title")

    # return
    s = sub.add_parser("return", help="Mark return to original task")
    s.add_argument("node_id")
    s.add_argument("--session-id")

    # branches
    sub.add_parser("branches", help="Show open branches")

    # tree
    s = sub.add_parser("tree", help="Show branch DAG")
    s.add_argument("root", nargs="?")

    # merge
    s = sub.add_parser("merge", help="Consolidate nodes")
    s.add_argument("node_ids", nargs="+")
    s.add_argument("--into", required=True, choices=list(NODE_TYPES.keys()))
    s.add_argument("--title", required=True)
    s.add_argument("--body", "-b")

    # stale
    s = sub.add_parser("stale", help="Show stale nodes")
    s.add_argument("days", type=int)

    # abandoned
    s = sub.add_parser("abandoned", help="Show abandoned steps")
    s.add_argument("--days", type=int, default=7)

    # glance
    sub.add_parser("glance", help="Quick summary")

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

    # Track usage (shared with upakarana)
    from upakarana.usage import track
    track(f"pathram2 {args.command}", None)

    handler = DISPATCH.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
