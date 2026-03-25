"""generation.py — Generation analysis, prediction, and validation.

Tools for understanding what nodes can be generated, predicting their
edges, and validating generated nodes against expectations.

Five tools:
1. expected_node   — predict what a compound node should look like
2. validate_node   — compare a live node against its expected spec
3. gen_candidates  — list valid generation targets for a base
4. gen_gaps        — gap report: missing compounds by domain
5. validate_all    — batch validate all generated nodes
"""

from collections import defaultdict
from upakarana.parsers import om5, shabda as shabda_mod
from upakarana.analysis.compose import (
    QUALIFIER_CONTEXT, VALID_QUALIFIERS_PER_BASE, decompose_name,
)


# Relations that a compound inherits from its base
INHERIT_RELS = ["vishesa"]

# Relations that are generated (not inherited)
GENERATED_RELS = {
    "swarupa": "points to base concept",
    "sthita": "points to qualifier context (sangati)",
}


def expected_node(qualifier, base, root=None):
    """Predict what qualifier-base compound should look like.

    Returns an expected spec dict with:
      name, layer, static_edges (what the om5 should contain),
      shabda_overrides (from existing shabda if any),
      live_extras (edges the engine may add: naama, mantra phala, etc.)
    """
    nodes = om5.load_all(root)
    shabda_nodes = shabda_mod.load_all(root)
    compound = f"{qualifier}-{base}"

    base_node = nodes.get(base)
    if not base_node:
        return {"error": f"base node '{base}' not found in om5"}

    base_edges = om5.edges_by_relation(base_node)
    qc = QUALIFIER_CONTEXT.get(qualifier)

    # --- Static expected (what the om5 file should declare) ---
    static_edges = {}

    # swarupa → base (IS-A link)
    static_edges["swarupa"] = [base]

    # sthita → context (from qualifier context mapping)
    if qc:
        static_edges["sthita"] = [qc[1]]
    else:
        static_edges["sthita"] = [qualifier]  # fallback: use qualifier itself

    # vishesa inherited from base
    if "vishesa" in base_edges:
        static_edges["vishesa"] = list(base_edges["vishesa"])

    # --- Shabda overrides (if shabda entry exists) ---
    shabda_entry = shabda_nodes.get(compound, {})
    shabda_fields = shabda_entry.get("fields", {}) if isinstance(shabda_entry, dict) else {}
    overrides = {}
    for key, val in shabda_fields.items():
        if key.startswith("override-"):
            rel = key[len("override-"):]
            targets = val if isinstance(val, list) else [v.strip() for v in str(val).split(",") if v.strip()]
            overrides[rel] = targets

    # Apply overrides to static edges
    for rel, targets in overrides.items():
        if rel in static_edges:
            static_edges[rel] = list(set(static_edges[rel] + targets))
        else:
            static_edges[rel] = targets

    # --- Live extras (engine-added edges we can predict) ---
    live_extras = {}

    # naama edges (word forms from shabda word: field or auto-generated)
    word_forms = [compound, compound.replace("-", " ")]
    live_extras["naama"] = word_forms

    # phala from mantras: if base has mantra children, compound gets phala edges
    # (this comes from mantra registration, not om5)
    mantra_name = f"{base}-mantra"
    compound_mantra = f"{compound}-mantra"
    if mantra_name in nodes:
        live_extras["phala_possible"] = [mantra_name]
    if compound_mantra in nodes:
        live_extras["phala_possible"] = live_extras.get("phala_possible", []) + [compound_mantra]

    # --- Existing state ---
    existing_om5 = nodes.get(compound)
    existing_live = None  # filled by validate_node if engine running

    return {
        "name": compound,
        "qualifier": qualifier,
        "base": base,
        "layer": base_node.get("layer", "kosha"),
        "domain": base_node.get("domain", ""),
        "context": qc[1] if qc else qualifier,
        "category": qc[0] if qc else "unknown",
        "static_edges": static_edges,
        "overrides": overrides,
        "live_extras": live_extras,
        "exists_om5": existing_om5 is not None,
        "exists_shabda": compound in shabda_nodes,
        "shabda_fields": shabda_fields,
        "base_edges": base_edges,
    }


def validate_node(name, client=None, root=None):
    """Compare a live/static node against its expected spec.

    If client is provided, validates against live engine state.
    Otherwise validates the om5 file against inheritance rules.

    Returns a validation report with:
      status: "ok", "warn", or "fail"
      checks: list of {check, status, detail}
    """
    nodes = om5.load_all(root)
    known = set(nodes.keys())
    checks = []

    # Decompose the name
    decomp = decompose_name(name, known)
    if not decomp or not decomp.get("prefix"):
        checks.append({
            "check": "decomposable",
            "status": "skip",
            "detail": f"'{name}' is not a qualifier-base compound",
        })
        return {"name": name, "status": "skip", "checks": checks}

    qualifier = decomp["prefix"]["qualifier"]
    base = decomp["prefix"]["base"]
    expected = expected_node(qualifier, base, root)

    if "error" in expected:
        checks.append({
            "check": "base_exists",
            "status": "fail",
            "detail": expected["error"],
        })
        return {"name": name, "status": "fail", "checks": checks}

    # Get actual edges (from live engine or om5)
    actual_edges = {}
    source = "live"
    if client:
        try:
            info = client.inspect(name)
            for e in info.get("out_edges", []):
                actual_edges.setdefault(e["relation"], []).append(e["target"])
        except Exception:
            source = "not_found"
    else:
        node = nodes.get(name)
        if node:
            actual_edges = om5.edges_by_relation(node)
            source = "om5"
        else:
            source = "not_found"

    if source == "not_found":
        checks.append({
            "check": "exists",
            "status": "info",
            "detail": f"node not found (expected to be generated at runtime by avastha)",
        })
        # Can't validate further without actual edges
        return {"name": name, "status": "info", "checks": checks, "expected": expected}

    checks.append({
        "check": "exists",
        "status": "ok",
        "detail": f"found in {source}",
    })

    # Check 1: swarupa → base
    actual_swarupa = set(actual_edges.get("swarupa", []))
    if base in actual_swarupa:
        checks.append({"check": "swarupa_to_base", "status": "ok",
                        "detail": f"swarupa → {base}"})
    else:
        checks.append({"check": "swarupa_to_base", "status": "fail",
                        "detail": f"missing swarupa → {base}, has: {actual_swarupa}"})

    # Check 2: sthita → context
    expected_sthita = set(expected["static_edges"].get("sthita", []))
    actual_sthita = set(actual_edges.get("sthita", []))
    if expected_sthita & actual_sthita:
        checks.append({"check": "sthita_context", "status": "ok",
                        "detail": f"sthita includes {expected_sthita & actual_sthita}"})
    elif expected_sthita:
        checks.append({"check": "sthita_context", "status": "warn",
                        "detail": f"expected sthita {expected_sthita}, has {actual_sthita}"})

    # Check 3: vishesa inherited from base
    expected_vishesa = set(expected["static_edges"].get("vishesa", []))
    actual_vishesa = set(actual_edges.get("vishesa", []))
    if expected_vishesa and expected_vishesa <= actual_vishesa:
        checks.append({"check": "vishesa_inherited", "status": "ok",
                        "detail": f"vishesa inherited: {expected_vishesa}"})
    elif expected_vishesa:
        missing = expected_vishesa - actual_vishesa
        checks.append({"check": "vishesa_inherited", "status": "warn",
                        "detail": f"missing vishesa: {missing}"})

    # Check 4: no ghost edges (targets that don't exist anywhere)
    all_targets = set()
    for targets in actual_edges.values():
        all_targets.update(targets)
    # Check against om5 known names (static check)
    ghosts = []
    for t in all_targets:
        if t not in known and not t.endswith("-mantra") and " " not in t:
            ghosts.append(t)
    if ghosts:
        checks.append({"check": "no_ghosts", "status": "warn",
                        "detail": f"targets not in om5: {ghosts[:5]}"})
    else:
        checks.append({"check": "no_ghosts", "status": "ok",
                        "detail": "all targets resolve"})

    # Check 5: shabda has word: field
    shabda_nodes = shabda_mod.load_all(root)
    s = shabda_nodes.get(name)
    if s and s.get("fields", {}).get("word"):
        checks.append({"check": "shabda_word", "status": "ok",
                        "detail": f"word: {s['fields']['word']}"})
    elif source == "live" and "naama" in actual_edges:
        checks.append({"check": "shabda_word", "status": "ok",
                        "detail": f"naama edges present (engine-injected)"})
    else:
        checks.append({"check": "shabda_word", "status": "info",
                        "detail": "no shabda word: entry (may be auto-generated)"})

    # Overall status
    statuses = [c["status"] for c in checks]
    if "fail" in statuses:
        overall = "fail"
    elif "warn" in statuses:
        overall = "warn"
    else:
        overall = "ok"

    return {
        "name": name,
        "status": overall,
        "source": source,
        "qualifier": qualifier,
        "base": base,
        "checks": checks,
        "expected": expected["static_edges"],
        "actual": actual_edges,
    }


def gen_candidates(base_name, root=None):
    """List valid generation targets for a base concept.

    Returns list of candidates with their predicted edges and status.
    """
    nodes = om5.load_all(root)
    base_node = nodes.get(base_name)
    if not base_node:
        return {"error": f"base '{base_name}' not found", "candidates": []}

    base_edges = om5.edges_by_relation(base_node)
    known = set(nodes.keys())

    # Get valid qualifiers for this base
    valid = VALID_QUALIFIERS_PER_BASE.get(base_name, set())
    # Also include qualifiers from existing avastha edges
    avastha_qualifiers = set(base_edges.get("avastha", []))

    all_qualifiers = valid | avastha_qualifiers
    candidates = []

    for q in sorted(all_qualifiers):
        compound = f"{q}-{base_name}"
        exp = expected_node(q, base_name, root)

        candidates.append({
            "name": compound,
            "qualifier": q,
            "exists_om5": compound in known,
            "exists_avastha": q in avastha_qualifiers,
            "in_validity": q in valid,
            "context": exp.get("context", ""),
            "category": exp.get("category", ""),
            "static_edges": exp.get("static_edges", {}),
        })

    return {
        "base": base_name,
        "layer": base_node.get("layer", ""),
        "domain": base_node.get("domain", ""),
        "total_qualifiers": len(all_qualifiers),
        "existing": sum(1 for c in candidates if c["exists_om5"]),
        "avastha_generated": sum(1 for c in candidates if c["exists_avastha"] and not c["exists_om5"]),
        "candidates": candidates,
    }


def gen_gaps(root=None, domain_filter=None):
    """Gap report: missing compounds grouped by domain.

    Finds bases with avastha edges where the compound doesn't exist as om5
    and isn't in the validity matrix.
    """
    nodes = om5.load_all(root)
    known = set(nodes.keys())

    gaps_by_domain = defaultdict(list)

    for name, node in nodes.items():
        # Skip domain-prefixed collision entries (e.g. "kosha/physics/.../name")
        if "/" in name:
            continue
        if domain_filter and not node.get("domain", "").startswith(domain_filter):
            continue

        edges = om5.edges_by_relation(node)
        avastha = edges.get("avastha", [])
        if not avastha:
            continue

        valid = VALID_QUALIFIERS_PER_BASE.get(name, set())
        domain = node.get("domain", "")

        for q in avastha:
            compound = f"{q}-{name}"
            if compound not in known:
                # This compound is avastha-generated (runtime only)
                # Check if it's in the validity matrix
                gaps_by_domain[domain].append({
                    "name": compound,
                    "base": name,
                    "qualifier": q,
                    "in_validity": q in valid,
                    "type": "avastha_only",
                })

        # Check validity matrix for qualifiers NOT in avastha
        for q in valid - set(avastha):
            compound = f"{q}-{name}"
            if compound not in known:
                gaps_by_domain[domain].append({
                    "name": compound,
                    "base": name,
                    "qualifier": q,
                    "in_validity": True,
                    "type": "validity_only",
                })

    return {
        "total_gaps": sum(len(v) for v in gaps_by_domain.values()),
        "by_domain": {d: gaps for d, gaps in sorted(gaps_by_domain.items(), key=lambda x: -len(x[1]))},
    }


def validate_all(client=None, root=None):
    """Batch validate all compound nodes (om5 + live if client provided).

    Returns summary + per-node results.
    """
    nodes = om5.load_all(root)
    known = set(nodes.keys())

    results = []
    for name in sorted(known):
        decomp = decompose_name(name, known)
        if decomp and decomp.get("prefix"):
            result = validate_node(name, client=client, root=root)
            results.append(result)

    ok = sum(1 for r in results if r["status"] == "ok")
    warn = sum(1 for r in results if r["status"] == "warn")
    fail = sum(1 for r in results if r["status"] == "fail")

    return {
        "total": len(results),
        "ok": ok,
        "warn": warn,
        "fail": fail,
        "results": results,
    }
