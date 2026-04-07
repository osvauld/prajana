"""inheritance.py — Find inheritance opportunities in the om5 corpus.

Identifies groups of nodes that share common edge declarations which could
be lifted into a varga parent node and inherited via a property-inheritance
boot tantra, making om5 files more compact.
"""

from collections import defaultdict
from upakarana2.parsers import om5

# Edges that are inherently per-node and should not be considered for inheritance
_SKIP_RELATIONS = frozenset(["vishesa", "naama", "domain", "naama-mudra"])


def _edges_by_relation(node):
    """Return {relation: [target, ...]} for a node, excluding skip relations."""
    result = defaultdict(list)
    for e in node["edges"]:
        rel = e["relation"]
        if rel not in _SKIP_RELATIONS:
            result[rel].append(e["target"])
    return dict(result)


def find_inheritance_opportunities(root=None, min_nodes=3, min_savings=6):
    """Find groups of nodes with shared edges, ranked by potential savings.

    Groups nodes by their swarupa tuple (type identity), then checks what
    other edges all members share. Also groups by vishesa parent to detect
    edges that should move up to the varga.

    Returns a list of opportunity dicts, sorted by savings descending.
    """
    nodes = om5.load_all(root)

    # --- Group by swarupa tuple ---
    by_swarupa = defaultdict(list)
    for name, node in nodes.items():
        swarupa_vals = sorted(
            e["target"] for e in node["edges"] if e["relation"] == "swarupa"
        )
        if swarupa_vals:
            by_swarupa[tuple(swarupa_vals)].append(name)

    # --- Group by vishesa parent ---
    by_vishesa = defaultdict(list)
    for name, node in nodes.items():
        for e in node["edges"]:
            if e["relation"] == "vishesa":
                by_vishesa[e["target"]].append(name)

    opportunities = []

    def _check_group(group_key, members, source):
        if len(members) < min_nodes:
            return
        # Find (relation, target) pairs shared by ALL members
        edge_counts = defaultdict(int)
        for name in members:
            node = nodes[name]
            seen = set()
            for e in node["edges"]:
                rel, tgt = e["relation"], e["target"]
                if rel in _SKIP_RELATIONS:
                    continue
                key = (rel, tgt)
                if key not in seen:
                    edge_counts[key] += 1
                    seen.add(key)

        total = len(members)
        shared = [
            (rel, tgt)
            for (rel, tgt), cnt in edge_counts.items()
            if cnt == total
        ]
        savings = total * len(shared)
        if savings >= min_savings:
            # Sample member names for display
            sample = sorted(members)[:6]
            opportunities.append({
                "group_key": group_key,
                "source": source,
                "members": sorted(members),
                "member_count": total,
                "shared_edges": shared,
                "shared_count": len(shared),
                "savings": savings,
                "sample": sample,
            })

    for swarupa_key, members in by_swarupa.items():
        _check_group(
            "swarupa=" + " ".join(swarupa_key),
            members,
            "swarupa-group",
        )

    for parent, members in by_vishesa.items():
        _check_group(
            "vishesa=" + parent,
            members,
            "vishesa-group",
        )

    opportunities.sort(key=lambda x: -x["savings"])
    return opportunities


def report(root=None, min_nodes=3, min_savings=6, verbose=False):
    """Print a human-readable inheritance opportunity report.

    Separates two categories:
      PROPERTY inheritance — non-swarupa edges shared (abheda, sthita, yukta, etc.)
        These are the real wins: removing redundant property declarations.
      STRUCTURAL inheritance — only swarupa itself is shared
        Requires a varga root node; saves less per node but covers more nodes.
    """
    opps = find_inheritance_opportunities(root, min_nodes=min_nodes, min_savings=min_savings)

    # Deduplicate: if same member set appears from both swarupa+vishesa grouping, keep highest savings
    seen_members = {}
    deduped = []
    for o in opps:
        key = frozenset(o["members"])
        if key not in seen_members:
            seen_members[key] = True
            deduped.append(o)
    opps = deduped

    # Classify into property vs structural
    def _is_property(o):
        non_swarupa = [r for r, t in o["shared_edges"] if r != "swarupa"]
        return len(non_swarupa) >= 2

    property_opps = [o for o in opps if _is_property(o)]
    structural_opps = [o for o in opps if not _is_property(o)]

    property_savings = sum(o["savings"] for o in property_opps)
    structural_savings = sum(o["savings"] for o in structural_opps)
    total_savings = property_savings + structural_savings

    def _print_group(o):
        key = o["group_key"]
        shared_str = ", ".join(f"({r}:{t})" for r, t in o["shared_edges"][:4])
        if len(o["shared_edges"]) > 4:
            shared_str += f" +{len(o['shared_edges'])-4}"
        print(f"  {key:<48} {o['member_count']:>5} {o['shared_count']:>6} {o['savings']:>6}")
        print(f"    shared: {shared_str}")
        if verbose:
            print(f"    nodes:  {', '.join(o['sample'])}" + (" ..." if len(o['members']) > 6 else ""))
        print()

    print(f"=== PROPERTY inheritance (multi-edge, high value) — saves {property_savings} declarations ===\n")
    print(f"  {'Group':<48} {'Nodes':>5} {'Shared':>6} {'Saves':>6}")
    print("  " + "-" * 70)
    for o in property_opps:
        _print_group(o)

    print(f"=== STRUCTURAL inheritance (swarupa-only) — saves {structural_savings} declarations ===\n")
    print(f"  {'Group':<48} {'Nodes':>5} {'Shared':>6} {'Saves':>6}")
    print("  " + "-" * 70)
    for o in structural_opps:
        _print_group(o)

    print(f"\nTotal potential savings: {total_savings} edge declarations")
    print(f"  Property inheritance: {property_savings}  |  Structural: {structural_savings}")
    return opps
