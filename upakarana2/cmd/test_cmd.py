"""test_cmd.py — test and cache commands."""

import sys


def cmd_test(args, store):
    # Resolve positional filter shorthand
    if getattr(args, "filter", None) and not args.layer and not args.gate and not args.pattern:
        f = args.filter
        known_layers = {
            "evaluator", "graph", "edges", "pipeline", "answers", "xfail",
            "physics", "logic", "grammar", "reasoning", "comparison",
            "arithmetic", "mixed", "entity",
        }
        if f.startswith("gate:"):
            args.gate = f[5:]
        elif f in known_layers:
            args.layer = f
        else:
            args.pattern = f

    if args.action == "list":
        from upakarana2.testing.discover import load_all, filter_tests
        tests = load_all()
        if args.layer or args.gate or args.pattern:
            tests = filter_tests(tests, layer=args.layer, gate=args.gate, pattern=args.pattern)
        for t in tests:
            xf = " [xfail]" if t["xfail"] else ""
            print(f"  {t['name']:40s} {t['layer']:20s}{xf}")
        print(f"\n{len(tests)} tests")

    elif args.action == "summary":
        from upakarana2.testing.discover import load_all, summary
        from upakarana2.cmd.dispatch import _print_json
        _print_json(summary(load_all()))

    elif args.action == "run":
        from upakarana2.testing.run import run
        par = None if args.parallel == "off" else args.parallel
        if getattr(args, "failed", False) or getattr(args, "xfailed", False):
            import os as _os
            outcome = "failed" if getattr(args, "failed", False) else "xfailed"
            nodeids = store.tests.query_by_outcome(outcome)
            if args.gate:
                gate_ids = set(store.tests.query_by_gate(args.gate))
                nodeids = [t for t in nodeids if t in gate_ids]
            if not nodeids:
                print(f"No {outcome} tests found in last run.")
            else:
                print(f"Re-running {len(nodeids)} {outcome} test(s)...")
                _os.environ["UPAKARANA_PARTIAL_RUN"] = "1"
                result = run(nodeids=nodeids, verbose=args.verbose, parallel=par)
                _os.environ.pop("UPAKARANA_PARTIAL_RUN", None)
                print(f"passed={result['passed']} failed={result['failed']} "
                      f"xfailed={result.get('xfailed',0)} {result.get('duration','')}")
        else:
            result = run(layer=args.layer, gate=args.gate, pattern=args.pattern,
                         last_failed=args.last_failed, verbose=args.verbose, parallel=par)
            print(f"passed={result['passed']} failed={result['failed']} "
                  f"xfailed={result.get('xfailed',0)} {result.get('duration','')}")

    elif args.action == "failed":
        from upakarana2.testing.cache import load, failed
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


def cmd_cache(args, store):
    from upakarana2.testing.cache import load, summarize, by_gate, slowest_calls, slowest_tests, timing_by_layer
    from upakarana2.cmd.dispatch import _print_json

    _, entries = load()

    if args.action == "summary":
        _print_json(summarize(entries))
        from upakarana2.testing.cache import history
        runs = history(5)
        if len(runs) > 1:
            print("\n── Last runs ──")
            for r in runs:
                rid = r.get("run_id", "?")
                print(f"  {rid}  passed={r.get('passed',0)} "
                      f"failed={r.get('failed',0)} xfailed={r.get('xfailed',0)}")

    elif args.action == "trace":
        name = getattr(args, "name", None)
        if not name:
            print("Usage: cache trace TEST_ID")
        else:
            trace = store.tests.get_trace(name)
            if trace is None:
                print(f"No trace found for '{name}' in last run.")
            else:
                _print_json(trace)

    elif args.action == "gates":
        gates = by_gate(entries)
        for gate, es in sorted(gates.items()):
            print(f"  {gate}: {len(es)}")

    elif args.action == "slow":
        def fmt_time(us):
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
