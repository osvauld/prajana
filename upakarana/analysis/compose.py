"""compose.py — Avastha composition analysis.

Discovers compound nodes, traces composition chains, finds base concepts
and their variants, identifies potential generators, and maps qualifier
categories to sangati roots.

The core idea: a compound node like angular-velocity is decomposable into
qualifier(angular) + base(velocity). The base concept's om5 could declare
(avastha angular kona) to generate this node automatically.
"""

from collections import defaultdict
from upakarana.parsers import om5, shabda as shabda_mod


# Qualifier → sangati context mapping
# These are the known avastha qualifiers and what graph context they carry
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

# Suffix → visheshanam type mapping
SUFFIX_TYPE = {
    "mantra": ("kriya", "computational rule"),
    "varga": ("vishesa", "classification group"),
    "sthalam": ("sthita", "domain location"),
    "setu": ("kriya", "bridge/interface"),
    "step": ("krama", "integration step"),
    "decay": ("kshaya", "diminishing process"),
}


def decompose_name(name, known_names):
    """Try to decompose a compound name into qualifier+base or base+suffix."""
    if "-" not in name:
        return None

    result = {"name": name, "prefix": None, "suffix": None, "base": None}

    # Try prefix decomposition: qualifier-base
    parts = name.split("-", 1)
    prefix, rest = parts[0], parts[1]
    if rest in known_names and prefix in QUALIFIER_CONTEXT:
        cat, context = QUALIFIER_CONTEXT[prefix]
        result["prefix"] = {
            "qualifier": prefix, "base": rest,
            "category": cat, "context": context,
        }
        result["base"] = rest

    # Try suffix decomposition: base-type
    parts = name.rsplit("-", 1)
    stem, suffix = parts[0], parts[1]
    if stem in known_names and suffix in SUFFIX_TYPE:
        vish, desc = SUFFIX_TYPE[suffix]
        result["suffix"] = {
            "type": suffix, "base": stem,
            "visheshanam": vish, "description": desc,
        }
        if result["base"] is None:
            result["base"] = stem

    if result["prefix"] is None and result["suffix"] is None:
        return None
    return result


def find_compounds(root=None):
    """Find all decomposable compound nodes."""
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

    bases = defaultdict(lambda: {
        "prefix_variants": [], "suffix_variants": [],
        "layer": "", "domain": "",
    })

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


def composition_chains(root=None):
    """Find multi-level composition chains (e.g. velocity → angular-velocity → angular-velocity-mantra)."""
    nodes = om5.load_all(root)
    names = set(nodes.keys())
    compounds = find_compounds(root)

    # Build parent→children map
    children = defaultdict(list)
    for c in compounds:
        if c["prefix"]:
            children[c["prefix"]["base"]].append(c["name"])
        if c["suffix"]:
            children[c["suffix"]["base"]].append(c["name"])

    # Find chains of depth > 1
    chains = []

    def walk(node, path):
        if node in children:
            for child in children[node]:
                if child not in path:
                    walk(child, path + [child])
        if len(path) > 2:
            chains.append(path)

    # Start from nodes that are bases but not compounds themselves
    compound_names = {c["name"] for c in compounds}
    pure_bases = [b for b in children if b not in compound_names]
    for b in pure_bases:
        walk(b, [b])

    return chains


def synthetic_nodes(root=None):
    """Find nodes in shabda but not in om5 (shabda-only stubs) that match composition patterns."""
    nodes = om5.load_all(root)
    shabda_nodes = shabda_mod.load_all(root)
    static_names = set(nodes.keys())

    synthetic = []
    for name in sorted(shabda_nodes.keys()):
        if name not in static_names:
            d = decompose_name(name, static_names)
            if d:
                synthetic.append(d)
    return synthetic


def potential_generators(root=None):
    """For each base concept, what avastha generators COULD be declared
    based on existing compound nodes?"""
    bases = base_concepts(root)
    generators = {}

    for base_name, info in bases.items():
        gens = []
        for v in info["prefix_variants"]:
            p = v["prefix"]
            gens.append({
                "qualifier": p["qualifier"],
                "context": p["context"],
                "category": p["category"],
                "generates": v["name"],
                "exists": True,
            })
        if gens:
            generators[base_name] = {
                "generators": gens,
                "domain": info["domain"],
                "total_variants": len(info["prefix_variants"]) + len(info["suffix_variants"]),
            }

    return generators


def qualifier_categories(root=None):
    """Group all qualifiers by category with counts."""
    compounds = find_compounds(root)
    cats = defaultdict(lambda: defaultdict(list))

    for c in compounds:
        if c["prefix"]:
            p = c["prefix"]
            cats[p["category"]][p["qualifier"]].append(c["name"])

    return {cat: dict(quals) for cat, quals in cats.items()}


def _edges_by_rel(node):
    """Group a node's edges by relation type."""
    d = {}
    for e in node.get("edges", []):
        d.setdefault(e["relation"], []).append(e["target"])
    return d


def inheritance_analysis(root=None):
    """For each compound, compare edges to its base — what's inherited, overridden, unique.

    Returns list of dicts with:
      name, base, swarupa_to_base, vishesa_match,
      inherited (rel→targets shared with base),
      overridden (rel→targets in compound but different from base),
      only_compound (rels only in compound),
      only_base (rels only in base),
      generatable (bool — could a generator produce this node?)
    """
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

        base_vishesa = set(base_edges.get("vishesa", []))
        comp_vishesa = set(comp_edges.get("vishesa", []))

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

        # A node is "generatable" if it mostly inherits from base
        # with minimal unique edges (swarupa→base + sthita + maybe 1-2 overrides)
        unique_edge_count = sum(len(v) for v in only_comp.values())
        override_count = sum(len(v) for v in overridden.values())
        generatable = unique_edge_count <= 4 and override_count <= 6

        results.append({
            "name": comp_name,
            "base": base_name,
            "qualifier": c["prefix"]["qualifier"],
            "category": c["prefix"]["category"],
            "swarupa_to_base": has_swarupa_to_base,
            "vishesa_match": base_vishesa == comp_vishesa,
            "inherited": inherited,
            "overridden": overridden,
            "only_compound": only_comp,
            "only_base": only_base,
            "unique_edge_count": unique_edge_count,
            "override_count": override_count,
            "generatable": generatable,
        })

    return results


def validity_matrix(root=None):
    """Which (qualifier, base) pairs actually exist and which are physically valid.

    Returns dict with:
      existing: set of (qualifier, base) pairs that exist as nodes
      valid: set of (qualifier, base) pairs deemed valid (exist + curated additions)
      by_base: {base: [valid qualifiers]}
      by_qualifier: {qualifier: [valid bases]}
    """
    nodes = om5.load_all(root)
    names = set(nodes.keys())
    compounds = find_compounds(root)

    existing = set()
    for c in compounds:
        if c.get("prefix"):
            existing.add((c["prefix"]["qualifier"], c["prefix"]["base"]))

    # Determine valid categories per domain
    # Physics quantities: temporal + spatial make sense
    # Forces: domain qualifiers (gravitational, electric, etc.) + spatial (net, centripetal)
    # Energy: domain qualifiers (kinetic, potential, etc.)
    # Bonds: bond qualifiers only
    # Oscillation: intensity (damped) only
    domain_categories = {}
    for base in set(b for _, b in existing):
        node = nodes.get(base, {})
        domain = node.get("domain", "")
        cats = set()
        for q, b in existing:
            if b == base:
                cat = QUALIFIER_CONTEXT.get(q, (None,))[0]
                if cat:
                    cats.add(cat)
        domain_categories[base] = cats

    # Build by_base and by_qualifier from existing
    by_base = defaultdict(list)
    by_qualifier = defaultdict(list)
    for q, b in existing:
        by_base[b].append(q)
        by_qualifier[q].append(b)

    # Identify missing but valid: same category as existing qualifiers for that base
    valid = set(existing)
    missing_valid = []
    for base, cats in domain_categories.items():
        for q, (cat, ctx) in QUALIFIER_CONTEXT.items():
            if cat in cats and (q, base) not in existing:
                candidate = f"{q}-{base}"
                # Only add if the candidate doesn't already exist as a node
                # AND the base is a physics quantity (not a suffix type like mantra)
                if candidate not in names and base in names:
                    node = nodes.get(base, {})
                    layer = node.get("layer", "")
                    if layer == "kosha":
                        missing_valid.append({
                            "qualifier": q,
                            "base": base,
                            "category": cat,
                            "context": ctx,
                            "name": candidate,
                        })

    return {
        "existing": existing,
        "existing_count": len(existing),
        "valid_missing": missing_valid,
        "valid_missing_count": len(missing_valid),
        "by_base": dict(by_base),
        "by_qualifier": dict(by_qualifier),
        "domain_categories": dict(domain_categories),
    }


def edge_inheritance_rules(root=None):
    """Derive what edge inheritance rules a generator should use.

    Analyzes all existing compounds to find patterns:
    - Which relations are always inherited from base?
    - Which are always overridden?
    - Which are compound-specific (never in base)?
    """
    ia = inheritance_analysis(root)

    # Count how often each relation appears in each bucket
    inherited_counts = defaultdict(int)
    overridden_counts = defaultdict(int)
    only_comp_counts = defaultdict(int)
    only_base_counts = defaultdict(int)
    total = len(ia)

    for item in ia:
        for rel in item["inherited"]:
            inherited_counts[rel] += 1
        for rel in item["overridden"]:
            overridden_counts[rel] += 1
        for rel in item["only_compound"]:
            only_comp_counts[rel] += 1
        for rel in item["only_base"]:
            only_base_counts[rel] += 1

    all_rels = set(inherited_counts) | set(overridden_counts) | set(only_comp_counts) | set(only_base_counts)

    rules = {}
    for rel in sorted(all_rels):
        inh = inherited_counts.get(rel, 0)
        ovr = overridden_counts.get(rel, 0)
        ocp = only_comp_counts.get(rel, 0)
        obp = only_base_counts.get(rel, 0)

        # Classify: mostly inherited → copy, mostly overridden → skip, mixed → case-by-case
        if inh > ovr and inh > ocp:
            action = "inherit"
        elif ovr > inh and ovr > ocp:
            action = "override"
        elif ocp > inh and ocp > ovr:
            action = "compound-specific"
        elif obp > 0 and inh == 0 and ovr == 0:
            action = "base-only"
        else:
            action = "mixed"

        rules[rel] = {
            "action": action,
            "inherited": inh,
            "overridden": ovr,
            "only_compound": ocp,
            "only_base": obp,
            "total": total,
        }

    return rules


def word_form_inventory(root=None):
    """What word forms each existing compound has in shabda,
    and what a generator would need to produce.

    Returns:
      existing_words: {node_name: shabda fields}
      missing_words: [nodes with no shabda]
      generator_word_needs: what forms auto-generated nodes need
    """
    nodes = om5.load_all(root)
    shabda_nodes = shabda_mod.load_all(root)
    compounds = find_compounds(root)

    existing_words = {}
    missing_words = []

    for c in compounds:
        if not c.get("prefix"):
            continue
        name = c["name"]
        if name in shabda_nodes:
            existing_words[name] = shabda_nodes[name]
        else:
            missing_words.append(name)

    # What word forms does a generated node need?
    # Analyze existing shabda entries to find the pattern
    field_counts = defaultdict(int)
    for name, fields in existing_words.items():
        for key in fields:
            field_counts[key] += 1

    return {
        "existing_words": existing_words,
        "existing_count": len(existing_words),
        "missing_words": missing_words,
        "missing_count": len(missing_words),
        "field_frequency": dict(field_counts),
    }


def generatability_report(root=None):
    """High-level report: which compounds can be auto-generated, which need hand-writing.

    Groups compounds into:
      auto: generatable with just swarupa→base + sthita→context + vishesa copy
      semi: generatable but need a few overrides declared
      manual: too many unique edges, must remain hand-written
    """
    ia = inheritance_analysis(root)

    auto = []
    semi = []
    manual = []

    for item in ia:
        if item["generatable"] and item["unique_edge_count"] <= 2:
            auto.append(item)
        elif item["generatable"]:
            semi.append(item)
        else:
            manual.append(item)

    return {
        "auto": auto,
        "auto_count": len(auto),
        "semi": semi,
        "semi_count": len(semi),
        "manual": manual,
        "manual_count": len(manual),
    }


# Curated validity: which (category, base) pairs are physically meaningful.
# This prevents nonsense like "friction-collision" or "drag-constant".
# If a (category, base) is not listed here, it's not valid for generation.
VALID_COMBINATIONS = {
    # temporal: quantities that have initial/final/average states
    ("temporal", "velocity"),
    ("temporal", "acceleration"),
    ("temporal", "momentum"),
    ("temporal", "displacement"),
    ("temporal", "energy"),
    ("temporal", "force"),
    ("temporal", "position"),
    # spatial: quantities with angular/linear/radial/tangential variants
    ("spatial", "velocity"),
    ("spatial", "acceleration"),
    ("spatial", "displacement"),
    ("spatial", "momentum"),
    ("spatial", "force"),
    # domain: energy types by source
    ("domain", "energy"),
    ("domain", "force"),
    ("domain", "power"),
    ("domain", "constant"),
    ("domain", "collision"),
    # intensity: damped/rated variants
    ("intensity", "oscillation"),
    ("intensity", "nuclear-force"),
    ("intensity", "torque"),
    ("intensity", "power"),
    # bond: chemistry only
    ("bond", "bond"),
}

# Curated subset of qualifiers valid per base (more restrictive than category alone)
# Only listed where the full category is too broad
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


def curated_validity(root=None):
    """Like validity_matrix but uses curated VALID_COMBINATIONS + VALID_QUALIFIERS_PER_BASE
    to produce only physically meaningful candidates."""
    nodes = om5.load_all(root)
    names = set(nodes.keys())
    compounds = find_compounds(root)

    existing = set()
    for c in compounds:
        if c.get("prefix"):
            existing.add((c["prefix"]["qualifier"], c["prefix"]["base"]))

    # Build candidate list from curated validity
    candidates = []
    for base, allowed_quals in VALID_QUALIFIERS_PER_BASE.items():
        if base not in names:
            continue
        for qualifier in sorted(allowed_quals):
            if qualifier not in QUALIFIER_CONTEXT:
                continue
            cat, ctx = QUALIFIER_CONTEXT[qualifier]
            pair = (qualifier, base)
            candidate_name = f"{qualifier}-{base}"
            is_existing = pair in existing
            in_graph = candidate_name in names

            candidates.append({
                "qualifier": qualifier,
                "base": base,
                "category": cat,
                "context": ctx,
                "name": candidate_name,
                "exists_as_pair": is_existing,
                "in_graph": in_graph,
                "status": "exists" if in_graph else "generate",
            })

    existing_list = [c for c in candidates if c["in_graph"]]
    missing_list = [c for c in candidates if not c["in_graph"]]

    # Group missing by base
    missing_by_base = defaultdict(list)
    for m in missing_list:
        missing_by_base[m["base"]].append(m)

    return {
        "existing": existing_list,
        "existing_count": len(existing_list),
        "missing": missing_list,
        "missing_count": len(missing_list),
        "missing_by_base": dict(missing_by_base),
        "total_candidates": len(candidates),
    }


# Logic/reasoning inference patterns that could be generated from base rules.
# Each pattern: (name, base_rule, transform, description)
# These are NOT qualifier+base compounds — they're inference rule variants.
LOGIC_GENERATORS = {
    # Base inference patterns (already exist or should exist as mantra nodes)
    "inference": {
        "base": "inference",
        "layer": "kosha/math/logic/structures",
        "existing": ["modus-ponens"],
        "missing": [
            {
                "name": "modus-tollens",
                "description": "if A->B and not-B, then not-A",
                "relation_to_base": "contrapositive of modus-ponens",
                "edges": {"swarupa": "inference", "janya": "implication",
                          "pratipaksha": "modus-ponens", "kriya": "pratishedha"},
            },
            {
                "name": "disjunctive-syllogism",
                "description": "if A-or-B and not-A, then B",
                "relation_to_base": "elimination on disjunction",
                "edges": {"swarupa": "inference", "janya": "disjunction",
                          "kriya": "pratishedha"},
            },
            {
                "name": "hypothetical-syllogism",
                "description": "if A->B and B->C, then A->C",
                "relation_to_base": "chain rule for implications",
                "edges": {"swarupa": "inference", "janya": "implication",
                          "kriya": "krama"},
            },
            {
                "name": "contrapositive",
                "description": "A->B iff not-B->not-A",
                "relation_to_base": "equivalence transform of implication",
                "edges": {"swarupa": "inference", "janya": "implication",
                          "abheda": "modus-tollens", "kriya": "pratishedha"},
            },
        ],
    },
    # Boolean algebra transforms
    "boolean": {
        "base": "logic-varga",
        "layer": "kosha/math/logic/operations",
        "existing": ["conjunction", "disjunction", "negation"],
        "missing": [
            {
                "name": "de-morgan-and",
                "description": "not(A and B) = not-A or not-B",
                "relation_to_base": "conjunction-negation duality",
                "edges": {"swarupa": "inference", "janya": "conjunction",
                          "abheda": "disjunction", "kriya": "pratishedha"},
            },
            {
                "name": "de-morgan-or",
                "description": "not(A or B) = not-A and not-B",
                "relation_to_base": "disjunction-negation duality",
                "edges": {"swarupa": "inference", "janya": "disjunction",
                          "abheda": "conjunction", "kriya": "pratishedha"},
            },
            {
                "name": "double-negation",
                "description": "not(not-A) = A",
                "relation_to_base": "negation self-inverse",
                "edges": {"swarupa": "inference", "janya": "negation",
                          "kriya": "pratishedha", "pratipaksha": "negation"},
            },
        ],
    },
    # Quantifier patterns
    "quantifier": {
        "base": "quantifier",
        "layer": "kosha/math/logic/operations",
        "existing": ["quantifier"],
        "missing": [
            {
                "name": "universal-quantifier",
                "description": "for all X, P(X) — walks entire swarupa chain",
                "relation_to_base": "universal instantiation",
                "edges": {"swarupa": "quantifier", "kriya": "swarupa-walk",
                          "yukta": "vrnda"},
            },
            {
                "name": "existential-quantifier",
                "description": "there exists X such that P(X)",
                "relation_to_base": "existential witness",
                "edges": {"swarupa": "quantifier", "kriya": "viveka",
                          "pratipaksha": "universal-quantifier"},
            },
        ],
    },
    # Transitivity patterns (graph walk rules)
    "transitivity": {
        "base": "krama",
        "layer": "sangati",
        "existing": [],
        "missing": [
            {
                "name": "transitive-swarupa",
                "description": "if A swarupa B and B swarupa C then A swarupa C",
                "relation_to_base": "IS-A chain transitivity",
                "edges": {"swarupa": "krama", "janya": "swarupa",
                          "kriya": "swarupa-walk"},
            },
            {
                "name": "transitive-comparison",
                "description": "if A > B and B > C then A > C",
                "relation_to_base": "ordering chain transitivity",
                "edges": {"swarupa": "krama", "janya": "viveka",
                          "kriya": "viveka"},
            },
        ],
    },
}


def logic_generator_analysis(root=None):
    """Analyze which logic/reasoning nodes exist and which could be generated.

    Unlike physics generators (qualifier+base compounds), logic generators
    are inference rule patterns — each with a base rule and transform.
    """
    nodes = om5.load_all(root)
    names = set(nodes.keys())

    results = []
    for group_name, group in LOGIC_GENERATORS.items():
        existing_in_graph = []
        missing_from_graph = []

        for name in group["existing"]:
            exists = name in names
            existing_in_graph.append({"name": name, "in_graph": exists})

        for item in group["missing"]:
            exists = item["name"] in names
            if exists:
                existing_in_graph.append({"name": item["name"], "in_graph": True})
            else:
                missing_from_graph.append(item)

        results.append({
            "group": group_name,
            "base": group["base"],
            "layer": group["layer"],
            "existing": existing_in_graph,
            "existing_count": len(existing_in_graph),
            "missing": missing_from_graph,
            "missing_count": len(missing_from_graph),
        })

    total_existing = sum(r["existing_count"] for r in results)
    total_missing = sum(r["missing_count"] for r in results)

    return {
        "groups": results,
        "total_existing": total_existing,
        "total_missing": total_missing,
    }


# Space-lift prefixes: operations lifted from scalars to higher algebraic spaces
SPACE_PREFIXES = {
    "vec": ("vector", "kosha/math/geometry/operations"),
    "mat": ("matrix", "kosha/math/geometry/operations"),
    "quat": ("quaternion", "kosha/math/geometry/operations"),
    "complex": ("complex", "kosha/math/number/operations"),
    "set": ("set", "kosha/math/set/operations"),
}

# Which scalar ops can meaningfully lift to each space
LIFTABLE_OPS = {
    "vec": {"add", "scale", "norm", "cross", "dot", "neg", "abs",
            "subtraction", "addition", "multiplication"},
    "mat": {"add", "scale", "transpose", "multiplication", "inverse",
            "determinant", "norm", "trace"},
    "quat": {"mul", "conjugate", "norm", "inverse", "to-rotation", "slerp"},
    "complex": {"mul", "magnitude", "phase", "conjugate", "add", "neg",
                "abs", "square", "square-root", "exponential", "logarithm"},
    "set": {"union", "intersection", "difference", "complement", "product",
            "subset", "membership"},
}


def space_lift_analysis(root=None):
    """Analyze which scalar operations have been lifted to vector/matrix/etc spaces,
    and which lifts are missing.

    Space lifting: scalar-op → space-op (e.g., addition → vec-add, mat-add)
    These are generated by: base_op.om5 declaring (avastha vec kshetra) etc.
    """
    nodes = om5.load_all(root)
    names = set(nodes.keys())

    results = []
    for prefix, (space_name, domain) in SPACE_PREFIXES.items():
        existing = []
        missing = []
        possible = LIFTABLE_OPS.get(prefix, set())

        # Find existing space-prefixed ops
        for name in sorted(names):
            if name.startswith(prefix + "-"):
                base = name[len(prefix) + 1:]
                existing.append({
                    "name": name,
                    "base_op": base,
                    "in_graph": True,
                })

        existing_bases = {e["base_op"] for e in existing}

        # Find missing lifts
        for op in sorted(possible):
            lifted_name = f"{prefix}-{op}"
            if op not in existing_bases and lifted_name not in names:
                missing.append({
                    "name": lifted_name,
                    "base_op": op,
                    "space": space_name,
                })

        results.append({
            "space": space_name,
            "prefix": prefix,
            "domain": domain,
            "existing": existing,
            "existing_count": len(existing),
            "missing": missing,
            "missing_count": len(missing),
        })

    return results


def pratipaksha_analysis(root=None):
    """Analyze inverse operation pairs (pratipaksha edges) in math.

    These are a form of generation: if op exists, its inverse could be auto-generated
    with pratipaksha→op + inverse krama. Identifies gaps.
    """
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
                    # Check if target also points back
                    bidirectional = False
                    if target_exists:
                        for te in nodes[target].get("edges", []):
                            if te["relation"] == "pratipaksha" and te["target"] == name:
                                bidirectional = True
                                break
                    pairs.append({
                        "a": name,
                        "b": target,
                        "domain": domain,
                        "b_exists": target_exists,
                        "bidirectional": bidirectional,
                        "self_inverse": name == target,
                    })

    # Find ops that SHOULD have inverses but don't
    missing_inverses = []
    has_inverse = {p["a"] for p in pairs} | {p["b"] for p in pairs}
    for name, node in sorted(nodes.items()):
        domain = node.get("domain", "")
        if "math" not in domain or "/operations" not in domain:
            continue
        if name not in has_inverse:
            missing_inverses.append({"name": name, "domain": domain})

    return {
        "pairs": pairs,
        "pair_count": len(pairs),
        "self_inverse": [p for p in pairs if p["self_inverse"]],
        "unidirectional": [p for p in pairs if not p["bidirectional"] and not p["self_inverse"]],
        "missing_inverses": missing_inverses,
        "missing_count": len(missing_inverses),
    }


def karma_varga_cross(root=None):
    """Math: which op × structure pairs are valid for specialization.

    An operation (karma edge → varga) can be specialized per structure
    (vishesa edge → varga). E.g. addition ∈ number-varga, integers ∈ number-varga
    → addition-in-integers is valid.

    Validity filter: an op×structure pair is valid when:
    1. The op's arity matches the structure (unary ops skip multi-element structures)
    2. The structure has the properties the op requires (e.g. commutativity)
    3. The op and structure share yukta/abheda connections (graph proximity)

    Returns ops, structures, and valid cross-product per varga.
    """
    nodes = om5.load_all(root)
    shabda_nodes = shabda_mod.load_all(root)

    # Collect karma (op→varga) and vishesa (structure→varga)
    ops_by_varga = defaultdict(list)
    structs_by_varga = defaultdict(list)
    for name, node in nodes.items():
        edges = _edges_by_rel(node)
        for v in edges.get("karma", []):
            ops_by_varga[v].append(name)
        for v in edges.get("vishesa", []):
            structs_by_varga[v].append(name)

    # Build connectivity index for proximity filter
    node_neighbors = {}
    for name, node in nodes.items():
        edges = _edges_by_rel(node)
        neighbors = set()
        for rel in ("yukta", "abheda", "sthita", "swarupa", "siddha", "janya", "phala"):
            for t in edges.get(rel, []):
                neighbors.add(t)
        node_neighbors[name] = neighbors

    # Collect lakshana (property→varga) for property-requirement filter
    props_by_varga = defaultdict(set)
    for name, node in nodes.items():
        for v in _edges_by_rel(node).get("lakshana", []):
            props_by_varga[v].add(name)

    # Collect rahita (lacks) for exclusion
    lacks = defaultdict(set)
    for name, node in nodes.items():
        for t in _edges_by_rel(node).get("rahita", []):
            lacks[name].add(t)

    results = {}
    total_valid = 0
    total_filtered = 0
    total_existing = 0
    names = set(nodes.keys())

    for varga in sorted(set(ops_by_varga) & set(structs_by_varga)):
        ops = sorted(ops_by_varga[varga])
        structs = sorted(structs_by_varga[varga])
        varga_props = props_by_varga.get(varga, set())
        pairs = []
        for op in ops:
            op_neighbors = node_neighbors.get(op, set())
            op_shabda = shabda_nodes.get(op, {})
            op_fields = op_shabda.get("fields", {}) if isinstance(op_shabda, dict) else {}
            op_arity = op_fields.get("arity", "")

            for struct in structs:
                struct_neighbors = node_neighbors.get(struct, set())
                struct_lacks = lacks.get(struct, set())

                # Filter 1: skip if structure explicitly lacks the op or its properties
                if op in struct_lacks:
                    total_filtered += 1
                    continue

                # Filter 2: graph proximity — op and structure share at least one neighbor
                # or the structure references the op's varga
                shared = op_neighbors & struct_neighbors
                op_refs_struct = struct in op_neighbors
                struct_refs_op = op in struct_neighbors
                proximate = bool(shared) or op_refs_struct or struct_refs_op

                # Filter 3: skip varga-internal nodes (the varga itself, meta nodes)
                if struct == varga or struct.endswith("-varga"):
                    total_filtered += 1
                    continue

                compound = f"{op}-in-{struct}"
                exists = compound in names
                if exists:
                    total_existing += 1

                valid = proximate or exists
                if valid:
                    total_valid += 1
                else:
                    total_filtered += 1

                pairs.append({
                    "op": op, "structure": struct,
                    "compound": compound, "exists": exists,
                    "valid": valid, "proximate": proximate,
                })

        valid_pairs = [p for p in pairs if p["valid"]]
        results[varga] = {
            "ops": ops, "structures": structs,
            "op_count": len(ops), "struct_count": len(structs),
            "cross": len(pairs),
            "valid": len(valid_pairs),
            "filtered": len(pairs) - len(valid_pairs),
            "existing": sum(1 for p in pairs if p["exists"]),
            "pairs": valid_pairs,
        }

    return {
        "vargas": results,
        "total_valid": total_valid,
        "total_filtered": total_filtered,
        "total_existing": total_existing,
        "total_missing": total_valid - total_existing,
    }


def lakshana_validity(root=None):
    """Math: property × structure truth table.

    A property (lakshana edge → varga) applies to structures in that varga.
    E.g. commutativity → number-varga, integers ∈ number-varga
    → commutativity holds for integers.

    Some properties DON'T hold for all structures in a varga
    (e.g. commutativity holds for reals but not matrices).
    This function generates the truth table; the graph can encode
    exceptions via pratipaksha or rahita edges.
    """
    nodes = om5.load_all(root)

    props_by_varga = defaultdict(list)
    structs_by_varga = defaultdict(list)
    for name, node in nodes.items():
        edges = _edges_by_rel(node)
        for v in edges.get("lakshana", []):
            props_by_varga[v].append(name)
        for v in edges.get("vishesa", []):
            structs_by_varga[v].append(name)

    # Check for rahita (lacks/without) edges that negate property×structure
    exceptions = set()  # (property, structure) pairs where property does NOT hold
    for name, node in nodes.items():
        edges = _edges_by_rel(node)
        for lacking in edges.get("rahita", []):
            exceptions.add((lacking, name))

    results = {}
    for varga in sorted(set(props_by_varga) & set(structs_by_varga)):
        props = sorted(props_by_varga[varga])
        structs = sorted(structs_by_varga[varga])
        matrix = {}
        for prop in props:
            row = {}
            for struct in structs:
                if (prop, struct) in exceptions:
                    row[struct] = False
                else:
                    row[struct] = True  # default: property holds
            matrix[prop] = row
        results[varga] = {
            "properties": props, "structures": structs,
            "matrix": matrix,
            "total_cells": len(props) * len(structs),
            "exceptions": len([(p, s) for p in props for s in structs
                               if (p, s) in exceptions]),
        }

    return {"vargas": results, "total_exceptions": len(exceptions)}


def declension_matrix(root=None):
    """Grammar: noun declension potential.

    subanta (noun) × vibhakti (case) × vachana (number) = inflected form.
    Returns the full matrix and what exists vs what can be generated.
    """
    nodes = om5.load_all(root)

    # Find subanta children (nouns)
    subanta_nodes = []
    for name, node in nodes.items():
        if "subanta" in _edges_by_rel(node).get("swarupa", []):
            subanta_nodes.append(name)

    # Find vibhakti (case) values
    vibhakti = []
    for name, node in nodes.items():
        if node.get("domain", "").endswith("vibhakti") and name != "vibhakti":
            vibhakti.append(name)

    # Find vachana (number) values — connected via amsha→vachana
    vachana = []
    for name, node in nodes.items():
        edges = _edges_by_rel(node)
        if ("vachana" in edges.get("amsha", [])
                or "vachana" in edges.get("swarupa", [])) and name != "vachana":
            vachana.append(name)

    # Build matrix
    total = len(subanta_nodes) * len(vibhakti) * len(vachana)

    return {
        "subanta": sorted(subanta_nodes),
        "subanta_count": len(subanta_nodes),
        "vibhakti": sorted(vibhakti),
        "vibhakti_count": len(vibhakti),
        "vachana": sorted(vachana),
        "vachana_count": len(vachana),
        "total_forms": total,
    }


def conjugation_matrix(root=None):
    """Grammar: verb conjugation potential.

    tinanta (verb) × kaala (tense) × vachana (number) × purusa (person) = conjugated form.
    Returns the full matrix dimensions.
    """
    nodes = om5.load_all(root)

    # Find tinanta children (verbs)
    tinanta_nodes = []
    for name, node in nodes.items():
        if "tinanta" in _edges_by_rel(node).get("swarupa", []):
            tinanta_nodes.append(name)

    # Find kaala (tense) — children of sangati/grammar/kaala
    kaala = []
    for name, node in nodes.items():
        domain = node.get("domain", "")
        if domain == "sangati/grammar/kaala" and name != "sangati/grammar/kaala/kaala":
            # Clean name for display
            short = name.split("/")[-1] if "/" in name else name
            kaala.append(short)

    # Find vachana and purusa
    vachana = []
    purusa = []
    for name, node in nodes.items():
        edges = _edges_by_rel(node)
        if ("vachana" in edges.get("amsha", [])
                or "vachana" in edges.get("swarupa", [])) and name != "vachana":
            vachana.append(name)
        if name.endswith("-purusa") and name != "purusa":
            purusa.append(name)

    total = len(tinanta_nodes) * len(kaala) * len(vachana) * len(purusa)

    return {
        "tinanta": sorted(tinanta_nodes),
        "tinanta_count": len(tinanta_nodes),
        "kaala": sorted(kaala),
        "kaala_count": len(kaala),
        "vachana": sorted(vachana),
        "vachana_count": len(vachana),
        "purusa": sorted(purusa),
        "purusa_count": len(purusa),
        "total_forms": total,
    }


def samasa_classifier(root=None):
    """Classify existing compound nodes by samasa type.

    tatpurusha: qualifier determines base (kinetic-energy = energy of kinetic type)
    dvandva:    co-equal pair (mass-velocity = mass AND velocity)
    bahuvrihi:  possessive (red-car = entity possessing red+car)
    karmadharaya: adjective+noun (angular-velocity = velocity that is angular)

    Classification rules (graph-derived):
    - If compound has swarupa→base: tatpurusha or karmadharaya
    - If compound has janya for BOTH parts: dvandva
    - If qualifier is in QUALIFIER_CONTEXT: karmadharaya (descriptive)
    - If suffix is in SUFFIX_TYPE: tatpurusha (determinative)
    """
    nodes = om5.load_all(root)
    names = set(nodes.keys())
    compounds = find_compounds(root)

    classified = []
    for c in compounds:
        name = c["name"]
        node = nodes.get(name, {})
        edges = _edges_by_rel(node)
        samasa_type = "unknown"

        if c.get("prefix"):
            qualifier = c["prefix"]["qualifier"]
            base = c["prefix"]["base"]
            has_swarupa_to_base = base in edges.get("swarupa", [])

            # Check if both parts exist as independent nodes with janya/phala
            both_janya = (qualifier in names and base in names
                          and _edges_by_rel(nodes.get(qualifier, {})).get("janya")
                          and _edges_by_rel(nodes.get(base, {})).get("janya"))

            if both_janya and not has_swarupa_to_base:
                samasa_type = "dvandva"
            elif qualifier in QUALIFIER_CONTEXT and has_swarupa_to_base:
                samasa_type = "karmadharaya"
            elif has_swarupa_to_base:
                samasa_type = "tatpurusha"

        elif c.get("suffix"):
            samasa_type = "tatpurusha"

        classified.append({
            "name": name,
            "samasa": samasa_type,
            "prefix": c.get("prefix"),
            "suffix": c.get("suffix"),
        })

    by_type = defaultdict(list)
    for item in classified:
        by_type[item["samasa"]].append(item["name"])

    return {
        "classified": classified,
        "by_type": {t: sorted(names) for t, names in by_type.items()},
        "counts": {t: len(names) for t, names in by_type.items()},
    }


def collision_analysis(root=None):
    """Detect same-name nodes from different domains in old brahman.

    When multiple om5 files define the same node name, Prakriti.join merges
    their edges. Returns ALL source definitions so generators can emit
    every instance (the engine merges at load time).

    Returns each collision with per-source edges so nothing is lost.
    """
    import glob
    import os
    import re
    from upakarana.paths import BRAHMAN

    # Pass 1: find which files define which node names
    files = glob.glob(os.path.join(str(BRAHMAN), "**", "*.om5"), recursive=True)
    name_to_files = defaultdict(list)
    for f in files:
        with open(f) as fh:
            for line in fh:
                m = re.match(
                    r"\((kosha|sangati|mantra|bhasha)\s+([a-zA-Z][a-zA-Z0-9-]*)", line
                )
                if m:
                    name_to_files[m.group(2)].append(
                        f.replace(str(BRAHMAN) + "/", "")
                    )

    # Pass 2: for collisions, parse each source file to get per-source edges
    collisions = {}
    for name, sources in name_to_files.items():
        if len(sources) <= 1:
            continue
        instances = []
        for src in sources:
            full = os.path.join(str(BRAHMAN), src)
            parsed = om5.parse_multi(full) if hasattr(om5, 'parse_multi') else []
            if not parsed:
                parsed_single = om5.parse(full)
                parsed = [parsed_single] if parsed_single else []
            for node in parsed:
                if node and node.get("name") == name:
                    instances.append({
                        "source": src,
                        "domain": os.path.dirname(src),
                        "layer": node.get("layer", ""),
                        "edges": node.get("edges", []),
                    })
        collisions[name] = {
            "instances": instances,
            "count": len(instances),
            "domains": [inst["domain"] for inst in instances],
        }

    return {
        "collisions": collisions,
        "total": len(collisions),
    }


def derivative_avastha_cross(root=None):
    """Kramanusara × avastha: derivative chain quantities with their qualifiers.

    Each quantity in a derivative chain (displacement → velocity → acceleration)
    has avastha qualifiers (angular, centripetal, etc.). The compounds must
    maintain chain coherence: angular-acceleration kramanusara→ angular-velocity.

    Returns chain-aware generation plan.
    """
    nodes = om5.load_all(root)

    # Build kramanusara forward map (derivative → base)
    krama_fwd = {}
    for name, node in nodes.items():
        for t in _edges_by_rel(node).get("kramanusara", []):
            krama_fwd[name] = t

    # Find chain nodes with avastha
    chain_nodes = set(krama_fwd.keys()) | set(krama_fwd.values())
    results = []

    for name in sorted(chain_nodes):
        node = nodes.get(name, {})
        avastha = _edges_by_rel(node).get("avastha", [])
        if not avastha:
            continue

        derives_from = krama_fwd.get(name)
        derived_by = [k for k, v in krama_fwd.items() if v == name]
        names_set = set(nodes.keys())

        for q in avastha:
            compound = f"{q}-{name}"
            # Check if the chain companion exists
            chain_companion = None
            if derives_from:
                chain_companion = f"{q}-{derives_from}"
            companion_exists = chain_companion in names_set if chain_companion else None

            results.append({
                "base": name,
                "qualifier": q,
                "compound": compound,
                "exists": compound in names_set,
                "derives_from": derives_from,
                "chain_companion": chain_companion,
                "companion_exists": companion_exists,
            })

    return {
        "cross": results,
        "total": len(results),
        "existing": sum(1 for r in results if r["exists"]),
        "missing": sum(1 for r in results if not r["exists"]),
        "chain_coherent": sum(1 for r in results
                              if r["companion_exists"] is True),
        "chain_broken": sum(1 for r in results
                            if r["companion_exists"] is False),
    }


def generation_summary(root=None):
    """Complete generation potential across all domains.

    Combines all analysis functions into one summary with projected counts.
    """
    nodes = om5.load_all(root)
    current = len(nodes)

    # Physics avastha
    avastha_missing = 0
    for name, node in nodes.items():
        for q in _edges_by_rel(node).get("avastha", []):
            if f"{q}-{name}" not in nodes:
                avastha_missing += 1

    # Math karma × varga
    kv = karma_varga_cross(root)

    # Math lakshana
    lv = lakshana_validity(root)
    lakshana_total = sum(v["total_cells"] for v in lv["vargas"].values())

    # Grammar
    decl = declension_matrix(root)
    conj = conjugation_matrix(root)

    # Space lifts
    sl = space_lift_analysis(root)
    lifts_missing = sum(s["missing_count"] for s in sl)

    # Logic
    lg = logic_generator_analysis(root)

    # Pratipaksha
    pp = pratipaksha_analysis(root)

    # Derivative × avastha
    da = derivative_avastha_cross(root)

    # Collisions
    col = collision_analysis(root)

    return {
        "current_nodes": current,
        "physics_avastha_missing": avastha_missing,
        "math_op_structure_total": kv["total_valid"],
        "math_op_structure_missing": kv["total_missing"],
        "math_lakshana_total": lakshana_total,
        "grammar_noun_forms": decl["total_forms"],
        "grammar_verb_forms": conj["total_forms"],
        "space_lifts_missing": lifts_missing,
        "logic_missing": lg["total_missing"],
        "pratipaksha_missing": pp["missing_count"],
        "derivative_avastha_missing": da["missing"],
        "collisions": col["total"],
        "projected_total": (current + avastha_missing + kv["total_missing"]
                            + decl["total_forms"] + conj["total_forms"]
                            + lifts_missing + lg["total_missing"]
                            + da["missing"]),
    }


def _inflect_verb(word):
    """Generate English verb inflections from base form."""
    w = word
    if w.endswith('e'):
        past = w + 'd'
        progressive = w[:-1] + 'ing'
    elif w.endswith('y') and len(w) > 2 and w[-2] not in 'aeiou':
        past = w[:-1] + 'ied'
        progressive = w + 'ing'
    else:
        past = w + 'ed'
        progressive = w + 'ing'
    if w.endswith(('s', 'sh', 'ch', 'x', 'z')):
        singular = w + 'es'
    elif w.endswith('y') and len(w) > 1 and w[-2] not in 'aeiou':
        singular = w[:-1] + 'ies'
    else:
        singular = w + 's'
    return {
        "vartamana-kaala": [w, singular],
        "bhuta-kaala": [past],
        "bhavishya-kaala": [f"will {w}"],
        "shatr-pratyaya": [progressive],
        "kta-pratyaya": [past],
        "eka-vachana": [singular],
        "bahu-vachana": [w],
    }


def _inflect_noun(word):
    """Generate English noun inflections from base form."""
    w = word
    if w.endswith(('s', 'sh', 'ch', 'x', 'z')):
        plural = w + 'es'
    elif w.endswith('y') and len(w) > 1 and w[-2] not in 'aeiou':
        plural = w[:-1] + 'ies'
    else:
        plural = w + 's'
    return {
        "eka-vachana": [w],
        "bahu-vachana": [plural],
    }


# Irregular English verbs — override generated forms
IRREGULAR_VERBS = {
    "copula": {
        "vartamana-kaala": ["is", "am", "are"],
        "bhuta-kaala": ["was", "were"],
        "bhavishya-kaala": ["will be"],
        "shatr-pratyaya": ["being"],
        "kta-pratyaya": ["been"],
        "eka-vachana": ["is", "was"],
        "bahu-vachana": ["are", "were"],
    },
}

# Irregular English nouns
IRREGULAR_NOUNS = {
    "mouse": "mice", "child": "children", "person": "people",
    "datum": "data", "radius": "radii", "vertex": "vertices",
    "matrix": "matrices", "axis": "axes", "index": "indices",
    "stimulus": "stimuli", "nucleus": "nuclei", "thesis": "theses",
}


def grammar_shabda_generator(root=None):
    """Generate grammar-tagged shabda for all bhasha words.

    For each tinanta (verb): tense, number, participle forms.
    For each subanta (noun): singular/plural forms.

    Returns:
      verbs: [{name, base_word, forms: {kaala→words, vachana→words, ...}}]
      nouns: [{name, base_word, forms: {vachana→words}}]
      reverse: {inflected_word → [(base, grammar_tag)]}
    """
    nodes = om5.load_all(root)
    shabda_nodes = shabda_mod.load_all(root)

    verbs = []
    nouns = []
    reverse = defaultdict(list)

    for name, node in nodes.items():
        edges = _edges_by_rel(node)
        swarupa = edges.get("swarupa", [])
        s = shabda_nodes.get(name, {})
        fields = s.get("fields", {}) if isinstance(s, dict) else {}
        word_list = fields.get("word", [])
        if isinstance(word_list, str):
            word_list = [word_list]
        base_word = word_list[0] if word_list else name.replace("-", " ")

        if "tinanta" in swarupa:
            # Verb — find the actual verb stem from shabda word/alias forms
            # Many tinanta nodes are process-nouns (combustion, collision)
            # that classify as verbs in the ontology but aren't English verb stems.
            # We need the real verb root to inflect properly.
            alias_list = fields.get("alias", [])
            if isinstance(alias_list, str):
                alias_list = [alias_list]
            all_forms = word_list + [a.rstrip(",") for a in alias_list
                                     if isinstance(a, str)]

            # Find the best verb stem: look for a form that inflects regularly
            # (ends in -s/-es/-ed/-ing) and extract the stem
            verb_stem = None
            if name in IRREGULAR_VERBS:
                verb_stem = base_word
            else:
                for w in all_forms:
                    w = w.strip().rstrip(",")
                    if not w:
                        continue
                    # Progressive form → stem
                    if w.endswith("ing") and len(w) > 4:
                        stem = w[:-3]
                        if stem.endswith("t") or stem.endswith("n"):
                            verb_stem = stem + "e" if not stem[-1] == stem[-2] else stem
                        else:
                            verb_stem = stem
                        break
                    # 3rd person -s form → stem
                    if w.endswith("es") and len(w) > 3:
                        verb_stem = w[:-2] if w[-3] in "shxz" else w[:-1]
                        break
                    if w.endswith("s") and not w.endswith("ss") and len(w) > 2:
                        verb_stem = w[:-1]
                        break
                    # Past tense -ed → stem
                    if w.endswith("ed") and len(w) > 3:
                        verb_stem = w[:-2] if not w[-3] == w[-4:-3] else w[:-1]
                        break

            if verb_stem is None:
                # No recognizable verb form — skip this process-noun
                continue

            forms = IRREGULAR_VERBS.get(name, _inflect_verb(verb_stem))
            verbs.append({"name": name, "base_word": verb_stem, "forms": forms})
            # Build reverse index
            for tag, words in forms.items():
                for w in words:
                    reverse[w].append((name, tag))

        elif "subanta" in swarupa:
            # Noun
            base_singular = base_word
            if base_singular in IRREGULAR_NOUNS:
                forms = {
                    "eka-vachana": [base_singular],
                    "bahu-vachana": [IRREGULAR_NOUNS[base_singular]],
                }
            else:
                forms = _inflect_noun(base_singular)
            nouns.append({"name": name, "base_word": base_singular, "forms": forms})
            for tag, words in forms.items():
                for w in words:
                    reverse[w].append((name, tag))

    return {
        "verbs": verbs,
        "verb_count": len(verbs),
        "nouns": nouns,
        "noun_count": len(nouns),
        "reverse": dict(reverse),
        "reverse_count": len(reverse),
        "total_forms": sum(sum(len(ws) for ws in v["forms"].values()) for v in verbs)
                      + sum(sum(len(ws) for ws in n["forms"].values()) for n in nouns),
    }


def full_analysis(root=None):
    """Complete composition analysis."""
    compounds = find_compounds(root)
    bases = base_concepts(root)
    chains = composition_chains(root)
    synthetic = synthetic_nodes(root)
    generators = potential_generators(root)
    categories = qualifier_categories(root)

    return {
        "compounds": compounds,
        "compound_count": len(compounds),
        "bases": bases,
        "base_count": len(bases),
        "chains": chains,
        "chain_count": len(chains),
        "synthetic": synthetic,
        "synthetic_count": len(synthetic),
        "generators": generators,
        "generator_count": len(generators),
        "categories": categories,
    }
