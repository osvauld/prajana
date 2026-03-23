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
