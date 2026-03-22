"""om5.py — convert .om compound-suffix format to .om5 s-expression format.

Current .om format:
  mantra kinetic-energy-mantra
    "kinetic-energy-swarupa"
    "mass-janya velocity-janya"
  done

Target .om5 format:
  (mantra kinetic-energy-mantra
    (swarupa kinetic-energy)
    (janya mass velocity))

The decomposition logic mirrors om_parser.ml: split compound words at the
last hyphen that yields a known visheshanam suffix, extract (target, relation).
Targets sharing a relation are grouped into one s-expression.
"""

import os
import re
from collections import defaultdict, OrderedDict

from .paths import BRAHMAN

# All known visheshanam suffixes — must match proof_graph.ml core + dynamic dims.
RELATION_SUFFIXES = [
    "swarupa", "abheda", "drishthanta", "sthita", "yukta",
    "siddha", "kriya", "phala", "janya", "pratipaksha",
    "varga", "vishesa", "amsha", "rahita", "karma",
]

_SUFFIX_SET = set(RELATION_SUFFIXES)

_HEADER_RE = re.compile(r"^(sangati|kosha|bhasha|mantra)\s+([a-z][a-z0-9-]*)")
_SLOKA_RE = re.compile(r'"([^"]+)"')
_COMMENT_RE = re.compile(r"^\s*--\s*(.*)")


def decompose_word(word):
    """Split 'target-relation' at last hyphen matching a known suffix.

    Returns (target, relation) or None.
    """
    for i in range(len(word) - 1, 0, -1):
        if word[i] == '-':
            suffix = word[i + 1:]
            if suffix in _SUFFIX_SET:
                return (word[:i], suffix)
    return None


def parse_om(path):
    """Parse a .om file into structured data for conversion."""
    with open(path) as f:
        source = f.read()

    header = _HEADER_RE.search(source)
    if not header:
        return None

    layer = header.group(1)
    name = header.group(2)

    slokas = _SLOKA_RE.findall(source)
    comments = []
    for line in source.split("\n"):
        m = _COMMENT_RE.match(line)
        if m:
            comments.append(m.group(1).strip())

    # Decompose all compound words into (target, relation) edges
    edges = []
    unmatched = []
    for sloka in slokas:
        for word in sloka.split():
            word = word.strip()
            if not word:
                continue
            result = decompose_word(word)
            if result:
                edges.append(result)
            else:
                unmatched.append(word)

    return {
        "layer": layer,
        "name": name,
        "edges": edges,
        "unmatched": unmatched,
        "comments": comments,
        "path": path,
        "source": source,
    }


def edges_to_grouped(edges):
    """Group edges by relation, preserving order of first occurrence."""
    groups = OrderedDict()
    for target, relation in edges:
        if relation not in groups:
            groups[relation] = []
        if target not in groups[relation]:
            groups[relation].append(target)
    return groups


def to_om5(parsed):
    """Convert parsed om data to om5 s-expression string."""
    if not parsed:
        return None

    layer = parsed["layer"]
    name = parsed["name"]
    grouped = edges_to_grouped(parsed["edges"])
    comments = parsed["comments"]

    lines = []

    # Comments before the node
    for c in comments:
        lines.append(f"; {c}")
    if comments:
        lines.append("")

    if not grouped:
        # No edges — bare node
        lines.append(f"({layer} {name})")
    else:
        lines.append(f"({layer} {name}")
        rels = list(grouped.items())
        for i, (rel, targets) in enumerate(rels):
            is_last = (i == len(rels) - 1)
            targets_str = " ".join(targets)
            closing = ")" if is_last else ""
            lines.append(f"  ({rel} {targets_str}){closing}")

    return "\n".join(lines) + "\n"


def convert_file(path):
    """Convert one .om file, return (om5_string, parsed) or (None, None)."""
    parsed = parse_om(path)
    if not parsed:
        return None, None
    return to_om5(parsed), parsed


def convert_all():
    """Convert all .om files under BRAHMAN. Returns list of results."""
    import glob
    results = []
    for path in sorted(glob.glob(os.path.join(BRAHMAN, "**", "*.om"), recursive=True)):
        om5, parsed = convert_file(path)
        if om5 and parsed:
            results.append({
                "path": parsed["path"],
                "name": parsed["name"],
                "layer": parsed["layer"],
                "om5": om5,
                "edges": len(parsed["edges"]),
                "unmatched": parsed["unmatched"],
            })
    return results


def om5_path(om_path):
    """Compute the .om5 output path for a given .om path."""
    return os.path.splitext(om_path)[0] + ".om5"


def write_om5(om_path, om5_string):
    """Write an om5 file alongside the original .om file."""
    out = om5_path(om_path)
    with open(out, "w") as f:
        f.write(om5_string)
    return out


def roundtrip_check(parsed, om5_string):
    """Verify that parsing the om5 back produces the same edges.

    Returns (ok, message).
    """
    # Parse the om5 string to extract edges
    edges_from_om5 = []
    for line in om5_string.split("\n"):
        line = line.strip()
        if line.startswith(";") or not line:
            continue
        # Match (relation target1 target2 ...)
        m = re.match(r"\((\w[\w-]*)\s+(.+?)\)?\s*\)?\s*$", line)
        if m:
            rel = m.group(1)
            if rel in _SUFFIX_SET:
                targets = m.group(2).rstrip(")").split()
                for t in targets:
                    t = t.strip().rstrip(")")
                    if t:
                        edges_from_om5.append((t, rel))

    orig_set = set(parsed["edges"])
    om5_set = set(edges_from_om5)

    if orig_set == om5_set:
        return True, "ok"
    missing = orig_set - om5_set
    extra = om5_set - orig_set
    msg = []
    if missing:
        msg.append(f"missing: {missing}")
    if extra:
        msg.append(f"extra: {extra}")
    return False, "; ".join(msg)


def stats():
    """Return conversion statistics."""
    results = convert_all()
    total = len(results)
    total_edges = sum(r["edges"] for r in results)
    with_unmatched = [r for r in results if r["unmatched"]]
    all_unmatched = []
    for r in results:
        all_unmatched.extend(r["unmatched"])
    unique_unmatched = sorted(set(all_unmatched))

    return {
        "total_nodes": total,
        "total_edges": total_edges,
        "nodes_with_unmatched": len(with_unmatched),
        "unique_unmatched_words": unique_unmatched,
        "unmatched_count": len(all_unmatched),
    }
