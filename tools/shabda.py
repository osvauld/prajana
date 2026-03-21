"""shabda.py — analysis of all shabda (word/metadata) declarations.

Shabda files use S-expression format:
    shabda node-name
      (word a b c)
      (eval mul)
      (arity 2)
      (desc "description text")
    done

Two sources:
  1. .shabda files (S-expression blocks) in brahman/shabda/ and brahman/kosha/
  2. inline shabda on .om nodes (legacy key:value format on node.shabda field)

This module reads both into a unified queryable view.
No server needed. Reads source directly from disk.
"""

import glob
import os
import re
from collections import defaultdict, OrderedDict

from .paths import BRAHMAN
from . import om as om_mod
from .shabda2 import parse_sexp_shabda, get_words, get_field


# ── .shabda file loading (S-expression format) ────────────────────────────


def find_shabda_files():
    """Find all .shabda files under brahman/."""
    return sorted(glob.glob(os.path.join(BRAHMAN, "**", "*.shabda"), recursive=True))


def domain_of(path):
    """Return the domain (relative directory) of a file."""
    return os.path.dirname(os.path.relpath(path, BRAHMAN))


def load_shabda_file(path):
    """Parse one .shabda file into structured node dicts."""
    try:
        with open(path) as f:
            source = f.read()
    except Exception:
        return []

    return parse_sexp_shabda(source)


def load_all():
    """Load all .shabda files. Returns OrderedDict: node-name -> node dict.

    Each node dict has:
        name, fields (OrderedDict), comments, path, domain, file_name
    """
    all_nodes = OrderedDict()
    for path in find_shabda_files():
        nodes = load_shabda_file(path)
        domain = domain_of(path)
        file_name = os.path.splitext(os.path.basename(path))[0]
        for n in nodes:
            n["path"] = path
            n["domain"] = domain
            n["file_name"] = file_name
            all_nodes[n["name"]] = n
    return all_nodes


# ── unified word index ───────────────────────────────────────────────────


def build_word_index(shabda_nodes=None):
    """Build word -> [node info] mapping from all shabda files.

    Returns dict: word -> [{node, path, domain, file_name, all_words}, ...]
    """
    if shabda_nodes is None:
        shabda_nodes = load_all()

    index = defaultdict(list)
    for n in shabda_nodes.values():
        words = get_words(n)
        for w in words:
            w_lower = w.lower().strip()
            if w_lower:
                index[w_lower].append({
                    "node": n["name"],
                    "path": n.get("path", ""),
                    "domain": n.get("domain", ""),
                    "file_name": n.get("file_name", ""),
                    "all_words": words,
                })
    return dict(index)


# ── analysis ─────────────────────────────────────────────────────────────


def summary(shabda_nodes=None):
    """Full summary of the shabda landscape."""
    if shabda_nodes is None:
        shabda_nodes = load_all()

    word_index = build_word_index(shabda_nodes)

    # files
    files = defaultdict(list)
    for n in shabda_nodes.values():
        files[n.get("file_name", "unknown")].append(n)

    # key distribution
    key_dist = defaultdict(int)
    for n in shabda_nodes.values():
        for k in n.get("fields", {}):
            key_dist[k] += 1

    # collisions
    collisions = {}
    for w, entries in word_index.items():
        nodes = list(set(e["node"] for e in entries))
        if len(nodes) > 1:
            collisions[w] = nodes

    # eval nodes
    eval_nodes = []
    for n in shabda_nodes.values():
        ev = get_field(n, "eval")
        if ev:
            eval_nodes.append({
                "node": n["name"],
                "eval": ev,
                "word": get_field(n, "word", ""),
                "arity": get_field(n, "arity", ""),
                "domain": n.get("domain", ""),
            })

    return {
        "total_nodes": len(shabda_nodes),
        "total_words": len(word_index),
        "total_files": len(files),
        "files": {name: len(nodes) for name, nodes in sorted(files.items())},
        "key_distribution": dict(key_dist),
        "collisions": collisions,
        "eval_nodes": eval_nodes,
    }


def search(shabda_nodes=None, pattern=""):
    """Search all shabda entries for a regex pattern (names + field values)."""
    if shabda_nodes is None:
        shabda_nodes = load_all()
    regex = re.compile(pattern, re.IGNORECASE)
    results = []
    for n in shabda_nodes.values():
        matches = []
        if regex.search(n["name"]):
            matches.append(f"name: {n['name']}")
        for k, v in n.get("fields", {}).items():
            val_str = ",".join(v) if isinstance(v, list) else str(v)
            if regex.search(val_str):
                matches.append(f"{k}: {val_str}")
        if matches:
            results.append({
                "name": n["name"],
                "file": n.get("file_name", ""),
                "domain": n.get("domain", ""),
                "matches": matches,
            })
    return results


def node_info(shabda_nodes=None, name=""):
    """Get complete shabda info for a single node."""
    if shabda_nodes is None:
        shabda_nodes = load_all()
    return shabda_nodes.get(name)


def gaps(shabda_nodes=None, oms=None):
    """Find om nodes that should have shabda word mappings but don't."""
    if oms is None:
        oms = om_mod.load_all()
    if shabda_nodes is None:
        shabda_nodes = load_all()

    # nodes that have word: keys
    has_word = set()
    for n in shabda_nodes.values():
        if get_words(n):
            has_word.add(n["name"])

    missing = []
    for o in oms.values():
        name = o["name"]
        if name in has_word:
            continue
        if any(name.endswith(s) for s in ("-varga", "-domain", "-engine", "-setu", "-expr")):
            continue
        if o["layer"] == "sangati":
            continue

        has_eval = "eval" in o["shabda_keys"]
        is_common_sense = o["domain"].startswith("kosha/common-sense")

        if has_eval or is_common_sense:
            reason = []
            if has_eval:
                reason.append(f"eval:{o['shabda_keys']['eval']}")
            if is_common_sense:
                reason.append("common-sense")
            reason.append(o["layer"])
            missing.append({
                "name": name,
                "layer": o["layer"],
                "domain": o["domain"],
                "reason": reason,
            })

    return missing


def words_by_node(shabda_nodes=None):
    """Invert: node -> list of words."""
    word_index = build_word_index(shabda_nodes)
    result = defaultdict(list)
    for word, entries in word_index.items():
        for e in entries:
            result[e["node"]].append(word)
    return dict(result)


def verbs(shabda_nodes=None):
    """Analyze verb coverage in common-sense-events."""
    if shabda_nodes is None:
        shabda_nodes = load_all()

    events = {}
    for n in shabda_nodes.values():
        if n.get("file_name") == "common-sense-events":
            val = get_field(n, "desc") or get_field(n, "alias") or ""
            if isinstance(val, list):
                val = val[0] if val else ""
            events[n["name"]] = str(val).strip()

    kshaya = [k for k, v in events.items() if v == "kshaya"]
    vriddhi = [k for k, v in events.items() if v == "vriddhi"]

    return {
        "total": len(events),
        "kshaya": sorted(kshaya),
        "vriddhi": sorted(vriddhi),
        "kshaya_bigrams": [v for v in kshaya if "-" in v],
        "vriddhi_bigrams": [v for v in vriddhi if "-" in v],
    }
