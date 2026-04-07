"""analyze.py — a command: static graph analysis (15 subcommands).

Dropped vs upakarana: all 29 cross-product discovery commands
(compose-karma, compose-lakshana, compose-declension, compose-conjugation,
compose-samasa, compose-collisions, compose-deriv-avastha, compose-grammar,
compose-summary, compose-inherit, compose-validity, compose-words,
compose-rules, compose-curated, compose-logic, compose-lift,
hubs-compose, derivative-chain, compose-potential, generator-product,
sangati-levels, sangati-at, sangati-tree, sangati-generates,
gen-expected, gen-candidates, gen-validate-all, patterns, grounding,
vocabulary, parallel, dataflow).
"""

import sys


def cmd_analyze(args, store):

    if args.action == "ghosts":
        from upakarana2.graph.health import find_ghosts
        result = find_ghosts()
        print(f"{result['total_ghosts']} ghost nodes ({result['total_ghost_edges']} broken edges):")
        for g in result["ghosts"][:30]:
            refs = ", ".join(f"{r[0]}({r[1]})" for r in g["referrers"][:3])
            print(f"  {g['name']:30s} {g['ref_count']:3d}x  {refs}")

    elif args.action == "incoming":
        from upakarana2.graph.structure import incoming
        if not args.name:
            print("usage: upakarana a incoming <name>", file=sys.stderr); return
        edges = incoming(args.name)
        if not edges:
            store.usage.track_miss("a", "incoming", args.name)
        print(f"{len(edges)} incoming edges for {args.name}:")
        for e in edges:
            print(f"  {e['source']:30s} --{e['relation']:20s} [{e['source_layer']}]")

    elif args.action == "hubs":
        from upakarana2.graph.structure import hub_nodes
        hubs = hub_nodes(top_n=30)
        print("Top hub nodes (most incoming edges):")
        for h in hubs:
            in_g = "" if h["in_graph"] else " [GHOST]"
            rels = ", ".join(f"{r}={c}" for r, c in h["top_relations"][:3])
            print(f"  {h['name']:30s} {h['in_count']:4d} in  {rels}{in_g}")

    elif args.action == "orphans":
        from upakarana2.graph.structure import orphan_nodes
        orphans = orphan_nodes()
        print(f"{len(orphans)} orphan nodes (zero incoming edges):")
        for o in orphans[:30]:
            print(f"  {o['name']:30s} [{o['layer']:8s}] {o['domain']}")

    elif args.action == "flow":
        from upakarana2.graph.structure import edge_flow
        result = edge_flow()
        layers = result["layers"]
        print(f"{'':15s} " + " ".join(f"{l:>10s}" for l in layers) + f" {'nowhere':>10s}")
        for src in layers:
            row = result["matrix"][src]
            vals = " ".join(f"{row.get(t, 0):10d}" for t in layers)
            nw = f"{row.get('nowhere', 0):10d}"
            print(f"{src:15s} {vals} {nw}")

    elif args.action == "ring":
        from upakarana2.graph.structure import pratipaksha_check, abheda_summary
        pp = pratipaksha_check()
        ab = abheda_summary()
        print(f"Pratipaksha (inverse — MUST be symmetric):")
        print(f"  {pp['health']}")
        if pp["broken"]:
            print(f"\n  BROKEN ({len(pp['broken'])} — need reverse edge):")
            for b in pp["broken"]:
                ghost = " [GHOST]" if not b["target_exists"] else ""
                rev = f" (has: {b['from']}→{b['reverse']})" if b["reverse"] else ""
                print(f"    {b['from']} → {b['to']}{ghost}{rev}")
        print(f"\nAbheda (non-difference — one-way is normal):")
        print(f"  {ab['total_edges']} declarations from {ab['declaring_nodes']} nodes")
        print(f"  top targets:")
        for target, count in ab["top_targets"][:10]:
            print(f"    {target:30s} ← {count} nodes")

    elif args.action == "signals":
        from upakarana2.graph.flow import signal_flow
        result = signal_flow()
        for s in result["signals"]:
            status = "DEAD" if s["dead"] else "ORPHAN" if s["orphan"] else "ok"
            prods = ", ".join(s["producers"][:3])
            cons = ", ".join(s["consumers"][:3])
            print(f"  {s['signal']:25s} [{status:6s}] ← {prods:30s} → {cons}")
        if result["dead"]:
            print(f"\n{len(result['dead'])} dead signals (written, never read)")

    elif args.action == "signals-gap":
        from upakarana2.graph.flow import signals_gap
        r = signals_gap()
        print("── Dispatch modes in detect-signals ──")
        for m in r["dispatch_modes"]:
            print(f"  {m}")
        print("\n── Intent words (role=intent → dispatch trigger) ──")
        for name, d in sorted(r["intent_words"].items()):
            status = "wired" if d["wired"] else "UNWIRED"
            print(f"  {name:25s} [{status}]  words: {', '.join(d['words'][:6])}")
        print("\n── Shunya-state nodes (yukta=shunya → absence signal) ──")
        for name, d in sorted(r["shunya_nodes"].items()):
            wired = "wired" if d["wired_in_detect"] else "UNWIRED"
            words = ', '.join(d['words']) if d['words'] else "NO WORD KEY"
            print(f"  {name:30s} [{wired}]  words={words}")
        print(f"\n── Gaps ──")
        print(f"  shunya nodes unwired: {r['gaps']['shunya_unwired']}")
        print(f"  shunya no word key:   {r['gaps']['shunya_no_word']}")
        print(f"  negation unwired:     {r['gaps']['negation_unwired']}")

    elif args.action == "swarupa":
        from upakarana2.graph.structure import swarupa_chains
        result = swarupa_chains()
        print("Swarupa roots (IS-A hierarchy endpoints):")
        for root_name, count in result["roots"][:20]:
            print(f"  {root_name:30s} {count:4d} descendants")
        print(f"\n{len(result['no_swarupa'])} nodes with no swarupa:")
        for n in result["no_swarupa"][:20]:
            print(f"  {n}")

    elif args.action == "components":
        from upakarana2.graph.structure import connected_components
        result = connected_components(layer=args.layer)
        print(f"{result['total_components']} components (main: {result['main_size']} nodes)")
        for island in result["islands"][:15]:
            sample = ", ".join(island["members"][:5])
            more = "..." if island["size"] > 5 else ""
            print(f"  island ({island['size']}): {sample}{more}")

    elif args.action == "compose":
        from upakarana2.graph.compose import find_compounds, base_concepts
        compounds = find_compounds()
        bases = base_concepts()
        print(f"── Composition overview ──")
        print(f"  Compound nodes:  {len(compounds)}")
        print(f"  Base concepts:   {len(bases)}")
        print(f"\n── Base concepts → variants ──")
        for base, info in sorted(bases.items(),
                key=lambda x: -(len(x[1]["prefix_variants"]) + len(x[1]["suffix_variants"])))[:20]:
            pv = len(info["prefix_variants"])
            sv = len(info["suffix_variants"])
            prefix_names = [c["prefix"]["qualifier"] for c in info["prefix_variants"]]
            suffix_names = [c["suffix"]["type"] for c in info["suffix_variants"]]
            parts = []
            if prefix_names:
                parts.append(f"qualifiers: {','.join(prefix_names)}")
            if suffix_names:
                parts.append(f"types: {','.join(suffix_names)}")
            print(f"  {base:30s} {pv+sv:2d} variants  {'  '.join(parts)}")

    elif args.action == "compose-gen":
        from upakarana2.graph.compose import generatability_report
        gr = generatability_report()
        print(f"── Generatability report ──")
        print(f"  AUTO (pure generation):      {gr['auto_count']}")
        print(f"  SEMI (generation+overrides): {gr['semi_count']}")
        print(f"  MANUAL (hand-written):       {gr['manual_count']}")
        if gr["auto"]:
            print(f"\n── AUTO: can dissolve into base om5 ──")
            for item in gr["auto"]:
                print(f"  {item['name']:30s} -> {item['base']}.om5 (avastha {item['qualifier']} ...)")
        if gr["semi"]:
            print(f"\n── SEMI: need override declarations ──")
            for item in gr["semi"]:
                overrides = list(item["only_compound"].keys())
                print(f"  {item['name']:30s} -> {item['base']}.om5 + overrides: {overrides}")
        if gr["manual"]:
            print(f"\n── MANUAL: must remain separate om5 ──")
            for item in gr["manual"]:
                print(f"  {item['name']:30s}  unique={item['unique_edge_count']} overrides={item['override_count']}")

    elif args.action == "compose-inverse":
        from upakarana2.graph.compose import pratipaksha_analysis
        pa = pratipaksha_analysis()
        print(f"── Pratipaksha (inverse) analysis ──")
        print(f"  Inverse pairs:       {pa['pair_count']}")
        print(f"  Self-inverse:        {len(pa['self_inverse'])}")
        print(f"  Unidirectional:      {len(pa['unidirectional'])}")
        print(f"  Ops without inverse: {pa['missing_count']}")
        print(f"\n── Inverse pairs ──")
        for p in pa["pairs"]:
            tag = "SELF" if p["self_inverse"] else ("BIDI" if p["bidirectional"] else "UNI ")
            b_tag = "" if p["b_exists"] else " [MISSING]"
            print(f"  [{tag}] {p['a']:30s} <-> {p['b']}{b_tag}")
        if pa["unidirectional"]:
            print(f"\n── Unidirectional (missing back-edge) ──")
            for p in pa["unidirectional"]:
                print(f"  {p['a']:30s} -> {p['b']} (no pratipaksha back)")
        if pa["missing_inverses"]:
            print(f"\n── Operations without any inverse (showing 15) ──")
            for m in pa["missing_inverses"][:15]:
                print(f"  {m['name']:30s} ({m['domain']})")

    elif args.action == "gen-gaps":
        from upakarana2.graph.compose import gen_gaps
        gg = gen_gaps(domain_filter=args.name)
        print(f"── Generation gaps: {gg['total_gaps']} missing compounds ──\n")
        for domain, gaps in gg["by_domain"].items():
            short = domain.replace("kosha/", "")
            avastha_only = [g for g in gaps if g["type"] == "avastha_only"]
            validity_only = [g for g in gaps if g["type"] == "validity_only"]
            print(f"  {short:40s} {len(gaps):3d} gaps ({len(avastha_only)} avastha, {len(validity_only)} validity)")
            for g in gaps[:5]:
                print(f"    {g['name']:35s} ← {g['qualifier']}+{g['base']} [{g['type']}]")
            if len(gaps) > 5:
                print(f"    ... +{len(gaps) - 5} more")

    elif args.action == "gen-validate":
        from upakarana2.graph.compose import validate_node
        if not args.name:
            print("Usage: a gen-validate NODE_NAME", file=sys.stderr); return
        client = None
        try:
            from upakarana2.engine.client import Client
            client = Client()
        except Exception:
            pass
        result = validate_node(args.name, client=client)
        status_sym = {"ok": "✓", "warn": "⚠", "fail": "✗", "info": "·", "skip": "—"}
        print(f"── Validate: {result['name']} [{result['status'].upper()}] ──\n")
        for c in result["checks"]:
            sym = status_sym.get(c["status"], "?")
            print(f"  {sym} {c['check']:20s} {c['detail']}")
        if "expected" in result and "actual" in result:
            exp = result.get("expected", {})
            act = result.get("actual", {})
            all_rels = sorted(set(list(exp.keys()) + list(act.keys())))
            print(f"\n── Edge comparison ──")
            for rel in all_rels:
                e = set(exp.get(rel, []))
                a = set(act.get(rel, []))
                if e == a:
                    print(f"  {rel:15s} = {sorted(a)}")
                else:
                    if e - a:
                        print(f"  {rel:15s} missing: {sorted(e - a)}")
                    if a - e:
                        print(f"  {rel:15s} extra:   {sorted(a - e)}")
                    if e & a:
                        print(f"  {rel:15s} match:   {sorted(e & a)}")
        if client:
            client.close()

    elif args.action == "inherit-gaps":
        from upakarana2.graph.inheritance import report
        verbose = getattr(args, "verbose", False)
        report(verbose=verbose)
