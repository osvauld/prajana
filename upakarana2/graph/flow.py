"""flow.py — Signal flow and live graph analysis.

Consolidates: signals.py + live.py
"""

import re
from collections import defaultdict
from upakarana2.parsers import tantra4


# ---------------------------------------------------------------------------
# Signal flow (static)
# ---------------------------------------------------------------------------

def signal_producers(root=None):
    """Find tantras that emit signals. Returns {signal_name: [tantra, ...]}."""
    tantras = tantra4.load_all(root)
    producers = defaultdict(list)
    for name, t in tantras.items():
        src = t["source"]
        for m in re.finditer(r'write-signal\s+\w+\s+"([^"]+)"', src):
            producers[m.group(1)].append(name)
        for m in re.finditer(r'\["([^"]+)",\s*', src):
            if "write-signal" in src or "_signal" in src:
                producers[m.group(1)].append(name)
    return {k: list(set(v)) for k, v in producers.items()}


def signal_consumers(root=None):
    """Find tantras that read signals. Returns {signal_name: [tantra, ...]}."""
    tantras = tantra4.load_all(root)
    consumers = defaultdict(list)
    for name, t in tantras.items():
        src = t["source"]
        for m in re.finditer(r'read-signal\s+\w+\s+"([^"]+)"', src):
            consumers[m.group(1)].append(name)
    return {k: list(set(v)) for k, v in consumers.items()}


def signal_flow(root=None):
    """Full signal flow: producers, consumers, dead signals."""
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
    """Semantic signals in graph with no path to detect-signals dispatch."""
    from upakarana2.parsers import om5, shabda as shabda_mod

    nodes = om5.load_all(root)
    shabda_nodes = shabda_mod.load_all(root)
    tantras = tantra4.load_all(root)

    detect_src = tantras.get("detect-signals", {}).get("source", "")

    dispatch_modes = []
    for m in re.finditer(r'"([a-z]+)"\s*\)', detect_src):
        candidate = m.group(1)
        if candidate in ("anumana", "viveka", "count", "derive", "none"):
            if candidate not in dispatch_modes:
                dispatch_modes.append(candidate)

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

    shunya_nodes = {}
    for name, n in nodes.items():
        yukta = [e["target"] for e in n.get("edges", []) if e["relation"] == "yukta"]
        if "shunya" in yukta:
            sh = shabda_nodes.get(name, {})
            words = sh.get("fields", {}).get("word", sh.get("fields", {}).get("alias", []))
            if isinstance(words, str):
                words = [words]
            shunya_nodes[name] = {
                "layer": n.get("layer", ""),
                "abheda": [e["target"] for e in n.get("edges", []) if e["relation"] == "abheda"],
                "words": words,
                "has_word": bool(words),
                "wired_in_detect": name in detect_src,
            }

    negation_nodes = {}
    for name, sn in shabda_nodes.items():
        fields = sn.get("fields", {})
        ev = fields.get("eval", "")
        if ev == "not" or name in ("negation", "pratishedha", "viparita"):
            words = fields.get("word", [])
            if isinstance(words, str):
                words = [words]
            negation_nodes[name] = {
                "words": words, "eval": ev,
                "wired_in_detect": name in detect_src,
            }

    pratipaksha_pairs = [
        (name, e["target"])
        for name, n in nodes.items()
        for e in n.get("edges", [])
        if e["relation"] == "pratipaksha"
    ]

    return {
        "dispatch_modes": dispatch_modes,
        "intent_words": intent_words,
        "shunya_nodes": shunya_nodes,
        "negation_nodes": negation_nodes,
        "pratipaksha_pairs_count": len(pratipaksha_pairs),
        "pratipaksha_sample": pratipaksha_pairs[:10],
        "gaps": {
            "shunya_unwired": [n for n, d in shunya_nodes.items() if not d["wired_in_detect"]],
            "shunya_no_word": [n for n, d in shunya_nodes.items() if not d["has_word"]],
            "negation_unwired": [n for n, d in negation_nodes.items() if not d["wired_in_detect"]],
        },
    }


def shabda_roles(root=None):
    """Analyze the shabda layer through a signals lens."""
    from upakarana2.parsers import om5, shabda as shabda_mod

    shabda_nodes = shabda_mod.load_all(root)
    om_nodes = om5.load_all(root)

    role_outcomes = {
        "intent":      "vidhi-kaala edge → solve-for → derive/viveka/count dispatch",
        "grammar":     "DROPPED — emit-triples returns []",
        "possession":  "shashthi-vibhakti edge → entity ownership",
        "pronoun":     "pronoun resolution → entity reference",
        "rashi-bandha":"numeric gate → rashi instance binding",
        "boundary":    "viraam edge → grade reset",
        "none":        "satya/mithya edge — concept present, no dispatch signal",
    }

    by_role = defaultdict(list)
    for name, sn in shabda_nodes.items():
        role = sn.get("fields", {}).get("role", "none")
        words = sn.get("fields", {}).get("word", [])
        if isinstance(words, str):
            words = [words]
        by_role[role].append({"name": name, "words": words})

    domains = defaultdict(lambda: {"total": 0, "with_word": 0})
    for name, n in om_nodes.items():
        domain = n.get("domain", "unknown").split("/")[0]
        domains[domain]["total"] += 1
        sh = shabda_nodes.get(name, {}).get("fields", {})
        if sh.get("word") or sh.get("alias"):
            domains[domain]["with_word"] += 1

    word_map = defaultdict(list)
    for name, sn in shabda_nodes.items():
        fields = sn.get("fields", {})
        words = fields.get("word", [])
        if isinstance(words, str):
            words = [words]
        aliases = fields.get("alias", [])
        if isinstance(aliases, str):
            aliases = [aliases]
        for w in words + aliases:
            w = w.strip().rstrip(",")
            if w and len(w) > 1:
                word_map[w].append(name)

    collisions = {w: ns for w, ns in word_map.items() if len(set(ns)) > 1}

    shunya_states = []
    for name, n in om_nodes.items():
        yukta = [e["target"] for e in n.get("edges", []) if e["relation"] == "yukta"]
        if "shunya" in yukta:
            sh = shabda_nodes.get(name, {}).get("fields", {})
            words = sh.get("word", sh.get("alias", []))
            if isinstance(words, str):
                words = [words]
            shunya_states.append({
                "name": name, "layer": n.get("layer", ""),
                "abheda": [e["target"] for e in n.get("edges", []) if e["relation"] == "abheda"],
                "words": words, "has_word": bool(words),
            })

    return {
        "role_outcomes": role_outcomes,
        "by_role": dict(by_role),
        "domain_coverage": {d: s for d, s in sorted(domains.items())},
        "collisions": collisions,
        "collision_count": len(collisions),
        "shunya_states": shunya_states,
        "total_words": sum(len(v) for v in by_role.values()),
    }


# ---------------------------------------------------------------------------
# Live analysis (requires running engine)
# ---------------------------------------------------------------------------

def live_walk(client, node, relation):
    """Walk an edge from a node in the live graph."""
    try:
        return client.walk(node, relation)
    except Exception as e:
        return {"error": str(e)}


def live_inspect(client, name):
    """Full node inspection from live graph."""
    try:
        return client.inspect(name)
    except Exception as e:
        return {"error": str(e)}


def pratipaksha_walk(client):
    """Walk pratipaksha edges on all ops and verify involution in live graph."""
    from upakarana2.parsers import shabda
    shabda_nodes = shabda.load_all()

    ops = [name for name, node in shabda_nodes.items() if "eval" in node.get("fields", {})]

    results = []
    for op in sorted(ops):
        try:
            pp = client.walk(op, "pratipaksha")
            if not pp:
                results.append({"op": op, "pratipaksha": None, "round_trip": None})
                continue
            inv = pp[0] if isinstance(pp, list) else str(pp)
            pp2 = client.walk(str(inv), "pratipaksha")
            back = pp2[0] if isinstance(pp2, list) and pp2 else None
            results.append({
                "op": op, "pratipaksha": str(inv),
                "round_trip": str(back) if back else None,
                "ok": str(back) == op if back else False,
            })
        except Exception as e:
            results.append({"op": op, "error": str(e)})

    return {
        "ops": results,
        "symmetric": [r for r in results if r.get("ok")],
        "broken": [r for r in results if not r.get("ok") and r.get("pratipaksha")],
        "no_pratipaksha": [r for r in results if r.get("pratipaksha") is None],
    }
