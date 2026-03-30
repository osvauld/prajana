"""meta.py — health, lint, usage, ocaml commands."""

import sys


def cmd_health(args, store):
    from upakarana2.graph.health import full_report, print_report
    client = None
    if not args.static_only:
        try:
            from upakarana2.engine.client import Client
            client = Client()
        except Exception:
            pass
    report = full_report(client=client)
    print_report(report)
    if client:
        client.close()


def cmd_lint(args, store):
    from upakarana2.graph.health import om5_lint, tantra4_lint

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
            sev = i.get("severity", "info")
            print(f"  [{sev}] {i.get('tantra', '?')}: {i['issue']}")


def cmd_usage(args, store):
    if args.action == "report":
        r = store.usage.report()
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
                for etype, cnt in m.get("error_types", []):
                    print(f"    [err] {cnt:4d}x  {etype}")
                for arg, cnt in m["top_args"]:
                    print(f"          {cnt:4d}x  {arg}")

    elif args.action == "never":
        unused = store.usage.never_used(_all_possible_commands())
        print(f"{len(unused)} commands never used:")
        for c in unused:
            print(f"  {c}")

    elif args.action == "reset":
        import shutil
        from upakarana2.paths import STORE_PATH
        if STORE_PATH.exists():
            shutil.rmtree(STORE_PATH)
            print("Usage data reset (full store deleted).")
        else:
            print("No usage data to reset.")


def cmd_ocaml(args, store):
    from upakarana2.tools import ocaml

    modules = ocaml.parse_all()
    if args.action == "report":
        ocaml.print_report(modules)
    elif args.action == "darshana":
        ocaml.print_darshana(modules)
    elif args.action == "patterns":
        ocaml.print_patterns(modules)
    elif args.action == "coupling":
        ocaml.print_coupling(modules)
    elif args.action == "functions":
        from upakarana2.cmd.dispatch import _print_json
        _print_json(ocaml.summary(modules))


def _all_possible_commands():
    return [
        "om summary", "om search", "om source", "om domain", "om with-relation",
        "tantra summary", "tantra search", "tantra source", "tantra group",
        "tantra callgraph", "tantra reachability",
        "shabda summary", "shabda search", "shabda node", "shabda gaps",
        "shabda roles", "shabda coverage",
        "vy start", "vy stop", "vy status", "vy reload",
        "vy eval", "vy ask", "vy walk", "vy inspect",
        "vy drift", "vy pratipaksha", "vy signal-trace", "vy panchaavayava",
        "test list", "test summary", "test run", "test failed",
        "cache summary", "cache gates", "cache slow", "cache trace",
        "lint", "health", "search",
        "ocaml report", "ocaml darshana", "ocaml patterns", "ocaml coupling", "ocaml functions",
        "a ghosts", "a incoming", "a hubs", "a orphans", "a flow", "a ring",
        "a signals", "a signals-gap", "a swarupa", "a components",
        "a compose", "a compose-gen", "a compose-inverse",
        "a gen-gaps", "a gen-validate",
        "usage report", "usage never",
    ]
