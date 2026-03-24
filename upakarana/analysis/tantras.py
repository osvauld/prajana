"""tantras.py — Tantra pattern classification and concept grounding.

Categorizes tantras by computational pattern.
Checks if tantras are grounded in sangati/kosha concepts.
Parallelism readiness analysis for pmap/pfilter/preduce.
"""

import re
from collections import defaultdict
from upakarana.parsers import tantra4, om5


def classify_patterns(root=None):
    """Classify all tantras by computational pattern.

    Patterns:
      fixpoint      — uses fixpoint builtin
      reduce-fold   — uses reduce (stateful scan)
      pipe-filter   — uses | where | collect (set comprehension)
      signal-rw     — uses read-signal or write-signal
      cond-dispatch — short body dominated by cond
      single-expr   — body is one expression (≤3 lines)
      compose-chain — sequence of named tantra calls
    """
    tantras = tantra4.load_all(root)

    patterns = defaultdict(list)

    for name, t in tantras.items():
        src = t["source"]
        lines = t["lines"]

        if "fixpoint" in src:
            patterns["fixpoint"].append(name)
        elif "reduce " in src:
            patterns["reduce-fold"].append(name)
        elif "| where" in src or "| collect" in src:
            patterns["pipe-filter"].append(name)
        elif "read-signal" in src or "write-signal" in src:
            patterns["signal-rw"].append(name)
        elif src.count("(cond ") > 0 and lines < 8:
            patterns["cond-dispatch"].append(name)
        elif lines <= 3:
            patterns["single-expr"].append(name)
        else:
            patterns["compose-chain"].append(name)

    return {
        "patterns": {k: {"count": len(v), "tantras": sorted(v)}
                     for k, v in sorted(patterns.items(), key=lambda x: -len(x[1]))},
        "total": sum(len(v) for v in patterns.values()),
    }


def concept_grounding(root=None):
    """Check which tantras have corresponding kosha/yantra om5 nodes.

    A tantra is "grounded" if a kosha/yantra node references it
    via kriya edges (the graph knows this tantra implements something).
    """
    tantras = tantra4.load_all(root)
    nodes = om5.load_all(root)

    # Build set of tantra names referenced by kriya edges in kosha/yantra
    grounded_names = set()
    grounding_map = defaultdict(list)  # tantra_name → [kosha_node, ...]

    for name, node in nodes.items():
        if not (node["domain"].startswith("kosha/yantra") or
                node["layer"] == "kosha"):
            continue
        for e in node["edges"]:
            if e["relation"] == "kriya":
                target = e["target"]
                if target in tantras:
                    grounded_names.add(target)
                    grounding_map[target].append(name)

    ungrounded = sorted(set(tantras.keys()) - grounded_names)
    grounded = sorted(grounded_names)

    return {
        "grounded": {"count": len(grounded), "tantras": grounded},
        "ungrounded": {"count": len(ungrounded), "tantras": ungrounded},
        "grounding_map": dict(grounding_map),
    }


def sangati_mapping(root=None):
    """Map pipeline concepts to their sangati roots.

    Checks if kosha/yantra nodes have abheda or swarupa edges
    pointing to sangati mathematical concepts.
    """
    nodes = om5.load_all(root)

    yantra_nodes = {n: v for n, v in nodes.items()
                    if v["domain"].startswith("kosha/yantra")}

    mappings = []
    for name, node in yantra_nodes.items():
        sangati_links = []
        for e in node["edges"]:
            target_node = nodes.get(e["target"])
            if target_node and target_node["layer"] == "sangati":
                sangati_links.append({
                    "relation": e["relation"],
                    "target": e["target"],
                })
            # Also check abheda to math concepts
            if e["relation"] == "abheda":
                target_node = nodes.get(e["target"])
                if target_node and target_node["domain"].startswith("kosha/math"):
                    sangati_links.append({
                        "relation": "abheda",
                        "target": e["target"],
                    })
        if sangati_links:
            mappings.append({"node": name, "links": sangati_links})

    unmapped = [n for n in yantra_nodes if n not in {m["node"] for m in mappings}]

    return {
        "mapped": mappings,
        "unmapped": unmapped,
    }


def helper_vocabulary(root=None):
    """Catalog the tantra4 helper vocabulary — the "words" pipeline tantras compose.

    Groups helpers by abstraction layer:
      primitive  — ≤4 lines, single operation
      operation  — 5-10 lines, composes primitives
      structure  — named field access or data construction
      composition — composes operations into higher concepts
    """
    tantras = tantra4.load_all(root)

    # Only tantra4 group (helpers)
    helpers = {n: t for n, t in tantras.items() if t["group"] == "tantra4"}

    vocab = {"primitive": [], "operation": [], "structure": [], "composition": []}

    for name, t in sorted(helpers.items()):
        lines = t["lines"]
        calls = len(t["calls"])
        has_reduce = "reduce " in t["source"]

        if lines <= 4 and calls <= 1:
            layer = "primitive"
        elif lines <= 10 and not has_reduce:
            layer = "operation"
        elif "-result" in name or "-field" in name or "-info" in name:
            layer = "structure"
        else:
            layer = "composition"

        vocab[layer].append({"name": name, "lines": lines, "calls": calls})

    return vocab


def parallelism_candidates(root=None):
    """Analyze tantras for pmap/pfilter/preduce upgrade candidates.

    Classifies each reduce/map/filter usage by:
    1. Is the lambda body pure (no emit-edge, write-signal, etc)?
    2. Does the lambda do graph walks (walk, om-*, shabda)?
    3. What is the iteration source (graph-all-nodes, walk-in, etc)?
    4. Is the reduce accumulator a list-append pattern?

    Categories:
      pmap-ready     — map with pure lambda doing graph work
      pfilter-ready  — filter with pure lambda
      preduce-ready  — reduce with list-append accumulator + pure body
      side-effects   — has emit/write in body (can't parallelize)
      sequential     — accumulator-dependent (not list-append)
      trivial        — body too simple to benefit from parallelism
    """
    tantras = tantra4.load_all(root)

    side_effect_ops = {"emit-edge", "emit-node", "write-signal", "set-shabda",
                       "remember-bindings", "set-comment"}
    graph_ops = {"walk", "walk-in", "om-janya", "om-phala", "om-kriya",
                 "om-yukta", "om-sthita", "om-swarupa", "om-abheda",
                 "om-contract", "shabda", "lookup", "edges", "neighbors",
                 "avrti", "ppr", "node-layer", "node-krama", "eval-krama",
                 "krama-path", "word-node", "eval-node"}
    tantra_call_ops = {"call-tantra"}

    candidates = {
        "pmap-ready": [], "pfilter-ready": [], "preduce-ready": [],
        "side-effects": [], "sequential": [], "trivial": [],
        "already-parallel": [],
    }

    for name, t in sorted(tantras.items()):
        src = t["source"]

        # Already using parallel ops?
        if re.search(r'\bpmap\b|\bpfilter\b|\bpreduce\b', src):
            candidates["already-parallel"].append({
                "tantra": name, "ops": re.findall(r'\b(pmap|pfilter|preduce)\b', src),
            })
            continue

        # Find all reduce/map/filter calls with their context
        for match in re.finditer(
            r'\b(reduce|map|filter)\s+(\S+)\s+', src
        ):
            op = match.group(1)
            source_var = match.group(2)
            # Extract the lambda body (rough — up to matching paren depth)
            pos = match.end()
            rest = src[pos:]

            # Check for side effects in the rest of this expression
            has_side_effects = any(se in rest for se in side_effect_ops)
            has_graph_ops = any(go in rest for go in graph_ops)
            has_tantra_calls = any(tc in rest for tc in tantra_call_ops)
            has_append = "append" in rest and op == "reduce"
            has_let = "let " in rest[:200]  # let bindings in lambda body

            # Classify
            entry = {
                "tantra": name,
                "op": op,
                "source": source_var,
                "has_graph": has_graph_ops,
                "has_tantra_calls": has_tantra_calls,
                "has_side_effects": has_side_effects,
                "lines": t["lines"],
                "group": t["group"],
            }

            if has_side_effects:
                candidates["side-effects"].append(entry)
            elif op == "map" and (has_graph_ops or has_tantra_calls):
                candidates["pmap-ready"].append(entry)
            elif op == "filter" and (has_graph_ops or has_tantra_calls):
                candidates["pfilter-ready"].append(entry)
            elif op == "reduce" and has_append and (has_graph_ops or has_tantra_calls or has_let):
                candidates["preduce-ready"].append(entry)
            elif op == "reduce":
                candidates["sequential"].append(entry)
            elif not has_graph_ops and not has_tantra_calls:
                candidates["trivial"].append(entry)
            else:
                # map/filter with graph ops but small bodies
                if op == "map":
                    candidates["pmap-ready"].append(entry)
                else:
                    candidates["pfilter-ready"].append(entry)

    # Summary
    summary = {k: len(v) for k, v in candidates.items()}
    summary["total_parallelizable"] = (
        summary["pmap-ready"] + summary["pfilter-ready"] + summary["preduce-ready"]
    )

    return {"candidates": candidates, "summary": summary}


def print_parallelism(root=None):
    """Print parallelism candidate analysis."""
    result = parallelism_candidates(root)
    candidates = result["candidates"]
    summary = result["summary"]

    print(f"\n{'=' * 80}")
    print(f"  TANTRA PARALLELISM CANDIDATES")
    print(f"{'=' * 80}\n")

    print(f"  Total parallelizable: {summary['total_parallelizable']}")
    print(f"    pmap-ready:    {summary['pmap-ready']}")
    print(f"    pfilter-ready: {summary['pfilter-ready']}")
    print(f"    preduce-ready: {summary['preduce-ready']}")
    print(f"  Blocked:")
    print(f"    side-effects:  {summary['side-effects']}")
    print(f"    sequential:    {summary['sequential']}")
    print(f"    trivial:       {summary['trivial']}")
    if summary.get("already-parallel", 0):
        print(f"  Already parallel: {summary['already-parallel']}")
    print()

    for category in ["preduce-ready", "pmap-ready", "pfilter-ready"]:
        items = candidates[category]
        if not items:
            continue
        print(f"  ── {category} ({len(items)}) ──")
        for c in items:
            graph = "graph" if c["has_graph"] else ""
            tantra = "tantra-call" if c["has_tantra_calls"] else ""
            flags = " ".join(f for f in [graph, tantra] if f)
            print(f"    {c['tantra']:35s} {c['op']:8s} source={c['source']:20s} [{flags}]")
        print()

    if candidates["side-effects"]:
        print(f"  ── side-effects (blocked) ({len(candidates['side-effects'])}) ──")
        for c in candidates["side-effects"]:
            print(f"    {c['tantra']:35s} {c['op']:8s}")
        print()
