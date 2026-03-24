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
