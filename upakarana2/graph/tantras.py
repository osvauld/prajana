"""tantras.py — Tantra pattern classification and concept grounding.

Categorizes tantras by computational pattern.
Checks if tantras are grounded in sangati/kosha concepts.
Parallelism readiness analysis for pmap/pfilter/preduce.
"""

import re
from collections import defaultdict
from upakarana2.parsers import tantra4, om5


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


# ── Pipeline dataflow analysis ──────────────────────────────────────────


# The main pipeline stages, in execution order.
PIPELINE_STAGES = [
    "build-question-graph",
    "avrti-refine-v2",
    "kosha-expand",
    "detect-signals",
    "dispatch-answer",
]

# Sub-tantras called by each stage (manually curated from callgraph).
STAGE_CHILDREN = {
    "build-question-graph": [
        "emit-triples", "sandhi-viveka", "has-grammar-sthita",
        "shabda-anveshana", "triples-by-edge",
    ],
    "avrti-refine-v2": [
        # phase 1 (sequential)
        "sandhi-kosha", "sandhi-avastha", "sandhi-bandhana",
        "vyakarana-sparsha", "shashthi-possession", "vibhakti-shashthi",
        "vishesa-instance", "rashi-viveka", "vishesa-bandhana", "rashi-anuvada",
        # phase 2 (fixpoint)
        "sankhya-bandha-v2", "swarupa-anuvada", "shunya-bandha-v2",
    ],
    "kosha-expand": [],
    "detect-signals": [
        "extract-solve-for", "detect-shunya", "detect-viveka",
        "detect-anumana", "detect-count",
    ],
    "dispatch-answer": [
        "dispatch-derive", "dispatch-shunya", "dispatch-viveka",
        "dispatch-count", "dispatch-anumana",
    ],
}


def _extract_edge_literals(source):
    """Extract quoted string literals that look like edge names from tantra source."""
    # Match "word-word" patterns (edge names are lowercase with hyphens)
    literals = re.findall(r'"([a-z][-a-z]*(?:-[a-z]+)*)"', source)
    # Filter out common non-edge strings
    noise = {
        "otherwise", "true", "false", "none", "string", "number",
        "fn", "let", "cond", "and", "or", "not", "graph", "acc",
        "word", "clean", "edge", "obj", "result", "found",
        "prefix", "compound", "prev", "next", "last", "first",
        "pending", "active", "current", "signal", "mode",
    }
    return sorted(set(l for l in literals if l not in noise))


def _extract_calls(source, all_tantra_names):
    """Extract tantra calls and builtin calls from source."""
    # Find all (name ...) patterns
    calls = re.findall(r'\(([a-z][-a-z]+)', source)
    keywords = {
        "tantra", "let", "fn", "cond", "otherwise", "and", "or", "not",
        "reduce", "map", "filter", "preduce", "fixpoint", "append", "concat",
        "nth", "eq", "neq", "gt", "lt", "ge", "le", "sub", "add", "mul", "div",
        "to-string", "to-number", "length", "has-text", "has-items", "exists",
        "member", "unique", "index-graph", "idx-has-edge", "idx-subjects",
        "idx-objects", "idx-append", "split", "format", "max", "min",
        "range", "reverse", "sort", "starts-with", "ends-with", "substr",
        "char-at", "string-length", "graph",
    }
    calls = [c for c in calls if c not in keywords]
    tantra_calls = sorted(set(c for c in calls if c in all_tantra_names))
    builtin_calls = sorted(set(c for c in calls if c not in all_tantra_names))
    return tantra_calls, builtin_calls


def _classify_scan(source):
    """Classify how a tantra scans its input graph."""
    patterns = []
    if "reduce graph" in source or "reduce g " in source or "reduce refined" in source:
        patterns.append("reduce-full")
    if "| where" in source:
        patterns.append("pipe-filter")
    if "idx-subjects" in source or "idx-objects" in source or "idx-has-edge" in source:
        patterns.append("indexed")
    if "fixpoint" in source:
        patterns.append("fixpoint")
    if "ppr " in source:
        patterns.append("ppr-walk")
    if "walk " in source and "walk-in" not in source:
        patterns.append("graph-walk")
    if "shabda " in source:
        patterns.append("shabda-lookup")
    if "om-contract" in source:
        patterns.append("om-contract")
    if "preduce " in source:
        patterns.append("parallel-reduce")
    return patterns


def pipeline_dataflow(root=None):
    """Analyze the tantra pipeline's data flow.

    For each pipeline stage and its sub-tantras:
    - What edge types it reads (filters on)
    - What edge types it writes (emits)
    - How it scans the graph (reduce-full, pipe-filter, indexed, ppr)
    - What builtins/graph operations it uses

    Returns a structure suitable for identifying subgraph partitions.
    """
    tantras = tantra4.load_all(root)
    all_names = set(tantras.keys())

    stages = []
    all_edges_read = defaultdict(set)   # edge → set of tantras that read it
    all_edges_write = defaultdict(set)  # edge → set of tantras that write it

    for stage_name in PIPELINE_STAGES:
        children = STAGE_CHILDREN.get(stage_name, [])
        members = [stage_name] + children

        stage_info = {
            "name": stage_name,
            "members": [],
            "edges_read": set(),
            "edges_write": set(),
            "scan_patterns": set(),
        }

        for member in members:
            t = tantras.get(member)
            if not t:
                continue

            src = t["source"]
            edges = _extract_edge_literals(src)
            tantra_calls, builtin_calls = _extract_calls(src, all_names)
            scans = _classify_scan(src)

            # Heuristic: edges appearing in "eq e" or "where" are reads,
            # edges appearing in [[..., "edge", ...]] triple construction are writes
            reads = set()
            writes = set()
            for edge in edges:
                # Check for read patterns: eq e "edge", eq edge "name", | and (eq e "edge")
                read_pats = [
                    f'eq e "{edge}"', f'eq edge "{edge}"',
                    f'eq (to-string e) "{edge}"',
                    f'eq (triple-edge', f'"{edge}" |',
                ]
                write_pats = [
                    f', "{edge}",', f'"{edge}", ',
                ]
                is_read = any(p in src for p in read_pats) or f'"{edge}"' in src
                is_write = f'[[' in src and f'"{edge}"' in src

                # If it appears in a triple literal [..., "edge", ...], likely a write
                triple_write = re.search(
                    rf'\[("[^"]*"|[a-z][-a-z]*),\s*"{re.escape(edge)}",\s*("[^"]*"|[a-z][-a-z]*)\]',
                    src
                )
                if triple_write:
                    writes.add(edge)
                    all_edges_write[edge].add(member)
                if is_read:
                    reads.add(edge)
                    all_edges_read[edge].add(member)

            stage_info["edges_read"].update(reads)
            stage_info["edges_write"].update(writes)
            stage_info["scan_patterns"].update(scans)

            stage_info["members"].append({
                "name": member,
                "lines": t["lines"],
                "edges": edges,
                "reads": sorted(reads),
                "writes": sorted(writes),
                "scans": scans,
                "tantra_calls": tantra_calls,
                "builtin_calls": builtin_calls,
            })

        # Convert sets to sorted lists for output
        stage_info["edges_read"] = sorted(stage_info["edges_read"])
        stage_info["edges_write"] = sorted(stage_info["edges_write"])
        stage_info["scan_patterns"] = sorted(stage_info["scan_patterns"])
        stages.append(stage_info)

    # Compute edge overlap between stages
    stage_edge_sets = {}
    for s in stages:
        stage_edge_sets[s["name"]] = set(s["edges_read"])

    overlaps = []
    stage_names = list(stage_edge_sets.keys())
    for i in range(len(stage_names)):
        for j in range(i + 1, len(stage_names)):
            a, b = stage_names[i], stage_names[j]
            shared = stage_edge_sets[a] & stage_edge_sets[b]
            if shared:
                overlaps.append({"stages": [a, b], "shared_edges": sorted(shared)})

    return {
        "stages": stages,
        "edge_producers": {k: sorted(v) for k, v in all_edges_write.items()},
        "edge_consumers": {k: sorted(v) for k, v in all_edges_read.items()},
        "overlaps": overlaps,
    }


def print_dataflow(root=None):
    """Print pipeline dataflow analysis."""
    result = pipeline_dataflow(root)

    print(f"\n{'═' * 80}")
    print(f"  TANTRA PIPELINE DATAFLOW")
    print(f"{'═' * 80}\n")

    for stage in result["stages"]:
        n_members = len(stage["members"])
        print(f"  ┌─ {stage['name']} ({n_members} tantras) ─────────")
        print(f"  │  reads:  {', '.join(stage['edges_read'][:15]) or '(none)'}")
        print(f"  │  writes: {', '.join(stage['edges_write'][:15]) or '(none)'}")
        print(f"  │  scans:  {', '.join(stage['scan_patterns']) or '(none)'}")
        for m in stage["members"]:
            scans = ','.join(m["scans"]) if m["scans"] else "—"
            print(f"  │    {m['name']:35s} {m['lines']:3d}L  [{scans}]")
            if m["reads"]:
                print(f"  │      reads:  {', '.join(m['reads'][:10])}")
            if m["writes"]:
                print(f"  │      writes: {', '.join(m['writes'][:10])}")
        print(f"  └{'─' * 50}")
        print()

    # Edge flow summary
    print(f"  ── EDGE FLOW (producer → consumer) ──")
    all_edges = sorted(set(list(result["edge_producers"].keys()) +
                           list(result["edge_consumers"].keys())))
    for edge in all_edges:
        producers = result["edge_producers"].get(edge, [])
        consumers = result["edge_consumers"].get(edge, [])
        if producers or len(consumers) > 1:
            p = ', '.join(producers) if producers else "BQG/external"
            c = ', '.join(consumers) if consumers else "—"
            print(f"    {edge:30s}  ← {p:30s}  → {c}")
    print()

    # Overlap
    if result["overlaps"]:
        print(f"  ── EDGE OVERLAP BETWEEN STAGES ──")
        for ov in result["overlaps"]:
            print(f"    {ov['stages'][0]} ∩ {ov['stages'][1]}: {', '.join(ov['shared_edges'])}")
        print()

    # Subgraph partition suggestion
    print(f"  ── SUBGRAPH PARTITIONS (suggested) ──")
    # Collect all unique read edges per stage
    for stage in result["stages"]:
        unique_reads = set(stage["edges_read"])
        for other in result["stages"]:
            if other["name"] != stage["name"]:
                unique_reads -= set(other["edges_read"])
        if unique_reads:
            print(f"    {stage['name']:30s} exclusive: {', '.join(sorted(unique_reads))}")
    print()
