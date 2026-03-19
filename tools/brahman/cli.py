"""
cli.py — CLI entry point for the brahman reader.

Usage:
  python3 tools/read_brahman.py [tantra|om] [command] [args]
  python3 -m tools.brahman [tantra|om] [command] [args]

Tantra commands:
  tantra summary                     one-line-per-tantra overview
  tantra groups                      list tantra groups
  tantra all                         dump all tantras with source
  tantra group pipeline              dump one group
  tantra source execute-mantra       dump one tantra
  tantra callgraph                   static call graph
  tantra callers derive-chain        who calls this?
  tantra callees anuvada-ganana      what does this call?
  tantra search "viveka"             regex search tantras

Om commands:
  om summary                         counts by layer and domain
  om domains                         list all domain paths (depth=2)
  om domains 3                       list at depth=3
  om domain kosha/math/number        dump all nodes in domain
  om source velocity                 dump one om node
  om search "pratipaksha"            regex search om files
  om with-key eval                   find nodes with shabda key
  om with-relation pratipaksha       find nodes with edge relation

Cross-cutting:
  search "viveka"                    search both tantras and om
  serve                              start socket server
  serve --socket /tmp/brahman.sock

Test commands:
  test list                          list all v2 tests with metadata
  test list evaluator                list tests in one layer
  test list --gate arithmetic        list xfails for one gate
  test summary                       counts by layer + gate
  test run                           run all v2 tests
  test run evaluator                 run one layer
  test run test_ke_basic             run one test by name
  test run --gate arithmetic         run xfails for one gate
  test run --pattern scope           run tests matching pattern
"""

import argparse
import json
import os
import sys
from pathlib import Path

from . import tantras, om, tests as test_meta, runner, cache as cache_mod
from .cache import DEFAULT_CACHE
from .server import BrahmanServer, DEFAULT_SOCKET


def _fmt_sep(title, width=80):
    return f"\n{'=' * width}\n  {title}\n{'=' * width}\n"


def _fmt_header(name, meta, path, width=80):
    return f"\n{'─' * width}\n  {name}  ({meta})\n  {path}\n{'─' * width}"


# ── tantra CLI ─────────────────────────────────────────────────────────────────


def cmd_tantra(args):
    ts = tantras.load_all()
    sub = args.subcmd if args.subcmd else "summary"

    if sub == "summary":
        bg = tantras.by_group(ts)
        total = sum(t["lines"] for t in ts.values())
        print(f"\n{'=' * 100}")
        print(f"  TANTRA SUMMARY -- {len(ts)} tantras, {total} total lines")
        print(f"{'=' * 100}\n")
        for gname in tantras.TANTRA_GROUPS:
            gt = bg.get(gname, [])
            if not gt:
                continue
            gl = sum(t["lines"] for t in gt)
            print(
                f"  {gname}/ ({len(gt)} files, {gl} lines) -- {tantras.TANTRA_GROUPS[gname]}"
            )
            print(f"  {'─' * 96}")
            print(
                f"  {'Name':<30} {'Lines':>5} {'Takes':>5} {'Binds':>5} {'Calls':>5} {'Scans':>5} {'Conds':>5} {'Returns'}"
            )
            print(f"  {'─' * 96}")
            for t in sorted(gt, key=lambda x: x["name"]):
                ret = t["returns"] or "—"
                if len(ret) > 30:
                    ret = ret[:30] + "..."
                print(
                    f"  {t['name']:<30} {t['lines']:>5} {len(t['takes']):>5} {len(t['bindings']):>5} {len(t['calls']):>5} {t['scans']:>5} {t['conds']:>5} {ret}"
                )
            print()

    elif sub == "groups":
        bg = tantras.by_group(ts)
        print(f"\nTantra groups ({len(tantras.TANTRA_GROUPS)}):\n")
        for gname, desc in tantras.TANTRA_GROUPS.items():
            gt = bg.get(gname, [])
            total = sum(t["lines"] for t in gt)
            print(f"  {gname:<12} {len(gt):>2} files  {total:>4} lines  {desc}")

    elif sub == "all":
        bg = tantras.by_group(ts)
        for gname in tantras.TANTRA_GROUPS:
            gt = bg.get(gname, [])
            if not gt:
                continue
            gl = sum(t["lines"] for t in gt)
            desc = tantras.TANTRA_GROUPS[gname]
            print(_fmt_sep(f"{gname}/ -- {len(gt)} files, {gl} lines -- {desc}"))
            for t in sorted(gt, key=lambda x: x["name"]):
                meta = f"[{t['group']}] {t['lines']} lines"
                if t["takes"]:
                    meta += f" | takes: {', '.join(t['takes'])}"
                print(_fmt_header(t["name"], meta, t["path"]))
                print(t["source"])

    elif sub == "group":
        group = args.name
        data = tantras.to_json_full(ts, group=group)
        if not data:
            print(
                f"Group '{group}' not found. Available: {', '.join(tantras.TANTRA_GROUPS.keys())}"
            )
            return
        for name, t in sorted(data.items()):
            meta = f"[{t['group']}] {t['lines']} lines"
            print(_fmt_header(name, meta, t["path"]))
            print(t["source"])

    elif sub == "source":
        name = args.name
        t = ts.get(name)
        if not t:
            print(f"Tantra '{name}' not found.")
            matches = [n for n in ts if name in n]
            if matches:
                print(f"Did you mean: {', '.join(matches)}?")
            return
        meta = f"[{t['group']}] {t['lines']} lines"
        if t["takes"]:
            meta += f" | takes: {', '.join(t['takes'])}"
        print(_fmt_header(t["name"], meta, t["path"]))
        print(t["source"])

    elif sub == "callgraph":
        cg = tantras.call_graph(ts)
        rcg = tantras.reverse_call_graph(cg)
        print(_fmt_sep("CALL GRAPH"))
        for name in sorted(cg.keys(), key=lambda n: (-len(cg[n]), n)):
            callees = cg[name]
            callers = rcg.get(name, [])
            if not callees and not callers:
                continue
            out = f"  {name:<35} [{ts[name]['group']}]"
            if callees:
                out += f"\n    calls  -> {', '.join(callees)}"
            if callers:
                out += f"\n    from   <- {', '.join(callers)}"
            print(out + "\n")

        print(_fmt_sep("HUB TANTRAS -- most called"))
        hubs = sorted(rcg.items(), key=lambda x: -len(x[1]))
        for name, callers in hubs[:15]:
            print(f"  {name:<35} called by {len(callers):>2}: {', '.join(callers)}")

    elif sub == "callers":
        name = args.name
        cg = tantras.call_graph(ts)
        rcg = tantras.reverse_call_graph(cg)
        callers = rcg.get(name, [])
        if not callers:
            print(f"No tantras call '{name}'.")
            if name not in ts:
                print(f"('{name}' is not a known tantra)")
            return
        print(f"\nTantras that call '{name}' ({len(callers)}):\n")
        for c in callers:
            t = ts[c]
            print(f"  {c:<35} [{t['group']}] {t['lines']} lines")

    elif sub == "callees":
        name = args.name
        if name not in ts:
            print(f"Tantra '{name}' not found.")
            return
        cg = tantras.call_graph(ts)
        callees = cg.get(name, [])
        print(f"\n'{name}' [{ts[name]['group']}] calls ({len(callees)}):\n")
        for c in callees:
            t = ts[c]
            print(f"  {c:<35} [{t['group']}] {t['lines']} lines")

    elif sub == "search":
        pattern = args.name
        results = tantras.search(ts, pattern)
        total = sum(len(r["matches"]) for r in results)
        for r in results:
            print(f"\n  {r['name']} [{r['group']}] -- {len(r['matches'])} matches")
            print(f"  {r['path']}")
            for m in r["matches"]:
                print(f"    {m['line']:>4}: {m['text']}")
        print(f"\n  Total: {total} matches across {len(ts)} tantras.")

    else:
        print(f"Unknown tantra command: {sub}")
        print(
            "Available: summary, groups, all, group, source, callgraph, callers, callees, search"
        )


# ── om CLI ─────────────────────────────────────────────────────────────────────


def cmd_om(args):
    oms = om.load_all()
    sub = args.subcmd if args.subcmd else "summary"

    if sub == "summary":
        layers = {}
        for o in oms.values():
            layers[o["layer"]] = layers.get(o["layer"], 0) + 1
        total = sum(o["lines"] for o in oms.values())

        print(f"\n{'=' * 80}")
        print(f"  OM SUMMARY -- {len(oms)} nodes, {total} total lines")
        print(f"{'=' * 80}\n")
        print("  Layers:")
        for layer, count in sorted(layers.items(), key=lambda x: -x[1]):
            print(f"    {layer:<12} {count:>5} nodes")

        depth = int(args.name) if args.name and args.name.isdigit() else 2
        domains = om.by_domain(oms, depth=depth)
        print(f"\n  Domains (depth={depth}):")
        for dname, nodes in domains.items():
            total_l = sum(n["lines"] for n in nodes)
            print(f"    {dname:<45} {len(nodes):>4} nodes  {total_l:>5} lines")

    elif sub == "domains":
        depth = int(args.name) if args.name and args.name.isdigit() else 2
        domains = om.by_domain(oms, depth=depth)
        print(f"\nOm domains (depth={depth}, {len(domains)} groups):\n")
        for dname, nodes in domains.items():
            total_l = sum(n["lines"] for n in nodes)
            print(f"  {dname:<45} {len(nodes):>4} nodes  {total_l:>5} lines")

    elif sub == "domain":
        domain = args.name
        if not domain:
            print("Usage: om domain DOMAIN_PATH")
            return
        info = om.domain_info(oms, domain)
        if info["total_count"] == 0:
            print(f"No nodes found under domain '{domain}'")
            return

        print(
            _fmt_sep(
                f"{domain}/ -- {info['total_count']} nodes, {info['total_lines']} lines"
            )
        )

        # show subdomains first
        subs = info["subdomains"]
        if len(subs) > 1 or (len(subs) == 1 and list(subs.keys())[0] != domain):
            print("  Subdomains:")
            print(f"  {'Path':<45} {'Nodes':>5} {'Lines':>6}  Direct nodes")
            print(f"  {'─' * 96}")
            for dname, dinfo in subs.items():
                label = dname if dname != domain else f"{dname} (direct)"
                node_preview = ", ".join(dinfo["nodes"][:5])
                if len(dinfo["nodes"]) > 5:
                    node_preview += f", ... (+{len(dinfo['nodes']) - 5})"
                print(
                    f"  {label:<45} {dinfo['count']:>5} {dinfo['lines']:>6}  {node_preview}"
                )
            print()

        # then show direct nodes with source
        direct = [o for o in oms.values() if o["domain"] == domain.rstrip("/")]
        if direct:
            print(f"  Direct nodes in {domain}/ ({len(direct)}):")
            for o in sorted(direct, key=lambda x: x["name"]):
                meta = f"[{o['layer']}] {o['lines']} lines | {o['domain']}"
                print(_fmt_header(o["name"], meta, o["path"]))
                print(o["source"])

    elif sub == "source":
        name = args.name
        o = oms.get(name)
        if not o:
            print(f"Om node '{name}' not found.")
            matches = [n for n in oms if name in n][:10]
            if matches:
                print(f"Did you mean: {', '.join(matches)}?")
            return
        meta = f"[{o['layer']}] {o['lines']} lines | {o['domain']}"
        print(_fmt_header(o["name"], meta, o["path"]))
        print(o["source"])

    elif sub == "search":
        pattern = args.name
        results = om.search(oms, pattern)
        total = sum(len(r["matches"]) for r in results)
        for r in results:
            print(
                f"\n  {r['name']} [{r['layer']}] {r['domain']} -- {len(r['matches'])} matches"
            )
            print(f"  {r['path']}")
            for m in r["matches"]:
                print(f"    {m['line']:>4}: {m['text']}")
        print(f"\n  Total: {total} matches across {len(oms)} om nodes.")

    elif sub == "with-key":
        key = args.name
        nodes = om.with_shabda_key(oms, key)
        print(f"\nOm nodes with shabda key '{key}' ({len(nodes)}):\n")
        for n in nodes:
            val = n["shabda_keys"].get(key, "")
            print(f"  {n['name']:<30} {val:<20} [{n['layer']}] {n['domain']}")

    elif sub == "with-relation":
        rel = args.name
        nodes = om.with_edge_relation(oms, rel)
        print(f"\nOm nodes with '{rel}' edges ({len(nodes)}):\n")
        for n in nodes:
            targets = [e["target"] for e in n["edges"] if e["relation"] == rel]
            print(f"  {n['name']:<30} -> {', '.join(targets)}")

    else:
        print(f"Unknown om command: {sub}")
        print(
            "Available: summary, domains, domain, source, search, with-key, with-relation"
        )


# ── cross-cutting ──────────────────────────────────────────────────────────────


def cmd_search(args):
    pattern = args.name if args.name else args.subcmd
    if not pattern:
        print("Usage: search PATTERN")
        return
    ts = tantras.load_all()
    oms = om.load_all()

    t_results = tantras.search(ts, pattern)
    o_results = om.search(oms, pattern)

    if t_results:
        print(_fmt_sep(f"TANTRA MATCHES ({sum(len(r['matches']) for r in t_results)})"))
        for r in t_results:
            print(f"\n  {r['name']} [{r['group']}]")
            for m in r["matches"]:
                print(f"    {m['line']:>4}: {m['text']}")

    if o_results:
        print(_fmt_sep(f"OM MATCHES ({sum(len(r['matches']) for r in o_results)})"))
        for r in o_results:
            print(f"\n  {r['name']} [{r['layer']}] {r['domain']}")
            for m in r["matches"]:
                print(f"    {m['line']:>4}: {m['text']}")

    t_total = sum(len(r["matches"]) for r in t_results)
    o_total = sum(len(r["matches"]) for r in o_results)
    print(f"\n  Total: {t_total} tantra + {o_total} om = {t_total + o_total} matches")


def cmd_test(args):
    """Test discovery, listing, and running."""
    sub = args.subcmd if args.subcmd else "summary"
    vy_socket = os.environ.get("VYAKARANA_SOCKET", "/tmp/vy.sock")

    if sub == "summary":
        all_tests = test_meta.load_all()
        s = test_meta.summary(all_tests)
        print(f"\n{'=' * 70}")
        print(
            f"  TEST SUMMARY  —  {s['total']} total  |  {s['passing']} passing  |  {s['xfail']} xfail"
        )
        print(f"{'=' * 70}\n")
        print(f"  {'Layer':<15} {'Tests':>6}")
        print(f"  {'─' * 25}")
        for layer, count in sorted(s["layers"].items()):
            print(f"  {layer:<15} {count:>6}")
        if s["gates"]:
            print(f"\n  {'Gate (xfail)':<25} {'Tests':>6}")
            print(f"  {'─' * 35}")
            for gate, count in sorted(s["gates"].items()):
                print(f"  {gate:<25} {count:>6}")
        print()

    elif sub == "list":
        all_tests = test_meta.load_all()
        # name or gate can come in args.name
        layer = args.name if args.name and not args.name.startswith("--") else None
        gate = None
        # check for --gate flag embedded in name (simple workaround)
        if args.name and args.name.startswith("gate:"):
            gate = args.name[5:]
            layer = None
        filtered = test_meta.filter_tests(all_tests, layer=layer, gate=gate)
        print(
            f"\n  {len(filtered)} tests{' in ' + (layer or gate or 'all') if (layer or gate) else ''}\n"
        )
        current_layer = None
        for t in filtered:
            if t["layer"] != current_layer:
                current_layer = t["layer"]
                print(f"  [{current_layer}]")
            xf = f" ✗ [{t['xfail_gate']}]" if t["xfail"] else ""
            doc = f" — {t['doc'][:60]}" if t["doc"] else ""
            print(f"    {t['name']}{xf}{doc}")
        print()

    elif sub == "run":
        # args.name can be: a layer name, a test name, or None (run all)
        name = args.name
        layer = None
        gate = None
        pattern = None

        if name:
            # detect what it is
            if name in ("evaluator", "graph", "pipeline", "answers", "xfail"):
                layer = name
                name = None
            elif name.startswith("test_"):
                pass  # it's a test name
            elif name.startswith("gate:"):
                gate = name[5:]
                name = None
            else:
                pattern = name
                name = None

        print(
            f"\n  Running tests{(' [' + (layer or gate or name or pattern or 'all') + ']') if any([layer, gate, name, pattern]) else ' [all]'}..."
        )
        result = runner.run(
            layer=layer,
            gate=gate,
            name=name,
            pattern=pattern,
            socket_path=vy_socket,
        )

        # print result
        status_icon = "✓" if result.get("status") == "ok" else "✗"
        print(f"\n  {status_icon} {result.get('summary', 'no summary')}")
        if result.get("failed_tests"):
            print(f"\n  FAILURES:")
            for ft in result["failed_tests"]:
                print(f"    {ft['nodeid']}")
                print(f"      {ft['reason'][:100]}")
        if result.get("error_tests"):
            print(f"\n  ERRORS (infrastructure, not test failures):")
            for et in result["error_tests"][:3]:
                print(f"    {et['nodeid']}")
        print()

    else:
        print(f"Unknown test command: {sub}")
        print("Available: summary, list, run")


def cmd_cache(args):
    """Query and act on the pytest result cache."""
    sub = args.subcmd if args.subcmd else "summary"
    cache_path = Path(DEFAULT_CACHE)

    if not cache_path.exists() and sub not in ("help",):
        print(f"  Cache not found: {cache_path}")
        print("  Run tests first: python3 tools/read_brahman.py test run")
        return

    _, entries = cache_mod.load(cache_path) if cache_path.exists() else ({}, [])

    if sub == "summary":
        if not entries:
            print("  Cache empty — run tests first.")
            return
        s = cache_mod.summarize(entries)
        print(f"\n{'=' * 70}")
        print(f"  CACHE SUMMARY  —  {s['total']} tests")
        print(f"{'=' * 70}")
        print(f"\n  passed:  {s['passed']}")
        print(f"  failed:  {s['failed']}")
        print(f"  xfailed: {s['xfailed']}")
        print(f"  xpassed: {s['xpassed']}")

        if s["failed_tests"]:
            print(f"\n  FAILED ({len(s['failed_tests'])}):")
            for t in s["failed_tests"]:
                print(f"    ✗ {t['test'].split('::')[-1]}")
                if t.get("sentences"):
                    print(f"      sentence: {t['sentences'][0][:70]}")
                if t.get("categories"):
                    print(f"      category: {', '.join(t['categories'])}")

        if s["xpass_tests"]:
            print(f"\n  XPASSED — remove @xfail ({len(s['xpass_tests'])}):")
            for t in s["xpass_tests"]:
                print(f"    ✓ {t['test'].split('::')[-1]}  {t['file']}:{t['line']}")

        if s["gates"]:
            print(f"\n  XFAIL GATES:")
            for gate, tests in sorted(s["gates"].items()):
                print(f"    [{gate}]  {len(tests)} tests")

        if s["slow_calls"]:
            print(f"\n  SLOWEST CALLS:")
            for sc in s["slow_calls"][:5]:
                print(f"    {sc['ms']:>5}ms  {sc['method']}  {sc['input'][:50]}")
        print()

    elif sub == "failed":
        fail_entries = cache_mod.failed(entries)
        if not fail_entries:
            print("  No failures in cache.")
            return
        for e in fail_entries:
            diag = cache_mod.diagnose(e)
            f = e.get("failure") or {}
            print(f"\n  {e['test']}")
            print(f"  categories: {diag['categories']}")
            if f.get("expected"):
                print(f"  expected:   {f['expected'][:70]!r}")
            chain = cache_mod.call_chain(e.get("calls", []))
            if chain:
                last = chain[-1]
                print(f"  last call:  {last['method']}({last['input'][:60]!r})")
                if last.get("output"):
                    print(f"  got:        {last['output'][:80]!r}")
            if len(chain) > 1:
                print(f"  call chain ({len(chain)} calls):")
                for step in chain:
                    print(
                        f"    [{step['elapsed_ms']:>4}ms] {step['method']}  {step['input'][:55]}"
                    )

    elif sub == "gates":
        gate = args.name
        if gate:
            gate_entries = cache_mod.entries_for_gate(entries, gate)
            print(f"\n  Gate '{gate}': {len(gate_entries)} xfailed tests\n")
            for e in gate_entries:
                xf = e.get("xfail") or {}
                print(f"  {e['test'].split('::')[-1]}")
                print(f"    {xf.get('reason', '')[:100]}")
        else:
            gates = cache_mod.by_gate(entries)
            print(f"\n  {len(gates)} xfail gates:\n")
            for g, g_entries in sorted(gates.items()):
                print(f"  [{g}]  {len(g_entries)} tests")
                for e in g_entries[:3]:
                    print(f"    {e['test'].split('::')[-1]}")
                if len(g_entries) > 3:
                    print(f"    ... +{len(g_entries) - 3} more")
            print()

    elif sub == "diff":
        previous = args.name
        if not previous:
            print("Usage: cache diff PATH_TO_PREVIOUS_SUMMARY.json")
            return
        result = cache_mod.diff(entries, previous)
        if "error" in result:
            print(f"  Error: {result['error']}")
            return
        dc = result.get("count_delta", {})
        sym = lambda n: f"+{n}" if n > 0 else str(n)
        print(
            f"\n  Δ failed {sym(dc.get('failed', 0))}  passed {sym(dc.get('passed', 0))}  xfailed {sym(dc.get('xfailed', 0))}"
        )
        if result.get("newly_failing"):
            print(f"\n  NEWLY FAILING ({len(result['newly_failing'])}):")
            for t in result["newly_failing"]:
                print(f"    ✗ {t}")
        if result.get("newly_passing"):
            print(f"\n  NEWLY PASSING ({len(result['newly_passing'])}):")
            for t in result["newly_passing"]:
                print(f"    ✓ {t}")
        if result.get("newly_xpassing"):
            print(f"\n  NOW XPASSING (remove @xfail):")
            for t in result["newly_xpassing"]:
                print(f"    ✓ {t}")
        print()

    elif sub == "fix-xpass":
        dry_run = args.name != "--apply"
        xp = cache_mod.xpassed(entries)
        if not xp:
            print("  No xpassed tests in cache.")
            return
        print(
            f"  {'[DRY RUN] ' if dry_run else ''}Fixing {len(xp)} xpassed test(s)...\n"
        )
        results = cache_mod.fix_xpass(entries, dry_run=dry_run)
        for r in results:
            status = r.get("status", "?")
            print(f"  {r['test'].split('::')[-1]}  [{status}]")
            if r.get("removed_lines"):
                for ln in r["removed_lines"]:
                    print(f"    - {ln}")
        if dry_run:
            print("\n  Pass --apply to actually write the files.")

    elif sub == "slow":
        s = cache_mod.summarize(entries)
        print(f"\n  SLOWEST CALLS:")
        for sc in s["slow_calls"]:
            print(f"  {sc['ms']:>5}ms  {sc['method']}  {sc['input'][:60]}")
            print(f"           in {sc['test'].split('::')[-1]}")
        print(f"\n  SLOWEST TESTS:")
        for t in s["slow_tests"][:10]:
            print(
                f"  {t['duration']:>6.2f}s  {t['calls']:>3} calls  {t['test'].split('::')[-1]}"
            )

    else:
        print(f"Unknown cache command: {sub}")
        print("Available: summary, failed, gates, diff, fix-xpass, slow")


def cmd_serve(args):
    socket_path = args.name if args.name else DEFAULT_SOCKET
    server = BrahmanServer(socket_path=socket_path)
    server.serve()


# ── JSON mode ──────────────────────────────────────────────────────────────────


def cmd_json(args):
    """Direct JSON command mode — same protocol as socket, but to stdout."""
    # JSON string can land in subcmd or name depending on quoting
    req_str = args.subcmd or args.name
    if not req_str:
        print('Usage: json \'{"command": "tantra-summary"}\'')
        return
    try:
        req = json.loads(req_str)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "error": f"invalid JSON: {e}"}))
        return

    # use in-process server (no socket needed)
    server = BrahmanServer.__new__(BrahmanServer)
    server.socket_path = ""
    server._load()
    resp = server.handle_command(req)
    print(json.dumps(resp, indent=2))


# ── main ───────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Read, query, and serve the brahman knowledge base (tantras + om files).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  tantra summary|groups|all|group|source|callgraph|callers|callees|search
  om     summary|domains|domain|source|search|with-key|with-relation
  search PATTERN          search both tantras and om
  serve [SOCKET_PATH]     start socket server (default: /tmp/brahman.sock)
  json '{"command":...}'  run one JSON command and print response

Examples:
  python3 tools/read_brahman.py tantra summary
  python3 tools/read_brahman.py tantra source execute-mantra
  python3 tools/read_brahman.py om domain kosha/math/number/operations
  python3 tools/read_brahman.py om with-key eval
  python3 tools/read_brahman.py search "pratipaksha"
  python3 tools/read_brahman.py serve
  python3 tools/read_brahman.py json '{"command":"ping"}'
""",
    )
    parser.add_argument(
        "mode", nargs="?", default="tantra", help="tantra, om, search, serve, json"
    )
    parser.add_argument(
        "subcmd",
        nargs="?",
        default=None,
        help="sub-command (e.g. summary, source, domain)",
    )
    parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="argument (e.g. tantra name, domain path, pattern)",
    )

    args = parser.parse_args()

    dispatch = {
        "tantra": cmd_tantra,
        "om": cmd_om,
        "search": cmd_search,
        "test": cmd_test,
        "cache": cmd_cache,
        "serve": cmd_serve,
        "json": cmd_json,
    }

    fn = dispatch.get(args.mode)
    if fn:
        fn(args)
    else:
        print(f"Unknown mode: {args.mode}")
        print(f"Available: {', '.join(dispatch.keys())}")
        sys.exit(1)
