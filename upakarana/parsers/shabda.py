"""shabda.py — Parse .shabda s-expression files.

Format:
    shabda node-name
      (key value ...)
      -- comment
    done

Merged from tools/shabda.py + tools/shabda2.py.
"""

import glob
import os
import re
from collections import defaultdict, OrderedDict

from upakarana.paths import BRAHMAN


def find_all(root=None):
    """Find all .shabda files."""
    r = str(root or BRAHMAN)
    return sorted(glob.glob(os.path.join(r, "**", "*.shabda"), recursive=True))


def _tokenize(s):
    """Tokenize sexp contents, respecting quoted strings."""
    tokens = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in (" ", "\t", "\n"):
            i += 1
        elif c == '"':
            j = i + 1
            while j < len(s) and s[j] != '"':
                if s[j] == '\\':
                    j += 1
                j += 1
            tokens.append(s[i + 1:j])
            i = j + 1
        else:
            j = i
            while j < len(s) and s[j] not in (" ", "\t", "\n", '"', "(", ")"):
                j += 1
            tokens.append(s[i:j])
            i = j
    return tokens


def parse_source(source):
    """Parse shabda source into list of node dicts."""
    nodes = []
    lines = source.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue

        m = re.match(r"^shabda\s+([a-zA-Z][a-zA-Z0-9_-]*)", line)
        if not m:
            i += 1
            continue

        name = m.group(1)
        fields = OrderedDict()
        comments = []
        i += 1

        while i < len(lines):
            bline = lines[i].strip()
            if bline == "done":
                i += 1
                break
            if not bline:
                i += 1
                continue
            if bline.startswith("--"):
                comments.append(bline[2:].strip())
                i += 1
                continue

            if bline.startswith("("):
                field_text = bline
                while field_text.count("(") > field_text.count(")") and i + 1 < len(lines):
                    i += 1
                    field_text += " " + lines[i].strip()

                inner = field_text.strip("()")
                tokens = _tokenize(inner)
                if tokens:
                    key = tokens[0]
                    values = tokens[1:]
                    if len(values) == 1:
                        fields[key] = values[0]
                    elif len(values) == 0:
                        fields[key] = True
                    else:
                        fields[key] = values

            i += 1

        nodes.append({"name": name, "fields": fields, "comments": comments})

    return nodes


def parse(path):
    """Parse one .shabda file."""
    try:
        with open(path) as f:
            return parse_source(f.read())
    except Exception:
        return []


def load_all(root=None):
    """Load all .shabda files, return OrderedDict keyed by node name."""
    all_nodes = OrderedDict()
    for path in find_all(root):
        for node in parse(path):
            node["path"] = path
            node["domain"] = os.path.dirname(
                os.path.relpath(path, str(root or BRAHMAN))
            )
            all_nodes[node["name"]] = node
    return all_nodes


# --- Queries ---

def get_field(node, key, default=None):
    """Get a field value from a parsed node."""
    return node.get("fields", {}).get(key, default)


def get_words(node):
    """Get word list from a node."""
    w = get_field(node, "word")
    if w is None:
        return []
    return w if isinstance(w, list) else [w]


def word_index(nodes):
    """Build {word → [node_names]} index."""
    idx = defaultdict(list)
    for name, node in nodes.items():
        for w in get_words(node):
            idx[w].append(name)
    return dict(idx)


def search(nodes, pattern):
    """Regex search across node names and fields."""
    rx = re.compile(pattern, re.IGNORECASE)
    results = []
    for name, node in nodes.items():
        if rx.search(name):
            results.append(node)
            continue
        for key, val in node.get("fields", {}).items():
            val_str = str(val)
            if rx.search(val_str):
                results.append(node)
                break
    return results


def with_field(nodes, key, value=None):
    """Nodes that have a field, optionally matching value."""
    results = []
    for node in nodes.values():
        v = get_field(node, key)
        if v is None:
            continue
        if value is None:
            results.append(node)
        elif isinstance(v, list) and value in v:
            results.append(node)
        elif str(v) == value:
            results.append(node)
    return results


def summary(nodes):
    """Compact summary."""
    all_keys = defaultdict(int)
    word_count = 0
    eval_count = 0
    for node in nodes.values():
        for key in node.get("fields", {}):
            all_keys[key] += 1
        word_count += len(get_words(node))
        if get_field(node, "eval"):
            eval_count += 1
    return {
        "total_nodes": len(nodes),
        "total_words": word_count,
        "total_files": len(set(n.get("path", "") for n in nodes.values())),
        "eval_nodes": eval_count,
        "keys": dict(sorted(all_keys.items(), key=lambda x: -x[1])),
    }
