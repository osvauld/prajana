"""cli.py — Single CLI dispatcher for upakarana."""

import argparse
import json
import sys


def _print_json(data):
    print(json.dumps(data, indent=2, default=str))


# --- Om5 commands ---

def cmd_om(args):
    from upakarana.parsers import om5
    from upakarana.usage import track_miss
    nodes = om5.load_all()

    if args.action == "summary":
        _print_json(om5.summary(nodes))
    elif args.action == "search":
        results = om5.search(nodes, args.pattern or args.name)
        if not results:
            track_miss("om", "search")
        for r in results:
            print(f"  {r['name']:30s} [{r['layer']}] {r['domain']}")
            for m in r["matches"][:3]:
                print(f"    L{m['line']}: {m['text']}")
    elif args.action == "source":
        node = nodes.get(args.name)
        if node:
            print(node["source"])
        else:
            track_miss("om", "source")
            print(f"Not found: {args.name}", file=sys.stderr)
    elif args.action == "domain":
        info = om5.by_domain(nodes, depth=args.depth)
        if not info:
            track_miss("om", "domain")
        for dom, ns in info.items():
            print(f"  {dom}: {len(ns)} nodes")
    elif args.action == "with-relation":
        results = om5.with_relation(nodes, args.relation)
        if not results:
            track_miss("om", "with-relation")
        print(f"{len(results)} nodes with {args.relation}:")
        for n in results[:20]:
            print(f"  {n['name']}")


# --- Tantra commands ---

def cmd_tantra(args):
    from upakarana.parsers import tantra4
    from upakarana.usage import track_miss
    tantras = tantra4.load_all()

    if args.action == "summary":
        _print_json(tantra4.summary(tantras))
    elif args.action == "search":
        results = tantra4.search(tantras, args.pattern or args.name)
        if not results:
            track_miss("tantra", "search")
        for r in results:
            print(f"  {r['name']:30s} [{r['group']}]")
            for m in r["matches"][:3]:
                print(f"    L{m['line']}: {m['text']}")
    elif args.action == "source":
        t = tantras.get(args.name)
        if t:
            print(t["source"])
        else:
            track_miss("tantra", "source")
            print(f"Not found: {args.name}", file=sys.stderr)
    elif args.action == "group":
        groups = tantra4.by_group(tantras)
        if args.name:
            gs = groups.get(args.name, [])
            if not gs:
                track_miss("tantra", "group")
            for t in gs:
                print(f"  {t['name']:30s} {t['lines']}L")
        else:
            for g, ts in groups.items():
                print(f"  {g}: {len(ts)} tantras")
    elif args.action == "callgraph":
        cg = tantra4.call_graph(tantras)
        for name, calls in sorted(cg.items()):
            if calls:
                print(f"  {name} → {', '.join(calls)}")


# --- Shabda commands ---

def cmd_shabda(args):
    from upakarana.parsers import shabda
    from upakarana.usage import track_miss
    nodes = shabda.load_all()

    if args.action == "summary":
        _print_json(shabda.summary(nodes))
    elif args.action == "search":
        results = shabda.search(nodes, args.pattern or args.name)
        if not results:
            track_miss("shabda", "search")
        for r in results:
            print(f"  {r['name']}")
    elif args.action == "node":
        node = nodes.get(args.name)
        if node:
            _print_json({"name": node["name"], "fields": node["fields"]})
        else:
            track_miss("shabda", "node")
            print(f"Not found: {args.name}", file=sys.stderr)
    elif args.action == "gaps":
        from upakarana.analysis.static import shabda_gaps
        gaps = shabda_gaps()
        print(f"{len(gaps)} nodes with kriya/phala but no shabda:")
        for g in gaps[:20]:
            print(f"  {g['name']:30s} [{g['layer']}] {g['domain']}")

    elif args.action == "roles":
        from upakarana.analysis.signals import shabda_roles
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

        print("\n── Missing roles (no pipeline wiring yet) ──")
        for role, outcome in r["missing_roles"].items():
            print(f"  [{role}]  →  {outcome}")

        print(f"\n── Shunya-state nodes ({len(r['shunya_states'])}) ──")
        for s in r["shunya_states"]:
            words = ', '.join(s['words']) if s['words'] else "NO WORD KEY"
            abheda = ', '.join(s['abheda']) if s['abheda'] else "—"
            flag = "" if s["has_word"] else " ← NEEDS word:"
            print(f"  {s['name']:35s}  abheda={abheda}  words={words}{flag}")

        print(f"\n── Word collisions: {r['collision_count']} ambiguous words ──")
        for w, ns in sorted(r["collisions"].items())[:15]:
            print(f"  {w:20s} → {list(set(ns))}")

    elif args.action == "coverage":
        from upakarana.analysis.signals import shabda_roles
        r = shabda_roles()
        print("── Word coverage by domain ──")
        print(f"  {'domain':15s}  {'coverage':10s}  nodes")
        for domain, stats in r["domain_coverage"].items():
            pct = stats["with_word"] * 100 // stats["total"] if stats["total"] else 0
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            print(f"  {domain:15s}  {bar}  {pct:3d}%  ({stats['with_word']}/{stats['total']})")


# --- Engine commands ---

def cmd_vy(args):
    from upakarana.engine import server

    if args.action == "start":
        server.start(background=True)
    elif args.action == "stop":
        server.stop()
    elif args.action == "status":
        _print_json(server.status())
    elif args.action == "reload":
        result = server.reload()
        if result:
            print("Reloaded.")
        else:
            print("Server not running.", file=sys.stderr)
    elif args.action == "eval":
        from upakarana.engine.client import Client
        c = Client()
        try:
            expr = args.expr or args.name
            if not expr:
                print("usage: upakarana vy eval '<expr>'", file=sys.stderr); return
            result = c.eval(expr)
            if isinstance(result, (list, dict)):
                _print_json(result)
            else:
                print(result)
        finally:
            c.close()
    elif args.action == "ask":
        from upakarana.engine.client import Client
        c = Client()
        try:
            question = args.question or args.name
            if not question:
                print("usage: upakarana vy ask '<question>'", file=sys.stderr); return
            print(c.ask(question))
        finally:
            c.close()
    elif args.action == "walk":
        from upakarana.engine.client import Client
        from upakarana.usage import track_miss
        c = Client()
        try:
            if args.incoming:
                result = c.walk_in(args.node, args.relation)
            else:
                result = c.walk(args.node, args.relation)
            if not result:
                track_miss("vy", "walk")
            for r in result:
                print(f"  {r}")
        finally:
            c.close()
    elif args.action == "inspect":
        from upakarana.engine.client import Client
        c = Client()
        try:
            _print_json(c.inspect(args.name))
        finally:
            c.close()


# --- Test commands ---

def cmd_test(args):
    # resolve positional filter shorthand
    if getattr(args, "filter", None) and not args.layer and not args.gate and not args.pattern:
        f = args.filter
        known_layers = {"evaluator", "graph", "edges", "pipeline", "answers", "xfail",
                        "physics", "logic", "grammar", "reasoning", "comparison",
                        "arithmetic", "mixed", "entity"}
        if f.startswith("gate:"):
            args.gate = f[5:]
        elif f in known_layers:
            args.layer = f
        else:
            args.pattern = f

    if args.action == "list":
        from upakarana.testing.discover import load_all, summary, filter_tests
        tests = load_all()
        if args.layer or args.gate or args.pattern:
            tests = filter_tests(tests, layer=args.layer, gate=args.gate, pattern=args.pattern)
        for t in tests:
            xf = " [xfail]" if t["xfail"] else ""
            print(f"  {t['name']:40s} {t['layer']:20s}{xf}")
        print(f"\n{len(tests)} tests")
    elif args.action == "summary":
        from upakarana.testing.discover import load_all, summary
        _print_json(summary(load_all()))
    elif args.action == "run":
        from upakarana.testing.run import run
        par = None if args.parallel == "off" else args.parallel
        result = run(layer=args.layer, gate=args.gate, pattern=args.pattern,
                     last_failed=args.last_failed, verbose=args.verbose,
                     parallel=par)
        print(f"passed={result['passed']} failed={result['failed']} "
              f"xfailed={result.get('xfailed',0)} {result.get('duration','')}")
    elif args.action == "failed":
        from upakarana.testing.cache import load, failed
        _, entries = load()
        fl = failed(entries)
        print(f"{len(fl)} failed tests:")
        for e in fl:
            test = e.get("test", "?")
            fail = e.get("failure") or {}
            expected = fail.get("expected", "")
            got = fail.get("got", "")
            detail = f"expected={expected}" if expected else ""
            if got:
                detail += f" got={got[:60]}"
            print(f"  {test:60s}  {detail}")


# --- Cache commands ---

def cmd_cache(args):
    from upakarana.testing.cache import load, summarize, by_gate, slowest_calls, slowest_tests, timing_by_layer

    _, entries = load()
    if args.action == "summary":
        _print_json(summarize(entries))
    elif args.action == "gates":
        gates = by_gate(entries)
        for gate, es in sorted(gates.items()):
            print(f"  {gate}: {len(es)}")
    elif args.action == "slow":
        def fmt_time(us):
            """Auto-scale: us / ms / s depending on magnitude."""
            if us < 1000:
                return f"{us:6.0f}us"
            elif us < 1_000_000:
                return f"{us / 1000:6.1f}ms"
            else:
                return f"{us / 1_000_000:6.2f}s "

        print("── Slowest tests (wall-clock) ──")
        for t in slowest_tests(entries):
            print(f"  {t['duration_s']:6.3f}s  {t['calls']} calls  ({fmt_time(t['call_us'])})  [{t['outcome']:>7s}]  {t['test']}")
        print()
        print("── Slowest calls ──")
        for c in slowest_calls(entries):
            print(f"  {fmt_time(c['elapsed_us'])} {c['test']:55s} {c['method']}")
        print()
        print("── Timing by layer ──")
        layers = timing_by_layer(entries)
        for layer, d in layers.items():
            print(f"  {d['duration_s']:6.1f}s  {d['count']:3d} tests  ({fmt_time(d['call_us'])})  {layer}")


# --- Lint commands ---

def cmd_lint(args):
    from upakarana.analysis.static import om5_lint, tantra4_lint

    if args.target in ("om5", "all"):
        result = om5_lint()
        issues = result["issues"]
        print(f"Om5: {result['total_nodes']} nodes, {len(issues)} issues")
        for i in issues[:20]:
            print(f"  [{i['severity']}] {i['node']}: {i['issue']}")

    if args.target in ("tantra4", "all"):
        result = tantra4_lint()
        issues = result["issues"]
        print(f"Tantra4: {result['total_tantras']} tantras, {len(issues)} issues")
        for i in issues[:20]:
            print(f"  [{i['severity']}] {i['tantra']}: {i['issue']}")


# --- Health command ---

def cmd_health(args):
    from upakarana.analysis.health import full_report, print_report
    client = None
    if not args.static_only:
        try:
            from upakarana.engine.client import Client
            client = Client()
        except Exception:
            pass
    report = full_report(client=client)
    print_report(report)
    if client:
        client.close()


# --- Search command ---

def cmd_search(args):
    results = []
    if args.scope in ("om", "all"):
        from upakarana.parsers import om5
        nodes = om5.load_all()
        for r in om5.search(nodes, args.pattern):
            results.append(("om5", r["name"], r.get("domain", "")))
    if args.scope in ("tantra", "all"):
        from upakarana.parsers import tantra4
        tantras = tantra4.load_all()
        for r in tantra4.search(tantras, args.pattern):
            results.append(("tantra4", r["name"], r.get("group", "")))
    if args.scope in ("shabda", "all"):
        from upakarana.parsers import shabda
        nodes = shabda.load_all()
        for r in shabda.search(nodes, args.pattern):
            results.append(("shabda", r["name"], ""))

    if not results:
        from upakarana.usage import track_miss
        track_miss("search")
    print(f"{len(results)} matches:")
    for kind, name, ctx in results:
        print(f"  [{kind:8s}] {name:30s} {ctx}")


# --- OCaml analysis commands ---

def cmd_ocaml(args):
    from upakarana.analysis import ocaml
    modules = ocaml.parse_all()

    if args.action == "report":
        ocaml.print_report(modules)
    elif args.action == "darshana":
        ocaml.print_darshana(modules)
    elif args.action == "patterns":
        ocaml.print_patterns(modules)
    elif args.action == "coupling":
        ocaml.print_coupling(modules)
    elif args.action == "consolidate":
        ocaml.print_consolidation(modules)
    elif args.action == "summary":
        _print_json(ocaml.summary(modules))
    elif args.action == "functions":
        dups = ocaml.duplicate_functions(modules)
        if dups:
            print(f"{len(dups)} duplicate function names (excluding facade):")
            for fn, mods in sorted(dups.items(), key=lambda x: -len(x[1])):
                print(f"  {fn:25s} {len(mods)}x: {', '.join(mods)}")
        else:
            print("No duplicate functions found.")
    elif args.action == "state":
        state = ocaml.mutable_state(modules)
        print(f"Refs ({len(state['refs'])}):")
        for r in state["refs"]:
            print(f"  {r['module']:20s} {r['name']}")
        print(f"\nHashtbls ({len(state['hashtbls'])}):")
        for h in state["hashtbls"]:
            print(f"  {h['module']:20s} {h['name']}")
    elif args.action == "parallel":
        ocaml.print_parallelism(modules)


# --- Query commands ---

def cmd_query(args):
    from upakarana.query import Q
    from upakarana.usage import track_miss
    q = Q()

    if args.action == "op":
        if not args.name:
            print("usage: upakarana query op <name>", file=sys.stderr); return
        result = q.op(args.name)
        if not result or result.get("error"):
            track_miss("q", "op")
        _print_json(result)
    elif args.action == "ops":
        ops = q.ops(args.pattern)
        for o in ops:
            arity = f"({o['arity']})" if o["arity"] != -1 else "(variadic)"
            print(f"  {o['name']:25s} {arity}")
        print(f"\n{len(ops)} ops")
    elif args.action == "dispatch":
        if not args.name:
            print("usage: upakarana query dispatch <name>", file=sys.stderr); return
        _print_json(q.dispatch_path(args.name))
    elif args.action == "missing":
        missing = q.missing_ops()
        for m in missing:
            print(f"  {m}")
        print(f"\n{len(missing)} ops registered but not dispatched")
    elif args.action == "explain":
        if not args.name:
            print("usage: upakarana query explain <name>", file=sys.stderr); return
        result = q.explain(args.name)
        print(f"  found in: {', '.join(result.get('found_in', []))}")
        if "module" in result:
            m = result["module"]
            print(f"  ocaml: {m['name']} ({m['lines']}L, layer={m['layer']})")
        if "tantra" in result:
            t = result["tantra"]
            print(f"  tantra: {t['name']} ({t['lines']}L, takes={t['takes']})")
        if "node" in result:
            n = result["node"]
            if "om5" in n:
                print(f"  om5: {n['om5']['layer']} ({len(n['om5']['edges'])} edges)")
            if "shabda" in n:
                print(f"  shabda: {list(n['shabda'].keys())[:8]}")
    elif args.action == "overview":
        _print_json(q.overview())
    elif args.action == "node":
        if not args.name:
            print("usage: upakarana query node <name>", file=sys.stderr); return
        result = q.node(args.name)
        if not result or result.get("error"):
            track_miss("q", "node")
        _print_json(result)
    elif args.action == "eval":
        if not args.expr:
            print("usage: upakarana query eval --expr '<expr>'", file=sys.stderr); return
        result = q.eval(args.expr)
        if isinstance(result, (list, dict)):
            _print_json(result)
        else:
            print(result)


# --- Parser ---

def build_parser():
    p = argparse.ArgumentParser(prog="upakarana", description="Agent-X tooling")
    sub = p.add_subparsers(dest="command")

    # om
    s = sub.add_parser("om", help="Om5 queries")
    s.add_argument("action", choices=["summary", "search", "source", "domain", "with-relation"])
    s.add_argument("name", nargs="?")
    s.add_argument("--pattern", "-p")
    s.add_argument("--depth", type=int, default=2)
    s.add_argument("--relation", "-r")

    # tantra
    s = sub.add_parser("tantra", help="Tantra4 queries")
    s.add_argument("action", choices=["summary", "search", "source", "group", "callgraph"])
    s.add_argument("name", nargs="?")
    s.add_argument("--pattern", "-p")

    # shabda
    s = sub.add_parser("shabda", help="Shabda queries")
    s.add_argument("action", choices=["summary", "search", "node", "gaps", "roles", "coverage"])
    s.add_argument("name", nargs="?")
    s.add_argument("--pattern", "-p")

    # vy
    s = sub.add_parser("vy", help="Engine management")
    s.add_argument("action", choices=["start", "stop", "status", "reload", "eval", "ask", "walk", "inspect"])
    s.add_argument("name", nargs="?")
    s.add_argument("--expr", "-e")
    s.add_argument("--question", "-q")
    s.add_argument("--node")
    s.add_argument("--relation", "-r")
    s.add_argument("--incoming", "-i", action="store_true")

    # test
    s = sub.add_parser("test", help="Test operations")
    s.add_argument("action", choices=["list", "summary", "run", "failed"])
    s.add_argument("filter", nargs="?", help="shorthand: layer name, gate:NAME, or test pattern")
    s.add_argument("--layer", "-l")
    s.add_argument("--gate", "-g")
    s.add_argument("--pattern", "-p")
    s.add_argument("--last-failed", action="store_true")
    s.add_argument("--verbose", "-v", action="store_true")
    s.add_argument("--parallel", "-n", default="auto",
                   help="xdist workers: 'auto', a number, or 'off' (default: auto)")

    # cache
    s = sub.add_parser("cache", help="Cache analysis")
    s.add_argument("action", choices=["summary", "gates", "slow"])

    # lint
    s = sub.add_parser("lint", help="Static lint")
    s.add_argument("target", choices=["om5", "tantra4", "all"], default="all", nargs="?")

    # health
    s = sub.add_parser("health", help="System health report")
    s.add_argument("--static-only", action="store_true")

    # search
    s = sub.add_parser("search", help="Cross-source search")
    s.add_argument("pattern")
    s.add_argument("--scope", choices=["om", "tantra", "shabda", "all"], default="all")

    # ocaml
    s = sub.add_parser("ocaml", help="OCaml codebase analysis")
    s.add_argument("action", choices=["report", "darshana", "patterns", "coupling",
                                       "consolidate", "summary", "functions", "state", "parallel"])

    # query
    s = sub.add_parser("q", help="Query primitives (LLM-friendly)")
    s.add_argument("action", choices=["op", "ops", "dispatch", "missing",
                                       "explain", "overview", "node", "eval"])
    s.add_argument("name", nargs="?")
    s.add_argument("--pattern", "-p")
    s.add_argument("--expr", "-e")

    # analyze (static)
    s = sub.add_parser("a", help="Graph analysis (static)")
    s.add_argument("action", choices=[
        "ghosts", "incoming", "hubs", "orphans",
        "flow", "fingerprint",
        "swarupa", "components",
        "ring",
        "signals", "signals-gap", "patterns", "grounding", "vocabulary",
        "parallel", "compose",
        "compose-inherit", "compose-validity", "compose-words",
        "compose-rules", "compose-gen", "compose-curated",
        "compose-logic", "compose-lift", "compose-inverse",
        "compose-karma", "compose-lakshana", "compose-declension",
        "compose-conjugation", "compose-samasa", "compose-collisions",
        "compose-deriv-avastha", "compose-grammar", "compose-summary",
        "hubs-compose", "derivative-chain", "compose-potential",
        "generator-product",
        "sangati-levels", "sangati-at", "sangati-tree", "sangati-generates",
        "gen-expected", "gen-validate", "gen-candidates", "gen-gaps", "gen-validate-all",
        "dataflow",
    ])
    s.add_argument("name", nargs="?")
    s.add_argument("name2", nargs="?")
    s.add_argument("--layer", "-l")

    # live analysis
    s = sub.add_parser("live", help="Live graph analysis (needs running engine)")
    s.add_argument("action", choices=[
        "drift", "pratipaksha", "panchaavayava", "ghosts", "signal-trace",
        "walk", "inspect",
    ])
    s.add_argument("name", nargs="?")
    s.add_argument("--sentence", "-s")
    s.add_argument("--relation", "-r")

    # generation / authoring
    s = sub.add_parser("gen", help="Node generation and authoring")
    s.add_argument("action", choices=[
        "preview", "create", "validate", "batch", "status",
    ])
    s.add_argument("name", nargs="?")
    s.add_argument("name2", nargs="?")
    s.add_argument("--to", default=None, help="Output directory (default: brahman)")
    s.add_argument("--domain", "-d", default=None)
    s.add_argument("--dry-run", action="store_true")

    # usage
    s = sub.add_parser("usage", help="Command usage tracking")
    s.add_argument("action", choices=["report", "never", "reset"], default="report", nargs="?")

    return p


def cmd_analyze(args):
    import json as _json

    if args.action == "ghosts":
        from upakarana.analysis.ghosts import find_ghosts
        result = find_ghosts()
        print(f"{result['total_ghosts']} ghost nodes ({result['total_ghost_edges']} broken edges):")
        for g in result["ghosts"][:30]:
            refs = ", ".join(f"{r[0]}({r[1]})" for r in g["referrers"][:3])
            print(f"  {g['name']:30s} {g['ref_count']:3d}x  {refs}")

    elif args.action == "incoming":
        from upakarana.analysis.edges import incoming
        if not args.name:
            print("usage: upakarana a incoming <name>", file=sys.stderr); return
        edges = incoming(args.name)
        if not edges:
            from upakarana.usage import track_miss
            track_miss("a", "incoming")
        print(f"{len(edges)} incoming edges for {args.name}:")
        for e in edges:
            print(f"  {e['source']:30s} --{e['relation']:20s} [{e['source_layer']}]")

    elif args.action == "hubs":
        from upakarana.analysis.edges import hub_nodes
        hubs = hub_nodes(top_n=30)
        print(f"Top hub nodes (most incoming edges):")
        for h in hubs:
            in_g = "" if h["in_graph"] else " [GHOST]"
            rels = ", ".join(f"{r}={c}" for r, c in h["top_relations"][:3])
            print(f"  {h['name']:30s} {h['in_count']:4d} in  {rels}{in_g}")

    elif args.action == "orphans":
        from upakarana.analysis.edges import orphan_nodes
        orphans = orphan_nodes()
        print(f"{len(orphans)} orphan nodes (zero incoming edges):")
        for o in orphans[:30]:
            print(f"  {o['name']:30s} [{o['layer']:8s}] {o['domain']}  out={o['out_edges']}")

    elif args.action == "flow":
        from upakarana.analysis.layers import edge_flow
        result = edge_flow()
        layers = result["layers"]
        print(f"{'':15s} " + " ".join(f"{l:>10s}" for l in layers) + f" {'nowhere':>10s}")
        for src in layers:
            row = result["matrix"][src]
            vals = " ".join(f"{row.get(t, 0):10d}" for t in layers)
            nw = f"{row.get('nowhere', 0):10d}"
            print(f"{src:15s} {vals} {nw}")

    elif args.action == "fingerprint":
        from upakarana.analysis.layers import relation_fingerprint
        result = relation_fingerprint()
        # Collect all relation names
        all_rels = set()
        for layer_data in result.values():
            all_rels.update(layer_data["relations"].keys())
        top_rels = sorted(all_rels, key=lambda r: -sum(
            result[l]["relations"].get(r, {}).get("pct", 0) for l in result))[:12]

        print(f"{'relation':<20s} " + " ".join(f"{l:>8s}" for l in sorted(result.keys())))
        for rel in top_rels:
            vals = " ".join(
                f"{result[l]['relations'].get(rel, {}).get('pct', 0):7d}%"
                for l in sorted(result.keys()))
            print(f"{rel:<20s} {vals}")

    elif args.action == "swarupa":
        from upakarana.analysis.chains import swarupa_chains
        result = swarupa_chains()
        print(f"Swarupa roots (IS-A hierarchy endpoints):")
        for root_name, count in result["roots"][:20]:
            print(f"  {root_name:30s} {count:4d} descendants")
        print(f"\n{len(result['no_swarupa'])} nodes with no swarupa (no IS-A):")
        for n in result["no_swarupa"][:20]:
            print(f"  {n}")

    elif args.action == "components":
        from upakarana.analysis.chains import connected_components
        result = connected_components(layer=args.layer)
        print(f"{result['total_components']} components (main: {result['main_size']} nodes)")
        for island in result["islands"][:15]:
            sample = ", ".join(island["members"][:5])
            more = f"..." if island["size"] > 5 else ""
            print(f"  island ({island['size']}): {sample}{more}")

    elif args.action == "ring":
        from upakarana.analysis.ring import pratipaksha_check, abheda_summary
        pp = pratipaksha_check()
        ab = abheda_summary()
        print(f"Pratipaksha (inverse — MUST be symmetric):")
        print(f"  {pp['health']}")
        print(f"  symmetric: {pp['symmetric']}")
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
        from upakarana.analysis.signals import signal_flow
        result = signal_flow()
        for s in result["signals"]:
            status = "DEAD" if s["dead"] else "ORPHAN" if s["orphan"] else "ok"
            prods = ", ".join(s["producers"][:3])
            cons = ", ".join(s["consumers"][:3])
            print(f"  {s['signal']:25s} [{status:6s}] ← {prods:30s} → {cons}")
        if result["dead"]:
            print(f"\n{len(result['dead'])} dead signals (written, never read)")

    elif args.action == "signals-gap":
        from upakarana.analysis.signals import signals_gap
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
            abheda = ', '.join(d['abheda']) if d['abheda'] else "—"
            print(f"  {name:30s} [{wired}]  abheda={abheda}  words={words}")

        print("\n── Negation/pratishedha nodes ──")
        for name, d in sorted(r["negation_nodes"].items()):
            wired = "wired" if d["wired_in_detect"] else "UNWIRED"
            print(f"  {name:25s} [{wired}]  words: {', '.join(d['words'])}  eval={d['eval']}")

        print(f"\n── Pratipaksha pairs in graph: {r['pratipaksha_pairs_count']} ──")
        for a, b in r["pratipaksha_sample"]:
            print(f"  {a} ↔ {b}")

        print("\n── Gaps ──")
        print(f"  shunya nodes unwired from detect-signals: {r['gaps']['shunya_unwired']}")
        print(f"  shunya nodes with no word key:            {r['gaps']['shunya_no_word']}")
        print(f"  negation nodes unwired:                   {r['gaps']['negation_unwired']}")

    elif args.action == "patterns":
        from upakarana.analysis.tantras import classify_patterns
        result = classify_patterns()
        for pat, data in result["patterns"].items():
            print(f"  {pat:20s} {data['count']:3d}  {data['tantras'][:5]}")

    elif args.action == "grounding":
        from upakarana.analysis.tantras import concept_grounding
        result = concept_grounding()
        g = result["grounded"]
        u = result["ungrounded"]
        print(f"Grounded: {g['count']} tantras (graph knows about them via kriya)")
        for name, nodes in sorted(result["grounding_map"].items()):
            print(f"  {name:30s} ← {', '.join(nodes)}")
        print(f"\nUngrounded: {u['count']} tantras (no kosha/yantra node references them)")
        for n in u["tantras"][:20]:
            print(f"  {n}")

    elif args.action == "vocabulary":
        from upakarana.analysis.tantras import helper_vocabulary
        vocab = helper_vocabulary()
        for layer, helpers in vocab.items():
            print(f"\n{layer} ({len(helpers)}):")
            for h in helpers:
                print(f"  {h['name']:30s} {h['lines']}L calls={h['calls']}")

    elif args.action == "parallel":
        from upakarana.analysis.tantras import print_parallelism
        print_parallelism()

    elif args.action == "dataflow":
        from upakarana.analysis.tantras import print_dataflow
        print_dataflow()

    elif args.action == "compose":
        from upakarana.analysis.compose import full_analysis
        r = full_analysis()

        print(f"── Composition overview ──")
        print(f"  Compound nodes:     {r['compound_count']}")
        print(f"  Base concepts:      {r['base_count']}")
        print(f"  Composition chains: {r['chain_count']}")
        print(f"  Synthetic (bare):   {r['synthetic_count']}")
        print(f"  Generator bases:    {r['generator_count']}")

        print(f"\n── Base concepts → variants ──")
        for base, info in sorted(r["bases"].items(),
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
            detail = "  ".join(parts)
            print(f"  {base:30s} {pv+sv:2d} variants  {detail}")

        print(f"\n── Qualifier categories ──")
        for cat, quals in sorted(r["categories"].items()):
            total = sum(len(ns) for ns in quals.values())
            qual_list = ", ".join(f"{q}({len(ns)})" for q, ns in sorted(quals.items()))
            print(f"  {cat:12s} ({total:2d}):  {qual_list}")

        print(f"\n── Composition chains (multi-level) ──")
        for chain in r["chains"][:10]:
            print(f"  {' → '.join(chain)}")

        print(f"\n── Potential generators (avastha edges for base om5) ──")
        for base, info in sorted(r["generators"].items(),
                key=lambda x: -len(x[1]["generators"]))[:12]:
            gens = info["generators"]
            gen_strs = [f"(avastha {g['qualifier']} {g['context']})" for g in gens]
            print(f"  {base}.om5:")
            for gs in gen_strs:
                print(f"    {gs}")

        if r["synthetic"]:
            print(f"\n── Synthetic nodes needing enrichment ──")
            for s in r["synthetic"][:10]:
                if s["prefix"]:
                    p = s["prefix"]
                    print(f"  {s['name']:30s}  = {p['qualifier']} + {p['base']}  [{p['category']}]  needs: swarupa→{p['base']}, sthita→{p['context']}")

    elif args.action == "compose-inherit":
        from upakarana.analysis.compose import inheritance_analysis
        ia = inheritance_analysis()
        print(f"── Edge inheritance: compound vs base ({len(ia)} compounds) ──\n")
        for item in ia:
            tag = "AUTO" if item["generatable"] and item["unique_edge_count"] <= 2 else \
                  "SEMI" if item["generatable"] else "MANUAL"
            swr = "Y" if item["swarupa_to_base"] else "N"
            vsh = "Y" if item["vishesa_match"] else "N"
            print(f"  [{tag:6s}] {item['name']:30s} (base: {item['base']})")
            print(f"           swarupa->base: {swr}  vishesa-match: {vsh}  "
                  f"unique: {item['unique_edge_count']}  overrides: {item['override_count']}")
            if item["inherited"]:
                parts = [f"{r}:{','.join(ts)}" for r, ts in item["inherited"].items()]
                print(f"           inherited: {'; '.join(parts)}")
            if item["overridden"]:
                parts = [f"{r}:{','.join(ts)}" for r, ts in item["overridden"].items()]
                print(f"           overridden: {'; '.join(parts)}")
            if item["only_compound"]:
                parts = [f"{r}:{','.join(ts)}" for r, ts in item["only_compound"].items()]
                print(f"           only-compound: {'; '.join(parts)}")
            if item["only_base"]:
                print(f"           only-base: {', '.join(item['only_base'])}")
            print()

    elif args.action == "compose-validity":
        from upakarana.analysis.compose import validity_matrix
        vm = validity_matrix()
        print(f"── Validity matrix ──")
        print(f"  Existing (qualifier,base) pairs: {vm['existing_count']}")
        print(f"  Valid missing candidates:        {vm['valid_missing_count']}")

        print(f"\n── Existing by base ──")
        for base, quals in sorted(vm["by_base"].items(), key=lambda x: -len(x[1])):
            print(f"  {base:25s} [{len(quals):2d}]: {', '.join(sorted(quals))}")

        print(f"\n── Accepted categories per base ──")
        for base, cats in sorted(vm["domain_categories"].items()):
            print(f"  {base:25s} {sorted(cats)}")

        print(f"\n── Valid missing candidates ──")
        for m in sorted(vm["valid_missing"], key=lambda x: (x["base"], x["qualifier"])):
            print(f"  {m['name']:35s} = {m['qualifier']:12s} + {m['base']:20s} [{m['category']}] ctx={m['context']}")

    elif args.action == "compose-rules":
        from upakarana.analysis.compose import edge_inheritance_rules
        rules = edge_inheritance_rules()
        print(f"── Edge inheritance rules (derived from {len(rules)} relations) ──\n")
        for rel, r in sorted(rules.items(), key=lambda x: x[1]["action"]):
            print(f"  {rel:20s} -> {r['action']:18s}  "
                  f"inh={r['inherited']:2d}  ovr={r['overridden']:2d}  "
                  f"comp={r['only_compound']:2d}  base={r['only_base']:2d}")

    elif args.action == "compose-words":
        from upakarana.analysis.compose import word_form_inventory
        wf = word_form_inventory()
        print(f"── Word form inventory ──")
        print(f"  Compounds with shabda:    {wf['existing_count']}")
        print(f"  Compounds without shabda: {wf['missing_count']}")

        print(f"\n── Shabda field frequency ──")
        for field, count in sorted(wf["field_frequency"].items(), key=lambda x: -x[1]):
            print(f"  {field:20s} {count:3d} nodes")

        if wf["missing_words"]:
            print(f"\n── Missing shabda (compounds without word entries) ──")
            for name in wf["missing_words"]:
                print(f"  {name}")

        print(f"\n── Existing shabda samples ──")
        for name, fields in list(wf["existing_words"].items())[:8]:
            print(f"  {name}: {fields}")

    elif args.action == "compose-gen":
        from upakarana.analysis.compose import generatability_report
        gr = generatability_report()
        print(f"── Generatability report ──")
        print(f"  AUTO (pure generation):    {gr['auto_count']}")
        print(f"  SEMI (generation+overrides): {gr['semi_count']}")
        print(f"  MANUAL (hand-written):     {gr['manual_count']}")

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

    elif args.action == "compose-curated":
        from upakarana.analysis.compose import curated_validity
        cv = curated_validity()
        print(f"── Curated validity ──")
        print(f"  Total candidates:  {cv['total_candidates']}")
        print(f"  Already exist:     {cv['existing_count']}")
        print(f"  To generate:       {cv['missing_count']}")

        print(f"\n── Missing by base ──")
        for base, items in sorted(cv["missing_by_base"].items(), key=lambda x: -len(x[1])):
            quals = [m["qualifier"] for m in items]
            print(f"  {base:25s} [{len(items):2d}]: {', '.join(quals)}")

        print(f"\n── Full candidate list ──")
        for c in sorted(cv["existing"] + cv["missing"], key=lambda x: (x["base"], x["qualifier"])):
            tag = "EXISTS" if c["in_graph"] else "GEN"
            print(f"  [{tag:6s}] {c['name']:35s} = {c['qualifier']:12s} + {c['base']:20s} [{c['category']}] ctx={c['context']}")

    elif args.action == "compose-logic":
        from upakarana.analysis.compose import logic_generator_analysis
        la = logic_generator_analysis()
        print(f"── Logic generator analysis ──")
        print(f"  Total existing: {la['total_existing']}")
        print(f"  Total missing:  {la['total_missing']}")

        for group in la["groups"]:
            print(f"\n── {group['group']} (base: {group['base']}, layer: {group['layer']}) ──")

            if group["existing"]:
                for item in group["existing"]:
                    tag = "IN-GRAPH" if item["in_graph"] else "MISSING"
                    print(f"  [{tag:8s}] {item['name']}")

            if group["missing"]:
                print(f"  --- to generate ---")
                for item in group["missing"]:
                    edges_str = ", ".join(f"{k}:{v}" for k, v in item["edges"].items())
                    print(f"  [GEN     ] {item['name']:30s} — {item['description']}")
                    print(f"              edges: {edges_str}")

    elif args.action == "compose-lift":
        from upakarana.analysis.compose import space_lift_analysis
        sla = space_lift_analysis()
        total_existing = sum(s["existing_count"] for s in sla)
        total_missing = sum(s["missing_count"] for s in sla)
        print(f"── Space-lift analysis ──")
        print(f"  Total existing lifted ops: {total_existing}")
        print(f"  Total missing lifts:       {total_missing}")

        for space in sla:
            print(f"\n── {space['space']} ({space['prefix']}-*) ──")
            print(f"  domain: {space['domain']}")
            if space["existing"]:
                print(f"  existing ({space['existing_count']}):")
                for e in space["existing"]:
                    print(f"    {e['name']:30s} ← {e['base_op']}")
            if space["missing"]:
                print(f"  missing ({space['missing_count']}):")
                for m in space["missing"]:
                    print(f"    {m['name']:30s} ← {m['base_op']} (gen)")

    elif args.action == "compose-inverse":
        from upakarana.analysis.compose import pratipaksha_analysis
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

        if pa["missing_inverses"][:15]:
            print(f"\n── Operations without any inverse ({pa['missing_count']} total, showing 15) ──")
            for m in pa["missing_inverses"][:15]:
                print(f"  {m['name']:30s} ({m['domain']})")

    elif args.action == "compose-karma":
        from upakarana.analysis.compose import karma_varga_cross
        kv = karma_varga_cross()
        print(f"── Math: op × structure cross-product ──")
        print(f"  Total valid pairs:   {kv['total_valid']}")
        print(f"  Already exist:       {kv['total_existing']}")
        print(f"  Missing:             {kv['total_missing']}")
        for varga, info in sorted(kv["vargas"].items(), key=lambda x: -x[1]["cross"]):
            print(f"\n  {varga}: {info['op_count']} ops × {info['struct_count']} structures = {info['cross']}")
            print(f"    ops: {info['ops'][:5]}{'...' if len(info['ops']) > 5 else ''}")
            print(f"    structures: {info['structures'][:5]}{'...' if len(info['structures']) > 5 else ''}")

    elif args.action == "compose-lakshana":
        from upakarana.analysis.compose import lakshana_validity
        lv = lakshana_validity()
        print(f"── Math: property × structure truth table ──")
        print(f"  Total exceptions: {lv['total_exceptions']}")
        for varga, info in sorted(lv["vargas"].items(), key=lambda x: -x[1]["total_cells"]):
            print(f"\n  {varga}: {len(info['properties'])} props × {len(info['structures'])} structs = {info['total_cells']} cells ({info['exceptions']} exceptions)")
            for prop, row in info["matrix"].items():
                falses = [s for s, v in row.items() if not v]
                if falses:
                    print(f"    {prop:30s} NOT valid for: {falses}")

    elif args.action == "compose-declension":
        from upakarana.analysis.compose import declension_matrix
        dm = declension_matrix()
        print(f"── Grammar: noun declension matrix ──")
        print(f"  Noun bases (subanta): {dm['subanta_count']}")
        print(f"  Cases (vibhakti):     {dm['vibhakti']}")
        print(f"  Numbers (vachana):    {dm['vachana']}")
        print(f"  Total forms:          {dm['total_forms']}")
        print(f"\n  Sample nouns: {dm['subanta'][:15]}")

    elif args.action == "compose-conjugation":
        from upakarana.analysis.compose import conjugation_matrix
        cm = conjugation_matrix()
        print(f"── Grammar: verb conjugation matrix ──")
        print(f"  Verb bases (tinanta): {cm['tinanta_count']}")
        print(f"  Tenses (kaala):       {cm['kaala']}")
        print(f"  Numbers (vachana):    {cm['vachana']}")
        print(f"  Persons (purusa):     {cm['purusa']}")
        print(f"  Total forms:          {cm['total_forms']}")
        print(f"\n  Sample verbs: {cm['tinanta'][:15]}")

    elif args.action == "compose-samasa":
        from upakarana.analysis.compose import samasa_classifier
        sc = samasa_classifier()
        print(f"── Samasa classification ──")
        for stype, names in sorted(sc["counts"].items(), key=lambda x: -x[1]):
            print(f"  {stype:20s} {sc['counts'][stype]:3d}")
            for n in sc["by_type"][stype][:5]:
                print(f"    {n}")
            if len(sc["by_type"][stype]) > 5:
                print(f"    ... +{len(sc['by_type'][stype])-5} more")

    elif args.action == "compose-collisions":
        from upakarana.analysis.compose import collision_analysis
        ca = collision_analysis()
        print(f"── Name collisions: {ca['total']} ──")
        print(f"   (each must appear in brahman with ALL edges from every source)\n")
        for name, info in sorted(ca["collisions"].items()):
            print(f"  {name} ({info['count']} instances):")
            for inst in info.get("instances", []):
                edge_summary = defaultdict(list)
                for e in inst["edges"]:
                    edge_summary[e["relation"]].append(e["target"])
                edges_str = "  ".join(f"{r}={','.join(ts[:3])}" for r, ts in edge_summary.items())
                print(f"    [{inst['domain']:45s}] {edges_str[:80]}")

    elif args.action == "compose-deriv-avastha":
        from upakarana.analysis.compose import derivative_avastha_cross
        da = derivative_avastha_cross()
        print(f"── Derivative × avastha cross ──")
        print(f"  Total:          {da['total']}")
        print(f"  Existing:       {da['existing']}")
        print(f"  Missing:        {da['missing']}")
        print(f"  Chain coherent: {da['chain_coherent']}")
        print(f"  Chain broken:   {da['chain_broken']}")
        for r in da["cross"]:
            tag = "✓" if r["exists"] else "·"
            chain = ""
            if r["chain_companion"]:
                ctag = "✓" if r["companion_exists"] else "✗"
                chain = f" chain:{r['chain_companion']}[{ctag}]"
            print(f"  {tag} {r['compound']:35s} (d/dt of {r['derives_from'] or '—'}){chain}")

    elif args.action == "compose-grammar":
        from upakarana.analysis.compose import grammar_shabda_generator
        gs = grammar_shabda_generator()
        print(f"── Grammar shabda generation ──")
        print(f"  Verbs:          {gs['verb_count']}")
        print(f"  Nouns:          {gs['noun_count']}")
        print(f"  Total forms:    {gs['total_forms']}")
        print(f"  Reverse index:  {gs['reverse_count']} inflected words")

        print(f"\n── Verb inflections ──")
        for v in gs["verbs"][:10]:
            forms_str = "  ".join(f"{k}={','.join(ws)}" for k, ws in v["forms"].items())
            print(f"  {v['name']:25s} ({v['base_word']:15s})  {forms_str}")
        if gs["verb_count"] > 10:
            print(f"  ... +{gs['verb_count']-10} more")

        print(f"\n── Noun inflections ──")
        for n in gs["nouns"][:10]:
            forms_str = "  ".join(f"{k}={','.join(ws)}" for k, ws in n["forms"].items())
            print(f"  {n['name']:25s} ({n['base_word']:15s})  {forms_str}")
        if gs["noun_count"] > 10:
            print(f"  ... +{gs['noun_count']-10} more")

        print(f"\n── Reverse lookup sample ──")
        for word in ["moved", "forces", "accelerating", "was", "energies", "collided"]:
            lookups = gs["reverse"].get(word, [])
            if lookups:
                for base, tag in lookups:
                    print(f"  \"{word}\" → {base} + {tag}")
            else:
                print(f"  \"{word}\" → (not found)")

    elif args.action == "compose-summary":
        from upakarana.analysis.compose import generation_summary
        gs = generation_summary()
        print(f"═══════════════════════════════════════════════════════")
        print(f" GENERATION SUMMARY")
        print(f"═══════════════════════════════════════════════════════")
        print(f"  Current nodes:                {gs['current_nodes']:,}")
        print(f"  Physics avastha missing:      +{gs['physics_avastha_missing']}")
        print(f"  Math op×structure missing:    +{gs['math_op_structure_missing']:,}  (of {gs['math_op_structure_total']:,})")
        print(f"  Math lakshana cells:          {gs['math_lakshana_total']:,}  (property×structure)")
        print(f"  Grammar noun forms:           +{gs['grammar_noun_forms']:,}")
        print(f"  Grammar verb forms:           +{gs['grammar_verb_forms']:,}")
        print(f"  Space lifts missing:          +{gs['space_lifts_missing']}")
        print(f"  Logic missing:                +{gs['logic_missing']}")
        print(f"  Pratipaksha missing:          {gs['pratipaksha_missing']}")
        print(f"  Derivative×avastha missing:   +{gs['derivative_avastha_missing']}")
        print(f"  Name collisions:              {gs['collisions']}")
        print(f"  ─────────────────────────────────────────────────────")
        print(f"  PROJECTED TOTAL:              ~{gs['projected_total']:,}")

    elif args.action == "hubs-compose":
        from upakarana.analysis.inheritance import hub_compose
        hubs = hub_compose(top_n=40, layer=args.layer)
        print(f"── Composition hubs (score = connectivity × generators × references) ──\n")
        print(f"  {'name':30s} {'layer':>8s} {'score':>7s} {'out':>4s} {'in':>4s} {'gen':>4s} {'ref':>4s} {'inh':>4s}")
        print(f"  {'─'*30} {'─'*8} {'─'*7} {'─'*4} {'─'*4} {'─'*4} {'─'*4} {'─'*4}")
        for h in hubs:
            print(f"  {h['name']:30s} {h['layer']:>8s} {h['score']:7d} {h['out']:4d} {h['in']:4d} "
                  f"{h['generators']:4d} {h['references']:4d} {h['inheritable']:4d}")
            detail = f"    gen({h['gen_type']}:{h['generators']})"
            detail += f"  ref({h['ref_type']}:{h['references']})"
            if h['gen_detail']:
                detail += f"  [{', '.join(h['gen_detail'][:6])}]"
            print(detail)

    elif args.action == "derivative-chain":
        from upakarana.analysis.inheritance import derivative_chain
        dc = derivative_chain()
        print(f"── Derivative chains (kramanusara: d/dt relationships) ──")
        print(f"  {dc['total_nodes']} nodes in derivative graph\n")

        print(f"── Chains (derivative → ... → base quantity) ──")
        for chain in dc["chains"]:
            labels = []
            for c in chain:
                info = dc["node_info"].get(c, {})
                avs = len(info.get("avastha", []))
                mnt = len(info.get("phala_mantras", []))
                matra = info.get("matra", [])
                unit = f" [{matra[0]}]" if matra else ""
                tag = f" (avs:{avs})" if avs else ""
                tag += f" (mnt:{mnt})" if mnt else ""
                labels.append(f"{c}{unit}{tag}")
            arrow = " ← d/dt ← "
            print(f"  {arrow.join(labels)}")

        print(f"\n── Roots (base quantities — no derivative of anything) ──")
        for r in dc["roots"]:
            derivs = dc["reverse"].get(r, [])
            print(f"  {r:30s} ← derivatives: {', '.join(derivs)}")

        print(f"\n── Leaves (highest derivatives — nothing derives from them) ──")
        for leaf in dc["leaves"]:
            bases = dc["forward"].get(leaf, [])
            print(f"  {leaf:30s} → base: {', '.join(bases)}")

    elif args.action == "compose-potential":
        from upakarana.analysis.inheritance import compose_potential
        if not args.name or " " not in args.name:
            print("usage: upakarana a compose-potential 'nodeA nodeB'", file=sys.stderr)
            return
        parts = args.name.split()
        a, b = parts[0], parts[1]
        cp = compose_potential(a, b)

        status = "EXISTS" if cp["exists"] else "NOT YET"
        print(f"── Composition potential: {a} × {b} → {cp['compound']} [{status}] ──\n")

        print(f"  [{a}] brings (as qualifier):")
        print(f"    swarupa chain: {a} → {' → '.join(cp['a_ancestors'][:5])}")
        for rel, targets in sorted(cp["a_context"].items()):
            print(f"    {rel:16s} → {', '.join(targets[:6])}")

        print(f"\n  [{b}] provides (as base):")
        print(f"    swarupa chain: {b} → {' → '.join(cp['b_ancestors'][:5])}")
        if cp["b_structural"]:
            print(f"    structural:")
            for rel, targets in sorted(cp["b_structural"].items()):
                print(f"      {rel:14s} → {', '.join(targets[:6])}")
        if cp["b_inheritable"]:
            print(f"    inheritable:")
            for rel, targets in sorted(cp["b_inheritable"].items()):
                print(f"      {rel:14s} → {', '.join(targets[:6])}")

        print(f"\n  [{cp['compound']}] would inherit:")
        for rel, targets in sorted(cp["predicted"].items()):
            print(f"    {rel:16s} → {', '.join(targets[:6])}")

        if cp["exists"]:
            print(f"\n  [{cp['compound']}] actually has:")
            for rel, targets in sorted(cp["actual"].items()):
                print(f"    {rel:16s} → {', '.join(targets[:6])}")

        if cp["similar_compounds"]:
            print(f"\n  Similar compounds (same base {b}):")
            for sim in cp["similar_compounds"][:10]:
                print(f"    {sim}")

        if cp["override_patterns"]:
            print(f"\n  Override patterns from similar compounds:")
            for rel, patterns in sorted(cp["override_patterns"].items()):
                for p in patterns[:3]:
                    print(f"    {p['compound']:25s} {rel}: {', '.join(p['has'][:4])}")

    elif args.action == "generator-product":
        from upakarana.analysis.inheritance import generator_product
        gp = generator_product(layer_filter=args.layer)
        print(f"── Generator product: sangati generators × kosha nodes ──")
        print(f"  {gp['total_analyzed']} nodes with 2+ sangati generators\n")

        print(f"── Distribution ──")
        for count, num_nodes in sorted(gp["by_count"].items(), reverse=True):
            bar = "█" * min(num_nodes, 40)
            print(f"  {count:2d} generators: {num_nodes:4d} nodes  {bar}")

        print(f"\n── Top sangati generators (most referenced) ──")
        for gen_name, freq in gp["top_generators"][:20]:
            roles = gp["generator_roles"].get(gen_name, {})
            role_str = ", ".join(f"{r}:{c}" for r, c in sorted(roles.items(), key=lambda x: -x[1]))
            print(f"  {gen_name:25s} {freq:4d} nodes  ({role_str})")

        # Show top nodes by generator count
        top_nodes = sorted(gp["nodes"].values(), key=lambda n: -n["generator_count"])
        print(f"\n── Richest nodes (most generators) ──")
        for ng in top_nodes[:25]:
            avs = f"  avs:{len(ng['avastha'])}" if ng['avastha'] else ""
            print(f"  {ng['name']:30s} [{ng['layer']:8s}] {ng['generator_count']:2d} generators{avs}")
            for g in ng["generators"]:
                roles = ", ".join(sorted(g["roles"]))
                print(f"    {g['name']:25s} ({roles})")

        # Show shared signatures
        if gp["shared_signatures"]:
            print(f"\n── Shared generator signatures (same generators = same 'type') ──")
            shown = 0
            for sig, names in gp["shared_signatures"].items():
                if shown >= 10:
                    break
                if len(names) >= 2:
                    print(f"  generators: {sig}")
                    print(f"    nodes: {', '.join(sorted(names)[:8])}")
                    shown += 1


    elif args.action == "sangati-levels":
        from upakarana.analysis.sangati_levels import level_summary
        ls = level_summary()
        print("── Sangati tower: swarupa hierarchy levels ──\n")
        for lvl in sorted(ls.keys()):
            info = ls[lvl]
            label = "cycles" if lvl == -1 else f"level {lvl}"
            print(f"  {label:10s}  {info['count']:3d} nodes")
            for name, refs in info["top"][:5]:
                print(f"    {name:30s} {refs:4d} non-sangati refs")
        total = sum(v["count"] for v in ls.values())
        print(f"\n  total: {total} sangati nodes")

    elif args.action == "sangati-at":
        from upakarana.analysis.sangati_levels import compute_levels
        levels = compute_levels()
        target = int(args.name) if args.name else 0
        nodes_at = sorted(n for n, info in levels.items() if info["level"] == target)
        label = "cycles" if target == -1 else f"level {target}"
        print(f"── Sangati {label}: {len(nodes_at)} nodes ──\n")
        for n in nodes_at:
            info = levels[n]
            parents = info["parents"]
            children = info["children"]
            p_str = f" ← {parents}" if parents else ""
            c_str = f" → {len(children)} children" if children else ""
            print(f"  {n:35s}{p_str}{c_str}")

    elif args.action == "sangati-tree":
        from upakarana.analysis.sangati_levels import level_tree
        lt = level_tree()
        print("── Sangati swarupa spine (top nodes per level) ──\n")
        for entry in lt["spine"]:
            lvl = entry["level"]
            label = "cycles" if lvl == -1 else f"level {lvl}"
            ct = lt["level_count"].get(lvl, 0)
            top_str = ", ".join(f"{n}({r})" for n, r in entry["nodes"])
            print(f"  {label:10s} [{ct:3d}]  {top_str}")
        print(f"\n── Main trunk (highest-ref per level) ──")
        for lvl, name, refs, parents in lt["trunk"]:
            p_str = f" ← {', '.join(parents)}" if parents else " (root)"
            print(f"  L{lvl}: {name:25s} ({refs:4d} refs){p_str}")

    elif args.action == "sangati-generates":
        from upakarana.analysis.sangati_levels import level_generates
        lg = level_generates()
        print("── Sangati levels → kosha domains shaped ──\n")
        for lvl in sorted(lg.keys()):
            info = lg[lvl]
            label = "cycles" if lvl == -1 else f"level {lvl}"
            print(f"  {label:10s}  {info['total_kosha']:4d} kosha nodes")
            for domain, count in list(info["domains"].items())[:8]:
                short = domain.replace("kosha/", "").replace("sangati/", "s/")
                print(f"    {short:40s} {count:3d}")
            if len(info["domains"]) > 8:
                print(f"    ... +{len(info['domains']) - 8} more domains")
            print()

    elif args.action == "gen-expected":
        from upakarana.analysis.generation import expected_node
        if not args.name or not args.name2:
            print("Usage: a gen-expected QUALIFIER BASE", file=sys.stderr)
            return
        exp = expected_node(args.name, args.name2)
        if "error" in exp:
            print(f"Error: {exp['error']}", file=sys.stderr)
            return
        print(f"── Expected: {exp['name']} ({exp['category']}) ──\n")
        print(f"  layer:   {exp['layer']}")
        print(f"  domain:  {exp['domain']}")
        print(f"  context: {exp['context']}")
        print(f"  om5:     {'exists' if exp['exists_om5'] else 'not found (avastha-generated)'}")
        print(f"  shabda:  {'exists' if exp['exists_shabda'] else 'none'}")
        print(f"\n── Static edges (what om5 should declare) ──")
        for rel, targets in exp["static_edges"].items():
            print(f"  ({rel} {' '.join(targets)})")
        if exp["overrides"]:
            print(f"\n── Shabda overrides applied ──")
            for rel, targets in exp["overrides"].items():
                print(f"  override-{rel}: {', '.join(targets)}")
        if exp["live_extras"]:
            print(f"\n── Engine-added (predicted) ──")
            for key, vals in exp["live_extras"].items():
                print(f"  {key}: {', '.join(vals)}")
        # Show om5 preview
        from upakarana.parsers.om5 import serialize_node
        print(f"\n── Om5 preview ──")
        print(serialize_node(exp["name"], exp["layer"], exp["static_edges"],
                             [f"generated: {exp['qualifier']} + {exp['base']}"]))

    elif args.action == "gen-validate":
        from upakarana.analysis.generation import validate_node
        if not args.name:
            print("Usage: a gen-validate NODE_NAME", file=sys.stderr)
            return
        # Try live validation if server is running
        client = None
        try:
            from upakarana.analysis.live import connect
            client = connect()
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

    elif args.action == "gen-candidates":
        from upakarana.analysis.generation import gen_candidates
        if not args.name:
            print("Usage: a gen-candidates BASE_NAME", file=sys.stderr)
            return
        gc = gen_candidates(args.name)
        if "error" in gc:
            print(f"Error: {gc['error']}", file=sys.stderr)
            return
        print(f"── Candidates for {gc['base']} ({gc['domain']}) ──")
        print(f"  {gc['total_qualifiers']} qualifiers, {gc['existing']} in om5, {gc['avastha_generated']} avastha-only\n")
        for c in gc["candidates"]:
            flags = []
            if c["exists_om5"]:
                flags.append("om5")
            if c["exists_avastha"]:
                flags.append("avastha")
            if c["in_validity"]:
                flags.append("valid")
            flag_str = ", ".join(flags) if flags else "missing"
            print(f"  {c['name']:35s} [{flag_str:15s}] ctx={c['context']}")

    elif args.action == "gen-gaps":
        from upakarana.analysis.generation import gen_gaps
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

    elif args.action == "gen-validate-all":
        from upakarana.analysis.generation import validate_all
        client = None
        try:
            from upakarana.analysis.live import connect
            client = connect()
        except Exception:
            pass
        va = validate_all(client=client)
        print(f"── Validate all compounds: {va['total']} nodes ──")
        print(f"  ok: {va['ok']}  warn: {va['warn']}  fail: {va['fail']}\n")
        for r in va["results"]:
            if r["status"] != "ok":
                sym = "⚠" if r["status"] == "warn" else "✗"
                issues = [c["detail"] for c in r["checks"] if c["status"] in ("warn", "fail")]
                print(f"  {sym} {r['name']:35s} {'; '.join(issues[:2])}")


def cmd_live(args):
    from upakarana.analysis.live import connect
    try:
        client = connect()
    except Exception as e:
        print(f"Engine not running: {e}", file=sys.stderr)
        return

    try:
        if args.action == "drift":
            from upakarana.analysis.live import static_vs_live
            result = static_vs_live(client)
            s = result["static"]
            l = result["live"]
            print(f"Static: {s['om5_nodes']} om5 nodes, {s['tantras_on_disk']} tantras on disk, {s['shabda_nodes']} shabda nodes")
            print(f"Live:   {l['tantras_loaded']} tantras loaded")
            if result["tantras_only_on_disk"]:
                print(f"\nOn disk but NOT loaded ({len(result['tantras_only_on_disk'])}):")
                for t in result["tantras_only_on_disk"][:15]:
                    print(f"  {t}")
            if result["tantras_only_in_engine"]:
                print(f"\nIn engine but NOT on disk ({len(result['tantras_only_in_engine'])}):")
                for t in result["tantras_only_in_engine"][:15]:
                    print(f"  {t}")
            gr = result["ghost_resolution"]
            if gr["resolved"]:
                print(f"\nStatic ghosts that RESOLVE in live graph ({len(gr['resolved'])}):")
                for g in gr["resolved"]:
                    print(f"  {g['name']:30s} [{g['layer']}]")
            if gr["truly_missing"]:
                print(f"\nTruly missing (ghost in both static and live) ({len(gr['truly_missing'])}):")
                for g in gr["truly_missing"][:15]:
                    print(f"  {g}")

        elif args.action == "pratipaksha":
            from upakarana.analysis.live import pratipaksha_walk
            result = pratipaksha_walk(client)
            print(f"Pratipaksha involution on {len(result['ops'])} ops:")
            print(f"  symmetric: {len(result['symmetric'])}")
            for r in result["symmetric"]:
                print(f"    {r['op']} ↔ {r['pratipaksha']}")
            if result["broken"]:
                print(f"  broken ({len(result['broken'])}):")
                for r in result["broken"]:
                    print(f"    {r['op']} → {r['pratipaksha']} → {r['round_trip'] or '(none)'}")
            if result["no_pratipaksha"]:
                print(f"  no pratipaksha ({len(result['no_pratipaksha'])}):")
                for r in result["no_pratipaksha"]:
                    print(f"    {r['op']}")

        elif args.action == "panchaavayava":
            from upakarana.analysis.live import panchaavayava_walk
            result = panchaavayava_walk(client)
            if not result.get("exists"):
                print("panchaavayava node not found in live graph")
                print("(may need engine reload after creating the om5 file)")
                return
            print("panchaavayava exists in live graph")
            if "limbs" in result:
                print(f"  yukta (limbs): {result['limbs']}")
            if "phala_chain" in result:
                print(f"  phala chain:")
                for step in result["phala_chain"]:
                    print(f"    {step}")

        elif args.action == "ghosts":
            from upakarana.analysis.ghosts import structural_ghosts
            from upakarana.analysis.live import ghost_walk
            top = [g["name"] for g in structural_ghosts()[:30]]
            result = ghost_walk(client, top)
            if result["resolved"]:
                print(f"Static ghosts that RESOLVE in live graph ({len(result['resolved'])}):")
                for g in result["resolved"]:
                    print(f"  {g['name']:30s} [{g['layer']}]")
            print(f"\nTruly missing ({len(result['truly_missing'])}):")
            for g in result["truly_missing"]:
                print(f"  {g}")

        elif args.action == "signal-trace":
            from upakarana.analysis.live import signal_trace
            sentence = args.sentence or args.name
            if not sentence:
                print("usage: upakarana live signal-trace -s 'question'", file=sys.stderr)
                return
            result = signal_trace(client, sentence)
            if "trace_error" in result:
                print(f"Error: {result['trace_error']}")
                return
            print(f"Sentence: {result['sentence']}")
            print(f"Stages: {' → '.join(result.get('stages', []))}")
            print(f"Triples after refine: {result.get('refine_triples', '?')}")
            if result.get("satya"):
                print(f"Recognized (satya): {result['satya']}")
            if result.get("sankhya"):
                print(f"Values (sankhya): {result['sankhya']}")
            if result.get("ownership"):
                print(f"Ownership: {result['ownership']}")
            if result.get("kaala"):
                print(f"Tense (kaala): {result['kaala']}")
            if result.get("vachana"):
                print(f"Number (vachana): {result['vachana']}")
            if result.get("answer"):
                print(f"\nAnswer: {result['answer']}")

        elif args.action == "walk":
            from upakarana.analysis.live import live_walk
            if not args.name or not args.relation:
                print("usage: upakarana live walk <node> -r <relation>", file=sys.stderr)
                return
            result = live_walk(client, args.name, args.relation)
            if isinstance(result, dict) and "error" in result:
                print(f"Error: {result['error']}")
            elif isinstance(result, list):
                for r in result:
                    print(f"  {r}")
            else:
                print(result)

        elif args.action == "inspect":
            if not args.name:
                print("usage: upakarana live inspect <name>", file=sys.stderr)
                return
            from upakarana.analysis.live import live_inspect
            _print_json(live_inspect(client, args.name))

    finally:
        client.close()


def cmd_gen(args):
    import os
    from upakarana.paths import BRAHMAN
    from upakarana.analysis.generation import expected_node, validate_node, gen_candidates, gen_gaps
    from upakarana.parsers import om5, shabda as shabda_mod

    out_root = args.to or str(BRAHMAN)

    if args.action == "preview":
        if not args.name or not args.name2:
            print("Usage: gen preview QUALIFIER BASE", file=sys.stderr)
            return
        exp = expected_node(args.name, args.name2)
        if "error" in exp:
            print(f"Error: {exp['error']}", file=sys.stderr)
            return
        # Show om5 preview
        text = om5.serialize_node(exp["name"], exp["layer"], exp["static_edges"],
                                  [f"generated: {exp['qualifier']} + {exp['base']}"])
        print(text)
        # Show shabda preview
        word_forms = f"{exp['name'].replace('-', ' ')},{exp['name']}"
        shabda_text = shabda_mod.serialize_shabda(exp["name"], {
            "word": word_forms,
            "name": exp["name"].replace("-", " "),
        })
        print(shabda_text)
        # Show where it would be written
        domain = exp["domain"]
        om5_path = os.path.join(out_root, domain, f"{exp['name']}.om5")
        shabda_path = os.path.join(out_root, "shabda", f"{domain.split('/')[0]}.shabda")
        print(f"om5 → {om5_path}")
        print(f"shabda → {shabda_path}")

    elif args.action == "create":
        if not args.name or not args.name2:
            print("Usage: gen create QUALIFIER BASE", file=sys.stderr)
            return
        exp = expected_node(args.name, args.name2)
        if "error" in exp:
            print(f"Error: {exp['error']}", file=sys.stderr)
            return
        if exp["exists_om5"]:
            print(f"Node {exp['name']} already exists as om5 file", file=sys.stderr)
            return

        domain = exp["domain"]
        om5_path = os.path.join(out_root, domain, f"{exp['name']}.om5")
        shabda_domain = domain.split("/")[0] if "/" in domain else domain
        shabda_path = os.path.join(out_root, "shabda", f"{shabda_domain}.shabda")

        # Write om5
        om5.write_node(om5_path, exp["name"], exp["layer"], exp["static_edges"],
                       [f"generated: {exp['qualifier']} + {exp['base']}"])
        print(f"wrote {om5_path}")

        # Write shabda
        word_forms = f"{exp['name'].replace('-', ' ')},{exp['name']}"
        shabda_mod.append_shabda(shabda_path, exp["name"], {
            "word": word_forms,
            "name": exp["name"].replace("-", " "),
        })
        print(f"wrote {shabda_path}")

        # Show what was created
        print(f"\nCreated {exp['name']} ({exp['category']}):")
        for rel, targets in exp["static_edges"].items():
            print(f"  ({rel} {' '.join(targets)})")

    elif args.action == "validate":
        if not args.name:
            print("Usage: gen validate NODE_NAME", file=sys.stderr)
            return
        client = None
        try:
            from upakarana.analysis.live import connect
            client = connect()
        except Exception:
            pass
        result = validate_node(args.name, client=client)
        status_sym = {"ok": "✓", "warn": "⚠", "fail": "✗", "info": "·", "skip": "—"}
        print(f"── Validate: {result['name']} [{result['status'].upper()}] ──\n")
        for c in result["checks"]:
            sym = status_sym.get(c["status"], "?")
            print(f"  {sym} {c['check']:20s} {c['detail']}")
        if "expected" in result and "actual" in result:
            exp_e = result.get("expected", {})
            act_e = result.get("actual", {})
            all_rels = sorted(set(list(exp_e.keys()) + list(act_e.keys())))
            print(f"\n── Edge comparison ──")
            for rel in all_rels:
                e = set(exp_e.get(rel, []))
                a = set(act_e.get(rel, []))
                if e == a:
                    print(f"  {rel:15s} = {sorted(a)}")
                else:
                    if e - a:
                        print(f"  {rel:15s} missing: {sorted(e - a)}")
                    if a - e:
                        print(f"  {rel:15s} extra:   {sorted(a - e)}")
                    if e & a:
                        print(f"  {rel:15s} match:   {sorted(e & a)}")

    elif args.action == "batch":
        domain = args.domain or args.name
        gg = gen_gaps(domain_filter=domain)
        total = gg["total_gaps"]
        if total == 0:
            print("No generation gaps found.")
            return

        created = 0
        for domain_path, gaps in gg["by_domain"].items():
            for g in gaps:
                if g["type"] != "avastha_only":
                    continue  # only auto-generate avastha compounds
                exp = expected_node(g["qualifier"], g["base"])
                if "error" in exp or exp["exists_om5"]:
                    continue
                om5_path = os.path.join(out_root, domain_path, f"{exp['name']}.om5")
                shabda_domain = domain_path.split("/")[0] if "/" in domain_path else domain_path
                shabda_path = os.path.join(out_root, "shabda", f"{shabda_domain}.shabda")

                if args.dry_run:
                    print(f"  [dry-run] {exp['name']:35s} → {om5_path}")
                else:
                    om5.write_node(om5_path, exp["name"], exp["layer"], exp["static_edges"],
                                   [f"generated: {exp['qualifier']} + {exp['base']}"])
                    word_forms = f"{exp['name'].replace('-', ' ')},{exp['name']}"
                    shabda_mod.append_shabda(shabda_path, exp["name"], {
                        "word": word_forms,
                        "name": exp["name"].replace("-", " "),
                    })
                    print(f"  {exp['name']:35s} → {om5_path}")
                created += 1

        action = "would create" if args.dry_run else "created"
        print(f"\n{action} {created} nodes")

    elif args.action == "status":
        # Count what's in brahman
        b2_files = []
        for dirpath, _, filenames in os.walk(out_root):
            for f in filenames:
                if f.endswith(".om5"):
                    b2_files.append(os.path.join(dirpath, f))
        shabda_files = []
        shabda_dir = os.path.join(out_root, "shabda")
        if os.path.isdir(shabda_dir):
            for f in os.listdir(shabda_dir):
                if f.endswith(".shabda"):
                    shabda_files.append(f)

        print(f"── brahman/ status ──")
        print(f"  om5 files:    {len(b2_files)}")
        print(f"  shabda files: {len(shabda_files)}")

        if b2_files:
            print(f"\n── Nodes ──")
            for path in sorted(b2_files):
                parsed = om5.parse(path)
                if parsed:
                    rel = os.path.relpath(path, out_root)
                    print(f"  {parsed['name']:35s} {rel}")

        # Show generation gaps
        gg = gen_gaps()
        print(f"\n── Gaps remaining: {gg['total_gaps']} ──")
        for domain, gaps in list(gg["by_domain"].items())[:5]:
            short = domain.replace("kosha/", "")
            print(f"  {short:40s} {len(gaps)} gaps")


def cmd_usage(args):
    from upakarana.usage import report, never_used

    r = report()
    if args.action == "report":
        print(f"Sessions: {r['sessions']}")
        print(f"Total invocations: {r['total_invocations']}")
        print(f"Total misses: {r['total_misses']}")
        print(f"Unique commands: {r['unique_commands']}")
        print(f"First use: {r['first_use']}")
        print(f"\nTop commands:")
        for t in r["top"]:
            print(f"  {t['command']:30s} {t['count']:5d}x  last: {t['last']}")
        if r["misses"]:
            print(f"\nNo-match commands:")
            for m in sorted(r["misses"], key=lambda x: -x["misses"]):
                print(f"  {m['command']:30s} {m['misses']:5d}/{m['count']} ({m['rate']}%)")
    elif args.action == "never":
        all_cmds = _all_possible_commands()
        unused = never_used(all_cmds)
        print(f"{len(unused)} commands never used:")
        for c in unused:
            print(f"  {c}")
    elif args.action == "reset":
        from upakarana.usage import USAGE_FILE
        if USAGE_FILE.exists():
            USAGE_FILE.unlink()
            print("Usage data reset.")
        else:
            print("No usage data to reset.")


def _all_possible_commands():
    """List all possible command+action pairs."""
    return [
        "om summary", "om search", "om source", "om domain", "om with-relation",
        "tantra summary", "tantra search", "tantra source", "tantra group", "tantra callgraph",
        "shabda summary", "shabda search", "shabda node", "shabda gaps",
        "shabda roles", "shabda coverage",
        "vy start", "vy stop", "vy status", "vy reload", "vy eval", "vy ask", "vy walk", "vy inspect",
        "test list", "test summary", "test run", "test failed",
        "cache summary", "cache gates", "cache slow",
        "lint", "health", "search",
        "ocaml report", "ocaml darshana", "ocaml patterns", "ocaml coupling",
        "ocaml consolidate", "ocaml summary", "ocaml functions", "ocaml state", "ocaml parallel",
        "q op", "q ops", "q dispatch", "q missing", "q explain", "q overview", "q node", "q eval",
        "a ghosts", "a incoming", "a hubs", "a orphans", "a flow", "a fingerprint",
        "a swarupa", "a components", "a ring", "a siblings", "a signals", "a signals-gap",
        "a compose",
        "a patterns", "a grounding", "a vocabulary", "a parallel",
        "usage report", "usage never",
    ]


DISPATCH = {
    "om": cmd_om,
    "tantra": cmd_tantra,
    "shabda": cmd_shabda,
    "vy": cmd_vy,
    "test": cmd_test,
    "cache": cmd_cache,
    "lint": cmd_lint,
    "health": cmd_health,
    "search": cmd_search,
    "ocaml": cmd_ocaml,
    "q": cmd_query,
    "a": cmd_analyze,
    "live": cmd_live,
    "gen": cmd_gen,
    "usage": cmd_usage,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    # Track usage
    from upakarana.usage import track
    action = getattr(args, "action", None) or getattr(args, "target", None)
    track(args.command, action)

    handler = DISPATCH.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
