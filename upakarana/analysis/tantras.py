"""tantras.py — Tantra pattern classification and concept grounding.

Categorizes tantras by computational pattern.
Checks if tantras are grounded in sangati/kosha concepts.
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
