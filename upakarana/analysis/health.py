"""health.py — Combined system health report (static + live)."""

import sys
from upakarana.parsers import om5, tantra4, shabda
from upakarana.analysis import static


def full_report(root=None, client=None):
    """Combined health check using parsers and optionally live graph."""
    report = {}

    # --- Static (always available) ---
    om_nodes = om5.load_all(root)
    om_sum = om5.summary(om_nodes)
    report["om5"] = om_sum

    tantras = tantra4.load_all()
    t_sum = tantra4.summary(tantras)
    report["tantra4"] = t_sum

    shabda_nodes = shabda.load_all(root)
    s_sum = shabda.summary(shabda_nodes)
    report["shabda"] = s_sum

    # Lint
    report["om5_lint"] = static.om5_lint(root)
    report["tantra4_lint"] = static.tantra4_lint()

    # Dead tantras
    dead = static.dead_tantras()
    report["dead_tantras"] = {"count": len(dead), "names": [d["name"] for d in dead[:10]]}

    # Complexity top 5
    cx = static.complexity()
    report["complexity_top5"] = cx[:5]

    # Shabda gaps
    gaps = static.shabda_gaps(root)
    report["shabda_gaps"] = {"count": len(gaps), "sample": gaps[:5]}

    # --- Live (if client provided) ---
    if client:
        try:
            from upakarana.analysis.graph import tantra_coverage, hub_nodes
            report["live_tantras"] = tantra_coverage(client)
            report["live_hubs"] = hub_nodes(client, top_n=5)
        except Exception as e:
            report["live_error"] = str(e)

    return report


def print_report(report, file=None):
    """Print health report to stdout."""
    f = file or sys.stdout

    print("## System Health Report", file=f)
    print(file=f)

    om = report.get("om5", {})
    print(f"**Om5**: {om.get('total', 0)} nodes, {om.get('total_lines', 0)} lines", file=f)
    for layer, count in om.get("layers", {}).items():
        print(f"  {layer}: {count}", file=f)

    t = report.get("tantra4", {})
    print(f"\n**Tantra4**: {t.get('total', 0)} tantras, {t.get('total_lines', 0)} lines", file=f)
    for group, count in t.get("groups", {}).items():
        print(f"  {group}: {count}", file=f)

    s = report.get("shabda", {})
    print(f"\n**Shabda**: {s.get('total_nodes', 0)} nodes, {s.get('total_words', 0)} words", file=f)

    # Lint issues
    om_lint = report.get("om5_lint", {})
    t_lint = report.get("tantra4_lint", {})
    om_issues = om_lint.get("issues", [])
    t_issues = t_lint.get("issues", [])
    if om_issues or t_issues:
        print(f"\n**Lint**: {len(om_issues)} om5 issues, {len(t_issues)} tantra4 issues", file=f)

    dead = report.get("dead_tantras", {})
    if dead.get("count"):
        print(f"\n**Dead tantras**: {dead['count']} (never called)", file=f)
        for name in dead.get("names", []):
            print(f"  {name}", file=f)

    gaps = report.get("shabda_gaps", {})
    if gaps.get("count"):
        print(f"\n**Shabda gaps**: {gaps['count']} nodes with kriya/phala but no shabda", file=f)

    cx = report.get("complexity_top5", [])
    if cx:
        print(f"\n**Top 5 complex tantras**:", file=f)
        for c in cx:
            print(f"  {c['name']:30s} score={c['score']} lines={c['lines']} conds={c['conds']}", file=f)

    live = report.get("live_tantras")
    if live:
        print(f"\n**Live engine**: {live['total']} tantras loaded", file=f)
