"""cli.py — CLI entry point for the tools package.

Usage:
  python3 -m tools [mode] [subcmd] [args]

Modes:
  tantra  summary|groups|all|group|source|callgraph|callers|callees|search|lint
  om      summary|domains|domain|source|search|with-key|with-relation|classify|ungrouped|sthalam
  shabda  summary|words|files|node|eval|gaps|search|lookup
  search  PATTERN              search both tantras and om
  test    summary|list|run     test discovery and execution
  cache   summary|failed|gates|diff|fix-xpass|slow
  vy      status|start|stop|restart|reload|run|eval|trace|walk|inspect|mantras|triples|help
  serve   [SOCKET_PATH]        start brahman (static knowledge) server
  ask     [QUESTION]           ask a question (auto-starts server, repl if no question)
  json    '{"command":...}'    run one JSON command
"""

import argparse
import json
import os
import sys
from pathlib import Path

from . import tests as test_meta, runner, cache as cache_mod, vyakarana
from .cache import DEFAULT_CACHE
from .server import BrahmanServer, DEFAULT_SOCKET
from .cli_tantra import cmd_tantra
from .cli_om import cmd_om, cmd_search
from .cli_shabda import cmd_shabda
from .cli_vy import cmd_vy, cmd_ask, ensure_vy
from .cli_analysis import cmd_analyze
from .cli_tantra4 import cmd_tantra4
from .cli_vyakarana import cmd_vyakarana


# ── test ──────────────────────────────────────────────────────────────────────


def cmd_test(args):
    sub = args.subcmd or "summary"
    vy_socket = os.environ.get("VYAKARANA_SOCKET", "/tmp/vy.sock")
    if sub == "run":
        vy_socket = ensure_vy()

    if sub == "summary":
        all_tests = test_meta.load_all()
        s = test_meta.summary(all_tests)
        print(f"\n{'=' * 70}")
        print(
            f"  TEST SUMMARY  --  {s['total']} total  |  {s['passing']} passing  |  {s['xfail']} xfail"
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
        layer = args.name if args.name and not args.name.startswith("gate:") else None
        gate = args.name[5:] if args.name and args.name.startswith("gate:") else None
        filtered = test_meta.filter_tests(all_tests, layer=layer, gate=gate)
        print(
            f"\n  {len(filtered)} tests{' in ' + (layer or gate or 'all') if (layer or gate) else ''}\n"
        )
        current_layer = None
        for t in filtered:
            if t["layer"] != current_layer:
                current_layer = t["layer"]
                print(f"  [{current_layer}]")
            xf = f" x [{t['xfail_gate']}]" if t["xfail"] else ""
            doc = f" -- {t['doc'][:60]}" if t["doc"] else ""
            print(f"    {t['name']}{xf}{doc}")
        print()

    elif sub == "run":
        name = args.name
        layer = gate = pattern = None
        if name:
            if name in ("evaluator", "graph", "pipeline", "answers", "xfail"):
                layer = name
                name = None
            elif name.startswith("test_"):
                pass
            elif name.startswith("gate:"):
                gate = name[5:]
                name = None
            else:
                pattern = name
                name = None

        label = layer or gate or name or pattern or "all"
        print(f"\n  Running tests [{label}]...")
        result = runner.run(
            layer=layer, gate=gate, name=name, pattern=pattern, socket_path=vy_socket
        )
        status_icon = "+" if result.get("status") == "ok" else "x"
        print(f"\n  {status_icon} {result.get('summary', 'no summary')}")
        if result.get("failed_tests"):
            print("\n  FAILURES:")
            for ft in result["failed_tests"]:
                print(f"    {ft['nodeid']}")
                print(f"      {ft['reason'][:100]}")
        if result.get("error_tests"):
            print("\n  ERRORS:")
            for et in result["error_tests"][:3]:
                print(f"    {et['nodeid']}")
        print()

    else:
        print(f"Unknown test command: {sub}")
        print("Available: summary, list, run")


# ── cache ─────────────────────────────────────────────────────────────────────


def cmd_cache(args):
    sub = args.subcmd or "summary"
    cache_path = Path(DEFAULT_CACHE)

    if not cache_path.exists() and sub not in ("help",):
        print(f"  Cache not found: {cache_path}")
        print("  Run tests first: python3 -m tools test run")
        return

    _, entries = cache_mod.load(cache_path) if cache_path.exists() else ({}, [])

    if sub == "summary":
        if not entries:
            print("  Cache empty -- run tests first.")
            return
        s = cache_mod.summarize(entries)
        print(f"\n{'=' * 70}")
        print(f"  CACHE SUMMARY  --  {s['total']} tests")
        print(f"{'=' * 70}")
        print(f"\n  passed:  {s['passed']}")
        print(f"  failed:  {s['failed']}")
        print(f"  xfailed: {s['xfailed']}")
        print(f"  xpassed: {s['xpassed']}")
        if s["failed_tests"]:
            print(f"\n  FAILED ({len(s['failed_tests'])}):")
            for t in s["failed_tests"]:
                print(f"    x {t['test'].split('::')[-1]}")
                if t.get("sentences"):
                    print(f"      sentence: {t['sentences'][0][:70]}")
                if t.get("categories"):
                    print(f"      category: {', '.join(t['categories'])}")
        if s["xpass_tests"]:
            print(f"\n  XPASSED -- remove @xfail ({len(s['xpass_tests'])}):")
            for t in s["xpass_tests"]:
                print(f"    + {t['test'].split('::')[-1]}  {t['file']}:{t['line']}")
        if s["gates"]:
            print(f"\n  XFAIL GATES:")
            for gate, gate_tests in sorted(s["gates"].items()):
                print(f"    [{gate}]  {len(gate_tests)} tests")
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
            f"\n  D failed {sym(dc.get('failed', 0))}  passed {sym(dc.get('passed', 0))}  xfailed {sym(dc.get('xfailed', 0))}"
        )
        if result.get("newly_failing"):
            print(f"\n  NEWLY FAILING ({len(result['newly_failing'])}):")
            for t in result["newly_failing"]:
                print(f"    x {t}")
        if result.get("newly_passing"):
            print(f"\n  NEWLY PASSING ({len(result['newly_passing'])}):")
            for t in result["newly_passing"]:
                print(f"    + {t}")
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
            print(f"  {r['test'].split('::')[-1]}  [{r.get('status', '?')}]")
            if r.get("removed_lines"):
                for ln in r["removed_lines"]:
                    print(f"    - {ln}")
        if dry_run:
            print("\n  Pass --apply to actually write the files.")

    elif sub == "slow":
        s = cache_mod.summarize(entries)
        print("\n  SLOWEST CALLS:")
        for sc in s["slow_calls"]:
            print(f"  {sc['ms']:>5}ms  {sc['method']}  {sc['input'][:60]}")
        print("\n  SLOWEST TESTS:")
        for t in s["slow_tests"][:10]:
            print(
                f"  {t['duration']:>6.2f}s  {t['calls']:>3} calls  {t['test'].split('::')[-1]}"
            )

    else:
        print(f"Unknown cache command: {sub}")
        print("Available: summary, failed, gates, diff, fix-xpass, slow")


# ── serve ─────────────────────────────────────────────────────────────────────


def cmd_serve(args):
    socket_path = args.name if args.name else DEFAULT_SOCKET
    server = BrahmanServer(socket_path=socket_path)
    server.serve()


# ── json ──────────────────────────────────────────────────────────────────────


def cmd_json(args):
    req_str = args.subcmd or args.name
    if not req_str:
        print('Usage: json \'{"command": "tantra-summary"}\'')
        return
    try:
        req = json.loads(req_str)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "error": f"invalid JSON: {e}"}))
        return
    server = BrahmanServer(socket_path="")
    resp = server.handle_command(req)
    print(json.dumps(resp, indent=2))


# ── main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Read, query, test, and serve the brahman knowledge base.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  tantra  summary|groups|all|group|source|callgraph|callers|callees|search|lint
  om      summary|domains|domain|source|search|with-key|with-relation|classify|ungrouped|sthalam
  shabda  summary|words|files|node|eval|gaps|search|lookup
  search  PATTERN              search both tantras and om
  test    summary|list|run     test discovery and execution
  cache   summary|failed|gates|diff|fix-xpass|slow
  vy      status|start|stop|restart|reload|run|eval|trace|walk|inspect|mantras|triples|help
  serve   [SOCKET_PATH]        start brahman (static knowledge) server
  ask     [QUESTION]           ask a question (auto-starts server, repl if no question)
  json    '{"command":...}'    run one JSON command

Live graph queries (auto-starts server):
  vy eval '<expr>'             evaluate any tantra expression
  vy inspect <node>            full node: satya, shabda keys, edges
  vy walk '<node> <relation>'  transitive chain walk with shabda at each hop
  vy triples <node>            all triples touching a node (subject + object)
  vy mantras '<sentence>'      which mantras fire and why (bound/missing concepts)
  vy trace '<sentence>'        pipeline stages with +/- triple diff

Static analysis (no server needed):
  tantra lint                  hardcoded refs, unrolled loops, word lists, scan vs reduce
  tantra callgraph             full call graph + hub tantras
  om with-key eval             all nodes with an 'eval' shabda key (fireable operations)
  om with-relation abheda      all nodes with 'abheda' edges
  shabda summary               unified view: words, .shabda files, shabda keys, gaps
  shabda words [domain|node]   word index by domain or for a specific node
  shabda eval                  all fireable operations (nodes with eval:)
  shabda gaps                  nodes missing word mappings
  shabda lookup WORD           trace a word to its node and shabda keys

Documentation (separate package — see patra/README.md):
  python3 -m patra glance             compact LLM context summary
  python3 -m patra discover "..."     record a discovery
  python3 -m patra steps              plan steps with status
  python3 -m patra topic NAME         cross-source search (patra + om + tantras + shabda)

Examples:
  python3 -m tools vy eval 'walk "viveka-max" "abheda"'
  python3 -m tools vy eval 'shabda "addition" "eval"'
  python3 -m tools vy inspect momentum
  python3 -m tools shabda summary
  python3 -m tools shabda lookup heavier
  python3 -m tools shabda gaps
  python3 -m tools shabda eval
  python3 -m tools tantra lint
  python3 -m tools test run
  python3 -m tools ask "ball has mass 5 velocity 10. find kinetic energy"
""",
    )
    parser.add_argument("mode", nargs="?", default="tantra")
    parser.add_argument("subcmd", nargs="?", default=None)
    parser.add_argument("name", nargs="?", default=None)
    args = parser.parse_args()

    dispatch = {
        "tantra": cmd_tantra,
        "om": cmd_om,
        "shabda": cmd_shabda,
        "search": cmd_search,
        "test": cmd_test,
        "cache": cmd_cache,
        "serve": cmd_serve,
        "vy": cmd_vy,
        "ask": cmd_ask,
        "json": cmd_json,
        "analyze": cmd_analyze,
        "tantra4": cmd_tantra4,
        "vyakarana": cmd_vyakarana,
    }

    fn = dispatch.get(args.mode)
    if fn:
        fn(args)
    else:
        print(f"Unknown mode: {args.mode}")
        print(f"Available: {', '.join(dispatch.keys())}")
        sys.exit(1)
