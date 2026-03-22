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

# Shabda keys that become graph edges in om5.
# key → (relation, value_transform)
#   value_transform: None means use value as target directly,
#   callable means transform value to target name.
_DEGREE_MAP = {
    "0.5": "sub-linear", "1": "linear", "2": "quadratic",
    "3": "cubic", "4": "quartic",
}

SHABDA_TO_EDGE = {
    "invertible":  ("siddha", lambda v: "inverse-element" if v == "yes" else None),
    "symmetric":   ("siddha", lambda v: "commutativity" if v == "yes" else None),
    "inverse":     ("pratipaksha", None),
    "math-op":     ("kriya", None),
    "unit":        ("matra", None),
    "degree":      ("sthita", lambda v: _DEGREE_MAP.get(v)),
}

# All known visheshanam suffixes.
# Core 10 (proof_graph.ml indices 0-9) + varga (10):
#   swarupa abheda drishthanta sthita yukta siddha kriya phala janya pratipaksha varga
# Dynamic 36 (visheshanam-ring declared):
#   adhikarana ahara amsha apeksha asprista-sankhya avastha bhavishya-kaala
#   bhuta-kaala chaturthi-vibhakti dhatu dvandva dvitiya-vibhakti kala krama
#   kramanusara matra mithya naama-mudra naama-pratibodha panchami-vibhakti
#   prathama-vibhakti prayoga purusa rashi-bandha sandhi sankhya
#   saptami-vibhakti satya shashthi-vibhakti trtiya-vibhakti vachana
#   vartamana-kaala vidhi-kaala viraam vishesa vrnda
# Ad-hoc (used in om slokas but not ring-declared):
#   karma janaka rahita lakshana poorva viparita pratibodha artha
#   vibheda daatri atita purna paripurna antya seema sama paschat
#   purva atikrama abhisarana garbha bhanga shakti nirodha
RELATION_SUFFIXES = [
    # core 0-10
    "swarupa", "abheda", "drishthanta", "sthita", "yukta",
    "siddha", "kriya", "phala", "janya", "pratipaksha",
    "varga",
    # ring-declared dynamic (36)
    "adhikarana", "ahara", "amsha", "apeksha", "asprista-sankhya",
    "avastha", "bhavishya-kaala", "bhuta-kaala", "chaturthi-vibhakti",
    "dhatu", "dvandva", "dvitiya-vibhakti", "kala", "krama",
    "kramanusara", "matra", "mithya", "naama-mudra", "naama-pratibodha",
    "panchami-vibhakti", "prathama-vibhakti", "prayoga", "purusa",
    "rashi-bandha", "sandhi", "sankhya", "saptami-vibhakti", "satya",
    "shashthi-vibhakti", "trtiya-vibhakti", "vachana", "vartamana-kaala",
    "vidhi-kaala", "viraam", "vishesa", "vrnda",
    # ad-hoc: used as compound suffixes in om slokas. All are now standalone
    # sangati nodes so om_parser.ml registers them as dynamic dims.
    "karma", "viparita", "pratibodha", "artha",
    "purna", "seema", "sama", "abhisarana", "shakti",
    "janaka", "rahita", "lakshana", "poorva", "daatri",
    "atita", "vibheda", "garbha", "antya", "bhanga",
    "nirodha", "paripurna", "paschat", "purva", "atikrama",
    # aliases
    "inverse",
]

# Normalize aliases to canonical relation names
_ALIAS_MAP = {
    "inverse": "pratipaksha",
}

_SUFFIX_SET = set(RELATION_SUFFIXES)

_HEADER_RE = re.compile(r"^(sangati|kosha|bhasha|mantra)\s+([a-zA-Z0-9][a-zA-Z0-9-]*)", re.MULTILINE)
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
                canonical = _ALIAS_MAP.get(suffix, suffix)
                return (word[:i], canonical)
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

    slokas = []
    comments = []
    for line in source.split("\n"):
        stripped = line.strip()
        if stripped == "done":
            continue
        m = _COMMENT_RE.match(stripped)
        if m:
            comments.append(m.group(1).strip())
            continue
        # Extract quoted strings from non-comment lines (including after done)
        for qm in _SLOKA_RE.finditer(line):
            slokas.append(qm.group(1))

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


def shabda_edges(name, shabda_nodes):
    """Extract graph edges from shabda intrinsic keys for a node."""
    node = shabda_nodes.get(name)
    if not node:
        return []
    fields = node.get("fields", {})
    extra = []
    for key, (relation, transform) in SHABDA_TO_EDGE.items():
        val = fields.get(key)
        if val is None:
            continue
        if transform is not None:
            target = transform(val)
        else:
            target = val
        if target:
            extra.append((target, relation))
    return extra


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


def convert_all(merge_shabda=False):
    """Convert all .om files under BRAHMAN. Returns list of results.

    If merge_shabda=True, intrinsic shabda keys (invertible, symmetric,
    inverse, math-op, unit, degree) are merged as edges into the om5 output.
    """
    import glob
    shabda_nodes = {}
    if merge_shabda:
        from .shabda import load_all
        shabda_nodes = load_all()

    results = []
    for path in sorted(glob.glob(os.path.join(BRAHMAN, "**", "*.om"), recursive=True)):
        parsed = parse_om(path)
        if not parsed:
            continue

        if merge_shabda:
            extra = shabda_edges(parsed["name"], shabda_nodes)
            # Deduplicate: don't add edges that already exist from slokas
            existing = set(parsed["edges"])
            for e in extra:
                if e not in existing:
                    parsed["edges"].append(e)

        om5_str = to_om5(parsed)
        results.append({
            "path": parsed["path"],
            "name": parsed["name"],
            "layer": parsed["layer"],
            "om5": om5_str,
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


def stats(merge_shabda=False):
    """Return conversion statistics."""
    results = convert_all(merge_shabda=merge_shabda)
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
