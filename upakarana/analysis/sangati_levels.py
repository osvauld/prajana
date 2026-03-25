"""sangati_levels.py — Sangati layer hierarchy analysis.

Computes the tower structure of sangati nodes:
- Level -1: cycle nodes (mutual swarupa references, Tarjan SCC)
- Level 0: roots (no sangati swarupa parents)
- Level N: nodes whose swarupa parents max out at level N-1

Four tools:
1. compute_levels   — full level assignment for all sangati nodes
2. level_summary    — counts and key nodes per level
3. level_generates  — which kosha domains each level shapes
4. level_tree       — swarupa spine from roots to tips
"""

from collections import defaultdict
from upakarana.parsers import om5


def _load_sangati(root=None):
    """Load graph, separate sangati, build swarupa parent/child maps."""
    nodes = om5.load_all(root)

    # All nodes by layer
    sangati = {n: nd for n, nd in nodes.items() if nd.get("layer") == "sangati"}

    # Build outgoing edge index for ALL nodes
    out = {}
    inc = defaultdict(lambda: defaultdict(list))
    for name, node in nodes.items():
        by_rel = defaultdict(list)
        for e in node["edges"]:
            by_rel[e["relation"]].append(e["target"])
            inc[e["target"]][e["relation"]].append(name)
        out[name] = dict(by_rel)

    # Sangati swarupa parents (only sangati→sangati links)
    sangati_names = set(sangati.keys())
    parents = {}
    children = defaultdict(list)
    for name in sangati_names:
        edges = out.get(name, {})
        p = [t for t in edges.get("swarupa", []) if t in sangati_names and t != name]
        parents[name] = p
        for t in p:
            children[t].append(name)

    return nodes, sangati, out, dict(inc), parents, dict(children)


def _tarjan_scc(nodes, parents):
    """Tarjan's SCC algorithm to find cycles in swarupa graph."""
    index_counter = [0]
    stack = []
    lowlink = {}
    index = {}
    on_stack = set()
    sccs = []

    def strongconnect(v):
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack.add(v)

        for w in parents.get(v, []):
            if w not in nodes:
                continue
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], index[w])

        if lowlink[v] == index[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                scc.append(w)
                if w == v:
                    break
            sccs.append(scc)

    for v in sorted(nodes):
        if v not in index:
            strongconnect(v)

    return sccs


def compute_levels(root=None):
    """Compute level assignment for all sangati nodes.

    Returns dict: {node_name: {"level": int, "scc_id": int|None,
                                "parents": [str], "children": [str]}}
    """
    nodes, sangati, out, inc, parents, children = _load_sangati(root)
    sangati_names = set(sangati.keys())

    # Find SCCs
    sccs = _tarjan_scc(sangati_names, parents)

    # Nodes in cycles (SCC size > 1) are level -1
    level_of = {}
    scc_of = {}
    cycle_nodes = set()

    for i, scc in enumerate(sccs):
        if len(scc) > 1:
            for n in scc:
                level_of[n] = -1
                scc_of[n] = i
                cycle_nodes.add(n)

    # Level 0: no sangati swarupa parents (or all parents are cycles)
    for name in sangati_names:
        if name in cycle_nodes:
            continue
        p = parents.get(name, [])
        if not p or all(pp in cycle_nodes for pp in p):
            level_of[name] = 0

    # Iteratively assign levels
    changed = True
    while changed:
        changed = False
        for name in sangati_names:
            if name in level_of:
                continue
            p = parents.get(name, [])
            if p and all(pp in level_of for pp in p):
                max_parent = max(level_of[pp] for pp in p)
                level_of[name] = max(max_parent + 1, 0)  # cycles (-1) → children at 0
                changed = True

    # Anything still unassigned has unresolved deps (shouldn't happen after SCC)
    for name in sangati_names:
        if name not in level_of:
            level_of[name] = -1
            scc_of[name] = -1

    result = {}
    for name in sangati_names:
        result[name] = {
            "level": level_of[name],
            "scc_id": scc_of.get(name),
            "parents": parents.get(name, []),
            "children": children.get(name, []),
        }

    return result


def level_summary(root=None):
    """Counts and key nodes per level."""
    levels = compute_levels(root)
    nodes_all, sangati, out, inc, parents, children = _load_sangati(root)

    by_level = defaultdict(list)
    for name, info in levels.items():
        by_level[info["level"]].append(name)

    summary = {}
    for lvl in sorted(by_level.keys()):
        names = sorted(by_level[lvl])
        # For each node, count how many non-sangati nodes reference it
        refs = {}
        for n in names:
            in_edges = inc.get(n, {})
            total = 0
            for rel, sources in in_edges.items():
                for s in sources:
                    if s in nodes_all and nodes_all[s].get("layer") != "sangati":
                        total += 1
            refs[n] = total

        top = sorted(names, key=lambda n: -refs[n])[:10]
        summary[lvl] = {
            "count": len(names),
            "nodes": names,
            "top": [(n, refs[n]) for n in top],
        }

    return summary


def level_generates(root=None):
    """For each sangati level, which kosha domains does it shape.

    Cross-references sangati levels with kosha nodes that point to them
    via swarupa, sthita, yukta, abheda, siddha, kriya, phala.
    """
    levels = compute_levels(root)
    nodes_all, sangati, out, inc, parents, children = _load_sangati(root)

    GENERATOR_RELS = ["swarupa", "sthita", "yukta", "abheda", "siddha", "kriya", "phala"]

    # For each sangati node, find which kosha domains reference it
    sangati_domains = defaultdict(lambda: defaultdict(set))  # sangati → {domain: {kosha_names}}

    for name, node in nodes_all.items():
        if node.get("layer") == "sangati":
            continue
        domain = node.get("domain", "")
        edges = out.get(name, {})
        for rel in GENERATOR_RELS:
            for t in edges.get(rel, []):
                if t in levels:
                    sangati_domains[t][domain].add(name)

    # Group by level
    by_level = defaultdict(lambda: defaultdict(set))  # level → {domain: {kosha_names}}
    for s_name, domains in sangati_domains.items():
        lvl = levels[s_name]["level"]
        for domain, kosha_names in domains.items():
            by_level[lvl][domain].update(kosha_names)

    result = {}
    for lvl in sorted(by_level.keys()):
        domains = by_level[lvl]
        result[lvl] = {
            "total_kosha": len(set().union(*domains.values())) if domains else 0,
            "domains": {
                d: len(names) for d, names in sorted(domains.items(), key=lambda x: -len(x[1]))
            },
        }

    return result


def level_tree(root=None):
    """The swarupa spine: chain from roots through each level to tips.

    Returns the main trunk (highest-ref node per level) plus branches.
    """
    levels = compute_levels(root)
    nodes_all, sangati, out, inc, parents, children = _load_sangati(root)

    # Count total incoming refs per sangati node
    refs = {}
    for name in levels:
        in_edges = inc.get(name, {})
        total = sum(len(srcs) for srcs in in_edges.values())
        refs[name] = total

    by_level = defaultdict(list)
    for name, info in levels.items():
        by_level[info["level"]].append(name)

    # For each level, find the spine node (most referenced)
    spine = []
    for lvl in sorted(by_level.keys()):
        if lvl == -1:
            # For cycles, pick top 5
            top = sorted(by_level[lvl], key=lambda n: -refs.get(n, 0))[:5]
            spine.append({"level": lvl, "nodes": [(n, refs.get(n, 0)) for n in top]})
        else:
            top = sorted(by_level[lvl], key=lambda n: -refs.get(n, 0))[:3]
            spine.append({"level": lvl, "nodes": [(n, refs.get(n, 0)) for n in top]})

    # Build the main trunk: follow highest-ref node's swarupa chain
    trunk = []
    for lvl in sorted(by_level.keys()):
        if lvl < 0:
            continue
        names = by_level[lvl]
        if names:
            best = max(names, key=lambda n: refs.get(n, 0))
            trunk.append((lvl, best, refs.get(best, 0), levels[best]["parents"]))

    return {"spine": spine, "trunk": trunk, "level_count": dict(
        (lvl, len(names)) for lvl, names in by_level.items()
    )}
