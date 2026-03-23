"""branch.py — Branch/return tracking for non-linear development."""

from pathram2.types import Node
from pathram2.graph.crud import add_node, get_node, link
from pathram2.graph.walk import walk, walk_in
from pathram2.graph.query import by_type, by_tag, stale


def branch(store, from_node: str, reason: str, title: str,
           type: str = "step", **kw) -> Node:
    """Create a branch (tangent) from an existing node.

    Records WHY we branched in edge shabda.
    """
    node = add_node(store, type, title, **kw)
    link(store, node.id, from_node, "branches-from", shabda={"reason": reason})
    return node


def return_to(store, session_id: str, original_node: str):
    """Mark that a session returned to an original task after a tangent."""
    link(store, session_id, original_node, "returns-to")


def open_branches(store) -> list[dict]:
    """Find branches that were never returned to.

    A branch is open if:
    - A node has a 'branches-from' edge (it IS a tangent)
    - No 'returns-to' edge points back to the branch origin
    """
    results = []

    # Find all nodes that branch from something
    branch_edge_keys = store.scan("idx_edges_rel", "branches-from:")
    for ek_key in branch_edge_keys:
        ek = ek_key.split(":", 1)[1]
        d = store.get("edges", ek)
        if not d:
            continue

        branch_node_id = d["source"]
        origin_id = d["target"]
        reason = d.get("shabda", {}).get("reason", "")

        # Check if any returns-to edge points to the origin
        returns = walk_in(store, origin_id, "returns-to")
        if not returns:
            branch_node = get_node(store, branch_node_id)
            origin_node = get_node(store, origin_id)
            results.append({
                "branch": branch_node,
                "origin": origin_node,
                "reason": reason,
            })

    return results


def abandoned(store, stale_days: int = 7) -> list[Node]:
    """Find nodes that are likely abandoned.

    A node is abandoned if:
    - It's a step with status pending/next
    - It hasn't been updated in stale_days
    - Its dependencies (nodes it depends-on) are all done
    """
    stale_nodes = stale(store, stale_days)
    results = []
    for node in stale_nodes:
        if node.type != "step":
            continue
        status = node.shabda.get("status", "pending")
        if status not in ("pending", "next"):
            continue

        # Check if all dependencies are done
        deps = walk(store, node.id, "depends-on")
        all_deps_done = True
        for dep_id in deps:
            dep = get_node(store, dep_id)
            if dep and dep.tag != "done" and dep.shabda.get("status") != "done":
                all_deps_done = False
                break

        if all_deps_done:
            results.append(node)

    return results


def branch_tree(store, root: str | None = None) -> dict:
    """Build the branch DAG as a nested dict.

    If root is None, finds all roots (nodes that branch but aren't branched from).
    """
    if root:
        return _build_subtree(store, root)

    # Find all roots: nodes that are targets of branches-from but don't branch themselves
    all_origins = set()
    all_branches = set()

    branch_edge_keys = store.scan("idx_edges_rel", "branches-from:")
    for ek_key in branch_edge_keys:
        ek = ek_key.split(":", 1)[1]
        d = store.get("edges", ek)
        if d:
            all_branches.add(d["source"])
            all_origins.add(d["target"])

    roots = all_origins - all_branches
    if not roots:
        roots = all_origins  # cycles — just show everything

    tree = {}
    for r in roots:
        node = get_node(store, r)
        if node:
            tree[r] = _build_subtree(store, r)
    return tree


def _build_subtree(store, node_id: str) -> dict:
    """Recursively build branch subtree."""
    node = get_node(store, node_id)
    if not node:
        return {"id": node_id, "not_found": True}

    # Find nodes that branch FROM this one
    children = walk_in(store, node_id, "branches-from")
    subtree = {
        "id": node_id,
        "title": node.title,
        "type": node.type,
        "tag": node.tag,
        "branches": [],
    }
    for child_id in children:
        # Get the reason from the edge
        ek = f"{child_id}|branches-from|{node_id}"
        edge_d = store.get("edges", ek)
        reason = edge_d.get("shabda", {}).get("reason", "") if edge_d else ""
        child_tree = _build_subtree(store, child_id)
        child_tree["reason"] = reason
        subtree["branches"].append(child_tree)

    return subtree
