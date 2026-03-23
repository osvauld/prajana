"""static.py — File-level analysis using parsers (no engine needed).

Lint, dead code detection, complexity metrics, pattern analysis.
"""

from collections import defaultdict
from upakarana.parsers import om5, tantra4, shabda


def om5_lint(root=None):
    """Check om5 files for issues."""
    nodes = om5.load_all(root)
    issues = []

    for name, node in nodes.items():
        edges = node["edges"]
        if not edges:
            issues.append({"node": name, "issue": "no edges", "severity": "warn"})

        # Check for self-referencing edges
        self_refs = [e for e in edges if e["target"] == name]
        if self_refs:
            rels = [e["relation"] for e in self_refs]
            issues.append({"node": name, "issue": f"self-reference via {rels}", "severity": "warn"})

        # Check for unknown targets (targets not in any node)
        for e in edges:
            if e["target"] not in nodes and not e["target"].startswith("domain-"):
                pass  # Many targets are in other layers — can't check without full graph

    return {"total_nodes": len(nodes), "issues": issues}


def tantra4_lint(root=None):
    """Check tantra4 files for issues."""
    tantras = tantra4.load_all(root)
    issues = []

    for name, t in tantras.items():
        # Deeply nested (many conds)
        if t["conds"] > 5:
            issues.append({"tantra": name, "issue": f"high cond count: {t['conds']}", "severity": "info"})

        # Very long tantras
        if t["lines"] > 100:
            issues.append({"tantra": name, "issue": f"long: {t['lines']} lines", "severity": "info"})

        # Unused params (mentioned in takes but not in source body)
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
    """Rank tantras by complexity (lines, conds, calls, reduces)."""
    tantras = tantra4.load_all(root)
    ranked = []
    for name, t in tantras.items():
        score = t["lines"] + t["conds"] * 3 + len(t["calls"]) * 2 + t["reduces"] * 2
        ranked.append({
            "name": name,
            "group": t["group"],
            "lines": t["lines"],
            "conds": t["conds"],
            "calls": len(t["calls"]),
            "reduces": t["reduces"],
            "score": score,
        })
    ranked.sort(key=lambda x: -x["score"])
    return ranked


def shabda_gaps(root=None, om_root=None):
    """Find om5 nodes that are missing shabda metadata."""
    nodes = om5.load_all(om_root)
    shabda_nodes = shabda.load_all(root)
    shabda_names = set(shabda_nodes.keys())

    missing = []
    for name, node in nodes.items():
        if name not in shabda_names:
            # Check if it has any edges that suggest it should have shabda
            has_kriya = any(e["relation"] == "kriya" for e in node["edges"])
            has_phala = any(e["relation"] == "phala" for e in node["edges"])
            if has_kriya or has_phala:
                missing.append({
                    "name": name,
                    "layer": node["layer"],
                    "domain": node["domain"],
                    "has_kriya": has_kriya,
                    "has_phala": has_phala,
                })
    return missing


def pattern_report(root=None):
    """Detect repeated patterns across tantras."""
    tantras = tantra4.load_all(root)
    cg = tantra4.call_graph(tantras)
    rcg = tantra4.reverse_call_graph(cg)

    # Fan-in: most depended-on tantras
    fan_in = [(name, len(callers)) for name, callers in rcg.items()]
    fan_in.sort(key=lambda x: -x[1])

    # Fan-out: tantras that call the most others
    fan_out = [(name, len(calls)) for name, calls in cg.items()]
    fan_out.sort(key=lambda x: -x[1])

    # Groups by size
    groups = tantra4.by_group(tantras)
    group_sizes = {g: len(ts) for g, ts in groups.items()}

    return {
        "fan_in_top10": fan_in[:10],
        "fan_out_top10": fan_out[:10],
        "group_sizes": group_sizes,
        "total_tantras": len(tantras),
        "total_lines": sum(t["lines"] for t in tantras.values()),
    }
