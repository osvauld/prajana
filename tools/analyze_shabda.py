#!/usr/bin/env python3
"""
analyze_shabda.py — complete surface-to-graph vocabulary analysis.

Scans all .om files in brahman for shabda lines and extracts:
  - All structured key:value pairs (name:, word:, eval:, math-op:, etc.)
  - Surface word aliases and their target nodes
  - Word collisions (same word → multiple nodes)
  - eval: map (graph op node → OCaml primitive name)
  - math-op, constants-key, parse-arity mappings
  - Rich nodes (4+ keys), sparse nodes (no shabda), orphan shabda
  - Cross-reference with tantra string refs from analysis.json
  - Graph edge type shabda coverage

Optionally reads /tmp/analysis.json for tantra cross-reference.

Usage:
    python3 tools/analyze_shabda.py [--brahman ../brahman] [--json]
    python3 tools/analyze_shabda.py --json | jq '.eval_ops'
    python3 tools/analyze_shabda.py --json | jq '.word_collisions'
"""

import json, re, glob, os, sys, argparse
from collections import defaultdict, Counter

BRAHMAN_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "brahman"
)

KEY_MEANINGS = {
    "name": "English label / display name",
    "word": "surface word alias (O(1) lookup)",
    "eval": "OCaml primitive dispatch name",
    "parse-arity": "parser arity override",
    "math-op": "math operation identifier",
    "constants-key": "physics/math constant lookup key",
    "role": "grammatical role",
    "rel": "grammatical relation type",
    "unit": "unit of measurement",
    "ring-op": "algebraic ring operation",
    "symmetric": "relation symmetry flag",
    "transitive": "relation transitivity flag",
    "reflexive": "relation reflexivity flag",
    "antisymmetric": "relation antisymmetry",
    "involutive": "relation involutivity",
    "congruence": "congruence relation flag",
    "composable": "composability flag",
    "dual": "dual relation name",
    "anuvada-setu": "translation bridge identifier",
    "degree": "algebraic degree",
    "invertible": "invertibility flag",
    "inverse": "inverse operation name",
    "per-element": "element-wise operation flag",
}

# edge types used by tantras — check if each has a shabda surface path
TANTRA_EDGE_TYPES = [
    "sankhya",
    "satya",
    "mithya",
    "vishesa",
    "prathama-vibhakti",
    "shashthi-vibhakti",
    "viraam",
    "rashi",
    "rashi-bandha",
    "matra",
    "asprista-sankhya",
    "derived-by",
    "sought",
    "sought-of",
    "greater-than",
    "viveka-sankhya",
    "direct-match",
    "vidhi-kaala",
    "sandhi-rename",
    "derived-sankhya",
    "relative-velocity",
]

SHABDA_LINE_RE = re.compile(r"^\s*shabda\s+(.+)", re.MULTILINE)
PAIR_RE = re.compile(r"([a-z_-]+):([^\s,]+)")
WORD_RE = re.compile(r"\b([a-z][a-z0-9-]{1,})\b")
FIRST_WORD_RE = re.compile(r"^([a-z]+)\s+([a-z][a-z0-9-]*)", re.MULTILINE)
STOP_WORDS = {"and", "or", "the", "a", "of", "for", "to", "in", "is"}


def collect(brahman_dir: str) -> dict:
    shabda_by_node = {}
    key_frequency = Counter()
    word_frequency = Counter()
    word_to_nodes = defaultdict(list)
    word_aliases = {}
    eval_ops = {}
    math_ops = {}
    constants = {}
    parse_arities = {}
    multi_word = []
    orphans = []

    for path in sorted(
        glob.glob(os.path.join(brahman_dir, "**", "*.om"), recursive=True)
    ):
        try:
            content = open(path).read()
        except:
            continue
        rel = os.path.relpath(path, brahman_dir)
        m = FIRST_WORD_RE.search(content)
        if not m:
            continue
        node_type, node_name = m.group(1), m.group(2)
        layer = rel.split("/")[0]

        for sm in SHABDA_LINE_RE.finditer(content):
            raw = sm.group(1).strip()

            # structured key:value pairs
            pairs = {}
            for pm in PAIR_RE.finditer(raw):
                k, v = pm.group(1), pm.group(2)
                pairs.setdefault(k, []).append(v)
                key_frequency[k] += 1

            # plain words (non-key:value tokens)
            cleaned = PAIR_RE.sub("", raw)
            plain = []
            for wm in WORD_RE.finditer(cleaned):
                w = wm.group(1)
                if len(w) >= 2 and w not in STOP_WORDS:
                    plain.append(w)
                    word_frequency[w] += 1
                    word_to_nodes[w].append(node_name)
                    word_aliases[w] = node_name

            # word: key — explicit surface aliases
            for wv in pairs.get("word", []):
                for w in re.split(r"[,\s]+", wv):
                    w = w.strip()
                    if w:
                        word_frequency[w] += 1
                        word_to_nodes[w].append(node_name)
                        word_aliases[w] = node_name

            # special keys
            if "eval" in pairs:
                eval_ops[node_name] = pairs["eval"][0]
            if "math-op" in pairs:
                math_ops[node_name] = pairs["math-op"][0]
            if "constants-key" in pairs:
                constants[node_name] = pairs["constants-key"][0]
            if "parse-arity" in pairs:
                try:
                    parse_arities[node_name] = int(pairs["parse-arity"][0])
                except:
                    pass

            if not pairs and not plain:
                orphans.append({"node": node_name, "raw": raw, "file": rel})

            all_words = plain + [
                w for wv in pairs.get("word", []) for w in re.split(r"[,\s]+", wv) if w
            ]
            if len(all_words) >= 3:
                multi_word.append(
                    {"node": node_name, "words": all_words[:8], "file": rel}
                )

            if node_name not in shabda_by_node:
                shabda_by_node[node_name] = {
                    "type": node_type,
                    "layer": layer,
                    "file": rel,
                    "keys": {},
                    "all_words": [],
                }
            d = shabda_by_node[node_name]
            for k, vs in pairs.items():
                d["keys"].setdefault(k, []).extend(vs)
            d["all_words"].extend(all_words)

    word_collisions = {
        w: list(set(ns)) for w, ns in word_to_nodes.items() if len(set(ns)) > 1
    }
    rich = {
        n: {"keys": list(d["keys"].keys()), "wc": len(d["all_words"])}
        for n, d in shabda_by_node.items()
        if len(d["keys"]) >= 4
    }
    sparse = [
        n for n, d in shabda_by_node.items() if not d["keys"] and not d["all_words"]
    ]

    return {
        "total_shabda_nodes": len(shabda_by_node),
        "total_unique_words": len(word_frequency),
        "total_word_aliases": len(word_aliases),
        "total_eval_ops": len(eval_ops),
        "total_math_ops": len(math_ops),
        "total_constants": len(constants),
        "word_collision_count": len(word_collisions),
        "key_frequency": dict(key_frequency.most_common()),
        "word_frequency_top": dict(word_frequency.most_common(100)),
        "word_collisions": word_collisions,
        "eval_ops": eval_ops,
        "math_ops": math_ops,
        "constants": constants,
        "parse_arities": parse_arities,
        "word_aliases": dict(list(sorted(word_aliases.items()))[:500]),
        "multi_word_nodes": multi_word[:80],
        "orphan_shabda": orphans[:50],
        "rich_nodes": rich,
        "sparse_nodes": sparse[:100],
        "shabda_by_layer": dict(
            Counter(d["layer"] for d in shabda_by_node.values()).most_common()
        ),
        "shabda_by_type": dict(
            Counter(d["type"] for d in shabda_by_node.values()).most_common()
        ),
    }


def print_report(s: dict, analysis_path: str = "/tmp/analysis.json"):
    SEP = "═" * 72

    print(SEP)
    print("  SHABDA ANALYSIS — SURFACE-TO-GRAPH VOCABULARY")
    print(SEP)
    print(f"""
  shabda nodes:            {s["total_shabda_nodes"]}
  unique surface words:    {s["total_unique_words"]}
  word aliases (word:key): {s["total_word_aliases"]}
  eval: ops (OCaml prim):  {s["total_eval_ops"]}
  math-op entries:         {s["total_math_ops"]}
  constants-key entries:   {s["total_constants"]}
  word collisions:         {s["word_collision_count"]}
""")

    print("── KEY FREQUENCY ────────────────────────────────────────────────────")
    for k, c in s["key_frequency"].items():
        print(f"  {k:<22} {c:>5}  {KEY_MEANINGS.get(k, '')}")

    print("\n── LAYER DISTRIBUTION ───────────────────────────────────────────────")
    for layer, c in s["shabda_by_layer"].items():
        print(f"  {layer:<25} {c} nodes")

    print("\n── TOP 40 SURFACE WORDS ─────────────────────────────────────────────")
    for w, c in list(s["word_frequency_top"].items())[:40]:
        node = s["word_aliases"].get(w, "?")
        print(f"  {w:<25} {c:>4}×  → {node}")

    print("\n── WORD COLLISIONS (ambiguous) ──────────────────────────────────────")
    for w, nodes in list(s["word_collisions"].items())[:30]:
        print(f"  {w:<25} → {nodes}")

    print("\n── eval: MAP (graph op → OCaml primitive) ───────────────────────────")
    for node, op in sorted(s["eval_ops"].items()):
        print(f"  {node:<35} → {op}")

    print("\n── math-op MAP ──────────────────────────────────────────────────────")
    for node, op in sorted(s["math_ops"].items()):
        print(f"  {node:<35} → {op}")

    print("\n── constants-key MAP ────────────────────────────────────────────────")
    for node, key in sorted(s["constants"].items()):
        print(f"  {node:<35} constants-key: {key}")

    print("\n── parse-arity OVERRIDES ────────────────────────────────────────────")
    for node, arity in sorted(s["parse_arities"].items()):
        print(f"  {node:<35} arity: {arity}")

    print("\n── RICH NODES (4+ keys) ─────────────────────────────────────────────")
    for node, d in sorted(
        s["rich_nodes"].items(), key=lambda x: len(x[1]["keys"]), reverse=True
    )[:20]:
        print(f"  {node:<35} keys={d['keys'][:6]}")

    print("\n── MULTI-WORD NODES (3+ surface aliases) ────────────────────────────")
    for m in s["multi_word_nodes"][:20]:
        print(f"  {m['node']:<35} {m['words'][:5]}")

    print("\n── ORPHAN SHABDA ────────────────────────────────────────────────────")
    for o in s["orphan_shabda"][:15]:
        print(f"  {o['node']:<35} raw: {o['raw'][:55]}")

    print("\n── GRAPH EDGE TYPES: shabda coverage ────────────────────────────────")
    rich_keys = {k for d in s["rich_nodes"].values() for k in d["keys"]}
    for e in sorted(TANTRA_EDGE_TYPES):
        found = e in s["word_aliases"] or e in rich_keys
        status = "✓" if found else "✗ NO shabda path"
        print(f"  {e:<35} {status}")

    print("\n── SPARSE NODES (no shabda) ─────────────────────────────────────────")
    for n in s["sparse_nodes"][:30]:
        print(f"  {n}")

    # tantra cross-reference if analysis.json available
    try:
        a = json.load(open(analysis_path))
        tantra_strs = set(a["tantra"]["global_str_refs"].keys())
        shabda_words = set(s["word_aliases"].keys())
        edge_set = set(TANTRA_EDGE_TYPES)
        overlap = sorted(tantra_strs & shabda_words - edge_set - {"", " "})
        tantra_only = sorted(
            (tantra_strs - shabda_words - edge_set)
            - {
                "",
                "(",
                ")",
                " ",
                ", ",
                "-",
                "anuvada-setu",
                "constants-key",
                "math-op",
                "prashna",
                "rashi",
                "rel-sankhya",
                "physics-constants",
            }
        )
        print("\n── TANTRA ↔ SHABDA CROSS-REFERENCE ──────────────────────────────────")
        print(f"  words in both: {len(overlap)}")
        for w in overlap[:20]:
            freq = a["tantra"]["global_str_refs"].get(w, 0)
            print(f"    {w:<30} tantra={freq}×  node={s['word_aliases'].get(w, '?')}")
        print(f"\n  tantra refs NOT in shabda: {len(tantra_only)}")
        for w in tantra_only[:15]:
            print(f"    {w}")
    except:
        pass

    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--brahman", default=BRAHMAN_DEFAULT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--analysis", default="/tmp/analysis.json")
    args = parser.parse_args()

    result = collect(args.brahman)

    if args.json:
        json.dump(result, sys.stdout, indent=2)
    else:
        print_report(result, args.analysis)
