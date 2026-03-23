"""ghosts.py — Find nodes referenced as edge targets but never defined.

A ghost is a name that appears as an edge target in some om5 node
but has no om5 file of its own. These are broken references —
every graph walk that hits a ghost silently returns nothing.

Not all ghosts are problems:
- Short names like 'in', 'of', 'is', 'at' are English prepositions
  used as compound tokens in slokas, not intended as graph nodes.
- OCaml primitive names like 'mul', 'add', 'sub' appear in krama
  edges — they're resolved by the engine, not the graph.
- domain-* prefixed names are expected (dynamic domain markers).

The actionable ghosts are structural concepts referenced by many
nodes — things like 'matra', 'float', 'kaala', 'vector', 'sphoTa'.
"""

from collections import defaultdict
from upakarana.parsers import om5

# Names that look like ghosts but are expected (primitives, prepositions, etc.)
EXPECTED_GHOSTS = {
    # OCaml eval primitives (resolved by engine, not graph)
    "add", "sub", "mul", "div", "sqrt", "sin", "cos", "tan",
    "log", "abs", "neg", "floor", "ceil", "min", "max", "mod",
    "asin", "acos", "atan", "exp", "half", "double", "square",
    "power", "factorial", "sum", "product",
    # English words used as compound tokens
    "in", "of", "at", "is", "the", "a", "an", "to", "for",
    "from", "by", "on", "with", "and", "or", "not", "as",
    "no", "if", "so", "up", "do", "we", "it", "be", "he",
    # Type names (OCaml types, not graph concepts)
    "int", "string", "bool", "unit", "list",
    # Punctuation/symbols from sloka text
    "(", ")", "+", "=", "→", "—", "...", "*", "/", "-",
    ">", "<", "≤", "≥", "≠", "×", "÷",
}


def find_ghosts(root=None, include_expected=False):
    """Find ghost nodes: referenced but not defined.

    By default excludes:
    - expected ghosts (primitives, prepositions)
    - disambiguation collisions (node exists as 'kosha/math/matra'
      but is referenced as 'matra' — the engine resolves these)
    Set include_expected=True for the full raw list.
    """
    nodes = om5.load_all(root)
    names = set(nodes.keys())

    # Build set of bare names that exist under domain-prefixed keys
    # e.g., 'matra' exists as 'kosha/math/matra' and 'sangati/pramana/matra'
    bare_names = set()
    for k in names:
        if "/" in k:
            bare = k.rsplit("/", 1)[-1]
            bare_names.add(bare)

    refs = defaultdict(list)
    for name, node in nodes.items():
        for e in node["edges"]:
            t = e["target"]
            if t not in names and not t.startswith("domain-"):
                if include_expected or t not in EXPECTED_GHOSTS:
                    # Skip if this is a disambiguation collision
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
    """High-impact ghosts: referenced by 5+ nodes, multi-layer.

    These are the ones worth creating — each one unblocks many edge walks.
    """
    result = find_ghosts(root)
    return [g for g in result["ghosts"]
            if g["ref_count"] >= min_refs and len(g["layers"]) >= 2]
