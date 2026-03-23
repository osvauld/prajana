"""signals.py — Signal flow tracing across the tantra pipeline.

Traces write-signal → _signal → read-signal chains.
Finds signals emitted but never consumed (dead signals).
"""

import re
from collections import defaultdict
from upakarana.parsers import tantra4


def signal_producers(root=None):
    """Find all tantras that emit signals via write-signal/write-signals.

    Returns {signal_name: [producing_tantra, ...]}
    """
    tantras = tantra4.load_all(root)
    producers = defaultdict(list)

    for name, t in tantras.items():
        src = t["source"]
        # write-signal with literal name
        for m in re.finditer(r'write-signal\s+\w+\s+"([^"]+)"', src):
            producers[m.group(1)].append(name)
        # write-signals with pairs containing literal names
        for m in re.finditer(r'\["([^"]+)",\s*', src):
            if "write-signal" in src or "_signal" in src:
                producers[m.group(1)].append(name)

    # Deduplicate
    return {k: list(set(v)) for k, v in producers.items()}


def signal_consumers(root=None):
    """Find all tantras that read signals via read-signal.

    Returns {signal_name: [consuming_tantra, ...]}
    """
    tantras = tantra4.load_all(root)
    consumers = defaultdict(list)

    for name, t in tantras.items():
        src = t["source"]
        for m in re.finditer(r'read-signal\s+\w+\s+"([^"]+)"', src):
            consumers[m.group(1)].append(name)

    return {k: list(set(v)) for k, v in consumers.items()}


def signal_flow(root=None):
    """Full signal flow: producers, consumers, and dead signals."""
    prods = signal_producers(root)
    cons = signal_consumers(root)

    all_signals = set(prods.keys()) | set(cons.keys())

    flow = []
    for sig in sorted(all_signals):
        flow.append({
            "signal": sig,
            "producers": prods.get(sig, []),
            "consumers": cons.get(sig, []),
            "dead": sig in prods and sig not in cons,
            "orphan": sig in cons and sig not in prods,
        })

    return {
        "signals": flow,
        "dead": [f for f in flow if f["dead"]],
        "orphan": [f for f in flow if f["orphan"]],
    }


def signals_gap(root=None):
    """Gap analysis: what semantic signals exist in the graph but are not
    wired into detect-signals (and therefore never reach dispatch).

    Sections:
    1. Dispatch modes — what modes detect-signals currently handles
    2. Intent words — bhasha nodes with role=intent (trigger derive/viveka/etc)
    3. Qualitative state nodes — kosha nodes with yukta=shunya (absence signal)
    4. Negation nodes — bhasha/sangati nodes with pratishedha/negation semantics
    5. Opposite signal — nodes with viparita/pratipaksha edges
    6. Gap summary — what has no path to detect-signals
    """
    from upakarana.parsers import om5, shabda as shabda_mod

    nodes = om5.load_all(root)
    shabda_nodes = shabda_mod.load_all(root)
    tantras = tantra4.load_all(root)

    detect_src = tantras.get("detect-signals", {}).get("source", "")

    # --- Section 1: dispatch modes in detect-signals ---
    dispatch_modes = []
    for m in re.finditer(r'"([a-z]+)"\s*\)', detect_src):
        candidate = m.group(1)
        if candidate in ("anumana", "viveka", "count", "derive", "none"):
            if candidate not in dispatch_modes:
                dispatch_modes.append(candidate)

    # --- Section 2: intent words (role=intent in shabda) ---
    intent_words = {}
    for name, sn in shabda_nodes.items():
        role = sn.get("fields", {}).get("role", "")
        if role == "intent":
            words = sn.get("fields", {}).get("word", [])
            if isinstance(words, str):
                words = [words]
            intent_words[name] = {
                "words": words,
                "wired": name in detect_src or any(w in detect_src for w in words),
            }

    # --- Section 3: shunya-state nodes (yukta shunya in kosha) ---
    shunya_nodes = {}
    for name, n in nodes.items():
        yukta = [e["target"] for e in n.get("edges", []) if e["relation"] == "yukta"]
        if "shunya" in yukta:
            abheda = [e["target"] for e in n.get("edges", []) if e["relation"] == "abheda"]
            sh = shabda_nodes.get(name, {})
            words = sh.get("fields", {}).get("word", sh.get("fields", {}).get("alias", []))
            if isinstance(words, str):
                words = [words]
            shunya_nodes[name] = {
                "layer": n.get("layer", ""),
                "abheda": abheda,
                "words": words,
                "has_word": bool(words),
                "wired_in_detect": name in detect_src,
            }

    # --- Section 4: negation/pratishedha nodes ---
    negation_nodes = {}
    for name, sn in shabda_nodes.items():
        fields = sn.get("fields", {})
        ev = fields.get("eval", "")
        if ev == "not" or name in ("negation", "pratishedha", "viparita"):
            words = fields.get("word", [])
            if isinstance(words, str):
                words = [words]
            negation_nodes[name] = {
                "words": words,
                "eval": ev,
                "wired_in_detect": name in detect_src,
            }

    # --- Section 5: opposite signal (viparita/pratipaksha edges) ---
    pratipaksha_pairs = []
    for name, n in nodes.items():
        for e in n.get("edges", []):
            if e["relation"] == "pratipaksha":
                pratipaksha_pairs.append((name, e["target"]))

    # --- Gap summary ---
    unwired_shunya = [n for n, d in shunya_nodes.items() if not d["wired_in_detect"]]
    no_word_shunya = [n for n, d in shunya_nodes.items() if not d["has_word"]]
    unwired_negation = [n for n, d in negation_nodes.items() if not d["wired_in_detect"]]

    return {
        "dispatch_modes": dispatch_modes,
        "intent_words": intent_words,
        "shunya_nodes": shunya_nodes,
        "negation_nodes": negation_nodes,
        "pratipaksha_pairs_count": len(pratipaksha_pairs),
        "pratipaksha_sample": pratipaksha_pairs[:10],
        "gaps": {
            "shunya_unwired": unwired_shunya,
            "shunya_no_word": no_word_shunya,
            "negation_unwired": unwired_negation,
        },
    }


def shabda_roles(root=None):
    """Analyze the shabda layer through a signals lens.

    For each role, shows: which nodes carry it, which words trigger it,
    and what the pipeline does with it. Also reports missing roles,
    domain word coverage, and word collisions.
    """
    from collections import defaultdict
    from upakarana.parsers import om5, shabda as shabda_mod

    shabda_nodes = shabda_mod.load_all(root)
    om_nodes = om5.load_all(root)

    # Role → pipeline outcome mapping
    role_outcomes = {
        "intent":      "vidhi-kaala edge → solve-for → derive/viveka/count dispatch",
        "grammar":     "DROPPED — emit-triples returns []",
        "possession":  "shashthi-vibhakti edge → entity ownership",
        "pronoun":     "pronoun resolution → entity reference",
        "rashi-bandha":"numeric gate → rashi instance binding",
        "boundary":    "viraam edge → grade reset",
        "none":        "satya/mithya edge — concept present, no dispatch signal",
    }
    missing_roles = {
        "shunya":      "yukta=shunya → absence → abhava dispatch (unwired)",
        "pratishedha": "negation → invert truth → pratishedha dispatch (unwired)",
        "state":       "avastha node → implicit value binding e.g. rest→v=0 (unwired)",
        "question":    "prashna marker → anumana/viveka dispatch (role=intent but unwired)",
        "viparita":    "pratipaksha walk → opposite concept (unwired)",
    }

    # Group nodes by role
    by_role = defaultdict(list)
    for name, sn in shabda_nodes.items():
        role = sn.get("fields", {}).get("role", "none")
        words = sn.get("fields", {}).get("word", [])
        if isinstance(words, str):
            words = [words]
        by_role[role].append({"name": name, "words": words})

    # Domain word coverage
    domains = defaultdict(lambda: {"total": 0, "with_word": 0})
    for name, n in om_nodes.items():
        domain = n.get("domain", "unknown").split("/")[0]
        domains[domain]["total"] += 1
        sh = shabda_nodes.get(name, {}).get("fields", {})
        if sh.get("word") or sh.get("alias"):
            domains[domain]["with_word"] += 1

    # Word collisions
    word_map = defaultdict(list)
    for name, sn in shabda_nodes.items():
        fields = sn.get("fields", {})
        words = fields.get("word", [])
        if isinstance(words, str): words = [words]
        aliases = fields.get("alias", [])
        if isinstance(aliases, str): aliases = [aliases]
        for w in words + aliases:
            w = w.strip().rstrip(",")
            if w and len(w) > 1:
                word_map[w].append(name)
    collisions = {w: ns for w, ns in word_map.items() if len(set(ns)) > 1}

    # Shunya-state nodes
    shunya_states = []
    for name, n in om_nodes.items():
        yukta = [e["target"] for e in n.get("edges", []) if e["relation"] == "yukta"]
        if "shunya" in yukta:
            sh = shabda_nodes.get(name, {}).get("fields", {})
            words = sh.get("word", sh.get("alias", []))
            if isinstance(words, str): words = [words]
            abheda = [e["target"] for e in n.get("edges", []) if e["relation"] == "abheda"]
            shunya_states.append({
                "name": name, "layer": n.get("layer", ""),
                "abheda": abheda, "words": words, "has_word": bool(words),
            })

    return {
        "role_outcomes": role_outcomes,
        "missing_roles": missing_roles,
        "by_role": {k: v for k, v in by_role.items()},
        "domain_coverage": {d: s for d, s in sorted(domains.items())},
        "collisions": collisions,
        "collision_count": len(collisions),
        "shunya_states": shunya_states,
        "total_words": sum(len(v) for v in by_role.values()),
    }


def emitted_edges(root=None):
    """Find triple edge types emitted by construct/refine but never consumed.

    Looks at emit-triples and refine tantras for edge types written,
    then checks which edge types are read by downstream tantras.
    """
    tantras = tantra4.load_all(root)

    # Edge types written (string literals after edge position in triples)
    written = defaultdict(list)
    read = defaultdict(list)

    for name, t in tantras.items():
        src = t["source"]
        group = t["group"]

        # Written: [X, "edge-name", Y] patterns
        for m in re.finditer(r'\[\w+,\s*"([a-z][\w-]*)"', src):
            edge = m.group(1)
            if edge not in ("_signal",):
                written[edge].append(name)

        # Read: eq e "edge-name" or eq (triple-edge ...) "edge-name"
        for m in re.finditer(r'eq\s+(?:\(triple-edge[^)]*\)|e)\s+"([a-z][\w-]*)"', src):
            edge = m.group(1)
            read[edge].append(name)

    all_edges = set(written.keys()) | set(read.keys())
    dead = []
    for edge in sorted(all_edges):
        if edge in written and edge not in read:
            dead.append({
                "edge": edge,
                "writers": list(set(written[edge])),
            })

    return {
        "written_edges": len(written),
        "read_edges": len(read),
        "dead_edges": dead,
    }
