"""cli_om.py — CLI commands for om queries and cross-search.

Handles: om (summary/domains/domain/source/search/with-key/with-relation)
         search (cross-search both tantras and om)
"""

from . import tantras, om


def _sep(title, width=80):
    return f"\n{'=' * width}\n  {title}\n{'=' * width}\n"


def _header(name, meta, path, width=80):
    return f"\n{'─' * width}\n  {name}  ({meta})\n  {path}\n{'─' * width}"


def cmd_om(args):
    oms = om.load_all()
    sub = args.subcmd or "summary"

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
            _sep(
                f"{domain}/ -- {info['total_count']} nodes, {info['total_lines']} lines"
            )
        )
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
        direct = [o for o in oms.values() if o["domain"] == domain.rstrip("/")]
        if direct:
            print(f"  Direct nodes in {domain}/ ({len(direct)}):")
            for o in sorted(direct, key=lambda x: x["name"]):
                meta = f"[{o['layer']}] {o['lines']} lines | {o['domain']}"
                print(_header(o["name"], meta, o["path"]))
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
        print(_header(o["name"], meta, o["path"]))
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
        print(_sep(f"TANTRA MATCHES ({sum(len(r['matches']) for r in t_results)})"))
        for r in t_results:
            print(f"\n  {r['name']} [{r['group']}]")
            for m in r["matches"]:
                print(f"    {m['line']:>4}: {m['text']}")
    if o_results:
        print(_sep(f"OM MATCHES ({sum(len(r['matches']) for r in o_results)})"))
        for r in o_results:
            print(f"\n  {r['name']} [{r['layer']}] {r['domain']}")
            for m in r["matches"]:
                print(f"    {m['line']:>4}: {m['text']}")
    t_total = sum(len(r["matches"]) for r in t_results)
    o_total = sum(len(r["matches"]) for r in o_results)
    print(f"\n  Total: {t_total} tantra + {o_total} om = {t_total + o_total} matches")
