"""cli_tantra.py — CLI commands for tantra queries and static analysis.

Handles: tantra (summary/groups/all/group/source/callgraph/callers/callees/search/lint)
"""

import re

from . import tantras, om


def _sep(title, width=80):
    return f"\n{'=' * width}\n  {title}\n{'=' * width}\n"


def _header(name, meta, path, width=80):
    return f"\n{'─' * width}\n  {name}  ({meta})\n  {path}\n{'─' * width}"


def cmd_tantra(args):
    ts = tantras.load_all()
    sub = args.subcmd or "summary"

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
            print(_sep(f"{gname}/ -- {len(gt)} files, {gl} lines -- {desc}"))
            for t in sorted(gt, key=lambda x: x["name"]):
                meta = f"[{t['group']}] {t['lines']} lines"
                if t["takes"]:
                    meta += f" | takes: {', '.join(t['takes'])}"
                print(_header(t["name"], meta, t["path"]))
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
            print(_header(name, f"[{t['group']}] {t['lines']} lines", t["path"]))
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
        print(_header(t["name"], meta, t["path"]))
        print(t["source"])

    elif sub == "callgraph":
        cg = tantras.call_graph(ts)
        rcg = tantras.reverse_call_graph(cg)
        print(_sep("CALL GRAPH"))
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
        print(_sep("HUB TANTRAS -- most called"))
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

    elif sub == "lint":
        _tantra_lint(ts)

    else:
        print(f"Unknown tantra command: {sub}")
        print(
            "Available: summary, groups, all, group, source, callgraph, callers, callees, search, lint"
        )


# ── tantra lint ────────────────────────────────────────────────────────────────


def _tantra_lint(ts):
    """Static analysis: hardcoded kosha refs, unrolled loops, word lists."""
    oms = om.load_all()
    kosha_names = set(
        name for name, n in oms.items() if n["layer"] in ("kosha", "mantra", "sangati")
    )

    # 1. Hardcoded kosha references
    print(_sep("HARDCODED KOSHA REFERENCES"))
    print("  Tantras that name kosha/mantra/sangati nodes as string literals.")
    print("  These are candidates for reading the graph instead.\n")
    total_refs = 0
    for name, t in sorted(ts.items()):
        source = t["source"]
        strings = re.findall(r'"([^"]+)"', source)
        hardcoded = sorted(set(s for s in strings if s in kosha_names))
        if hardcoded:
            total_refs += len(hardcoded)
            print(f"  {name:<30} [{t['group']}]")
            for s in hardcoded:
                print(f'    "{s}"')
    print(f"\n  Total: {total_refs} hardcoded references across {len(ts)} tantras\n")

    # 2. Unrolled step patterns
    print(_sep("UNROLLED LOOPS"))
    print("  Tantras with numbered step/level variables (copy-pasted blocks).")
    print("  Candidates for scan-ref or fixpoint rewrite.\n")
    for name, t in sorted(ts.items()):
        source = t["source"]
        steps = re.findall(r"\b(step\d+|l\d+[-_])", source)
        if len(steps) >= 3:
            nums = sorted(set(re.findall(r"(\d+)", " ".join(steps))))
            print(
                f"  {name:<30} [{t['group']}]  {len(steps)} refs, steps {','.join(nums)}"
            )

    # 3. Hardcoded word lists
    print(_sep("HARDCODED WORD LISTS"))
    print("  Tantras with inline string arrays that may belong in the kosha.\n")
    for name, t in sorted(ts.items()):
        source = t["source"]
        lists = re.findall(r'\["[a-z]+"(?:,\s*"[a-z]+"){3,}', source)
        if lists:
            for lst in lists:
                words = re.findall(r'"([a-z]+)"', lst)
                preview = ", ".join(words[:6])
                suffix = "..." if len(words) > 6 else ""
                print(
                    f"  {name:<30} [{t['group']}]  [{preview}{suffix}] ({len(words)} words)"
                )

    # 4. Scan vs reduce summary
    print(_sep("ITERATION PATTERNS"))
    print("  scan = declarative pattern matching (target form)")
    print("  reduce = manual accumulator (candidate for rewrite)\n")
    scan_tantras = []
    reduce_tantras = []
    for name, t in sorted(ts.items()):
        has_scan = t["scans"] > 0
        if has_scan:
            scan_tantras.append((name, t))
        elif t["reduces"] >= 3:
            reduce_tantras.append((name, t))

    if scan_tantras:
        print(f"  Using scan ({len(scan_tantras)}):")
        for name, t in scan_tantras:
            extra = f"  +{t['reduces']} reduces" if t["reduces"] > 0 else ""
            print(f"    {name:<30} [{t['group']}]  scans={t['scans']}{extra}")
    if reduce_tantras:
        print(f"\n  Heavy reduce, no scan ({len(reduce_tantras)}):")
        for name, t in reduce_tantras:
            print(
                f"    {name:<30} [{t['group']}]  reduces={t['reduces']}  conds={t['conds']}"
            )
    print()
