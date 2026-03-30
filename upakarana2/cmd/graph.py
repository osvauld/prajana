"""graph.py — om, tantra, shabda, search commands."""

import sys


def cmd_om(args, store):
    from upakarana2.parsers import om5
    nodes = om5.load_all()

    if args.action == "summary":
        from upakarana2.cmd.dispatch import _print_json
        _print_json(om5.summary(nodes))

    elif args.action == "search":
        results = om5.search(nodes, args.pattern or args.name)
        if not results:
            store.usage.track_miss("om", "search", args.pattern or args.name)
        for r in results:
            print(f"  {r['name']:30s} [{r['layer']}] {r['domain']}")
            for m in r["matches"][:3]:
                print(f"    L{m['line']}: {m['text']}")

    elif args.action == "source":
        node = nodes.get(args.name)
        if node:
            print(node["source"])
        else:
            # Check if it's a generated (avastha) compound node
            _show_generator_source(args.name, nodes)
            store.usage.track_miss("om", "source", args.name)

    elif args.action == "domain":
        info = om5.by_domain(nodes, depth=args.depth)
        if not info:
            store.usage.track_miss("om", "domain")
        for dom, ns in info.items():
            print(f"  {dom}: {len(ns)} nodes")

    elif args.action == "with-relation":
        results = om5.with_relation(nodes, args.relation)
        if not results:
            store.usage.track_miss("om", "with-relation", args.relation)
        print(f"{len(results)} nodes with {args.relation}:")
        for n in results[:20]:
            print(f"  {n['name']}")


def _show_generator_source(name, nodes):
    """Show generator declaration for a compound (avastha-generated) node."""
    from upakarana2.graph.compose import decompose_name, QUALIFIER_CONTEXT, expected_node
    known = set(nodes.keys())
    decomp = decompose_name(name, known)

    if not decomp or not decomp.get("prefix"):
        print(f"Not found: {name}", file=sys.stderr)
        return

    qualifier = decomp["prefix"]["qualifier"]
    base = decomp["prefix"]["base"]
    context = decomp["prefix"]["context"]
    base_node = nodes.get(base)

    print(f"── generator source ({name} ← {base} + avastha {qualifier} {context}) ──\n")

    if base_node:
        print(f"# Base node source ({base}.om5):")
        print(base_node["source"])

    exp = expected_node(qualifier, base)
    if "error" not in exp:
        print(f"\n# Inferred edges for {name}:")
        for rel, targets in exp["static_edges"].items():
            print(f"  ({rel} {' '.join(targets)})")
        if exp.get("overrides"):
            print(f"\n# Shabda overrides applied:")
            for rel, targets in exp["overrides"].items():
                print(f"  override-{rel}: {', '.join(targets)}")
        print(f"\n# Engine extras (injected at runtime):")
        for key, vals in exp.get("live_extras", {}).items():
            print(f"  {key}: {', '.join(vals)}")


def cmd_tantra(args, store):
    from upakarana2.parsers import tantra4
    tantras = tantra4.load_all()

    if args.action == "summary":
        from upakarana2.cmd.dispatch import _print_json
        _print_json(tantra4.summary(tantras))

    elif args.action == "search":
        results = tantra4.search(tantras, args.pattern or args.name)
        if not results:
            store.usage.track_miss("tantra", "search", args.pattern or args.name)
        for r in results:
            print(f"  {r['name']:30s} [{r['group']}]")
            for m in r["matches"][:3]:
                print(f"    L{m['line']}: {m['text']}")

    elif args.action == "source":
        t = tantras.get(args.name)
        if t:
            print(t["source"])
        else:
            store.usage.track_miss("tantra", "source", args.name)
            print(f"Not found: {args.name}", file=sys.stderr)

    elif args.action == "group":
        groups = tantra4.by_group(tantras)
        if args.name:
            gs = groups.get(args.name, [])
            if not gs:
                store.usage.track_miss("tantra", "group", args.name)
            for t in gs:
                print(f"  {t['name']:30s} {t['lines']}L")
        else:
            for g, ts in groups.items():
                print(f"  {g}: {len(ts)} tantras")

    elif args.action == "callgraph":
        cg = tantra4.call_graph(tantras)
        rcg = tantra4.reverse_call_graph(cg)
        callers_count = sum(1 for v in cg.values() if v)
        callees_count = len(rcg)
        isolated = sorted(n for n, calls in cg.items() if not calls and n not in rcg)
        print(f"  {callers_count} callers, {callees_count} callees, {len(isolated)} isolated\n")
        for name, calls in sorted(cg.items()):
            if calls:
                print(f"  {name} → {', '.join(calls)}")
        if isolated:
            print(f"\n  isolated ({len(isolated)}):")
            for n in isolated:
                print(f"    {n}")

    elif args.action == "reachability":
        r = tantra4.reachability(tantras)
        print(f"  entry points: {', '.join(r['entry_points'])}")
        print(f"  reachable: {len(r['reachable'])}, unreachable: {len(r['unreachable'])}\n")
        for depth, names in sorted(r["layers"].items()):
            print(f"  depth {depth}: {', '.join(names)}")
        if r["unreachable"]:
            print(f"\n  unreachable ({len(r['unreachable'])}):")
            for n in sorted(r["unreachable"]):
                g = tantras[n]["group"] if n in tantras else "?"
                print(f"    {n:40s} [{g}]")


def cmd_shabda(args, store):
    from upakarana2.parsers import shabda
    from upakarana2.cmd.dispatch import _print_json
    nodes = shabda.load_all()

    if args.action == "summary":
        _print_json(shabda.summary(nodes))

    elif args.action == "search":
        results = shabda.search(nodes, args.pattern or args.name)
        if not results:
            store.usage.track_miss("shabda", "search", args.pattern or args.name)
        for r in results:
            print(f"  {r['name']}")

    elif args.action == "node":
        node = nodes.get(args.name)
        if node:
            _print_json({"name": node["name"], "fields": node["fields"]})
        else:
            store.usage.track_miss("shabda", "node", args.name)
            print(f"Not found: {args.name}", file=sys.stderr)

    elif args.action == "gaps":
        from upakarana2.graph.health import shabda_gaps
        gaps = shabda_gaps()
        print(f"{len(gaps)} nodes with kriya/phala but no shabda:")
        for g in gaps[:20]:
            print(f"  {g['name']:30s} [{g['layer']}] {g['domain']}")

    elif args.action == "roles":
        from upakarana2.graph.flow import shabda_roles
        r = shabda_roles()
        print("── Existing roles → pipeline outcome ──")
        for role, outcome in r["role_outcomes"].items():
            nodes_with_role = r["by_role"].get(role, [])
            all_words = [w for n in nodes_with_role for w in n["words"]]
            print(f"\n  [{role}] ({len(nodes_with_role)} nodes)  →  {outcome}")
            if all_words:
                print(f"    words: {', '.join(sorted(set(all_words))[:12])}")
            else:
                for n in nodes_with_role[:5]:
                    print(f"    {n['name']}")
        print(f"\n── Shunya-state nodes ({len(r['shunya_states'])}) ──")
        for s in r["shunya_states"]:
            words = ', '.join(s['words']) if s['words'] else "NO WORD KEY"
            flag = "" if s["has_word"] else " ← NEEDS word:"
            print(f"  {s['name']:35s}  words={words}{flag}")
        print(f"\n── Word collisions: {r['collision_count']} ambiguous words ──")
        for w, ns in sorted(r["collisions"].items())[:15]:
            print(f"  {w:20s} → {list(set(ns))}")

    elif args.action == "coverage":
        from upakarana2.graph.flow import shabda_roles
        r = shabda_roles()
        print("── Word coverage by domain ──")
        print(f"  {'domain':15s}  {'coverage':10s}  nodes")
        for domain, stats in r["domain_coverage"].items():
            pct = stats["with_word"] * 100 // stats["total"] if stats["total"] else 0
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            print(f"  {domain:15s}  {bar}  {pct:3d}%  ({stats['with_word']}/{stats['total']})")


def cmd_search(args, store):
    results = []
    if args.scope in ("om", "all"):
        from upakarana2.parsers import om5
        nodes = om5.load_all()
        for r in om5.search(nodes, args.pattern):
            results.append(("om5", r["name"], r.get("domain", "")))
    if args.scope in ("tantra", "all"):
        from upakarana2.parsers import tantra4
        tantras = tantra4.load_all()
        for r in tantra4.search(tantras, args.pattern):
            results.append(("tantra4", r["name"], r.get("group", "")))
    if args.scope in ("shabda", "all"):
        from upakarana2.parsers import shabda
        nodes = shabda.load_all()
        for r in shabda.search(nodes, args.pattern):
            results.append(("shabda", r["name"], ""))

    if not results:
        store.usage.track_miss("search", arg=args.pattern)
    print(f"{len(results)} matches:")
    for kind, name, ctx in results:
        print(f"  [{kind:8s}] {name:30s} {ctx}")
