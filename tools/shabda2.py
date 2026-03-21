"""shabda2.py — S-expression shabda format: parser, converter, writer.

New format (matches .om structure):

    shabda velocity-mantra
      (word velocity speed)
      (name "velocity")
      (unit "metre-per-second")
      (math-op multiplication)
      (eval mul)
      (arity 2)
    done

    shabda avastha
      (word initial final angular linear net total average relative)
      (name "state-at-a-krama-point")
      -- qualifier adjectives that compound with concepts
    done

Rules:
  - header: `shabda <node-name>`
  - body: S-expression fields `(key value ...)`
  - comments: `-- text`
  - terminator: `done`
  - values: barewords or "quoted strings"
  - multi-value fields: `(word initial final angular)` → list
  - single-value fields: `(eval mul)` → string
  - description: `(desc "the transport of...")` replaces / separator

Advantages over flat format:
  - Same parser as .om files (OCaml sexplib compatible)
  - Multi-line fields supported
  - No ambiguity between key:value and free text
  - No duplicate node problem (one block per node)
  - Comments per-field
  - Machine-readable AND human-readable
"""

import os
import re
from collections import OrderedDict

from .paths import BRAHMAN


# ── S-expression shabda parser ─────────────────────────────────────────────

def parse_sexp_shabda(source: str) -> list[dict]:
    """Parse S-expression shabda format into list of node dicts.

    Returns list of:
        {
            "name": str,
            "fields": OrderedDict of key -> value(s),
            "comments": list[str],
        }
    """
    nodes = []
    lines = source.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # skip blank lines and standalone comments
        if not line or line.startswith("#"):
            i += 1
            continue

        # header: shabda <name>
        m = re.match(r"^shabda\s+([a-zA-Z][a-zA-Z0-9_-]*)", line)
        if not m:
            i += 1
            continue

        name = m.group(1)
        fields = OrderedDict()
        comments = []
        i += 1

        # body until done
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

            # S-expression field: (key value ...)
            if bline.startswith("("):
                field_text = bline
                # handle multi-line S-expressions
                while field_text.count("(") > field_text.count(")") and i + 1 < len(lines):
                    i += 1
                    field_text += " " + lines[i].strip()

                # parse: strip parens, extract key and values
                inner = field_text.strip("()")
                # tokenize: respect quoted strings
                tokens = _tokenize_sexp(inner)
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

        nodes.append({
            "name": name,
            "fields": fields,
            "comments": comments,
        })

    return nodes


def _tokenize_sexp(s: str) -> list[str]:
    """Tokenize S-expression contents, respecting quoted strings."""
    tokens = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in (" ", "\t", "\n"):
            i += 1
        elif c == '"':
            # quoted string
            j = i + 1
            while j < len(s) and s[j] != '"':
                if s[j] == '\\':
                    j += 1
                j += 1
            tokens.append(s[i+1:j])
            i = j + 1
        else:
            # bareword
            j = i
            while j < len(s) and s[j] not in (" ", "\t", "\n", '"', "(", ")"):
                j += 1
            tokens.append(s[i:j])
            i = j
    return tokens


def parse_sexp_file(path: str) -> list[dict]:
    """Parse a .shabda2 file (S-expression format)."""
    try:
        with open(path) as f:
            return parse_sexp_shabda(f.read())
    except Exception:
        return []


# ── converter: flat → S-expression ─────────────────────────────────────────

def convert_flat_entry(node_name: str, flat_value: str) -> str:
    """Convert one flat shabda entry to S-expression block.

    Input:  "word:initial,final,angular name:state / description-text unit:newton"
    Output: shabda block string

    Key:value pairs are extracted from the ENTIRE line (both sides of /).
    Non-key words before / become alias, non-key words after / become desc.
    """
    lines = [f"shabda {node_name}"]

    # split on / for description boundary
    before_slash = flat_value
    after_slash = ""
    if " / " in flat_value:
        idx = flat_value.index(" / ")
        before_slash = flat_value[:idx].strip()
        after_slash = flat_value[idx + 3:].strip()

    # extract key:value pairs and remaining words from BOTH parts
    kv_pairs = []
    alias_words = []
    desc_words = []

    for token in before_slash.split():
        kv_match = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*):(.+)$", token)
        if kv_match:
            kv_pairs.append((kv_match.group(1), kv_match.group(2)))
        else:
            alias_words.append(token)

    for token in after_slash.split():
        kv_match = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*):(.+)$", token)
        if kv_match:
            kv_pairs.append((kv_match.group(1), kv_match.group(2)))
        else:
            desc_words.append(token)

    # emit key:value pairs as S-expressions
    for key, val in kv_pairs:
        if "," in val:
            parts = [v.strip() for v in val.split(",") if v.strip()]
            lines.append(f"  ({key} {' '.join(parts)})")
        else:
            lines.append(f"  ({key} {val})")

    # alias words (before /)
    if alias_words:
        joined = " ".join(alias_words)
        if not kv_pairs and not desc_words:
            lines.append(f'  (desc "{joined}")')
        else:
            lines.append(f'  (alias {joined})')

    # description words (after /, excluding key:value pairs)
    if desc_words:
        lines.append(f'  (desc "{"-".join(desc_words) if len(desc_words) > 1 else desc_words[0]}")')

    lines.append("done")
    return "\n".join(lines)


def convert_flat_file(flat_path: str) -> str:
    """Convert an entire flat .shabda file to S-expression format.

    Returns the converted source string.
    """
    with open(flat_path) as f:
        source = f.read()

    blocks = []
    header_comments = []

    for line in source.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            header_comments.append(stripped)
            continue

        # parse flat entry: node-name: rest
        m = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*)\s*:\s*(.*)", stripped)
        if not m:
            continue

        node = m.group(1)
        rest = m.group(2).strip()
        blocks.append(convert_flat_entry(node, rest))

    parts = []
    if header_comments:
        parts.append("\n".join(header_comments))
        parts.append("")
    parts.append("\n\n".join(blocks))
    parts.append("")  # trailing newline
    return "\n".join(parts)


# ── writer: dict → S-expression string ────────────────────────────────────

def write_sexp_node(node: dict) -> str:
    """Write a parsed node dict back to S-expression format."""
    lines = [f"shabda {node['name']}"]

    for comment in node.get("comments", []):
        lines.append(f"  -- {comment}")

    for key, value in node.get("fields", {}).items():
        if isinstance(value, list):
            # multi-value
            lines.append(f"  ({key} {' '.join(str(v) for v in value)})")
        elif isinstance(value, bool):
            lines.append(f"  ({key})")
        elif " " in str(value) or "/" in str(value):
            lines.append(f'  ({key} "{value}")')
        else:
            lines.append(f"  ({key} {value})")

    lines.append("done")
    return "\n".join(lines)


# ── query helpers ──────────────────────────────────────────────────────────

def get_field(node: dict, key: str, default=None):
    """Get a field value from a parsed sexp node."""
    return node.get("fields", {}).get(key, default)


def get_words(node: dict) -> list[str]:
    """Get word list from a node. Handles both single and multi-value."""
    w = get_field(node, "word")
    if w is None:
        return []
    if isinstance(w, list):
        return w
    return [w]


def find_by_word(nodes: list[dict], word: str) -> list[dict]:
    """Find all nodes that have a given word."""
    return [n for n in nodes if word in get_words(n)]


def find_by_field(nodes: list[dict], key: str, value: str = None) -> list[dict]:
    """Find nodes that have a field, optionally matching a value."""
    results = []
    for n in nodes:
        v = get_field(n, key)
        if v is None:
            continue
        if value is None:
            results.append(n)
        elif isinstance(v, list) and value in v:
            results.append(n)
        elif str(v) == value:
            results.append(n)
    return results


# ── analysis: compare flat vs sexp ─────────────────────────────────────────

def analyze_flat_file(flat_path: str) -> dict:
    """Analyze a flat shabda file for migration readiness."""
    with open(flat_path) as f:
        source = f.read()

    entries = []
    duplicates = {}
    seen = {}

    for line in source.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*)\s*:\s*(.*)", stripped)
        if not m:
            continue

        node = m.group(1)
        rest = m.group(2).strip()

        # check duplicates
        if node in seen:
            duplicates.setdefault(node, [seen[node]]).append(rest)
        else:
            seen[node] = rest

        # parse structure
        kv_pairs = re.findall(r"([a-zA-Z][a-zA-Z0-9_-]*):(\S+)", rest)
        has_desc = " / " in rest

        entries.append({
            "node": node,
            "value": rest,
            "keys": [k for k, v in kv_pairs],
            "has_desc": has_desc,
            "key_count": len(kv_pairs),
        })

    return {
        "path": flat_path,
        "total_entries": len(entries),
        "unique_nodes": len(seen),
        "duplicates": duplicates,
        "entries": entries,
        "keys_used": sorted(set(k for e in entries for k in e["keys"])),
    }
