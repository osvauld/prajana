"""cli_tantra4.py — deep analysis of all tantras for abstraction opportunities.

Analyzes: repeated patterns, deep nesting, long expressions, graph queries,
reduce/filter/map chains, signal bus opportunities, and cross-layer commonality.
"""

import os
import re
from collections import defaultdict

from . import tantras
from .paths import YANTRA

TANTRA4_DIR = os.path.join(YANTRA, "tantra4")


def _load_tantra4():
    """Load only tantra4 files."""
    import glob
    result = {}
    for path in sorted(glob.glob(os.path.join(TANTRA4_DIR, "*.tantra3"))):
        parsed = tantras.parse(path)
        if parsed:
            result[parsed["name"]] = parsed
    return result


def _load_all():
    """Load all tantras from all groups."""
    return tantras.load_all()


def _sep(title, width=80):
    return f"\n{'=' * width}\n  {title}\n{'=' * width}\n"


def _nesting_depth(line):
    depth = 0
    max_d = 0
    for ch in line:
        if ch == '(':
            depth += 1
            max_d = max(max_d, depth)
        elif ch == ')':
            depth -= 1
    return max_d


def _extract_graph_queries(source):
    """Find all graph | where ... | collect patterns."""
    return re.findall(
        r'(\w[\w-]*)\s*\|\s*where\s*\[([^\]]+)\]\s*\|[^|]*\|\s*collect\s+([^\n)]+)',
        source
    )


def _extract_reduces(source):
    return re.findall(
        r'reduce\s+([\w-]+)\s+(\[[^\]]*\]|"[^"]*"|\d+)\s*\(fn\s+(\w+)\s+(\w+)\s*->',
        source
    )


def _code_lines(source):
    """Return non-comment, non-header code lines."""
    for line in source.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("--") and not stripped.startswith("tantra3"):
            yield stripped


# ── Analysis functions that work on any tantra set ──────────────────────────


def _analyze_inline_replacements(ts, helpers_only=False):
    """Find inline expressions that could use existing tantra4 helpers."""
    patterns = [
        ('gt (string-length', 'has-text', r'gt\s*\(string-length\s+\w[\w-]*\)\s*0'),
        ('gt (length', 'has-items', r'gt\s*\(length\s+[\w(]'),
        ('to-string (nth t 0)', 'triple-subj', r'to-string\s*\(nth\s+\w+\s+0\)'),
        ('to-string (nth t 2)', 'triple-obj', r'to-string\s*\(nth\s+\w+\s+2\)'),
        ('nth t 1', 'triple-edge', r'(?:eq\s*\()?nth\s+\w+\s+1\)?(?:\s*"|\s*\))'),
        ('filter X eq nth 1', 'triples-by-edge', r'filter\s+\w+\s*\(fn\s+\w+\s*->\s*eq\s*\(nth\s+\w+\s+1\)'),
        ('to-string (word-node', 'word-resolve', r'to-string\s*\(word-node\s+\w+\)'),
        ('eq (string-length X) 0', 'is-empty', r'eq\s*\(string-length\s+\w[\w-]*\)\s*0'),
        ('neq X ""', 'has-text (neq form)', r'neq\s+\w[\w-]*\s+""'),
    ]

    skip_names = {'has-text', 'has-items', 'triple-subj', 'triple-edge',
                  'triple-obj', 'triples-by-edge', 'word-resolve', 'is-empty',
                  'last-concept', 'is-system-concept'}

    print(_sep("INLINE → HELPER OPPORTUNITIES"))
    total_ops = 0
    for desc, helper, pat in patterns:
        hits = []
        for name, t in sorted(ts.items()):
            if name in skip_names:
                continue
            if helpers_only and t.get("group") == "tantra4":
                continue
            for i, line in enumerate(t["source"].split("\n"), 1):
                stripped = line.strip()
                if stripped.startswith("--"):
                    continue
                if re.search(pat, stripped):
                    hits.append((name, t.get("group", "?"), i, stripped[:100]))
        if hits:
            total_ops += len(hits)
            print(f"  '{desc}' → {helper}  ({len(hits)} occurrences)")
            for tname, group, ln, text in hits:
                print(f"    {tname} [{group}] L{ln}: {text}")
            print()
    print(f"  Total replaceable: {total_ops}")


def _analyze_graph_queries(ts):
    """Find all graph queries and group by edge type."""
    print(_sep("GRAPH QUERIES BY EDGE TYPE"))

    edge_queries = defaultdict(list)  # edge -> [(tantra, group, line, full_query)]
    for name, t in sorted(ts.items()):
        queries = _extract_graph_queries(t["source"])
        for src_var, destructure, collect_expr in queries:
            full = f"{src_var} | where [{destructure.strip()}] | collect {collect_expr.strip()}"
            edge_match = re.search(r'eq\s+\w+\s+"([\w-]+)"', destructure + " " + collect_expr)
            if edge_match:
                edge = edge_match.group(1)
                edge_queries[edge].append((name, t.get("group", "?"), full[:100]))

    for edge, hits in sorted(edge_queries.items(), key=lambda x: -len(x[1])):
        if len(hits) < 2:
            continue
        groups = sorted(set(g for _, g, _ in hits))
        print(f"  \"{edge}\"  ({len(hits)} queries across {', '.join(groups)})")
        for tname, group, query in hits:
            print(f"    {tname} [{group}]: {query}")
        print()


def _analyze_speech_reads(ts):
    """Find shabda 'anuvada-setu' reads — speech template pattern."""
    print(_sep("SPEECH TEMPLATE READS (shabda \"anuvada-setu\" ...)"))

    speech_reads = defaultdict(list)  # tantra -> [key, key, ...]
    for name, t in sorted(ts.items()):
        for m in re.finditer(r'shabda\s+"anuvada-setu"\s+"([\w-]+)"', t["source"]):
            speech_reads[name].append(m.group(1))

    total = sum(len(v) for v in speech_reads.values())
    unique_keys = sorted(set(k for keys in speech_reads.values() for k in keys))
    print(f"  {total} reads across {len(speech_reads)} tantras")
    print(f"  Unique keys: {', '.join(unique_keys)}")
    print()
    for name, keys in sorted(speech_reads.items(), key=lambda x: -len(x[1])):
        group = ts[name].get("group", "?")
        print(f"  {name} [{group}]: {', '.join(keys)}")


def _analyze_viveka_branching(ts):
    """Find is-viveka branching — emit layer duality."""
    print(_sep("VIVEKA/PHYSICS BRANCHING (cond is-viveka ...)"))

    for name, t in sorted(ts.items()):
        src = t["source"]
        viveka_conds = len(re.findall(r'cond\s+is-viveka\b', src))
        not_viveka = len(re.findall(r'not\s+is-viveka\b', src))
        if viveka_conds + not_viveka >= 1:
            group = t.get("group", "?")
            print(f"  {name} [{group}] ({t['lines']}L): "
                  f"{viveka_conds} viveka branches, {not_viveka} not-viveka branches")


def _analyze_signal_opportunities(ts):
    """Find data threaded through params that could be signals."""
    print(_sep("SIGNAL BUS OPPORTUNITIES"))

    # Find tantras with 4+ takes params (data threading)
    print("\n  HIGH-ARITY TANTRAS (≥4 takes params — data threading candidates)")
    for name, t in sorted(ts.items()):
        takes = t.get("takes", [])
        if len(takes) >= 4:
            group = t.get("group", "?")
            params = ", ".join(takes)
            print(f"    {name} [{group}] ({t['lines']}L): takes {len(takes)} — {params}")

    # Find repeated proof-graph edge reads
    print("\n\n  PROOF EDGE READS (same edge queried in multiple tantras)")
    proof_edges = ["greater-than", "viveka-concept", "viveka-direction",
                   "viveka-sankhya", "derived-by", "derived-sankhya",
                   "sought", "sought-of", "prathama-vibhakti",
                   "count-step", "count-entity", "count-container"]

    for edge in proof_edges:
        readers = []
        for name, t in ts.items():
            if f'"{edge}"' in t["source"]:
                readers.append((name, t.get("group", "?")))
        if len(readers) >= 2:
            groups = sorted(set(g for _, g in readers))
            names = ", ".join(f"{n}[{g}]" for n, g in sorted(readers))
            print(f"    \"{edge}\": {names}")


def _analyze_scan_patterns(ts):
    """Find reduce-based state machines (scan pattern)."""
    print(_sep("STATE MACHINE SCANS (reduce with multi-element state)"))

    for name, t in sorted(ts.items()):
        reduces = _extract_reduces(t["source"])
        for inp, seed, acc, elem in reduces:
            # Multi-element state = list seed with 2+ elements
            if seed.startswith("[") and "," in seed:
                group = t.get("group", "?")
                n_elems = seed.count(",") + 1
                print(f"  {name} [{group}]: reduce {inp} {seed[:50]}... "
                      f"({n_elems}-element state)")


def _analyze_entity_value_scan(ts):
    """Find the entity-value pairing pattern across tantras."""
    print(_sep("ENTITY-VALUE PAIRING (scan for entity + sankhya)"))

    for name, t in sorted(ts.items()):
        src = t["source"]
        has_sankhya = '"sankhya"' in src
        has_entity_track = any(x in src for x in ['"prathama-vibhakti"', '"satya"', 'active'])
        has_reduce = 'reduce' in src
        if has_sankhya and has_entity_track and has_reduce:
            group = t.get("group", "?")
            print(f"  {name} [{group}] ({t['lines']}L)")


def _analyze_cross_layer(ts):
    """Find patterns shared across layer boundaries."""
    print(_sep("CROSS-LAYER SHARED PATTERNS"))

    # Group tantras by group
    by_group = defaultdict(dict)
    for name, t in ts.items():
        by_group[t.get("group", "?")][name] = t

    # Find expression patterns that appear in 2+ groups
    expr_patterns = [
        ('filter graph/triples by edge', r'filter\s+\w+\s*\(fn\s+\w+\s*->\s*eq\s*\(nth\s+\w+\s+1\)\s*"([\w-]+)"'),
        ('walk + member check', r'member\s+"[\w-]+"\s*\(walk\s'),
        ('unique + map + filter', r'unique\s*\(map\s*\(filter'),
        ('concat with shabda reads', r'concat\s+.*shabda\s+"anuvada-setu"'),
        ('list-join call', r'list-join\s'),
        ('reduce to empty string', r'reduce\s+\w+\s+""\s*\(fn\s+\w+\s+\w+\s*->'),
        ('reduce to empty list', r'reduce\s+\w+\s+\[\]\s*\(fn\s+\w+\s+\w+\s*->'),
        ('bound-state call', r'bound-state\s'),
        ('prathama-sparsha call', r'prathama-sparsha\s'),
        ('weave-strands / format-strand', r'weave-strands\s|format-strand\s'),
    ]

    for desc, pat in expr_patterns:
        hits_by_group = defaultdict(list)
        for name, t in ts.items():
            if re.search(pat, t["source"]):
                hits_by_group[t.get("group", "?")].append(name)
        if len(hits_by_group) >= 2:
            total = sum(len(v) for v in hits_by_group.values())
            groups = ", ".join(f"{g}({len(v)})" for g, v in sorted(hits_by_group.items()))
            print(f"  {desc}: {total}x across {groups}")
            for g, names in sorted(hits_by_group.items()):
                for n in names:
                    print(f"    {n} [{g}]")
            print()


def _analyze_collisions(ts):
    """Find tantra4 helper names that collide with variable names in other tantras."""
    t4 = {n: t for n, t in ts.items() if t.get("group") == "tantra4"}
    non_t4 = {n: t for n, t in ts.items() if t.get("group") != "tantra4"}
    helper_names = set(t4.keys())

    print(_sep("NAME COLLISIONS — tantra4 helpers vs variable names in other tantras"))

    collisions = []
    for helper in sorted(helper_names):
        for tname, t in non_t4.items():
            src = t["source"]
            if re.search(rf'^{re.escape(helper)}\s*=', src, re.MULTILINE) or \
               re.search(rf'\blet\s+{re.escape(helper)}\s*=', src):
                collisions.append((helper, tname, t.get("group", "?")))

    if collisions:
        for helper, tname, group in collisions:
            print(f"  COLLISION: \"{helper}\" shadows variable in {tname} [{group}]")
            for tname2, t in non_t4.items():
                if tname2 != tname:
                    continue
                for i, line in enumerate(t["source"].split("\n"), 1):
                    if re.search(rf'^{re.escape(helper)}\s*=', line) or \
                       re.search(rf'\blet\s+{re.escape(helper)}\s*=', line):
                        print(f"    L{i}: {line.strip()[:100]}")
        print(f"\n  Total: {len(collisions)} collisions")
    else:
        print("  No collisions found.")
    print()

    print(_sep("POTENTIAL BUILTIN SHADOWS"))
    from . import tantras as t_mod
    keywords = t_mod._KEYWORDS
    for helper in sorted(helper_names):
        if helper in keywords:
            print(f"  WARNING: \"{helper}\" matches a tantra3 keyword/builtin")

    existing_names = set(non_t4.keys())
    overlap = helper_names & existing_names
    if overlap:
        print(_sep("DUPLICATE TANTRA NAMES (helper exists in another group too)"))
        for name in sorted(overlap):
            other = non_t4[name]
            print(f"  \"{name}\" exists in both tantra4/ and {other.get('group', '?')}/")
    print()


def _analyze_idioms(ts):
    """Find repeated multi-word expression patterns across all tantras."""
    composites = [
        (r'to-string\s*\(nth\s+\w+\s+\d+\)', 'to-string (nth X N)'),
        (r'eq\s*\(nth\s+\w+\s+\d+\)\s*"[\w-]+"', 'eq (nth X N) "edge"'),
        (r'eq\s*\(to-string\s+\w+\)\s*"[\w-]+"', 'eq (to-string X) "str"'),
        (r'gt\s*\(string-length\s+\w+\)\s*0', 'gt (string-length X) 0'),
        (r'gt\s*\(length\s+', 'gt (length ...) N'),
        (r'eq\s+e\s+"[\w-]+"', 'eq e "edge-type"'),
        (r'eq\s*\(string-length\s+\w+\)\s*0', 'eq (string-length X) 0'),
        (r'not\s*\(exists\s+\w+\)', 'not (exists X)'),
        (r'cond\s*\(exists\s+\w+\)', 'cond (exists X)'),
        (r'append\s+\w+\s*\[', 'append X [...]'),
        (r'nth\s*\(.*\|\s*where.*\|\s*collect', 'nth (query) 0 — first-match'),
        (r'concat\s+say-\w+\s+": "', 'concat say-X ": " — speech prefix'),
        (r'filter\s+\w+\s*\(fn\s+\w+\s*->\s*gt\s*\(string-length', 'filter non-empty strings'),
        (r'map\s*\(walk\s+\w+\s+"[\w-]+"\)', 'map (walk X "edge") — chain to strings'),
    ]

    print(_sep("REPEATED EXPRESSION IDIOMS (all tantras)"))

    idiom_counts = defaultdict(list)
    for pattern, label in composites:
        for name, t in sorted(ts.items()):
            matches = re.findall(pattern, t["source"])
            if matches:
                idiom_counts[label].append((name, t.get("group", "?"), len(matches)))

    for label, occurrences in sorted(idiom_counts.items(), key=lambda x: -sum(c for _, _, c in x[1])):
        total = sum(c for _, _, c in occurrences)
        if total < 3:
            continue
        groups = sorted(set(g for _, g, _ in occurrences))
        print(f"  {label}  ({total}x across {', '.join(groups)})")
        for tname, group, count in occurrences:
            print(f"    {tname} [{group}]: {count}")
        print()

    # Exact repeated sub-expressions
    print(_sep("EXACT REPEATED SUB-EXPRESSIONS (≥ 3 occurrences, all tantras)"))
    subexpr_counts = defaultdict(list)
    for name, t in ts.items():
        for m in re.finditer(r'\([^()]{20,80}\)', t["source"]):
            expr = m.group(0)
            if expr.startswith('("') or expr.startswith("(--"):
                continue
            subexpr_counts[expr].append((name, t.get("group", "?")))

    for expr, hits in sorted(subexpr_counts.items(), key=lambda x: -len(x[1])):
        if len(hits) < 3:
            continue
        unique = sorted(set(f"{n}[{g}]" for n, g in hits))
        print(f"  {expr[:100]}")
        print(f"    {len(hits)}x in: {', '.join(unique)}")
        print()


def _analyze_first_match(ts):
    """Find nth (query) 0 pattern — single-result graph queries."""
    print(_sep("FIRST-MATCH PATTERN: nth (graph | where ... | collect X) 0"))

    hits = []
    for name, t in sorted(ts.items()):
        for i, line in enumerate(t["source"].split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            if re.search(r'nth\s*\(.*\|\s*where.*\|\s*collect', stripped):
                group = t.get("group", "?")
                hits.append((name, group, i, stripped[:120]))

    print(f"  {len(hits)} occurrences — candidate: query-first tantra\n")
    for tname, group, ln, text in hits:
        print(f"  {tname} [{group}] L{ln}: {text}")
    print()


def _analyze_viveka_proof_reads(ts):
    """Find repeated viveka proof edge reads across emit tantras."""
    print(_sep("VIVEKA PROOF READS (repeated edge queries across emit layer)"))

    viveka_edges = ["greater-than", "viveka-concept", "viveka-direction",
                    "viveka-sankhya", "sought", "sought-of"]

    for edge in viveka_edges:
        readers = []
        for name, t in sorted(ts.items()):
            src = t["source"]
            # Count actual query reads, not just string mentions
            count = len(re.findall(
                rf'(?:graph|expanded)\s*\|\s*where.*eq\s+\w+\s+"{re.escape(edge)}"', src))
            if count == 0:
                count = len(re.findall(rf'eq\s+e\s+"{re.escape(edge)}"', src))
            if count > 0:
                readers.append((name, t.get("group", "?"), count))
        if len(readers) >= 2:
            total = sum(c for _, _, c in readers)
            print(f"  \"{edge}\" ({total} reads across {len(readers)} tantras)")
            for n, g, c in readers:
                print(f"    {n} [{g}]: {c}")
            print()

    # Show which viveka values are computed in multiple tantras
    print("  DUPLICATED VIVEKA COMPUTATIONS:")
    viveka_vars = ["vk-winner", "vk-loser", "vc-concept", "vk-direction",
                   "gt-triples", "sought-label"]
    for var in viveka_vars:
        readers = []
        for name, t in sorted(ts.items()):
            if re.search(rf'^{re.escape(var)}\s*=', t["source"], re.MULTILINE) or \
               re.search(rf'\blet\s+{re.escape(var)}\s*=', t["source"]):
                readers.append((name, t.get("group", "?")))
        if len(readers) >= 2:
            names = ", ".join(f"{n}[{g}]" for n, g in readers)
            print(f"    {var}: computed in {names}")


def _analyze_param_threading(ts):
    """Trace data flow through call chains to find signal candidates."""
    print(_sep("PARAMETER THREADING DEPTH"))

    # Find tantras that pass data from takes → calls → takes
    # High fan-out = data threading (signal candidate)
    for name, t in sorted(ts.items()):
        takes = t.get("takes", [])
        calls = t.get("calls", [])
        if len(takes) < 3:
            continue

        # Check which takes params appear in call args
        src = t["source"]
        passed_params = []
        for param in takes:
            # Count how many times this param is used as an argument to other calls
            uses = len(re.findall(rf'\b{re.escape(param)}\b', src)) - 1  # -1 for 'takes' line
            if uses >= 2:
                passed_params.append((param, uses))

        if passed_params:
            group = t.get("group", "?")
            total_threading = sum(u for _, u in passed_params)
            if total_threading >= 5:
                print(f"  {name} [{group}] ({t['lines']}L, takes {len(takes)})")
                for param, uses in sorted(passed_params, key=lambda x: -x[1]):
                    print(f"    {param}: used {uses}x")
                print()


def _analyze_wordnode_collisions(ts):
    """Find variable names that collide with word-node aliases (dangerous)."""
    print(_sep("WORD-NODE VARIABLE COLLISIONS"))
    print("  (variables whose names resolve to DIFFERENT graph nodes via word-node)")
    print("  These cause silent value corruption — the variable gets the node value.\n")

    # Known dangerous mappings from our debugging
    known_dangerous = {
        "role": "op-role", "pair": "pair", "hit": "kshaya",
        "found": "vriddhi", "base": "acid-base", "name": "(broken-param)",
    }

    # Extract all variable names from all tantras
    all_vars = defaultdict(list)  # var_name -> [(tantra, group, line_no)]
    for tname, t in ts.items():
        for i, line in enumerate(t["source"].split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            # takes X
            m = re.match(r'^takes\s+([\w-]+)', stripped)
            if m:
                all_vars[m.group(1)].append((tname, t.get("group", "?"), i, "takes"))
            # let X =
            for m in re.finditer(r'\blet\s+([\w-]+)\s*=', stripped):
                all_vars[m.group(1)].append((tname, t.get("group", "?"), i, "let"))
            # fn X Y ->
            for m in re.finditer(r'\bfn\s+([\w-]+(?:\s+[\w-]+)*)\s*->', stripped):
                for p in m.group(1).split():
                    all_vars[p].append((tname, t.get("group", "?"), i, "lambda"))

    # Check known dangerous ones
    print("  KNOWN DANGEROUS (from prior debugging):")
    for var, node in sorted(known_dangerous.items()):
        if var in all_vars:
            tantras_using = sorted(set(f"{n}[{g}]" for n, g, _, kind in all_vars[var]
                                       if kind in ("takes", "let")))
            if tantras_using:
                print(f"    {var} → {node}: {', '.join(tantras_using[:5])}")
    print()

    # Flag any 'takes' params that match common node names
    print("  TAKES PARAMS MATCHING COMMON WORDS (check word-node):")
    common_words = {"name", "type", "value", "result", "state", "role", "pair",
                    "base", "found", "hit", "direction", "field", "rate", "time",
                    "angle", "height", "mass", "force", "energy", "frequency",
                    "period", "velocity", "acceleration", "gravity", "sentence",
                    "word", "number", "unit", "label", "concept", "entity"}
    for var in sorted(common_words):
        takes_uses = [(n, g) for n, g, _, kind in all_vars.get(var, []) if kind == "takes"]
        if takes_uses:
            tantras_str = ", ".join(f"{n}[{g}]" for n, g in sorted(set(takes_uses)))
            print(f"    takes {var}: {tantras_str}")


def _analyze_emit_duality(ts):
    """Analyze the viveka/physics split in emit tantras for unification."""
    print(_sep("EMIT LAYER DUALITY — viveka vs physics paths"))

    emit_tantras = {n: t for n, t in ts.items() if t.get("group") == "emit"}

    for name, t in sorted(emit_tantras.items()):
        src = t["source"]
        viveka_lines = []
        physics_lines = []

        for i, line in enumerate(src.split("\n"), 1):
            stripped = line.strip()
            if "is-viveka" in stripped or "viveka" in stripped.lower():
                viveka_lines.append(i)
            if any(x in stripped for x in ["derived-by", "mantra", "sankhya", "derived"]):
                physics_lines.append(i)

        if viveka_lines and physics_lines:
            v_pct = len(viveka_lines) * 100 // t["lines"]
            p_pct = len(physics_lines) * 100 // t["lines"]
            print(f"  {name} ({t['lines']}L): viveka={len(viveka_lines)}L ({v_pct}%), "
                  f"physics={len(physics_lines)}L ({p_pct}%)")

    print("\n  If viveka wrote proof edges in the same format as physics,")
    print("  emit tantras could be unified — removing the is-viveka branching.")


def _analyze_compression_potential(ts):
    """Summary: estimated line savings from each abstraction opportunity."""
    print(_sep("COMPRESSION POTENTIAL — estimated line savings"))

    t4 = {n: t for n, t in ts.items() if t.get("group") == "tantra4"}
    non_t4 = {n: t for n, t in ts.items() if t.get("group") != "tantra4"}

    opportunities = []

    # 1. has-text replacement
    count = 0
    for t in non_t4.values():
        count += len(re.findall(r'gt\s*\(string-length\s+\w[\w-]*\)\s*0', t["source"]))
    if count:
        opportunities.append(("has-text replacement", count, count * 0.3,
                              "gt (string-length X) 0 → has-text X"))

    # 2. has-items replacement
    count = 0
    for t in non_t4.values():
        count += len(re.findall(r'gt\s*\(length\s+', t["source"]))
    if count:
        opportunities.append(("has-items replacement", count, count * 0.3,
                              "gt (length X) 0 → has-items X"))

    # 3. triple-subj/edge/obj replacement
    count = 0
    for t in non_t4.values():
        count += len(re.findall(r'to-string\s*\(nth\s+\w+\s+[02]\)', t["source"]))
        count += len(re.findall(r'nth\s+\w+\s+1', t["source"]))
    if count:
        opportunities.append(("triple-subj/edge/obj", count, count * 0.2,
                              "nth t 0/1/2 → triple-subj/edge/obj"))

    # 4. first-match pattern
    count = 0
    for t in non_t4.values():
        count += len(re.findall(r'nth\s*\(.*\|\s*where.*\|\s*collect', t["source"]))
    if count:
        opportunities.append(("first-match (query-first)", count, count * 1.5,
                              "nth (graph | where ... | collect) 0 → query-first"))

    # 5. speech reads
    count = 0
    for t in non_t4.values():
        count += len(re.findall(r'shabda\s+"anuvada-setu"\s+"[\w-]+"', t["source"]))
    if count:
        opportunities.append(("speech template reads", count, count * 0.5,
                              "shabda \"anuvada-setu\" \"X\" → speech \"X\""))

    # 6. viveka branching
    count = 0
    for t in non_t4.values():
        count += len(re.findall(r'cond\s+is-viveka\b', t["source"]))
        count += len(re.findall(r'not\s+is-viveka\b', t["source"]))
    if count:
        opportunities.append(("viveka/physics unification", count, count * 3,
                              "cond is-viveka → unified proof edge format"))

    # 7. filter non-empty
    count = 0
    for t in non_t4.values():
        count += len(re.findall(r'filter\s+\w+\s*\(fn\s+\w+\s*->\s*gt\s*\(string-length', t["source"]))
    if count:
        opportunities.append(("filter non-empty strings", count, count * 0.8,
                              "filter X (fn s -> gt ...) → filter-nonempty X"))

    # Sort by estimated savings
    opportunities.sort(key=lambda x: -x[2])

    total_savings = 0
    print(f"  {'Opportunity':<35} {'Hits':>5} {'~Lines':>6}  Description")
    print(f"  {'─' * 90}")
    for opp_name, hits, savings, desc in opportunities:
        total_savings += savings
        print(f"  {opp_name:<35} {hits:>5} {savings:>6.0f}  {desc}")

    non_t4_lines = sum(t["lines"] for t in non_t4.values())
    print(f"\n  Pipeline total: {non_t4_lines} lines")
    print(f"  Estimated saveable: ~{total_savings:.0f} lines ({total_savings*100/non_t4_lines:.0f}%)")


def cmd_tantra4(args):
    sub = args.subcmd or "analyze"

    if sub in ("summary",):
        ts = _load_tantra4()
    else:
        ts = _load_all()

    if sub == "analyze":
        t4 = {n: t for n, t in ts.items() if t.get("group") == "tantra4"}
        non_t4 = {n: t for n, t in ts.items() if t.get("group") != "tantra4"}
        print(_sep("FULL TANTRA ANALYSIS — %d tantras (%d tantra4 helpers + %d pipeline)" % (
            len(ts), len(t4), len(non_t4))))
        _analyze_inline_replacements(non_t4)
        _analyze_graph_queries(non_t4)
        _analyze_first_match(non_t4)
        _analyze_speech_reads(ts)
        _analyze_viveka_branching(ts)
        _analyze_viveka_proof_reads(ts)
        _analyze_signal_opportunities(ts)
        _analyze_param_threading(ts)
        _analyze_scan_patterns(ts)
        _analyze_entity_value_scan(ts)
        _analyze_emit_duality(ts)
        _analyze_cross_layer(ts)
        _analyze_compression_potential(ts)

    elif sub == "summary":
        total = sum(t["lines"] for t in ts.values())
        print(f"\n  tantra4/ ({len(ts)} files, {total} lines)\n")
        print(f"  {'Name':<25} {'Lines':>5} {'Takes':>5} {'Binds':>5} {'Reduces':>7} {'Conds':>5} {'Queries':>7}")
        print(f"  {'─' * 80}")
        for name, t in sorted(ts.items()):
            queries = len(_extract_graph_queries(t["source"]))
            print(f"  {name:<25} {t['lines']:>5} {len(t['takes']):>5} {len(t['bindings']):>5} {t['reduces']:>7} {t['conds']:>5} {queries:>7}")

    elif sub == "nesting":
        print(_sep("ALL NESTING (depth ≥ 3)"))
        for name, t in sorted(ts.items()):
            for i, line in enumerate(t["source"].split("\n"), 1):
                stripped = line.strip()
                if stripped.startswith("--"):
                    continue
                depth = _nesting_depth(stripped)
                if depth >= 3:
                    group = t.get("group", "?")
                    print(f"  {name} [{group}] L{i:>3} d={depth}: {stripped[:120]}")

    elif sub == "queries":
        _analyze_graph_queries(ts)

    elif sub == "idioms":
        _analyze_idioms(ts)

    elif sub == "signals":
        _analyze_signal_opportunities(ts)
        _analyze_viveka_branching(ts)
        _analyze_param_threading(ts)

    elif sub == "speech":
        _analyze_speech_reads(ts)

    elif sub == "scans":
        _analyze_scan_patterns(ts)
        _analyze_entity_value_scan(ts)

    elif sub == "cross":
        _analyze_cross_layer(ts)

    elif sub == "inline":
        _analyze_inline_replacements(ts)

    elif sub == "first-match":
        _analyze_first_match(ts)

    elif sub == "viveka":
        _analyze_viveka_branching(ts)
        _analyze_viveka_proof_reads(ts)
        _analyze_emit_duality(ts)

    elif sub == "threading":
        _analyze_param_threading(ts)

    elif sub == "wordnode":
        _analyze_wordnode_collisions(ts)

    elif sub == "potential":
        _analyze_compression_potential(ts)

    elif sub == "collisions":
        _analyze_collisions(ts)

    elif sub == "compose":
        t4 = _load_tantra4()
        _analyze_compositions_legacy(t4)

    else:
        print(f"Unknown subcmd: {sub}")
        print("Usage: tantra4 analyze|summary|nesting|queries|idioms|signals|speech|")
        print("               scans|cross|inline|first-match|viveka|threading|")
        print("               wordnode|potential|collisions|compose")


def _analyze_compositions_legacy(ts):
    """Legacy compose analysis for tantra4 only."""
    helper_names = {n for n, t in ts.items() if t["lines"] <= 30}

    print(_sep("HELPER CALLS PER TANTRA"))
    for name, t in sorted(ts.items()):
        if name in helper_names:
            continue
        calls_to_helpers = sorted(set(c for c in t["calls"] if c in helper_names))
        if calls_to_helpers:
            print(f"  {name} ({t['lines']}L) calls {len(calls_to_helpers)} helpers:")
            print(f"    {', '.join(calls_to_helpers)}")
            print()

    print(_sep("HELPERS NOT CALLED BY ANY PIPELINE TANTRA"))
    all_called = set()
    for name, t in ts.items():
        if name not in helper_names:
            all_called.update(c for c in t["calls"] if c in helper_names)
    helper_called = set()
    for name, t in ts.items():
        if name in helper_names:
            helper_called.update(c for c in t["calls"] if c in helper_names)
    uncalled = helper_names - all_called - helper_called
    for n in sorted(uncalled):
        print(f"  {n} ({ts[n]['lines']}L) — not used by any tantra")
