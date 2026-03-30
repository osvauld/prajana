"""compose.py — Compound node validation, generatability, and gap analysis.

Consolidates the *operational* subset of compose.py + generation.py.
Discovery-phase cross-product tools (karma_varga_cross, declension_matrix,
grammar_shabda_generator, etc.) have been dropped — that work is complete.

Key exports:
  decompose_name      — parse qualifier-base compound name
  find_compounds      — all decomposable nodes in the graph
  base_concepts       — base nodes and their variant compounds
  inheritance_analysis — what compounds inherit from vs override their base
  generatability_report — auto/semi/manual classification
  expected_node       — predict edges for a generated compound
  validate_node       — validate a node against its expected spec
  gen_candidates      — valid generation targets for a base
  gen_gaps            — missing compounds by domain
  pratipaksha_analysis — inverse pair completeness
  VALID_COMBINATIONS, VALID_QUALIFIERS_PER_BASE — curated validity constants
"""

from collections import defaultdict
from upakarana2.parsers import om5, shabda as shabda_mod


# ---------------------------------------------------------------------------
# Qualifier context mapping  (qualifier → (category, sangati context))
# ---------------------------------------------------------------------------

QUALIFIER_CONTEXT = {
    # temporal
    "initial": ("temporal", "aarambham"),
    "final": ("temporal", "antya"),
    "average": ("temporal", "madhya"),
    # spatial
    "angular": ("spatial", "kona"),
    "linear": ("spatial", "rekha"),
    "centripetal": ("spatial", "kendra"),
    "radial": ("spatial", "kendra"),
    "tangential": ("spatial", "sparsha"),
    "normal": ("spatial", "lamba"),
    "net": ("spatial", "samanya"),
    "total": ("spatial", "dvandva"),
    "relative": ("spatial", "apeksha"),
    # domain — force/energy source
    "kinetic": ("domain", "gati"),
    "potential": ("domain", "sthiti"),
    "elastic": ("domain", "sthiti"),
    "electric": ("domain", "vidyut"),
    "gravitational": ("domain", "gurutva"),
    "magnetic": ("domain", "ayaskanta"),
    "thermal": ("domain", "ushna"),
    "nuclear": ("domain", "paramanu"),
    "photon": ("domain", "prakasha"),
    "spring": ("domain", "sthiti"),
    "friction": ("domain", "ghasana"),
    "drag": ("domain", "ghasana"),
    "tension": ("domain", "tana"),
    # intensity/state
    "strong": ("intensity", "vriddhi"),
    "weak": ("intensity", "kshaya"),
    "damped": ("intensity", "kshaya"),
    "rated": ("intensity", "matra"),
    # chemistry
    "covalent": ("bond", "sahabhaga"),
    "ionic": ("bond", "vidyut"),
    "hydrogen": ("bond", "setu"),
}

SUFFIX_TYPE = {
    "mantra": ("kriya", "computational rule"),
    "beeja": ("kriya", "seed/generator"),
    "krama": ("kriya", "ordered step"),
    "prakar": ("drishthanta", "concrete instance"),
    "varga": ("abheda", "class/group"),
    "linga": ("swarupa", "marker/indicator"),
}


# ---------------------------------------------------------------------------
# Curated validity constants
# ---------------------------------------------------------------------------

VALID_COMBINATIONS = {
    ("temporal", "velocity"), ("temporal", "acceleration"),
    ("temporal", "momentum"), ("temporal", "displacement"),
    ("temporal", "energy"), ("temporal", "force"),
    ("temporal", "position"),
    ("spatial", "velocity"), ("spatial", "acceleration"),
    ("spatial", "displacement"), ("spatial", "momentum"),
    ("spatial", "force"),
    ("domain", "energy"), ("domain", "force"),
    ("domain", "power"), ("domain", "constant"),
    ("domain", "collision"),
    ("intensity", "oscillation"), ("intensity", "nuclear-force"),
    ("intensity", "torque"), ("intensity", "power"),
    ("bond", "bond"),
}

VALID_QUALIFIERS_PER_BASE = {
    "velocity": {"initial", "final", "average", "angular", "relative",
                 "tangential", "radial", "linear", "centripetal"},
    "acceleration": {"angular", "centripetal", "tangential", "radial",
                     "linear", "average", "initial", "final"},
    "displacement": {"angular", "total", "linear", "radial", "tangential",
                     "initial", "final", "average"},
    "momentum": {"angular", "initial", "final", "total", "linear"},
    "force": {"gravitational", "electric", "magnetic", "friction", "spring",
              "centripetal", "normal", "net", "drag", "tension", "nuclear",
              "applied", "elastic", "tangential", "radial"},
    "energy": {"kinetic", "potential", "photon", "thermal", "elastic",
               "gravitational", "nuclear", "electric", "magnetic"},
    "power": {"electric", "rated"},
    "constant": {"gravitational", "spring", "electric", "magnetic"},
    "collision": {"elastic"},
    "oscillation": {"damped", "rated"},
    "nuclear-force": {"strong", "weak"},
    "torque": {"rated"},
    "bond": {"covalent", "ionic", "hydrogen"},
}


# ---------------------------------------------------------------------------
# Decomposition
# ---------------------------------------------------------------------------

def decompose_name(name, known_names):
    """Try to decompose a compound name into qualifier+base or base+suffix."""
    if "-" not in name:
        return None

    result = {"name": name, "prefix": None, "suffix": None, "base": None}

    parts = name.split("-", 1)
    prefix, rest = parts[0], parts[1]
    if rest in known_names and prefix in QUALIFIER_CONTEXT:
        cat, context = QUALIFIER_CONTEXT[prefix]
        result["prefix"] = {"qualifier": prefix, "base": rest,
                             "category": cat, "context": context}
        result["base"] = rest

    parts = name.rsplit("-", 1)
    stem, suffix = parts[0], parts[1]
    if stem in known_names and suffix in SUFFIX_TYPE:
        vish, desc = SUFFIX_TYPE[suffix]
        result["suffix"] = {"type": suffix, "base": stem,
                             "visheshanam": vish, "description": desc}
        if result["base"] is None:
            result["base"] = stem

    if result["prefix"] is None and result["suffix"] is None:
        return None
    return result


def find_compounds(root=None):
    """Find all decomposable compound nodes in the graph."""
    nodes = om5.load_all(root)
    names = set(nodes.keys())
    compounds = []
    for name in sorted(names):
        d = decompose_name(name, names)
        if d:
            d["layer"] = nodes[name].get("layer", "")
            d["domain"] = nodes[name].get("domain", "")
            compounds.append(d)
    return compounds


def base_concepts(root=None):
    """Find base concepts and all their existing variants."""
    nodes = om5.load_all(root)
    names = set(nodes.keys())
    compounds = find_compounds(root)

    bases = defaultdict(lambda: {"prefix_variants": [], "suffix_variants": [],
                                  "layer": "", "domain": ""})
    for c in compounds:
        if c["prefix"]:
            b = c["prefix"]["base"]
            bases[b]["prefix_variants"].append(c)
            if not bases[b]["layer"]:
                bases[b]["layer"] = nodes.get(b, {}).get("layer", "")
                bases[b]["domain"] = nodes.get(b, {}).get("domain", "")
        if c["suffix"]:
            b = c["suffix"]["base"]
            bases[b]["suffix_variants"].append(c)
            if not bases[b]["layer"]:
                bases[b]["layer"] = nodes.get(b, {}).get("layer", "")
                bases[b]["domain"] = nodes.get(b, {}).get("domain", "")

    return dict(bases)


# ---------------------------------------------------------------------------
# Inheritance analysis
# ---------------------------------------------------------------------------

def _edges_by_rel(node):
    d = {}
    for e in node.get("edges", []):
        d.setdefault(e["relation"], []).append(e["target"])
    return d


def inheritance_analysis(root=None):
    """For each compound, compare edges to its base — inherited vs overridden vs unique."""
    nodes = om5.load_all(root)
    compounds = find_compounds(root)
    results = []

    for c in sorted(compounds, key=lambda x: x["name"]):
        if not c.get("prefix"):
            continue
        base_name = c["prefix"]["base"]
        comp_name = c["name"]
        base_node = nodes.get(base_name, {})
        comp_node = nodes.get(comp_name, {})

        base_edges = _edges_by_rel(base_node)
        comp_edges = _edges_by_rel(comp_node)

        base_rels = set(base_edges.keys())
        comp_rels = set(comp_edges.keys())
        shared = base_rels & comp_rels

        has_swarupa_to_base = base_name in comp_edges.get("swarupa", [])

        inherited = {}
        overridden = {}
        for rel in shared:
            bt = set(base_edges[rel])
            ct = set(comp_edges[rel])
            common = bt & ct
            if common:
                inherited[rel] = sorted(common)
            diff = ct - bt
            if diff:
                overridden[rel] = sorted(diff)

        only_comp = {r: comp_edges[r] for r in sorted(comp_rels - base_rels)}
        only_base = sorted(base_rels - comp_rels)

        unique_edge_count = sum(len(v) for v in only_comp.values())
        override_count = sum(len(v) for v in overridden.values())
        generatable = unique_edge_count <= 4 and override_count <= 6

        results.append({
            "name": comp_name,
            "base": base_name,
            "qualifier": c["prefix"]["qualifier"],
            "category": c["prefix"]["category"],
            "swarupa_to_base": has_swarupa_to_base,
            "inherited": inherited,
            "overridden": overridden,
            "only_compound": only_comp,
            "only_base": only_base,
            "unique_edge_count": unique_edge_count,
            "override_count": override_count,
            "generatable": generatable,
        })

    return results


def generatability_report(root=None):
    """Group compounds into auto/semi/manual generatability tiers."""
    ia = inheritance_analysis(root)
    auto, semi, manual = [], [], []
    for item in ia:
        if item["generatable"] and item["unique_edge_count"] <= 2:
            auto.append(item)
        elif item["generatable"]:
            semi.append(item)
        else:
            manual.append(item)
    return {
        "auto": auto, "auto_count": len(auto),
        "semi": semi, "semi_count": len(semi),
        "manual": manual, "manual_count": len(manual),
    }


# ---------------------------------------------------------------------------
# Expected node prediction + validation
# ---------------------------------------------------------------------------

def expected_node(qualifier, base, root=None):
    """Predict what a qualifier-base compound should look like."""
    nodes = om5.load_all(root)
    shabda_nodes = shabda_mod.load_all(root)
    compound = f"{qualifier}-{base}"

    base_node = nodes.get(base)
    if not base_node:
        return {"error": f"base node '{base}' not found in om5"}

    base_edges = om5.edges_by_relation(base_node)
    qc = QUALIFIER_CONTEXT.get(qualifier)

    static_edges = {}
    static_edges["swarupa"] = [base]
    static_edges["sthita"] = [qc[1] if qc else qualifier]

    if "vishesa" in base_edges:
        static_edges["vishesa"] = list(base_edges["vishesa"])

    shabda_entry = shabda_nodes.get(compound, {})
    shabda_fields = shabda_entry.get("fields", {}) if isinstance(shabda_entry, dict) else {}
    overrides = {}
    for key, val in shabda_fields.items():
        if key.startswith("override-"):
            rel = key[len("override-"):]
            targets = val if isinstance(val, list) else [v.strip() for v in str(val).split(",") if v.strip()]
            overrides[rel] = targets
    for rel, targets in overrides.items():
        if rel in static_edges:
            static_edges[rel] = list(set(static_edges[rel] + targets))
        else:
            static_edges[rel] = targets

    live_extras = {
        "naama": [compound, compound.replace("-", " ")],
    }
    mantra_name = f"{base}-mantra"
    compound_mantra = f"{compound}-mantra"
    if mantra_name in nodes:
        live_extras["phala_possible"] = [mantra_name]
    if compound_mantra in nodes:
        live_extras["phala_possible"] = live_extras.get("phala_possible", []) + [compound_mantra]

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
        "exists_om5": compound in nodes,
        "exists_shabda": compound in shabda_nodes,
        "shabda_fields": shabda_fields,
        "base_edges": base_edges,
    }


def validate_node(name, client=None, root=None):
    """Compare a node against its expected spec (om5 or live engine)."""
    nodes = om5.load_all(root)
    known = set(nodes.keys())
    checks = []

    decomp = decompose_name(name, known)
    if not decomp or not decomp.get("prefix"):
        checks.append({"check": "decomposable", "status": "skip",
                        "detail": f"'{name}' is not a qualifier-base compound"})
        return {"name": name, "status": "skip", "checks": checks}

    qualifier = decomp["prefix"]["qualifier"]
    base = decomp["prefix"]["base"]
    expected = expected_node(qualifier, base, root)

    if "error" in expected:
        checks.append({"check": "base_exists", "status": "fail", "detail": expected["error"]})
        return {"name": name, "status": "fail", "checks": checks}

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
        checks.append({"check": "exists", "status": "info",
                        "detail": "node not found — expected to be generated at runtime by avastha"})
        return {"name": name, "status": "info", "checks": checks, "expected": expected}

    checks.append({"check": "exists", "status": "ok", "detail": f"found in {source}"})

    actual_swarupa = set(actual_edges.get("swarupa", []))
    if base in actual_swarupa:
        checks.append({"check": "swarupa_to_base", "status": "ok", "detail": f"swarupa → {base}"})
    else:
        checks.append({"check": "swarupa_to_base", "status": "fail",
                        "detail": f"missing swarupa → {base}, has: {actual_swarupa}"})

    expected_sthita = set(expected["static_edges"].get("sthita", []))
    actual_sthita = set(actual_edges.get("sthita", []))
    if expected_sthita & actual_sthita:
        checks.append({"check": "sthita_context", "status": "ok",
                        "detail": f"sthita includes {expected_sthita & actual_sthita}"})
    elif expected_sthita:
        checks.append({"check": "sthita_context", "status": "warn",
                        "detail": f"expected sthita {expected_sthita}, has {actual_sthita}"})

    expected_vishesa = set(expected["static_edges"].get("vishesa", []))
    actual_vishesa = set(actual_edges.get("vishesa", []))
    if expected_vishesa and expected_vishesa <= actual_vishesa:
        checks.append({"check": "vishesa_inherited", "status": "ok",
                        "detail": f"vishesa inherited: {expected_vishesa}"})
    elif expected_vishesa:
        missing = expected_vishesa - actual_vishesa
        checks.append({"check": "vishesa_inherited", "status": "warn",
                        "detail": f"missing vishesa: {missing}"})

    all_targets = {t for targets in actual_edges.values() for t in targets}
    ghosts = [t for t in all_targets if t not in known and not t.endswith("-mantra") and " " not in t]
    checks.append({"check": "no_ghosts",
                   "status": "warn" if ghosts else "ok",
                   "detail": f"targets not in om5: {ghosts[:5]}" if ghosts else "all targets resolve"})

    shabda_nodes = shabda_mod.load_all(root)
    s = shabda_nodes.get(name)
    if s and s.get("fields", {}).get("word"):
        checks.append({"check": "shabda_word", "status": "ok",
                        "detail": f"word: {s['fields']['word']}"})
    elif source == "live" and "naama" in actual_edges:
        checks.append({"check": "shabda_word", "status": "ok",
                        "detail": "naama edges present (engine-injected)"})
    else:
        checks.append({"check": "shabda_word", "status": "info",
                        "detail": "no shabda word: entry (may be auto-generated)"})

    statuses = [c["status"] for c in checks]
    overall = "fail" if "fail" in statuses else "warn" if "warn" in statuses else "ok"
    return {"name": name, "status": overall, "source": source,
            "qualifier": qualifier, "base": base,
            "checks": checks, "expected": expected["static_edges"], "actual": actual_edges}


def gen_candidates(base_name, root=None):
    """List valid generation targets for a base concept."""
    nodes = om5.load_all(root)
    base_node = nodes.get(base_name)
    if not base_node:
        return {"error": f"base '{base_name}' not found", "candidates": []}

    base_edges = om5.edges_by_relation(base_node)
    known = set(nodes.keys())
    valid = VALID_QUALIFIERS_PER_BASE.get(base_name, set())
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
    """Gap report: compounds that exist as avastha but not in om5, by domain."""
    nodes = om5.load_all(root)
    known = set(nodes.keys())

    gaps_by_domain = defaultdict(list)
    for name, node in nodes.items():
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
                gaps_by_domain[domain].append({
                    "name": compound, "base": name, "qualifier": q,
                    "in_validity": q in valid, "type": "avastha_only",
                })
        for q in valid - set(avastha):
            compound = f"{q}-{name}"
            if compound not in known:
                gaps_by_domain[domain].append({
                    "name": compound, "base": name, "qualifier": q,
                    "in_validity": True, "type": "validity_only",
                })

    return {
        "total_gaps": sum(len(v) for v in gaps_by_domain.values()),
        "by_domain": {d: gaps for d, gaps in sorted(gaps_by_domain.items(), key=lambda x: -len(x[1]))},
    }


# ---------------------------------------------------------------------------
# Pratipaksha pair completeness
# ---------------------------------------------------------------------------

def pratipaksha_analysis(root=None):
    """Analyze inverse operation pairs for completeness."""
    nodes = om5.load_all(root)
    pairs = []
    seen = set()

    for name, node in sorted(nodes.items()):
        domain = node.get("domain", "")
        if "math" not in domain:
            continue
        for e in node.get("edges", []):
            if e["relation"] == "pratipaksha":
                target = e["target"]
                pair = tuple(sorted([name, target]))
                if pair not in seen:
                    seen.add(pair)
                    target_exists = target in nodes
                    bidirectional = False
                    if target_exists:
                        for te in nodes[target].get("edges", []):
                            if te["relation"] == "pratipaksha" and te["target"] == name:
                                bidirectional = True
                                break
                    pairs.append({
                        "a": name, "b": target, "domain": domain,
                        "b_exists": target_exists, "bidirectional": bidirectional,
                        "self_inverse": name == target,
                    })

    has_inverse = {p["a"] for p in pairs} | {p["b"] for p in pairs}
    missing_inverses = [
        {"name": name, "domain": node.get("domain", "")}
        for name, node in sorted(nodes.items())
        if "math" in node.get("domain", "") and "/operations" in node.get("domain", "")
        and name not in has_inverse
    ]

    return {
        "pairs": pairs, "pair_count": len(pairs),
        "self_inverse": [p for p in pairs if p["self_inverse"]],
        "unidirectional": [p for p in pairs if not p["bidirectional"] and not p["self_inverse"]],
        "missing_inverses": missing_inverses, "missing_count": len(missing_inverses),
    }
