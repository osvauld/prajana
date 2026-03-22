"""cli_om5.py — CLI commands for om5 conversion and analysis.

Handles: om5 (stats|preview|convert|check|diff)
"""

from . import om5


def cmd_om5(args):
    sub = args.subcmd or "stats"
    merge = getattr(args, "merge_shabda", False)

    if sub == "stats":
        s = om5.stats(merge_shabda=merge)
        print(f"\n{'=' * 70}")
        print(f"  OM5 CONVERSION STATS")
        print(f"{'=' * 70}\n")
        print(f"  Total nodes:              {s['total_nodes']}")
        print(f"  Total edges:              {s['total_edges']}")
        print(f"  Nodes with unmatched:     {s['nodes_with_unmatched']}")
        print(f"  Total unmatched words:    {s['unmatched_count']}")
        if s['unique_unmatched_words']:
            print(f"\n  Unique unmatched words ({len(s['unique_unmatched_words'])}):")
            for w in s['unique_unmatched_words'][:30]:
                print(f"    {w}")
            if len(s['unique_unmatched_words']) > 30:
                print(f"    ... +{len(s['unique_unmatched_words']) - 30} more")
        print()

    elif sub == "preview":
        name = args.name
        if not name:
            # Preview first 5 nodes
            results = om5.convert_all()[:5]
        else:
            results = [r for r in om5.convert_all() if r["name"] == name]

        if not results:
            print(f"  No node found: {name}")
            return

        for r in results:
            print(f"\n{'─' * 70}")
            print(f"  {r['name']}  [{r['layer']}]  {r['edges']} edges")
            print(f"  {r['path']}")
            print(f"{'─' * 70}")
            print(r["om5"])
            if r["unmatched"]:
                print(f"  ⚠ unmatched: {', '.join(r['unmatched'])}")

    elif sub == "convert":
        target = args.name  # "all" or a specific node name
        if not target:
            print("Usage: om5 convert all|NODE_NAME")
            print("  Writes .om5 files alongside .om files")
            return

        results = om5.convert_all()
        if target != "all":
            results = [r for r in results if r["name"] == target]

        written = 0
        for r in results:
            out = om5.write_om5(r["path"], r["om5"])
            written += 1

        print(f"  Wrote {written} .om5 files")

    elif sub == "check":
        # Roundtrip check: parse .om → om5 → re-parse → compare edges
        results = om5.convert_all()
        ok_count = 0
        fail_count = 0
        failures = []

        for r in results:
            parsed = om5.parse_om(r["path"])
            if not parsed:
                continue
            ok, msg = om5.roundtrip_check(parsed, r["om5"])
            if ok:
                ok_count += 1
            else:
                fail_count += 1
                failures.append((r["name"], msg))

        print(f"\n  Roundtrip check: {ok_count} ok, {fail_count} failed")
        if failures:
            print(f"\n  Failures:")
            for name, msg in failures[:20]:
                print(f"    {name}: {msg}")
        print()

    elif sub == "diff":
        # Show before/after for a specific node
        name = args.name
        if not name:
            print("Usage: om5 diff NODE_NAME")
            return

        results = [r for r in om5.convert_all() if r["name"] == name]
        if not results:
            print(f"  No node found: {name}")
            return

        r = results[0]
        parsed = om5.parse_om(r["path"])
        print(f"\n  === BEFORE (.om) ===")
        print(parsed["source"])
        print(f"  === AFTER (.om5) ===")
        print(r["om5"])
        if r["unmatched"]:
            print(f"  unmatched: {', '.join(r['unmatched'])}")

    else:
        print(f"Unknown om5 command: {sub}")
        print("Available: stats, preview, convert, check, diff")
