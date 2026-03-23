"""cli.py — Single CLI dispatcher for upakarana."""

import argparse
import json
import sys


def _print_json(data):
    print(json.dumps(data, indent=2, default=str))


# --- Om5 commands ---

def cmd_om(args):
    from upakarana.parsers import om5
    nodes = om5.load_all()

    if args.action == "summary":
        _print_json(om5.summary(nodes))
    elif args.action == "search":
        results = om5.search(nodes, args.pattern or args.name)
        for r in results:
            print(f"  {r['name']:30s} [{r['layer']}] {r['domain']}")
            for m in r["matches"][:3]:
                print(f"    L{m['line']}: {m['text']}")
    elif args.action == "source":
        node = nodes.get(args.name)
        if node:
            print(node["source"])
        else:
            print(f"Not found: {args.name}", file=sys.stderr)
    elif args.action == "domain":
        info = om5.by_domain(nodes, depth=args.depth)
        for dom, ns in info.items():
            print(f"  {dom}: {len(ns)} nodes")
    elif args.action == "with-relation":
        results = om5.with_relation(nodes, args.relation)
        print(f"{len(results)} nodes with {args.relation}:")
        for n in results[:20]:
            print(f"  {n['name']}")


# --- Tantra commands ---

def cmd_tantra(args):
    from upakarana.parsers import tantra4
    tantras = tantra4.load_all()

    if args.action == "summary":
        _print_json(tantra4.summary(tantras))
    elif args.action == "search":
        results = tantra4.search(tantras, args.pattern or args.name)
        for r in results:
            print(f"  {r['name']:30s} [{r['group']}]")
            for m in r["matches"][:3]:
                print(f"    L{m['line']}: {m['text']}")
    elif args.action == "source":
        t = tantras.get(args.name)
        if t:
            print(t["source"])
        else:
            print(f"Not found: {args.name}", file=sys.stderr)
    elif args.action == "group":
        groups = tantra4.by_group(tantras)
        if args.name:
            gs = groups.get(args.name, [])
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
    nodes = shabda.load_all()

    if args.action == "summary":
        _print_json(shabda.summary(nodes))
    elif args.action == "search":
        results = shabda.search(nodes, args.pattern or args.name)
        for r in results:
            print(f"  {r['name']}")
    elif args.action == "node":
        node = nodes.get(args.name)
        if node:
            _print_json({"name": node["name"], "fields": node["fields"]})
        else:
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
            result = c.eval(args.expr)
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
            print(c.ask(args.question))
        finally:
            c.close()
    elif args.action == "walk":
        from upakarana.engine.client import Client
        c = Client()
        try:
            if args.incoming:
                result = c.walk_in(args.node, args.relation)
            else:
                result = c.walk(args.node, args.relation)
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
        result = run(layer=args.layer, gate=args.gate, pattern=args.pattern,
                     last_failed=args.last_failed, verbose=args.verbose)
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
    from upakarana.testing.cache import load, summarize, by_gate, slowest_calls

    _, entries = load()
    if args.action == "summary":
        _print_json(summarize(entries))
    elif args.action == "gates":
        gates = by_gate(entries)
        for gate, es in sorted(gates.items()):
            print(f"  {gate}: {len(es)}")
    elif args.action == "slow":
        for c in slowest_calls(entries):
            print(f"  {c['elapsed_ms']:6d}ms {c['test']:30s} {c['method']}")


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


# --- Query commands ---

def cmd_query(args):
    from upakarana.query import Q
    q = Q()

    if args.action == "op":
        if not args.name:
            print("usage: upakarana query op <name>", file=sys.stderr); return
        _print_json(q.op(args.name))
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
        _print_json(q.node(args.name))
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
    s.add_argument("--layer", "-l")
    s.add_argument("--gate", "-g")
    s.add_argument("--pattern", "-p")
    s.add_argument("--last-failed", action="store_true")
    s.add_argument("--verbose", "-v", action="store_true")

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
                                       "consolidate", "summary", "functions", "state"])

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
    ])
    s.add_argument("name", nargs="?")
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


def cmd_usage(args):
    from upakarana.usage import report, never_used

    r = report()
    if args.action == "report":
        print(f"Sessions: {r['sessions']}")
        print(f"Total invocations: {r['total_invocations']}")
        print(f"Unique commands: {r['unique_commands']}")
        print(f"First use: {r['first_use']}")
        print(f"\nTop commands:")
        for t in r["top"]:
            print(f"  {t['command']:30s} {t['count']:5d}x  last: {t['last']}")
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
        "ocaml consolidate", "ocaml summary", "ocaml functions", "ocaml state",
        "q op", "q ops", "q dispatch", "q missing", "q explain", "q overview", "q node", "q eval",
        "a ghosts", "a incoming", "a hubs", "a orphans", "a flow", "a fingerprint",
        "a swarupa", "a components", "a ring", "a siblings", "a signals", "a signals-gap",
        "a patterns", "a grounding", "a vocabulary",
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
