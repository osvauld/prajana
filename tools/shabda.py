"""shabda.py — unified analysis of all shabda (word/metadata) declarations.

Three sources of shabda data in the codebase:
  1. inline shabda in .om files  — `shabda word:x,y eval:add arity:2 ...`
  2. .shabda template files      — standalone key:value tables loaded via shabda-tmpl
  3. the link between them       — .om nodes with `shabda-tmpl:physics` point to
                                   physics-constants.shabda etc.

This module unifies all three into a single queryable view:
  - every word the engine knows and which node it maps to
  - every shabda key on every node (eval, arity, word, role, math-op, ...)
  - the .shabda template files and their contents
  - gaps: nodes that should have word mappings but don't
  - collisions: words that map to multiple nodes

No server needed. Reads source directly from disk.
"""

import glob
import os
import re
from collections import defaultdict, OrderedDict

from .paths import BRAHMAN
from . import om as om_mod

# ── .shabda file parsing ─────────────────────────────────────────────────────


def find_shabda_files():
    """Find all .shabda files under brahman/."""
    return sorted(glob.glob(os.path.join(BRAHMAN, "**", "*.shabda"), recursive=True))


def domain_of(path):
    """Return the domain (relative directory) of a file."""
    return os.path.dirname(os.path.relpath(path, BRAHMAN))


def parse_shabda_file(path):
    """Parse one .shabda file into a structured dict."""
    try:
        with open(path) as f:
            source = f.read()
    except Exception:
        return None

    name = os.path.splitext(os.path.basename(path))[0]
    domain = domain_of(path)

    entries = []
    keys = {}
    comments = []

    for line in source.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            comments.append(stripped[1:].strip())
            continue
        colon = stripped.find(":")
        if colon > 0:
            k = stripped[:colon].strip()
            v = stripped[colon + 1 :].strip()
            if k:
                entries.append((k, v))
                keys[k] = v

    return {
        "name": name,
        "path": path,
        "domain": domain,
        "entries": entries,
        "keys": keys,
        "comments": comments,
        "lines": len(source.split("\n")),
        "source": source,
    }


def load_shabda_files():
    """Load all .shabda files, return OrderedDict keyed by name."""
    shabdas = OrderedDict()
    for path in find_shabda_files():
        parsed = parse_shabda_file(path)
        if not parsed:
            continue
        shabdas[parsed["name"]] = parsed
    return shabdas


# ── unified word index ───────────────────────────────────────────────────────


def build_word_index(oms=None, shabda_files=None):
    """Build a unified word -> node mapping from both .om and .shabda sources.

    Returns dict:
        word -> [{
            "node":        node name,
            "source_type": "om-inline" | "shabda-file",
            "layer":       om layer or "shabda-file",
            "domain":      domain path,
            "path":        file path,
            "all_words":   full comma-separated word list this word came from,
            "shabda_keys": dict of all shabda keys on that node,
        }, ...]
    """
    if oms is None:
        oms = om_mod.load_all()
    if shabda_files is None:
        shabda_files = load_shabda_files()

    index = defaultdict(list)

    # source 1: .om file inline shabda word: declarations
    # om.py's regex only captures word:FIRST_WORD (stops at comma).
    # but the raw shabda has the full comma list: word:count,number,many,...
    # we parse the full list from shabda_raw, plus shabda_words as fallback.
    for o in oms.values():
        raw = o.get("shabda_raw", "")
        # extract full word: value from raw shabda (everything after word: until / or next key:)
        word_match = re.search(r"word:([^\s/]+(?:,[^\s/]+)*)", raw)
        if word_match:
            word_val = word_match.group(1)
            words = [w.strip() for w in word_val.split(",") if w.strip()]
        elif o["shabda_words"]:
            # fallback: shabda_words contains bare words from before the /
            word_val = ",".join(o["shabda_words"])
            words = list(o["shabda_words"])
        else:
            continue
        seen = set()
        for w in words:
            if w in seen:
                continue
            seen.add(w)
            index[w].append(
                {
                    "node": o["name"],
                    "source_type": "om-inline",
                    "layer": o["layer"],
                    "domain": o["domain"],
                    "path": o["path"],
                    "all_words": word_val,
                    "shabda_keys": o["shabda_keys"],
                }
            )

    # source 2: .shabda file word: entries (from matra-beeja etc.)
    for s in shabda_files.values():
        # matra-beeja.shabda has entries like:
        #   joule: energy-yukta ... | ... | word:joule,J ...
        # extract word: from value side
        for _k, v in s["entries"]:
            word_match = re.search(r"word:([^\s]+)", v)
            if word_match:
                word_val = word_match.group(1)
                words = [w.strip() for w in word_val.split(",") if w.strip()]
                for w in words:
                    index[w].append(
                        {
                            "node": _k,
                            "source_type": "shabda-file",
                            "layer": "shabda-file",
                            "domain": s["domain"],
                            "path": s["path"],
                            "all_words": word_val,
                            "shabda_keys": {},
                        }
                    )

    return dict(index)


# ── node shabda index (all metadata, not just words) ─────────────────────────


def build_node_index(oms=None, shabda_files=None):
    """Build a unified node -> shabda metadata view.

    For every .om node, collects ALL shabda keys (word, eval, arity, math-op,
    role, inverse, etc.) plus its .shabda template link if any.

    Returns dict:
        node_name -> {
            "name":         node name,
            "layer":        om layer,
            "domain":       domain path,
            "path":         file path,
            "shabda_keys":  {key: value, ...} from inline shabda,
            "shabda_raw":   raw shabda string,
            "shabda_words": list of word aliases,
            "shabda_tmpl":  name of linked .shabda template file or None,
            "edges":        list of edges from the .om file,
        }
    """
    if oms is None:
        oms = om_mod.load_all()

    index = OrderedDict()
    for o in oms.values():
        index[o["name"]] = {
            "name": o["name"],
            "layer": o["layer"],
            "domain": o["domain"],
            "path": o["path"],
            "shabda_keys": o["shabda_keys"],
            "shabda_raw": o["shabda_raw"],
            "shabda_words": o["shabda_words"],
            "shabda_tmpl": o["shabda_keys"].get("shabda-tmpl"),
            "edges": o["edges"],
        }

    return index


# ── analysis ─────────────────────────────────────────────────────────────────


def summary(oms=None, shabda_files=None):
    """Return a full summary of the shabda landscape."""
    if oms is None:
        oms = om_mod.load_all()
    if shabda_files is None:
        shabda_files = load_shabda_files()

    word_index = build_word_index(oms, shabda_files)
    node_index = build_node_index(oms)

    # nodes with words
    om_word_nodes = set()
    for entries in word_index.values():
        for e in entries:
            if e["source_type"] == "om-inline":
                om_word_nodes.add(e["node"])

    # words by domain
    domain_word_counts = defaultdict(int)
    for entries in word_index.values():
        for e in entries:
            domain_word_counts[e["domain"]] += 1

    # words by layer
    layer_word_counts = defaultdict(int)
    for entries in word_index.values():
        for e in entries:
            layer_word_counts[e["layer"]] += 1

    # collisions: words that map to multiple different nodes
    collisions = {}
    for w, es in word_index.items():
        nodes = set(e["node"] for e in es)
        if len(nodes) > 1:
            collisions[w] = [e["node"] for e in es]

    # shabda key distribution across all .om files
    key_distribution = defaultdict(int)
    for o in oms.values():
        for k in o["shabda_keys"]:
            key_distribution[k] += 1

    # .shabda file summary
    shabda_file_entries = {}
    for s in shabda_files.values():
        shabda_file_entries[s["name"]] = {
            "domain": s["domain"],
            "entry_count": len(s["entries"]),
            "path": s["path"],
        }

    # nodes with shabda-tmpl links
    tmpl_links = {}
    for o in oms.values():
        tmpl = o["shabda_keys"].get("shabda-tmpl")
        if tmpl:
            tmpl_links[o["name"]] = tmpl

    # eval nodes: the fireable operations
    eval_nodes = []
    for o in oms.values():
        ev = o["shabda_keys"].get("eval")
        if ev:
            eval_nodes.append(
                {
                    "node": o["name"],
                    "eval": ev,
                    "word": o["shabda_keys"].get("word", ""),
                    "arity": o["shabda_keys"].get("arity", ""),
                    "inverse": o["shabda_keys"].get("inverse", ""),
                    "domain": o["domain"],
                }
            )

    return {
        "total_words": len(word_index),
        "total_om_nodes_with_words": len(om_word_nodes),
        "total_om_nodes": len(oms),
        "total_shabda_files": len(shabda_files),
        "shabda_file_entries": shabda_file_entries,
        "tmpl_links": tmpl_links,
        "domain_word_counts": dict(domain_word_counts),
        "layer_word_counts": dict(layer_word_counts),
        "collisions": collisions,
        "key_distribution": dict(key_distribution),
        "eval_nodes": eval_nodes,
    }


def words_by_node(oms=None, shabda_files=None):
    """Invert the word index: node -> list of words that map to it."""
    word_index = build_word_index(oms, shabda_files)
    node_words = defaultdict(list)
    for word, entries in word_index.items():
        for e in entries:
            node_words[e["node"]].append(word)
    return dict(node_words)


def words_by_domain(oms=None, shabda_files=None):
    """Group all words by their domain."""
    word_index = build_word_index(oms, shabda_files)
    domain_words = defaultdict(list)
    for word, entries in word_index.items():
        for e in entries:
            domain_words[e["domain"]].append(
                {"word": word, "node": e["node"], "source_type": e["source_type"]}
            )
    for d in domain_words:
        domain_words[d].sort(key=lambda x: x["word"])
    return dict(domain_words)


def search_words(oms=None, shabda_files=None, pattern=""):
    """Search the unified word index for a regex pattern."""
    word_index = build_word_index(oms, shabda_files)
    regex = re.compile(pattern, re.IGNORECASE)
    results = []
    for word, entries in sorted(word_index.items()):
        if regex.search(word):
            results.append({"word": word, "entries": entries})
    return results


def search_files(shabda_files=None, pattern=""):
    """Search .shabda file contents for a regex pattern."""
    if shabda_files is None:
        shabda_files = load_shabda_files()
    regex = re.compile(pattern, re.IGNORECASE)
    results = []
    for s in shabda_files.values():
        matches = []
        for i, line in enumerate(s["source"].split("\n"), 1):
            if regex.search(line):
                matches.append({"line": i, "text": line.rstrip()})
        if matches:
            results.append(
                {
                    "name": s["name"],
                    "domain": s["domain"],
                    "path": s["path"],
                    "matches": matches,
                }
            )
    return results


def gaps(oms=None, shabda_files=None):
    """Find nodes that probably should have word mappings but don't.

    Checks:
    - kosha/mantra nodes with eval: but no word:
    - common-sense domain nodes missing words
    - kosha concept nodes (not structural) missing words
    """
    if oms is None:
        oms = om_mod.load_all()

    missing = []
    for o in oms.values():
        has_word = "word" in o["shabda_keys"]
        if has_word:
            continue

        name = o["name"]
        # skip structural/meta nodes
        if any(
            name.endswith(s) for s in ("-varga", "-domain", "-engine", "-setu", "-expr")
        ):
            continue
        if o["layer"] == "sangati":
            continue

        has_eval = "eval" in o["shabda_keys"]
        is_common_sense = o["domain"].startswith("kosha/common-sense")
        is_kosha = o["layer"] == "kosha"
        is_mantra = o["layer"] == "mantra"

        if has_eval or is_common_sense:
            reason = []
            if has_eval:
                reason.append(f"eval:{o['shabda_keys']['eval']}")
            if is_common_sense:
                reason.append("common-sense")
            if is_kosha:
                reason.append("kosha")
            if is_mantra:
                reason.append("mantra")
            missing.append(
                {
                    "name": name,
                    "layer": o["layer"],
                    "domain": o["domain"],
                    "reason": reason,
                    "path": o["path"],
                }
            )

    return missing


def node_shabda(oms=None, node_name=""):
    """Get complete shabda info for a single node."""
    if oms is None:
        oms = om_mod.load_all()
    o = oms.get(node_name)
    if not o:
        return None
    return {
        "name": o["name"],
        "layer": o["layer"],
        "domain": o["domain"],
        "path": o["path"],
        "shabda_raw": o["shabda_raw"],
        "shabda_keys": o["shabda_keys"],
        "shabda_words": o["shabda_words"],
        "edges": o["edges"],
    }
