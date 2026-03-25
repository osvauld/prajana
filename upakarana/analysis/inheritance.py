"""inheritance.py — Full inheritance chain analysis.

Three tools:
1. hub_compose    — nodes ranked by composition potential
2. derivative_chain — walk kramanusara to trace calculus chains
3. compose_potential — for two nodes, show what their composition would inherit
"""

from collections import defaultdict
from upakarana.parsers import om5

# Relations that carry meaning for composition
INHERITABLE = [
    "yukta", "phala", "abheda", "pratipaksha", "sthita",
    "siddha", "kriya", "janya", "matra", "drishthanta",
]

# Relations that define structure (not inherited, define the node itself)
STRUCTURAL = ["swarupa", "vishesa", "avastha", "krama"]


def _load_graph(root=None):
    """Load graph and build edge indices."""
    nodes = om5.load_all(root)
    # outgoing: node → {relation: [targets]}
    out = {}
    # incoming: node → {relation: [sources]}
    inc = defaultdict(lambda: defaultdict(list))
    for name, node in nodes.items():
        by_rel = defaultdict(list)
        for e in node["edges"]:
            by_rel[e["relation"]].append(e["target"])
            inc[e["target"]][e["relation"]].append(name)
        out[name] = dict(by_rel)
    return nodes, out, dict(inc)


def _swarupa_ancestors(name, out, max_depth=10):
    """Walk swarupa chain upward, return ordered ancestor list."""
    chain = []
    visited = {name}
    current = name
    for _ in range(max_depth):
        targets = out.get(current, {}).get("swarupa", [])
        # Filter self-refs and mantras for cleaner chains
        parents = [t for t in targets if t not in visited and not t.endswith("-mantra")]
        if not parents:
            break
        nxt = parents[0]
        chain.append(nxt)
        visited.add(nxt)
        current = nxt
    return chain


def hub_compose(root=None, top_n=30, layer=None):
    """Rank nodes by composition potential across ALL layers.

    Generative power comes from different sources per layer:
    - kosha: avastha qualifiers × mantra connections
    - sangati: swarupa children × incoming yukta/sthita references
    - mantra: krama chain depth × janya connections

    Score = connectivity × (generators + 1) × (references + 1)
    where generators = avastha OR swarupa-children (whichever is bigger)
    and references = mantras OR incoming-yukta+sthita (whichever is bigger)
    """
    nodes, out, inc = _load_graph(root)

    results = []
    for name, node in nodes.items():
        node_layer = node.get("layer", "")
        if layer and node_layer != layer:
            continue

        edges_out = out.get(name, {})
        edges_in = inc.get(name, {})

        # Count unique outgoing targets (deduplicated)
        all_targets = set()
        for rel, targets in edges_out.items():
            for t in targets:
                all_targets.add(t)
        out_count = len(all_targets)

        # Count unique incoming sources
        all_sources = set()
        for rel, sources in edges_in.items():
            for s in sources:
                all_sources.add(s)
        in_count = len(all_sources)

        # Avastha qualifiers (kosha-style generation)
        avastha = edges_out.get("avastha", [])
        avastha_count = len(avastha)

        # Swarupa children (sangati-style generation — IS-A hierarchy)
        swarupa_children = len(set(edges_in.get("swarupa", [])))

        # Generators = max(avastha, swarupa-children)
        generators = max(avastha_count, swarupa_children)
        gen_type = "avastha" if avastha_count >= swarupa_children else "swarupa"

        # Mantra connections (kosha — phala edges to mantras)
        phala = edges_out.get("phala", [])
        mantra_count = len([p for p in phala if p.endswith("-mantra")])

        # Incoming references (sangati — yukta + sthita pointing here)
        yukta_in = len(set(edges_in.get("yukta", [])))
        sthita_in = len(set(edges_in.get("sthita", [])))
        ref_in = yukta_in + sthita_in

        # References = max(mantras, incoming-references)
        references = max(mantra_count, ref_in)
        ref_type = "mantras" if mantra_count >= ref_in else "yukta+sthita"

        # Inheritable richness (yukta, abheda, etc.)
        inheritable_count = 0
        for rel in INHERITABLE:
            inheritable_count += len(set(edges_out.get(rel, [])))

        # kramanusara (derivative chain) connections
        krama_out = edges_out.get("kramanusara", [])
        krama_in = edges_in.get("kramanusara", [])
        derivative_depth = len(krama_out) + len(krama_in)

        # Score: connectivity × (generators + 1) × (references + 1)
        score = (out_count + in_count) * (generators + 1) * (references + 1)

        results.append({
            "name": name,
            "score": score,
            "out": out_count,
            "in": in_count,
            "generators": generators,
            "gen_type": gen_type,
            "gen_detail": avastha if gen_type == "avastha" else [],
            "references": references,
            "ref_type": ref_type,
            "inheritable": inheritable_count,
            "derivative_depth": derivative_depth,
            "layer": node_layer,
        })

    results.sort(key=lambda r: -r["score"])
    return results[:top_n]


def derivative_chain(root=None):
    """Walk kramanusara edges to trace the full calculus/derivative chain.

    kramanusara encodes "is the derivative of" / "rate of change of".
    velocity kramanusara→ displacement means velocity = d(displacement)/dt.

    Returns chains from highest derivative down to base quantity,
    plus the reverse (integral) direction.
    """
    nodes, out, inc = _load_graph(root)

    # Build kramanusara graph (directed: source is derivative of target)
    krama_forward = {}   # derivative → base (velocity → displacement)
    krama_reverse = defaultdict(list)  # base → [derivatives]
    for name in nodes:
        targets = out.get(name, {}).get("kramanusara", [])
        if targets:
            krama_forward[name] = targets
            for t in targets:
                krama_reverse[t].append(name)

    # Find chain roots: nodes that are derivatives but not derived from anything
    # (highest derivative in the chain)
    all_derivatives = set(krama_forward.keys())
    all_bases = set()
    for targets in krama_forward.values():
        all_bases.update(targets)
    # Roots: bases that are not themselves derivatives
    chain_roots = all_bases - all_derivatives
    # Leaves: derivatives that nobody derives from
    chain_leaves = all_derivatives - all_bases

    # Walk full chains from roots (base) upward through derivatives
    chains = []
    visited_global = set()

    def walk_up(base, visited):
        """Walk from base quantity up through derivatives."""
        chain = [base]
        visited.add(base)
        derivatives = krama_reverse.get(base, [])
        for d in derivatives:
            if d not in visited:
                sub = walk_up(d, visited)
                chains.append([base] + sub)
        return chain

    for r in sorted(chain_roots):
        if r not in visited_global:
            walk_up(r, visited_global)

    # Build full linear chains
    linear_chains = []
    for leaf in sorted(chain_leaves):
        chain = [leaf]
        visited = {leaf}
        current = leaf
        while current in krama_forward:
            targets = krama_forward[current]
            nxt = [t for t in targets if t not in visited]
            if not nxt:
                break
            chain.append(nxt[0])
            visited.add(nxt[0])
            current = nxt[0]
        if len(chain) > 1:
            linear_chains.append(chain)

    # Collect all nodes in kramanusara graph with their properties
    krama_nodes = set(krama_forward.keys()) | all_bases
    node_info = {}
    for name in krama_nodes:
        edges_out = out.get(name, {})
        node_info[name] = {
            "avastha": edges_out.get("avastha", []),
            "phala_mantras": [p for p in edges_out.get("phala", [])
                             if p.endswith("-mantra")],
            "matra": edges_out.get("matra", []),
            "layer": nodes.get(name, {}).get("layer", ""),
        }

    return {
        "chains": linear_chains,
        "roots": sorted(chain_roots),
        "leaves": sorted(chain_leaves),
        "forward": dict(krama_forward),
        "reverse": dict(krama_reverse),
        "node_info": node_info,
        "total_nodes": len(krama_nodes),
    }


def compose_potential(name_a, name_b, root=None):
    """For two nodes, show what their composition A-B would inherit.

    Traces:
    1. What edges A has (potential qualifiers/context it brings)
    2. What edges B has (base properties)
    3. What A-B would get: B's inheritable edges + A's context
    4. What overrides would be needed (from existing similar compounds)
    5. Whether A-B already exists
    """
    nodes, out, inc = _load_graph(root)

    compound_name = f"{name_a}-{name_b}"
    exists = compound_name in nodes

    a_edges = out.get(name_a, {})
    b_edges = out.get(name_b, {})

    # What A brings (as qualifier/context)
    a_context = {}
    for rel in INHERITABLE + STRUCTURAL:
        targets = a_edges.get(rel, [])
        if targets:
            a_context[rel] = list(set(targets))

    # What B brings (as base — inheritable properties)
    b_inheritable = {}
    for rel in INHERITABLE:
        targets = b_edges.get(rel, [])
        if targets:
            b_inheritable[rel] = list(set(targets))

    b_structural = {}
    for rel in STRUCTURAL:
        targets = b_edges.get(rel, [])
        if targets:
            b_structural[rel] = list(set(targets))

    # Swarupa chains
    a_ancestors = _swarupa_ancestors(name_a, out)
    b_ancestors = _swarupa_ancestors(name_b, out)

    # If compound exists, show what it actually has vs prediction
    actual = {}
    if exists:
        compound_edges = out.get(compound_name, {})
        for rel in INHERITABLE + STRUCTURAL:
            targets = compound_edges.get(rel, [])
            if targets:
                actual[rel] = list(set(targets))

    # Find similar compounds (same base, different qualifier)
    similar = []
    for name in nodes:
        if name.endswith(f"-{name_b}") and name != compound_name:
            similar.append(name)

    # Predicted edges for A-B
    predicted = {}
    # Start with B's inheritable edges
    for rel, targets in b_inheritable.items():
        predicted[rel] = list(targets)
    # Add swarupa → B (the IS-A link)
    predicted["swarupa"] = [name_b]
    # Add vishesa from B (varga inheritance)
    if "vishesa" in b_structural:
        predicted["vishesa"] = list(b_structural["vishesa"])

    # Override analysis: what similar compounds changed from base
    override_patterns = defaultdict(list)
    for sim in similar:
        sim_edges = out.get(sim, {})
        for rel in INHERITABLE:
            sim_targets = set(sim_edges.get(rel, []))
            base_targets = set(b_edges.get(rel, []))
            if sim_targets != base_targets and sim_targets:
                override_patterns[rel].append({
                    "compound": sim,
                    "has": list(sim_targets),
                    "base_has": list(base_targets),
                })

    return {
        "a": name_a,
        "b": name_b,
        "compound": compound_name,
        "exists": exists,
        "a_context": a_context,
        "a_ancestors": a_ancestors,
        "b_inheritable": b_inheritable,
        "b_structural": b_structural,
        "b_ancestors": b_ancestors,
        "predicted": predicted,
        "actual": actual,
        "similar_compounds": similar,
        "override_patterns": dict(override_patterns),
    }


# ── Sangati generator roots ─────────────────────────────────────────────────
# These are the root sangati concepts that act as generators for kosha nodes.
# A node is a generator root if it's sangati layer AND has significant
# incoming sthita/yukta/swarupa from other layers.

# The connection types from kosha → sangati that define generation:
GENERATOR_EDGES = {
    "sthita":  "context",       # kosha.sthita → sangati = "exists in this pattern"
    "swarupa": "is-a",          # kosha.swarupa → sangati = "is a kind of this"
    "yukta":   "dependency",    # kosha.yukta → sangati = "depends on this pattern"
    "abheda":  "equivalence",   # kosha.abheda → sangati = "same as this pattern"
    "kriya":   "operation",     # kosha.kriya → sangati = "operated on by this"
    "siddha":  "established",   # kosha.siddha → sangati = "grounded in this"
    "phala":   "produces",      # kosha.phala → sangati = "produces this pattern"
}


def generator_product(root=None, min_generators=2, layer_filter=None):
    """For each node, show which sangati generators shape it.

    A node's identity = product of all sangati generators it connects to.
    Multiple generators on the same node = richer composition potential.

    Works for ALL layers including sangati itself — sangati nodes compose
    each other (krama shaped by niyama+kaala, parampara shaped by avrti+krama).

    Returns nodes grouped by their generator signature (set of sangati roots).
    """
    nodes, out, inc = _load_graph(root)

    # Identify sangati nodes (layer == sangati)
    sangati_names = set(
        name for name, node in nodes.items()
        if node.get("layer") == "sangati"
    )

    # For each node, find which sangati generators it connects to
    node_generators = {}
    for name, node in nodes.items():
        node_layer = node.get("layer", "")
        if layer_filter and node_layer != layer_filter:
            continue

        edges_out = out.get(name, {})
        generators = {}  # sangati_name → {relations connecting to it}

        for rel, role in GENERATOR_EDGES.items():
            targets = edges_out.get(rel, [])
            for t in targets:
                # A sangati generator must be: (a) sangati layer, (b) not self
                if t in sangati_names and t != name:
                    if t not in generators:
                        generators[t] = {"roles": set(), "name": t}
                    generators[t]["roles"].add(role)

        # Also check swarupa ancestors — walk up to find sangati roots
        ancestors = _swarupa_ancestors(name, out)
        for anc in ancestors:
            if anc in sangati_names and anc != name:
                if anc not in generators:
                    generators[anc] = {"roles": set(), "name": anc}
                generators[anc]["roles"].add("ancestor")

        if len(generators) >= min_generators:
            # Sort generators by number of roles (most connected first)
            gen_list = sorted(
                generators.values(),
                key=lambda g: -len(g["roles"])
            )
            node_generators[name] = {
                "name": name,
                "layer": node_layer,
                "generator_count": len(generators),
                "generators": gen_list,
                "avastha": edges_out.get("avastha", []),
                "signature": frozenset(generators.keys()),
            }

    # Group by generator count for summary
    by_count = defaultdict(list)
    for ng in node_generators.values():
        by_count[ng["generator_count"]].append(ng)

    # Find shared generator signatures (nodes with same sangati generators)
    by_signature = defaultdict(list)
    for ng in node_generators.values():
        by_signature[ng["signature"]].append(ng["name"])

    # Find the most common generators across all nodes
    generator_frequency = defaultdict(int)
    generator_roles = defaultdict(lambda: defaultdict(int))
    for ng in node_generators.values():
        for g in ng["generators"]:
            generator_frequency[g["name"]] += 1
            for role in g["roles"]:
                generator_roles[g["name"]][role] += 1

    return {
        "nodes": node_generators,
        "by_count": {k: len(v) for k, v in sorted(by_count.items(), reverse=True)},
        "top_generators": sorted(
            generator_frequency.items(), key=lambda x: -x[1]
        ),
        "generator_roles": {
            name: dict(roles)
            for name, roles in sorted(
                generator_roles.items(),
                key=lambda x: -sum(x[1].values())
            )
        },
        "shared_signatures": {
            str(sorted(sig)): names
            for sig, names in sorted(
                by_signature.items(), key=lambda x: -len(x[1])
            )
            if len(names) > 1
        },
        "total_analyzed": len(node_generators),
    }
