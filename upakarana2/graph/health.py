"""health.py — Static health checks: lint, ghosts, shabda gaps.

Consolidates: health.py + static.py + ghosts.py
"""

import sys
from collections import defaultdict
from upakarana2.parsers import om5, tantra4, shabda


# ---------------------------------------------------------------------------
# Ghosts
# ---------------------------------------------------------------------------

EXPECTED_GHOSTS = {
    # OCaml eval primitives
    "add", "sub", "mul", "div", "sqrt", "sin", "cos", "tan",
    "log", "abs", "neg", "floor", "ceil", "min", "max", "mod",
    "asin", "acos", "atan", "exp", "half", "double", "square",
    "power", "factorial", "sum", "product",
    # English compound tokens
    "in", "of", "at", "is", "the", "a", "an", "to", "for",
    "from", "by", "on", "with", "and", "or", "not", "as",
    "no", "if", "so", "up", "do", "we", "it", "be", "he",
    # OCaml types
    "int", "string", "bool", "unit", "list",
    # Symbols from sloka text
    "(", ")", "+", "=", "→", "—", "...", "*", "/", "-",
    ">", "<", "≤", "≥", "≠", "×", "÷",
}


def find_ghosts(root=None, include_expected=False):
    """Find ghost nodes: referenced as targets but never defined."""
    nodes = om5.load_all(root)
    names = set(nodes.keys())

    bare_names = set()
    for k in names:
        if "/" in k:
            bare_names.add(k.rsplit("/", 1)[-1])

    refs = defaultdict(list)
    for name, node in nodes.items():
        for e in node["edges"]:
            t = e["target"]
            if t not in names and not t.startswith("domain-"):
                if include_expected or t not in EXPECTED_GHOSTS:
                    if not include_expected and t in bare_names:
                        continue
                    refs[t].append((name, e["relation"]))

    ghosts = []
    for target, referrers in sorted(refs.items(), key=lambda x: -len(x[1])):
        ghosts.append({
            "name": target,
            "ref_count": len(referrers),
            "referrers": referrers[:10],
            "layers": list(set(nodes[r[0]]["layer"] for r in referrers if r[0] in nodes)),
        })

    return {
        "ghosts": ghosts,
        "total_ghosts": len(ghosts),
        "total_ghost_edges": sum(len(r) for r in refs.values()),
    }


def structural_ghosts(root=None, min_refs=5):
    """High-impact ghosts referenced by 5+ nodes across 2+ layers."""
    result = find_ghosts(root)
    return [g for g in result["ghosts"]
            if g["ref_count"] >= min_refs and len(g["layers"]) >= 2]


# ---------------------------------------------------------------------------
# Static lint
# ---------------------------------------------------------------------------

def om5_lint(root=None):
    """Check om5 files for issues."""
    nodes = om5.load_all(root)
    issues = []
    for name, node in nodes.items():
        if not node["edges"]:
            issues.append({"node": name, "issue": "no edges", "severity": "warn"})
        self_refs = [e for e in node["edges"] if e["target"] == name]
        if self_refs:
            rels = [e["relation"] for e in self_refs]
            issues.append({"node": name, "issue": f"self-reference via {rels}", "severity": "warn"})
    return {"total_nodes": len(nodes), "issues": issues}


def tantra4_lint(root=None):
    """Check tantra4 files for issues."""
    tantras = tantra4.load_all(root)
    issues = []
    for name, t in tantras.items():
        if t["conds"] > 5:
            issues.append({"tantra": name, "issue": f"high cond count: {t['conds']}", "severity": "info"})
        if t["lines"] > 100:
            issues.append({"tantra": name, "issue": f"long: {t['lines']} lines", "severity": "info"})
        for param in t["takes"]:
            if param not in t["source"].split(")", 1)[-1]:
                issues.append({"tantra": name, "issue": f"unused param: {param}", "severity": "warn"})
    return {"total_tantras": len(tantras), "issues": issues}


def dead_tantras(root=None):
    """Find tantras never called by any other tantra."""
    tantras = tantra4.load_all(root)
    cg = tantra4.call_graph(tantras)
    rcg = tantra4.reverse_call_graph(cg)
    dead = []
    for name in tantras:
        callers = rcg.get(name, [])
        if not callers and name not in ("anuvada-ganana", "boot"):
            dead.append({
                "name": name,
                "group": tantras[name]["group"],
                "lines": tantras[name]["lines"],
            })
    return dead


def complexity(root=None):
    """Rank tantras by complexity score."""
    tantras = tantra4.load_all(root)
    ranked = []
    for name, t in tantras.items():
        score = t["lines"] + t["conds"] * 3 + len(t["calls"]) * 2 + t["reduces"] * 2
        ranked.append({
            "name": name, "group": t["group"], "lines": t["lines"],
            "conds": t["conds"], "calls": len(t["calls"]),
            "reduces": t["reduces"], "score": score,
        })
    ranked.sort(key=lambda x: -x["score"])
    return ranked


def shabda_gaps(root=None, om_root=None):
    """Om5 nodes with kriya/phala edges but no shabda metadata."""
    nodes = om5.load_all(om_root)
    shabda_nodes = shabda.load_all(root)
    shabda_names = set(shabda_nodes.keys())

    missing = []
    for name, node in nodes.items():
        if name not in shabda_names:
            has_kriya = any(e["relation"] == "kriya" for e in node["edges"])
            has_phala = any(e["relation"] == "phala" for e in node["edges"])
            if has_kriya or has_phala:
                missing.append({
                    "name": name, "layer": node["layer"], "domain": node["domain"],
                    "has_kriya": has_kriya, "has_phala": has_phala,
                })
    return missing


# ---------------------------------------------------------------------------
# Combined report
# ---------------------------------------------------------------------------

def full_report(root=None, client=None):
    """Combined health check using parsers and optionally live graph."""
    report = {}

    om_nodes = om5.load_all(root)
    report["om5"] = om5.summary(om_nodes)

    tantras = tantra4.load_all()
    report["tantra4"] = tantra4.summary(tantras)

    shabda_nodes = shabda.load_all(root)
    report["shabda"] = shabda.summary(shabda_nodes)

    report["om5_lint"] = om5_lint(root)
    report["tantra4_lint"] = tantra4_lint()

    dead = dead_tantras()
    report["dead_tantras"] = {"count": len(dead), "names": [d["name"] for d in dead[:10]]}

    cx = complexity()
    report["complexity_top5"] = cx[:5]

    gaps = shabda_gaps(root)
    report["shabda_gaps"] = {"count": len(gaps), "sample": gaps[:5]}

    if client:
        try:
            result = client.eval("graph-stats")
            report["live"] = result if isinstance(result, dict) else {}
        except Exception as e:
            report["live_error"] = str(e)

    return report


def print_report(report, file=None):
    """Print health report to stdout."""
    f = file or sys.stdout

    print("## System Health Report", file=f)

    om = report.get("om5", {})
    print(f"\n**Om5**: {om.get('total', 0)} nodes, {om.get('total_lines', 0)} lines", file=f)
    for layer, count in om.get("layers", {}).items():
        print(f"  {layer}: {count}", file=f)

    t = report.get("tantra4", {})
    print(f"\n**Tantra4**: {t.get('total', 0)} tantras, {t.get('total_lines', 0)} lines", file=f)

    s = report.get("shabda", {})
    print(f"\n**Shabda**: {s.get('total_nodes', 0)} nodes, {s.get('total_words', 0)} words", file=f)

    om_issues = report.get("om5_lint", {}).get("issues", [])
    t_issues = report.get("tantra4_lint", {}).get("issues", [])
    if om_issues or t_issues:
        print(f"\n**Lint**: {len(om_issues)} om5 issues, {len(t_issues)} tantra4 issues", file=f)

    dead = report.get("dead_tantras", {})
    if dead.get("count"):
        print(f"\n**Dead tantras**: {dead['count']}", file=f)
        for name in dead.get("names", []):
            print(f"  {name}", file=f)

    gaps = report.get("shabda_gaps", {})
    if gaps.get("count"):
        print(f"\n**Shabda gaps**: {gaps['count']}", file=f)

    cx = report.get("complexity_top5", [])
    if cx:
        print(f"\n**Top 5 complex tantras**:", file=f)
        for c in cx:
            print(f"  {c['name']:30s} score={c['score']} lines={c['lines']}", file=f)
