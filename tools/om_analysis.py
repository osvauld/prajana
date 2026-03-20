"""analysis.py — composable graph analysis primitives.

Reusable functions for analyzing .om graph structure.
Each returns plain data (dicts/lists). CLI and reports compose these.
"""

import os
from collections import defaultdict
from . import om as _om

ALL_RELATIONS = list(_om.RELATION_SUFFIXES.keys())
ALL_LAYERS = _om.LAYERS


# ── Filtering ────────────────────────────────────────────────────────────────


def by_layer(oms, layer):
    """Filter nodes by layer."""
    return {n: o for n, o in oms.items() if o["layer"] == layer}


def by_domain_prefix(oms, prefix):
    """Filter nodes whose domain starts with prefix."""
    prefix = prefix.rstrip("/")
    return {n: o for n, o in oms.items() if o["domain"].startswith(prefix)}


def subdir_of(node):
    """Return subdirectory (second path component) or None."""
    parts = node["domain"].split(os.sep)
    return parts[1] if len(parts) > 1 else None


def group_by_subdir(nodes):
    """Group nodes dict by subdirectory. Returns {subdir: [nodes]}."""
    groups = defaultdict(list)
    for name, o in nodes.items():
        sub = subdir_of(o) or "(top-level)"
        groups[sub].append(o)
    return dict(groups)


def group_by_domain(nodes, depth=None):
    """Group by full domain or domain at depth."""
    groups = defaultdict(list)
    for name, o in nodes.items():
        dom = o["domain"]
        if depth:
            parts = dom.split(os.sep)
            dom = os.sep.join(parts[:depth])
        groups[dom].append(o)
    return dict(groups)


# ── Edge Analysis ────────────────────────────────────────────────────────────


def edge_density(nodes):
    """Edge count per node. Returns list of (name, edge_count, domain)."""
    return sorted(
        [(o["name"], len(o["edges"]), o["domain"]) for o in nodes.values()],
        key=lambda x: x[1],
    )


def edge_density_by_group(nodes, group_fn=None):
    """Avg edge density per group. group_fn(node) -> group_key, default=subdir."""
    if group_fn is None:
        group_fn = lambda o: subdir_of(o) or "(top-level)"
    groups = defaultdict(lambda: {"nodes": 0, "edges": 0})
    for o in nodes.values():
        key = group_fn(o)
        groups[key]["nodes"] += 1
        groups[key]["edges"] += len(o["edges"])
    return {
        k: {**v, "avg": v["edges"] / v["nodes"] if v["nodes"] else 0}
        for k, v in sorted(groups.items())
    }


def relation_usage(nodes):
    """Count relation usage. Returns {relation: {uses, nodes, pct}}."""
    all_rels = ALL_RELATIONS
    counts = defaultdict(int)
    node_sets = defaultdict(set)
    for name, o in nodes.items():
        for e in o["edges"]:
            counts[e["relation"]] += 1
            node_sets[e["relation"]].add(name)
    total = len(nodes)
    return {
        rel: {
            "uses": counts.get(rel, 0),
            "nodes": len(node_sets.get(rel, set())),
            "pct": len(node_sets.get(rel, set())) / total * 100 if total else 0,
        }
        for rel in all_rels
    }


def relation_signature(nodes):
    """Dominant relation types as percentages. Returns {group: {rel: pct}}."""
    groups = defaultdict(lambda: defaultdict(int))
    group_totals = defaultdict(int)
    for o in nodes.values():
        sub = subdir_of(o) or "(top-level)"
        for e in o["edges"]:
            groups[sub][e["relation"]] += 1
            group_totals[sub] += 1
    result = {}
    for sub, rels in sorted(groups.items()):
        total = group_totals[sub]
        result[sub] = {r: c / total * 100 for r, c in sorted(rels.items(), key=lambda x: -x[1])}
    return result


# ── Identity Analysis ────────────────────────────────────────────────────────


def without_swarupa(nodes, min_edges=0):
    """Nodes missing swarupa. Optional filter by minimum edge count."""
    result = []
    for name, o in nodes.items():
        if not any(e["relation"] == "swarupa" for e in o["edges"]):
            if len(o["edges"]) >= min_edges:
                result.append(o)
    return sorted(result, key=lambda o: o["name"])


def without_swarupa_by_group(nodes, group_fn=None):
    """Count nodes missing swarupa per group."""
    if group_fn is None:
        group_fn = lambda o: subdir_of(o) or "(top-level)"
    groups = defaultdict(lambda: {"total": 0, "missing": 0})
    for o in nodes.values():
        key = group_fn(o)
        groups[key]["total"] += 1
        if not any(e["relation"] == "swarupa" for e in o["edges"]):
            groups[key]["missing"] += 1
    return dict(sorted(groups.items()))


def without_shabda(nodes):
    """Nodes with no shabda metadata."""
    return [o for o in nodes.values() if not o["shabda_raw"]]


# ── Swarupa Hierarchy ────────────────────────────────────────────────────────


def swarupa_tree(nodes, all_oms=None):
    """Build IS-A tree. Returns {parent: [children]} and chain function."""
    if all_oms is None:
        all_oms = nodes
    all_names = set(o["name"] for o in all_oms.values())
    node_names = set(o["name"] for o in nodes.values())

    children = defaultdict(list)
    parents = defaultdict(list)
    for name, o in nodes.items():
        for e in o["edges"]:
            if e["relation"] == "swarupa":
                children[e["target"]].append(o["name"])
                parents[o["name"]].append(e["target"])

    def chain(name, visited=None):
        if visited is None:
            visited = set()
        if name in visited:
            return [name]
        visited.add(name)
        result = [name]
        node = next((o for o in nodes.values() if o["name"] == name), None)
        if node:
            for e in node["edges"]:
                if e["relation"] == "swarupa" and e["target"] in node_names:
                    result.extend(chain(e["target"], visited))
                    break  # follow first swarupa only for chain
        return result

    def tree_size(name, visited=None):
        if visited is None:
            visited = set()
        if name in visited:
            return 0
        visited.add(name)
        return 1 + sum(tree_size(c, visited) for c in children.get(name, []))

    # Classify nodes
    leaves = set()
    inner = set()
    roots = set()
    for name in node_names:
        has_parent = name in parents
        has_children = name in children
        if has_parent and not has_children:
            leaves.add(name)
        elif has_parent and has_children:
            inner.add(name)
        elif not has_parent and has_children:
            roots.add(name)

    disconnected = node_names - leaves - inner - roots
    disconnected -= set(n for n in node_names if n in parents)

    return {
        "children": dict(children),
        "parents": dict(parents),
        "chain": chain,
        "tree_size": tree_size,
        "roots": roots,
        "inner": inner,
        "leaves": leaves,
        "disconnected": disconnected,
    }


# ── Orphan & Ghost Analysis ─────────────────────────────────────────────────


def orphan_targets(nodes, all_oms=None):
    """Edge targets that exist nowhere. Returns {target: {count, sources}}."""
    if all_oms is None:
        all_oms = nodes
    all_names = set(o["name"] for o in all_oms.values())
    orphans = defaultdict(lambda: {"count": 0, "sources": []})
    for name, o in nodes.items():
        for e in o["edges"]:
            if e["target"] not in all_names:
                orphans[e["target"]]["count"] += 1
                orphans[e["target"]]["sources"].append((o["name"], e["relation"]))
    return dict(sorted(orphans.items(), key=lambda x: -x[1]["count"]))


def cross_layer_targets(nodes, all_oms):
    """Where edges point by layer. Returns {layer: count, "(nowhere)": count}."""
    names_by_layer = defaultdict(set)
    for o in all_oms.values():
        names_by_layer[o["layer"]].add(o["name"])
    hits = defaultdict(int)
    nowhere = 0
    for o in nodes.values():
        for e in o["edges"]:
            found = False
            for layer, names in names_by_layer.items():
                if e["target"] in names:
                    hits[layer] += 1
                    found = True
                    break
            if not found:
                nowhere += 1
    hits["(nowhere)"] = nowhere
    return dict(sorted(hits.items(), key=lambda x: -x[1]))


# ── Connected Components ─────────────────────────────────────────────────────


def connected_components(nodes):
    """Find connected components (undirected). Returns list of sets, largest first."""
    node_names = set(o["name"] for o in nodes.values())
    adj = defaultdict(set)
    for o in nodes.values():
        for e in o["edges"]:
            if e["target"] in node_names:
                adj[o["name"]].add(e["target"])
                adj[e["target"]].add(o["name"])

    visited = set()
    components = []
    for node in node_names:
        if node in visited:
            continue
        component = set()
        queue = [node]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            component.add(current)
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(component)
    return sorted(components, key=len, reverse=True)


# ── Hub Analysis ─────────────────────────────────────────────────────────────


def hubs(nodes, min_incoming=5):
    """Most-referenced nodes. Returns [(name, total, {rel: count})]."""
    node_names = set(o["name"] for o in nodes.values())
    in_degree = defaultdict(lambda: defaultdict(int))
    for o in nodes.values():
        for e in o["edges"]:
            if e["target"] in node_names:
                in_degree[e["target"]][e["relation"]] += 1
    result = [
        (t, sum(rels.values()), dict(rels))
        for t, rels in in_degree.items()
        if sum(rels.values()) >= min_incoming
    ]
    return sorted(result, key=lambda x: -x[1])


# ── Sibling Consistency ──────────────────────────────────────────────────────


def sibling_consistency(nodes, min_children=3):
    """For each swarupa parent with min_children+, check relation consistency.

    Returns {parent: {relation: {have: [names], missing: [names]}}}
    Only includes relations where majority have it but some don't.
    """
    node_names = set(o["name"] for o in nodes.values())
    children_of = defaultdict(list)
    for o in nodes.values():
        for e in o["edges"]:
            if e["relation"] == "swarupa" and e["target"] in node_names:
                children_of[e["target"]].append(o["name"])

    result = {}
    for parent, children in children_of.items():
        if len(children) < min_children:
            continue
        child_rels = {}
        for child in children:
            node = next((o for o in nodes.values() if o["name"] == child), None)
            if node:
                child_rels[child] = set(e["relation"] for e in node["edges"])

        all_rels = set()
        for rels in child_rels.values():
            all_rels.update(rels)

        inconsistent = {}
        for rel in all_rels - {"swarupa"}:
            have = [c for c, rels in child_rels.items() if rel in rels]
            missing = [c for c, rels in child_rels.items() if rel not in rels]
            if have and missing and len(missing) <= len(have):
                inconsistent[rel] = {"have": have, "missing": missing}

        if inconsistent:
            result[parent] = inconsistent
    return result


# ── Pratipaksha (Opposite) Analysis ──────────────────────────────────────────


def pratipaksha_pairs(nodes):
    """Find declared and undeclared opposite pairs."""
    node_names = set(o["name"] for o in nodes.values())
    declared = []
    for o in nodes.values():
        for e in o["edges"]:
            if e["relation"] == "pratipaksha" and e["target"] in node_names:
                declared.append((o["name"], e["target"]))
    return declared


# ── Membership Analysis ──────────────────────────────────────────────────────


def sthalam_membership(nodes):
    """Check sthalam-sthita membership completeness.

    Returns {sthalam_name: {total, declared, missing: [names]}}
    """
    sthalams = {o["name"]: o for o in nodes.values() if o["name"].endswith("-sthalam")}
    result = {}
    for sthalam_name in sorted(sthalams):
        subdir = sthalam_name.replace("-sthalam", "")
        members = []
        for o in nodes.values():
            parts = o["domain"].split(os.sep)
            if len(parts) > 1 and parts[1] == subdir:
                members.append(o)
        declared = []
        missing = []
        for m in members:
            has = any(
                e["target"] == sthalam_name and e["relation"] == "sthita"
                for e in m["edges"]
            )
            if has:
                declared.append(m["name"])
            else:
                missing.append(m["name"])
        result[sthalam_name] = {
            "total": len(members),
            "declared": len(declared),
            "missing": sorted(missing),
        }
    return result


def varga_categories(nodes):
    """Analyze varga (category) membership. Returns {category: [member_names]}."""
    categories = defaultdict(list)
    for o in nodes.values():
        for e in o["edges"]:
            if e["relation"] == "varga":
                categories[e["target"]].append(o["name"])
    return dict(sorted(categories.items(), key=lambda x: -len(x[1])))


# ── Production Web ───────────────────────────────────────────────────────────


def production_chains(nodes, max_depth=4):
    """Follow phala edges transitively. Returns chains of length > 1."""
    node_names = set(o["name"] for o in nodes.values())
    phala = defaultdict(list)
    for o in nodes.values():
        for e in o["edges"]:
            if e["relation"] == "phala" and e["target"] in node_names:
                phala[o["name"]].append(e["target"])

    chains = []

    def walk(start, path):
        for nxt in phala.get(path[-1], []):
            if nxt == start and len(path) > 1:
                chains.append(path + [nxt])  # cycle
            elif nxt not in path and len(path) < max_depth:
                walk(start, path + [nxt])

    for node in phala:
        walk(node, [node])

    # dedupe cycles
    seen = set()
    unique = []
    for chain in chains:
        key = tuple(sorted(chain[:-1])) if chain[0] == chain[-1] else tuple(chain)
        if key not in seen:
            seen.add(key)
            unique.append(chain)
    return unique


def broken_phala_janya(nodes):
    """Find phala edges where target has no janya back. Returns [(producer, product)]."""
    node_names = set(o["name"] for o in nodes.values())
    broken = []
    for o in nodes.values():
        for e in o["edges"]:
            if e["relation"] == "phala" and e["target"] in node_names:
                target = next((t for t in nodes.values() if t["name"] == e["target"]), None)
                if target:
                    has_janya = any(
                        j["target"] == o["name"] and j["relation"] == "janya"
                        for j in target["edges"]
                    )
                    if not has_janya:
                        broken.append((o["name"], e["target"]))
    return broken


# ── Isolation Analysis ───────────────────────────────────────────────────────


def subdir_isolation(nodes):
    """Find subdirectory pairs with zero cross-edges. Returns [(a, b)]."""
    node_subdir = {}
    for o in nodes.values():
        node_subdir[o["name"]] = subdir_of(o) or "(top-level)"

    subdirs = sorted(set(node_subdir.values()))
    matrix = defaultdict(lambda: defaultdict(int))
    for o in nodes.values():
        src = node_subdir[o["name"]]
        for e in o["edges"]:
            if e["target"] in node_subdir:
                tgt = node_subdir[e["target"]]
                if src != tgt:
                    matrix[src][tgt] += 1

    isolated = []
    checked = set()
    for a in subdirs:
        for b in subdirs:
            if a >= b:
                continue
            if (a, b) in checked:
                continue
            checked.add((a, b))
            if matrix[a][b] == 0 and matrix[b][a] == 0:
                isolated.append((a, b))
    return isolated


# ── Comment Analysis ─────────────────────────────────────────────────────────


def comment_stats(nodes):
    """Analyze comment patterns. Returns {with_comments, total_lines, themes}."""
    with_comments = 0
    total_lines = 0
    themes = defaultdict(int)
    for o in nodes.values():
        if o["comments"]:
            with_comments += 1
            total_lines += len(o["comments"])
            for c in o["comments"]:
                cl = c.lower()
                if "member" in cl or "point here" in cl:
                    themes["membership"] += 1
                elif any(w in cl for w in ["not ", "distinct from", "unlike"]):
                    themes["negation"] += 1
                elif any(w in cl for w in ["example", "e.g."]):
                    themes["examples"] += 1
                else:
                    themes["narrative"] += 1
    return {
        "with_comments": with_comments,
        "total_nodes": len(nodes),
        "total_lines": total_lines,
        "themes": dict(themes),
    }


# ── Full Report ──────────────────────────────────────────────────────────────


# ── Cross-Layer Analysis ──────────────────────────────────────────────────────


def cross_layer_edges(oms, from_layer, to_layer):
    """All edges from one layer to another. Returns [(source, target, relation)]."""
    from_nodes = by_layer(oms, from_layer)
    to_names = set(o["name"] for o in oms.values() if o["layer"] == to_layer)
    edges = []
    for o in from_nodes.values():
        for e in o["edges"]:
            if e["target"] in to_names:
                edges.append((o["name"], e["target"], e["relation"]))
    return edges


def cross_layer_matrix(oms):
    """Edge counts between all layer pairs. Returns {(from, to): count}."""
    names_by_layer = defaultdict(set)
    for o in oms.values():
        names_by_layer[o["layer"]].add(o["name"])
    layers = sorted(names_by_layer.keys())
    matrix = {}
    for from_layer in layers:
        from_nodes = by_layer(oms, from_layer)
        for to_layer in layers:
            to_names = names_by_layer[to_layer]
            count = 0
            for o in from_nodes.values():
                for e in o["edges"]:
                    if e["target"] in to_names:
                        count += 1
            matrix[(from_layer, to_layer)] = count
    return matrix


def shared_names(oms, layer_a, layer_b):
    """Names that exist in both layers. Returns [(name, layer_a_domain, layer_b_domain)]."""
    a_nodes = {o["name"]: o for o in oms.values() if o["layer"] == layer_a}
    b_nodes = {o["name"]: o for o in oms.values() if o["layer"] == layer_b}
    shared = []
    for name in sorted(set(a_nodes) & set(b_nodes)):
        shared.append((name, a_nodes[name]["domain"], b_nodes[name]["domain"]))
    return shared


def swarupa_grounding(oms, from_layer, to_layer):
    """Nodes in from_layer whose swarupa targets are in to_layer.

    Returns {target_in_to_layer: [source_nodes_in_from_layer]}.
    """
    from_nodes = by_layer(oms, from_layer)
    to_names = set(o["name"] for o in oms.values() if o["layer"] == to_layer)
    grounding = defaultdict(list)
    for o in from_nodes.values():
        for e in o["edges"]:
            if e["relation"] == "swarupa" and e["target"] in to_names:
                grounding[e["target"]].append(o["name"])
    return dict(sorted(grounding.items(), key=lambda x: -len(x[1])))


def domain_bridge(oms, layer_a, layer_b):
    """Cross-domain connections between two layers.

    Groups edges by (source_domain, target_domain) pair.
    Returns {(src_domain, tgt_domain): count}.
    """
    a_nodes = by_layer(oms, layer_a)
    b_names = {}
    for o in oms.values():
        if o["layer"] == layer_b:
            b_names[o["name"]] = o["domain"]

    bridges = defaultdict(int)
    for o in a_nodes.values():
        src_parts = o["domain"].split(os.sep)
        src_dom = os.sep.join(src_parts[:2]) if len(src_parts) > 1 else src_parts[0]
        for e in o["edges"]:
            if e["target"] in b_names:
                tgt_parts = b_names[e["target"]].split(os.sep)
                tgt_dom = os.sep.join(tgt_parts[:2]) if len(tgt_parts) > 1 else tgt_parts[0]
                bridges[(src_dom, tgt_dom)] += 1
    return dict(sorted(bridges.items(), key=lambda x: -x[1]))


def ghost_names_across_layers(oms):
    """Names referenced from ANY layer that exist in NO layer.

    Returns {name: {count, layers_referencing: {layer: count}}}.
    """
    all_names = set(o["name"] for o in oms.values())
    ghosts = defaultdict(lambda: {"count": 0, "layers": defaultdict(int)})
    for o in oms.values():
        for e in o["edges"]:
            if e["target"] not in all_names:
                ghosts[e["target"]]["count"] += 1
                ghosts[e["target"]]["layers"][o["layer"]] += 1
    # Convert inner defaultdicts
    return {
        k: {"count": v["count"], "layers": dict(v["layers"])}
        for k, v in sorted(ghosts.items(), key=lambda x: -x[1]["count"])
    }


def abheda_bridges(oms, from_layer, to_layer):
    """Non-difference declarations across layers.

    Returns [(from_name, to_name, from_domain)].
    """
    from_nodes = by_layer(oms, from_layer)
    to_names = set(o["name"] for o in oms.values() if o["layer"] == to_layer)
    bridges = []
    for o in from_nodes.values():
        for e in o["edges"]:
            if e["relation"] == "abheda" and e["target"] in to_names:
                bridges.append((o["name"], e["target"], o["domain"]))
    return sorted(bridges, key=lambda x: x[0])


def grounding_fragility(oms, from_layer, to_layer):
    """How fragile is the swarupa grounding between layers?

    Identifies which target nodes carry the most weight AND whether
    they're in the main component or islands.
    Returns {target: {dependents, in_main, target_edges}}.
    """
    grounding = swarupa_grounding(oms, from_layer, to_layer)
    to_nodes = by_layer(oms, to_layer)
    comps = connected_components(to_nodes)
    main = comps[0] if comps else set()

    result = {}
    for target, sources in grounding.items():
        target_node = next((o for o in to_nodes.values() if o["name"] == target), None)
        target_edges = len(target_node["edges"]) if target_node else 0
        result[target] = {
            "dependents": len(sources),
            "in_main": target in main,
            "target_edges": target_edges,
            "sources_sample": sources[:5],
        }
    return dict(sorted(result.items(), key=lambda x: -x[1]["dependents"]))


def universal_vocabulary(oms, target_layer, source_layer, min_domains=5):
    """Sangati/kosha nodes referenced from many distinct source subdomains.

    Returns [(name, domain_count, domains)].
    """
    source = by_layer(oms, source_layer)
    target_names = set(o["name"] for o in oms.values() if o["layer"] == target_layer)
    ref_domains = defaultdict(set)
    for o in source.values():
        parts = o["domain"].split(os.sep)
        sub = parts[1] if len(parts) > 1 else "(top)"
        for e in o["edges"]:
            if e["target"] in target_names:
                ref_domains[e["target"]].add(sub)
    return sorted(
        [(name, len(doms), sorted(doms)) for name, doms in ref_domains.items() if len(doms) >= min_domains],
        key=lambda x: -x[1],
    )


def layer_relation_comparison(oms, layers=None):
    """Compare relation usage signatures across layers.

    Returns {layer: {relation: {uses, pct}}}.
    """
    if layers is None:
        layers = ALL_LAYERS
    result = {}
    for layer in layers:
        nodes = by_layer(oms, layer)
        usage = relation_usage(nodes)
        result[layer] = usage
    return result


def identity_gap_overlap(oms, layer_a, layer_b):
    """Nodes without swarupa in layer_a whose swarupa targets in layer_b also lack swarupa.

    Finds cascading identity failures: A has no identity, and its would-be
    identity target B is also identity-less.
    """
    a_nodes = by_layer(oms, layer_a)
    b_nodes = by_layer(oms, layer_b)
    b_no_swarupa = set(o["name"] for o in without_swarupa(b_nodes))

    # Nodes in A that DO have swarupa pointing to B, but B target has no swarupa
    cascading = []
    for o in a_nodes.values():
        for e in o["edges"]:
            if e["relation"] == "swarupa" and e["target"] in b_no_swarupa:
                cascading.append((o["name"], e["target"], o["domain"]))
    return cascading


def membership_comparison(oms):
    """Compare sthita vs varga membership patterns across layers.

    Returns {layer: {sthita_count, varga_count, both, neither}}.
    """
    result = {}
    for layer in ALL_LAYERS:
        nodes = by_layer(oms, layer)
        sthita_count = 0
        varga_count = 0
        both = 0
        neither = 0
        for o in nodes.values():
            has_sthita = any(e["relation"] == "sthita" for e in o["edges"])
            has_varga = any(e["relation"] == "varga" for e in o["edges"])
            if has_sthita and has_varga:
                both += 1
            elif has_sthita:
                sthita_count += 1
            elif has_varga:
                varga_count += 1
            else:
                neither += 1
        result[layer] = {
            "total": len(nodes),
            "sthita_only": sthita_count,
            "varga_only": varga_count,
            "both": both,
            "neither": neither,
        }
    return result


def abheda_mapping_completeness(oms, bridge_layer, target_layer):
    """For bridge nodes (abheda→target), check if target has swarupa.

    Returns {complete: [(bridge, target)], broken: [(bridge, target)]}.
    """
    bridges = abheda_bridges(oms, bridge_layer, target_layer)
    target_nodes = by_layer(oms, target_layer)
    target_with_swarupa = set(
        o["name"] for o in target_nodes.values()
        if any(e["relation"] == "swarupa" for e in o["edges"])
    )
    complete = [(b, t, d) for b, t, d in bridges if t in target_with_swarupa]
    broken = [(b, t, d) for b, t, d in bridges if t not in target_with_swarupa]
    return {"complete": complete, "broken": broken}


def graph_health(oms):
    """The optimization function: graph connectivity metrics.

    More connected → faster resolution → better answers.
    Returns dict of measurable health indicators.
    """
    total = len(oms)
    total_edges = sum(len(o["edges"]) for o in oms.values())
    total_swarupa = sum(
        1 for o in oms.values()
        if any(e["relation"] == "swarupa" for e in o["edges"])
    )
    total_shabda = sum(1 for o in oms.values() if o["shabda_raw"])

    layers = {}
    for layer_name in ALL_LAYERS:
        nodes = by_layer(oms, layer_name)
        if not nodes:
            continue
        comps = connected_components(nodes)
        no_sw = len(without_swarupa(nodes))
        layers[layer_name] = {
            "nodes": len(nodes),
            "edges": sum(len(o["edges"]) for o in nodes.values()),
            "avg_density": sum(len(o["edges"]) for o in nodes.values()) / len(nodes),
            "swarupa_pct": (len(nodes) - no_sw) / len(nodes) * 100,
            "components": len(comps),
            "main_component": len(comps[0]) if comps else 0,
            "islands": len(comps) - 1,
        }

    # Orphan count
    all_names = set(o["name"] for o in oms.values())
    orphan_count = 0
    for o in oms.values():
        for e in o["edges"]:
            if e["target"] not in all_names:
                orphan_count += 1

    # Relation completeness
    usage = relation_usage(oms)
    active_rels = sum(1 for r, info in usage.items() if info["uses"] > 0)

    return {
        "total_nodes": total,
        "total_edges": total_edges,
        "avg_density": total_edges / total if total else 0,
        "swarupa_coverage": total_swarupa / total * 100 if total else 0,
        "shabda_coverage": total_shabda / total * 100 if total else 0,
        "orphan_edges": orphan_count,
        "active_relations": active_rels,
        "total_relations": len(ALL_RELATIONS),
        "layers": layers,
    }


def full_report(oms, layer=None, domain_prefix=None):
    """Run all analyses. Returns dict of all results."""
    if layer:
        nodes = by_layer(oms, layer)
    elif domain_prefix:
        nodes = by_domain_prefix(oms, domain_prefix)
    else:
        nodes = oms

    label = layer or domain_prefix or "all"
    total = len(nodes)

    tree = swarupa_tree(nodes, oms)
    comps = connected_components(nodes)

    return {
        "label": label,
        "total_nodes": total,
        "total_lines": sum(o["lines"] for o in nodes.values()),
        "edge_density": edge_density_by_group(nodes),
        "relation_usage": relation_usage(nodes),
        "without_swarupa": {
            "count": len(without_swarupa(nodes)),
            "with_edges": len(without_swarupa(nodes, min_edges=3)),
        },
        "without_shabda": len(without_shabda(nodes)),
        "swarupa_tree": {
            "roots": len(tree["roots"]),
            "inner": len(tree["inner"]),
            "leaves": len(tree["leaves"]),
            "disconnected": len(tree["disconnected"]),
        },
        "components": {
            "count": len(comps),
            "main_size": len(comps[0]) if comps else 0,
            "islands": len(comps) - 1,
        },
        "hubs": hubs(nodes)[:15],
        "orphan_targets": {
            k: v for k, v in list(orphan_targets(nodes, oms).items())[:20]
        },
        "cross_layer": cross_layer_targets(nodes, oms),
        "sibling_gaps": sibling_consistency(nodes),
        "comment_stats": comment_stats(nodes),
    }
