"""cli_analysis.py — CLI commands for graph analysis.

Handles: analyze (report/edges/swarupa/orphans/components/hubs/siblings/membership/isolation/relations/comments)

Composes primitives from om_analysis.py to produce readable output.
"""

from collections import defaultdict

from . import om, om_analysis as A


def _sep(title, width=80):
    return f"\n{'=' * width}\n  {title}\n{'=' * width}\n"


def _bar(count, total, width=30):
    filled = int(count / total * width) if total else 0
    return "█" * filled + "░" * (width - filled)


def cmd_analyze(args):
    oms = om.load_all()
    sub = args.subcmd or "report"
    layer = args.name  # optional layer or domain filter

    # Resolve target nodes
    if layer and "/" in layer:
        nodes = A.by_domain_prefix(oms, layer)
        label = layer
    elif layer:
        nodes = A.by_layer(oms, layer)
        label = layer
    else:
        nodes = oms
        label = "all"

    if not nodes:
        print(f"No nodes found for '{layer}'")
        return

    if sub == "report":
        _report(nodes, oms, label)

    elif sub == "edges":
        _edges(nodes, label)

    elif sub == "swarupa":
        _swarupa(nodes, oms, label)

    elif sub == "orphans":
        _orphans(nodes, oms, label)

    elif sub == "components":
        _components(nodes, label)

    elif sub == "hubs":
        _hubs(nodes, label)

    elif sub == "siblings":
        _siblings(nodes, label)

    elif sub == "membership":
        _membership(nodes, label)

    elif sub == "isolation":
        _isolation(nodes, label)

    elif sub == "relations":
        _relations(nodes, label)

    elif sub == "comments":
        _comments(nodes, label)

    elif sub == "chains":
        _chains(nodes, label)

    elif sub == "identity":
        _identity(nodes, label)

    elif sub == "cross":
        _cross(oms, args.name)

    elif sub == "ghosts":
        _ghosts(oms)

    elif sub == "fragility":
        _fragility(oms)

    elif sub == "vocabulary":
        _vocabulary(oms)

    elif sub == "cascade":
        _cascade(oms)

    elif sub == "compare":
        _compare(oms)

    elif sub == "health":
        _health(oms)

    else:
        print(f"Unknown analyze command: {sub}")
        print(
            "Available: report, edges, swarupa, orphans, components, hubs, "
            "siblings, membership, isolation, relations, comments, chains, "
            "identity, cross, ghosts, fragility, vocabulary, cascade, compare"
        )


# ── Subcommand implementations ───────────────────────────────────────────────


def _report(nodes, oms, label):
    """Full summary report."""
    r = A.full_report(oms, layer=label if "/" not in label else None,
                      domain_prefix=label if "/" in label else None)
    total = r["total_nodes"]

    print(_sep(f"{label.upper()} ANALYSIS — {total} nodes, {r['total_lines']} lines"))

    # Identity
    no_sw = r["without_swarupa"]
    tree = r["swarupa_tree"]
    print(f"  Identity:")
    print(f"    Without swarupa:  {no_sw['count']:>4} ({no_sw['count']/total*100:.0f}%)  ({no_sw['with_edges']} have 3+ other edges)")
    print(f"    Without shabda:   {r['without_shabda']:>4}")
    print(f"    Swarupa tree:     {tree['roots']} roots, {tree['inner']} inner, {tree['leaves']} leaves, {tree['disconnected']} disconnected")

    # Components
    c = r["components"]
    print(f"\n  Connectivity:")
    print(f"    Components:       {c['count']} ({c['main_size']} in main, {c['islands']} islands)")

    # Relations
    print(f"\n  Relation usage:")
    for rel, info in r["relation_usage"].items():
        bar = _bar(info["nodes"], total)
        print(f"    {rel:<14} {info['uses']:>5} uses  {info['nodes']:>4} nodes ({info['pct']:>4.0f}%)  {bar}")

    # Cross-layer
    print(f"\n  Cross-layer edges:")
    for layer_name, count in r["cross_layer"].items():
        print(f"    → {layer_name:<12} {count:>5}")

    # Hubs
    print(f"\n  Top hubs:")
    for name, total_in, rels in r["hubs"][:8]:
        rel_str = ", ".join(f"{r}:{c}" for r, c in sorted(rels.items(), key=lambda x: -x[1])[:3])
        print(f"    {name:<25} {total_in:>3} incoming  ({rel_str})")

    # Comments
    cs = r["comment_stats"]
    print(f"\n  Comments: {cs['with_comments']} nodes, {cs['total_lines']} lines")

    # Orphans summary
    orphs = r["orphan_targets"]
    total_orphan = sum(v["count"] for v in orphs.values())
    print(f"\n  Orphan targets: {total_orphan} edges → {len(orphs)} unique missing names (top 20 shown)")
    for target, info in list(orphs.items())[:8]:
        print(f"    {target:<25} {info['count']:>3}x")

    print()


def _edges(nodes, label):
    """Edge density analysis."""
    print(_sep(f"{label.upper()} — EDGE DENSITY"))
    density = A.edge_density_by_group(nodes)
    print(f"  {'Group':<30} {'Nodes':>5} {'Total':>6} {'Avg':>6}")
    print(f"  {'─' * 55}")
    for group, d in density.items():
        print(f"  {group:<30} {d['nodes']:>5} {d['edges']:>6} {d['avg']:>6.1f}")
    print()

    # Bottom 15
    sparse = A.edge_density(nodes)
    print(f"  Sparsest nodes:")
    for name, edges, domain in sparse[:15]:
        print(f"    {name:<30} {edges:>2} edges  {domain}")
    print()


def _swarupa(nodes, oms, label):
    """Swarupa hierarchy analysis."""
    tree = A.swarupa_tree(nodes, oms)
    print(_sep(f"{label.upper()} — SWARUPA HIERARCHY"))
    print(f"  {len(tree['roots'])} roots, {len(tree['inner'])} inner, "
          f"{len(tree['leaves'])} leaves, {len(tree['disconnected'])} disconnected\n")

    # Show biggest trees
    children = tree["children"]
    sizes = {}
    for root in tree["roots"]:
        sizes[root] = tree["tree_size"](root)
    for root, size in sorted(sizes.items(), key=lambda x: -x[1])[:10]:
        print(f"  {root} ({size} nodes):")
        for child in sorted(children.get(root, []))[:8]:
            grandchildren = len(children.get(child, []))
            gc_str = f" ({grandchildren} children)" if grandchildren else ""
            print(f"    → {child}{gc_str}")
        if len(children.get(root, [])) > 8:
            print(f"    ... +{len(children[root]) - 8} more")
        print()

    # Show swarupa chains for key nodes
    print(f"  Key chains:")
    for name in sorted(tree["roots"])[:10]:
        chain = tree["chain"](name)
        if len(chain) > 1:
            print(f"    {' → '.join(chain)}")
    print()


def _orphans(nodes, oms, label):
    """Orphan target analysis."""
    orphs = A.orphan_targets(nodes, oms)
    total = sum(v["count"] for v in orphs.values())
    print(_sep(f"{label.upper()} — ORPHAN TARGETS ({len(orphs)} unique, {total} total edges)"))
    for target, info in list(orphs.items())[:30]:
        srcs = info["sources"][:3]
        src_str = ", ".join(f"{s}({r})" for s, r in srcs)
        if len(info["sources"]) > 3:
            src_str += f" +{len(info['sources'])-3}"
        print(f"  {target:<30} {info['count']:>3}x  ← {src_str}")
    print()


def _components(nodes, label):
    """Connected components analysis."""
    comps = A.connected_components(nodes)
    print(_sep(f"{label.upper()} — CONNECTED COMPONENTS ({len(comps)})"))
    print(f"  Main: {len(comps[0])} nodes")
    if len(comps) > 1:
        print(f"  Islands ({len(comps)-1}):")
        for comp in comps[1:20]:
            names = sorted(comp)
            print(f"    {len(comp)} nodes: {', '.join(names[:5])}")
        if len(comps) > 20:
            print(f"    ... +{len(comps)-20} more")
    print()


def _hubs(nodes, label):
    """Hub analysis."""
    hub_list = A.hubs(nodes, min_incoming=3)
    print(_sep(f"{label.upper()} — STRUCTURAL HUBS ({len(hub_list)})"))
    for name, total_in, rels in hub_list[:25]:
        rel_str = ", ".join(f"{r}:{c}" for r, c in sorted(rels.items(), key=lambda x: -x[1])[:5])
        print(f"  {name:<25} {total_in:>3} incoming  ({rel_str})")
    print()


def _siblings(nodes, label):
    """Sibling consistency analysis."""
    gaps = A.sibling_consistency(nodes)
    print(_sep(f"{label.upper()} — SIBLING CONSISTENCY GAPS"))
    for parent, rels in sorted(gaps.items(), key=lambda x: -sum(len(v["missing"]) for v in x[1].values())):
        children_count = len(rels[list(rels.keys())[0]]["have"]) + len(rels[list(rels.keys())[0]]["missing"])
        print(f"\n  {parent}-swarupa ({children_count} children):")
        for rel, info in sorted(rels.items()):
            if len(info["missing"]) <= 3:
                missing_str = ", ".join(info["missing"])
            else:
                missing_str = ", ".join(info["missing"][:3]) + f" +{len(info['missing'])-3}"
            print(f"    {rel}: {len(info['have'])} have it, MISSING from: {missing_str}")
    print()


def _membership(nodes, label):
    """Sthalam/varga membership analysis."""
    # sthalam
    sthalam = A.sthalam_membership(nodes)
    if sthalam:
        print(_sep(f"{label.upper()} — STHALAM MEMBERSHIP"))
        for name, info in sthalam.items():
            status = "✓" if not info["missing"] else f"✗ ({len(info['missing'])} missing)"
            print(f"  {name:<25} {info['declared']}/{info['total']} declared  {status}")
            if info["missing"]:
                for m in info["missing"][:8]:
                    print(f"    - {m}")
                if len(info["missing"]) > 8:
                    print(f"    ... +{len(info['missing'])-8} more")
        print()

    # varga
    varga = A.varga_categories(nodes)
    if varga:
        print(_sep(f"{label.upper()} — VARGA CATEGORIES ({len(varga)})"))
        for cat, members in list(varga.items())[:20]:
            print(f"  {cat:<30} {len(members):>3} members")
        print()


def _isolation(nodes, label):
    """Subdirectory isolation analysis."""
    isolated = A.subdir_isolation(nodes)
    print(_sep(f"{label.upper()} — SUBDIRECTORY ISOLATION ({len(isolated)} zero-connection pairs)"))
    for a, b in isolated:
        print(f"  {a:<15} ↔ {b}")
    print()


def _relations(nodes, label):
    """Relation usage and signatures."""
    usage = A.relation_usage(nodes)
    total = len(nodes)
    print(_sep(f"{label.upper()} — RELATION USAGE"))
    for rel, info in usage.items():
        bar = _bar(info["nodes"], total)
        print(f"  {rel:<14} {info['uses']:>5} uses  {info['nodes']:>4} nodes ({info['pct']:>4.0f}%)  {bar}")

    sigs = A.relation_signature(nodes)
    print(f"\n  Signatures by subdirectory:")
    for sub, rels in sigs.items():
        top3 = list(rels.items())[:3]
        sig_str = ", ".join(f"{r}:{p:.0f}%" for r, p in top3)
        print(f"    {sub:<20} {sig_str}")
    print()


def _comments(nodes, label):
    """Comment analysis."""
    stats = A.comment_stats(nodes)
    print(_sep(f"{label.upper()} — COMMENTS"))
    print(f"  {stats['with_comments']} of {stats['total_nodes']} nodes have comments ({stats['total_lines']} lines)")
    if stats["themes"]:
        print(f"\n  Themes:")
        for theme, count in sorted(stats["themes"].items(), key=lambda x: -x[1]):
            print(f"    {theme:<25} {count}")
    print()


def _chains(nodes, label):
    """Production chain analysis."""
    chains = A.production_chains(nodes)
    broken = A.broken_phala_janya(nodes)
    print(_sep(f"{label.upper()} — PRODUCTION CHAINS"))
    if chains:
        print(f"  Chains ({len(chains)}):")
        for chain in chains[:20]:
            print(f"    {' → '.join(chain)}")
    print(f"\n  Broken phala→janya ({len(broken)}):")
    for prod, product in broken[:20]:
        print(f"    {prod} →(phala) {product}  (no janya back)")
    if len(broken) > 20:
        print(f"    ... +{len(broken)-20} more")
    print()


def _identity(nodes, label):
    """Identity gap analysis (no swarupa)."""
    missing = A.without_swarupa(nodes, min_edges=0)
    by_group = A.without_swarupa_by_group(nodes)
    print(_sep(f"{label.upper()} — IDENTITY GAPS ({len(missing)} nodes without swarupa)"))

    print(f"  By subdirectory:")
    for group, info in by_group.items():
        pct = info["missing"] / info["total"] * 100 if info["total"] else 0
        bar = _bar(info["missing"], info["total"])
        print(f"    {group:<25} {info['missing']:>3}/{info['total']:<3} ({pct:.0f}%)  {bar}")

    print(f"\n  Significant identity-less nodes (3+ edges):")
    with_edges = A.without_swarupa(nodes, min_edges=3)
    for o in with_edges[:20]:
        rels = sorted(set(e["relation"] for e in o["edges"]))
        print(f"    {o['name']:<30} {len(o['edges']):>2} edges ({', '.join(rels)})  {o['domain']}")
    if len(with_edges) > 20:
        print(f"    ... +{len(with_edges)-20} more")
    print()


def _cross(oms, scope):
    """Cross-layer analysis."""
    print(_sep("CROSS-LAYER ANALYSIS"))

    # Layer matrix
    matrix = A.cross_layer_matrix(oms)
    layers = sorted(set(k[0] for k in matrix))
    print(f"  Edge flow matrix (from row → to column):\n")
    print(f"  {'':>12}", end="")
    for to_l in layers:
        print(f" {to_l:>8}", end="")
    print(f" {'nowhere':>8}")
    print(f"  {'─' * (12 + 9 * (len(layers) + 1))}")

    # Get nowhere counts
    all_names = set(o["name"] for o in oms.values())
    names_by_layer = defaultdict(set)
    for o in oms.values():
        names_by_layer[o["layer"]].add(o["name"])

    for from_l in layers:
        print(f"  {from_l:>12}", end="")
        for to_l in layers:
            c = matrix.get((from_l, to_l), 0)
            if c == 0:
                print(f" {'·':>8}", end="")
            else:
                print(f" {c:>8}", end="")
        # nowhere count
        nw = 0
        for o in oms.values():
            if o["layer"] == from_l:
                for e in o["edges"]:
                    if e["target"] not in all_names:
                        nw += 1
        print(f" {nw:>8}")
    print()

    # Swarupa grounding: which layers ground their identity in which
    print(f"  Swarupa grounding (where layers get their IS-A from):\n")
    for from_l in layers:
        for to_l in layers:
            if from_l == to_l:
                continue
            grounding = A.swarupa_grounding(oms, from_l, to_l)
            if grounding:
                total = sum(len(v) for v in grounding.values())
                top3 = list(grounding.items())[:3]
                top_str = ", ".join(f"{t}({len(s)})" for t, s in top3)
                print(f"    {from_l} → {to_l}: {total} nodes ground identity  (top: {top_str})")
    print()

    # Domain bridges
    if scope and "/" not in (scope or ""):
        # Show domain bridges for specific pair e.g. "sangati" → show sangati↔kosha
        from_l = scope
        to_layers = [l for l in layers if l != from_l]
        for to_l in to_layers:
            bridges = A.domain_bridge(oms, from_l, to_l)
            if bridges:
                print(f"  Domain bridges {from_l} → {to_l}:")
                for (src, tgt), count in list(bridges.items())[:15]:
                    print(f"    {src:<25} → {tgt:<25} {count:>3} edges")
                print()

    # Shared names
    print(f"  Names existing in multiple layers:\n")
    for i, a in enumerate(layers):
        for b in layers[i+1:]:
            shared = A.shared_names(oms, a, b)
            if shared:
                print(f"    {a} ∩ {b}: {len(shared)} shared names")
                for name, dom_a, dom_b in shared[:5]:
                    print(f"      {name:<25} {dom_a} | {dom_b}")
                if len(shared) > 5:
                    print(f"      ... +{len(shared)-5} more")
    print()

    # Abheda bridges (concept mapping)
    for i, a in enumerate(layers):
        for b in layers[i+1:]:
            ab = A.abheda_bridges(oms, a, b)
            ba = A.abheda_bridges(oms, b, a)
            if ab or ba:
                print(f"  Abheda bridges {a} ↔ {b}: {len(ab)} → + {len(ba)} ←")
                for name, target, domain in (ab + ba)[:8]:
                    print(f"    {name:<25} abheda→ {target:<25} ({domain})")
                total = len(ab) + len(ba)
                if total > 8:
                    print(f"    ... +{total-8} more")
                print()


def _ghosts(oms):
    """Ghost names analysis — referenced from any layer, exist in none."""
    ghosts = A.ghost_names_across_layers(oms)
    total = sum(v["count"] for v in ghosts.values())
    print(_sep(f"GHOST NAMES — {len(ghosts)} names, {total} edges pointing nowhere"))

    print(f"  {'Name':<30} {'Total':>5}  {'Layers referencing':>40}")
    print(f"  {'─' * 80}")
    for name, info in list(ghosts.items())[:40]:
        layer_str = ", ".join(f"{l}({c})" for l, c in sorted(info["layers"].items(), key=lambda x: -x[1]))
        print(f"  {name:<30} {info['count']:>5}  {layer_str}")
    if len(ghosts) > 40:
        print(f"\n  ... +{len(ghosts)-40} more ghost names")
    print()


def _fragility(oms):
    """Grounding fragility — how fragile are cross-layer swarupa dependencies?"""
    print(_sep("GROUNDING FRAGILITY"))

    pairs = [("kosha", "sangati"), ("bhasha", "sangati"), ("mantra", "kosha")]
    for from_l, to_l in pairs:
        frag = A.grounding_fragility(oms, from_l, to_l)
        if not frag:
            continue
        total_deps = sum(v["dependents"] for v in frag.values())
        islands = sum(1 for v in frag.values() if not v["in_main"])
        island_deps = sum(v["dependents"] for v in frag.values() if not v["in_main"])
        print(f"\n  {from_l} → {to_l}: {total_deps} nodes depend on {len(frag)} targets")
        print(f"    {islands} targets are ISLANDS ({island_deps} nodes grounded in disconnected targets)")
        print(f"\n    {'Target':<25} {'Deps':>5} {'Own edges':>9} {'Status':>8}")
        print(f"    {'─' * 55}")
        for target, info in list(frag.items())[:15]:
            status = "MAIN" if info["in_main"] else "ISLAND"
            print(f"    {target:<25} {info['dependents']:>5} {info['target_edges']:>9} {status:>8}")
    print()


def _vocabulary(oms):
    """Universal vocabulary — sangati nodes referenced across many kosha subdomains."""
    print(_sep("UNIVERSAL VOCABULARY (sangati nodes used by 5+ kosha subdomains)"))
    vocab = A.universal_vocabulary(oms, "sangati", "kosha", min_domains=5)
    for name, count, domains in vocab:
        print(f"  {name:<25} {count:>2} subdomains: {', '.join(domains[:8])}")
        if len(domains) > 8:
            print(f"  {'':<25}    +{len(domains)-8} more")

    print(f"\n  Total: {len(vocab)} universal vocabulary nodes")

    # Also show membership comparison
    print()
    mc = A.membership_comparison(oms)
    print(f"  Membership patterns:")
    print(f"  {'Layer':<12} {'Total':>6} {'sthita':>7} {'varga':>6} {'both':>5} {'neither':>8}")
    print(f"  {'─' * 50}")
    for layer, info in mc.items():
        print(f"  {layer:<12} {info['total']:>6} {info['sthita_only']:>7} {info['varga_only']:>6} {info['both']:>5} {info['neither']:>8}")
    print()


def _cascade(oms):
    """Cascading identity failures — A's swarupa target B also has no swarupa."""
    print(_sep("CASCADING IDENTITY FAILURES"))

    pairs = [("kosha", "sangati"), ("bhasha", "sangati"), ("kosha", "kosha")]
    for from_l, to_l in pairs:
        cascading = A.identity_gap_overlap(oms, from_l, to_l)
        if cascading:
            print(f"\n  {from_l} → {to_l}: {len(cascading)} cascading failures")
            for src, tgt, domain in cascading[:15]:
                print(f"    {src:<25} → swarupa → {tgt:<20} (identity-less)  {domain}")
            if len(cascading) > 15:
                print(f"    ... +{len(cascading)-15} more")

    # Abheda mapping completeness
    print(f"\n  Abheda mapping completeness:")
    for from_l, to_l in [("kosha", "sangati"), ("bhasha", "sangati")]:
        comp = A.abheda_mapping_completeness(oms, from_l, to_l)
        total = len(comp["complete"]) + len(comp["broken"])
        if total:
            print(f"    {from_l} → {to_l}: {len(comp['complete'])}/{total} complete "
                  f"({len(comp['broken'])} point to identity-less targets)")
            for b, t, d in comp["broken"][:5]:
                print(f"      {b:<25} abheda→ {t:<20} (no swarupa)")
            if len(comp["broken"]) > 5:
                print(f"      ... +{len(comp['broken'])-5} more")
    print()


def _compare(oms):
    """Compare relation usage across layers side-by-side."""
    print(_sep("RELATION COMPARISON ACROSS LAYERS"))

    comparison = A.layer_relation_comparison(oms)
    rels = [
        "swarupa", "abheda", "sthita", "yukta", "kriya", "phala",
        "janya", "siddha", "pratipaksha", "varga",
    ]
    layers = list(comparison.keys())

    print(f"  {'Relation':<14}", end="")
    for layer in layers:
        print(f" {layer:>12}", end="")
    print()
    print(f"  {'─' * (14 + 13 * len(layers))}")

    for rel in rels:
        print(f"  {rel:<14}", end="")
        for layer in layers:
            info = comparison[layer].get(rel, {"pct": 0})
            pct = info["pct"]
            if pct == 0:
                print(f" {'·':>12}", end="")
            else:
                print(f" {pct:>10.0f}%", end="")
        print()

    # Edge density comparison
    print(f"\n  Edge density:")
    for layer in layers:
        nodes = A.by_layer(oms, layer)
        total_edges = sum(len(o["edges"]) for o in nodes.values())
        avg = total_edges / len(nodes) if nodes else 0
        print(f"    {layer:<12} {len(nodes):>5} nodes  {avg:.1f} avg edges/node")
    print()


def _health(oms):
    """Graph health — the optimization function."""
    h = A.graph_health(oms)
    print(_sep("GRAPH HEALTH — the optimization function"))
    print(f"  More connected → faster resolution → better answers\n")

    print(f"  {'Metric':<25} {'Value':>10} {'Target':>10}")
    print(f"  {'─' * 50}")
    print(f"  {'Total nodes':<25} {h['total_nodes']:>10}")
    print(f"  {'Total edges':<25} {h['total_edges']:>10}")
    print(f"  {'Avg edge density':<25} {h['avg_density']:>10.1f} {'>7.0':>10}")
    print(f"  {'Swarupa coverage':<25} {h['swarupa_coverage']:>9.0f}% {'>85%':>10}")
    print(f"  {'Shabda coverage':<25} {h['shabda_coverage']:>9.0f}% {'>90%':>10}")
    print(f"  {'Orphan edges':<25} {h['orphan_edges']:>10} {'→ 0':>10}")
    tr = h['total_relations']
    print(f"  {'Active relations':<25} {h['active_relations']:>7}/{tr} {f'{tr}/{tr}':>10}")

    print(f"\n  Per-layer:")
    print(f"  {'Layer':<12} {'Nodes':>6} {'Density':>8} {'Swarupa%':>9} {'Components':>11} {'Islands':>8}")
    print(f"  {'─' * 60}")
    for layer, info in h["layers"].items():
        print(f"  {layer:<12} {info['nodes']:>6} {info['avg_density']:>8.1f} {info['swarupa_pct']:>8.0f}% {info['components']:>11} {info['islands']:>8}")
    print()
