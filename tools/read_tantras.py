#!/usr/bin/env python3
"""
read_tantras.py — read, group, search, and query all tantra3 files.

Purpose: give an LLM (or human) a single tool to ingest all 72 tantras
in one go, by logical group, or via targeted queries.

Modes:
  --all              dump every tantra file, grouped by directory
  --group NAME       dump one group (pipeline, sankhya, avrti, ...)
  --tantra NAME      dump a single tantra by name (no path needed)
  --summary          one-line-per-tantra: name, lines, takes, calls, return type
  --callgraph        static call graph: which tantra calls which
  --search PATTERN   regex search across all tantra source
  --callers NAME     who calls this tantra?
  --callees NAME     what does this tantra call?
  --json             structured JSON output (combines with other modes)

Groups (from session 10 analysis):
  pipeline     — 19 files, main pipeline orchestration + steps
  avrti        — 5 files, refinement passes (fixpoint, anumana)
  sankhya      — 4 files, number handling + count chain
  match        — 6 files, mantra matching + scope
  anuvada      — 9 files, proof/reasoning emission
  equations    — 11 files, physics equation tantras
  vishesa      — 4 files, entity typing + rashi
  sandhi       — 3 files, compound resolution
  vibhakti     — 2 files, grammar case handling
  boot         — 2 files, bootstrap + reload
  debug        — 1 file, mantra coverage
  lookup       — 1 file, shabda lookup

Usage:
  python3 tools/read_tantras.py --all
  python3 tools/read_tantras.py --group pipeline
  python3 tools/read_tantras.py --summary
  python3 tools/read_tantras.py --callgraph
  python3 tools/read_tantras.py --search "viveka"
  python3 tools/read_tantras.py --tantra execute-mantra
  python3 tools/read_tantras.py --callers derive-chain
  python3 tools/read_tantras.py --callees anuvada-ganana
  python3 tools/read_tantras.py --summary --json | jq '.'
"""

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict, OrderedDict

# ── paths ──────────────────────────────────────────────────────────────────────

HERE = os.path.dirname(os.path.abspath(__file__))
BRAHMAN = os.path.join(HERE, "..", "brahman")
YANTRA = os.path.join(BRAHMAN, "yantra")

# ── group definitions (ten natural groups from session 10) ─────────────────────

GROUPS = OrderedDict(
    [
        ("pipeline", "main pipeline orchestration + derive/execute steps"),
        ("avrti", "refinement passes (fixpoint, assertion, anumana)"),
        ("sankhya", "number handling + count chain"),
        ("match", "mantra matching + scope + forward/inverse"),
        ("anuvada", "proof/reasoning emission (pratijna, hetu, etc.)"),
        ("equations", "physics equation tantras (ke, momentum, etc.)"),
        ("vishesa", "entity typing, rashi, agra-bandha"),
        ("sandhi", "compound resolution"),
        ("vibhakti", "grammar case handling"),
        ("boot", "bootstrap + reload"),
        ("debug", "mantra coverage"),
        ("lookup", "shabda lookup"),
    ]
)

# ── tantra3 source parser (regex-based, no server needed) ─────────────────────


def find_all_tantras():
    """Find all .tantra3 files under brahman/yantra/, return sorted list."""
    pattern = os.path.join(YANTRA, "**", "*.tantra3")
    return sorted(glob.glob(pattern, recursive=True))


def tantra_group(path):
    """Extract group name from path (the directory under yantra/)."""
    rel = os.path.relpath(path, YANTRA)
    parts = rel.split(os.sep)
    return parts[0] if len(parts) > 1 else "root"


def tantra_name(path):
    """Extract tantra name from path (filename without extension)."""
    return os.path.splitext(os.path.basename(path))[0]


def parse_tantra(path):
    """Parse a tantra3 file into a structured dict (no server needed).

    Extracts:
      - name: tantra name from 'tantra3 NAME' header
      - takes: list of parameter names
      - bindings: list of {name, expr_summary} for each let-binding
      - calls: list of tantra/function names called (heuristic)
      - returns: the return expression summary
      - comments: list of comment lines (stripped of --)
      - scans: count of scan blocks
      - conds: count of cond expressions
      - froms: count of from/where expressions
      - lines: total line count
      - source: raw source text
    """
    try:
        source = open(path).read()
    except Exception:
        return None

    lines = source.split("\n")
    line_count = len(lines)

    # tantra name
    name_match = re.match(r"^tantra3\s+([a-z][a-z0-9-]*)", source)
    name = name_match.group(1) if name_match else tantra_name(path)

    # takes (parameters)
    takes = re.findall(r"^takes\s+([a-z][a-z0-9-]*)", source, re.MULTILINE)

    # comments
    comments = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("--"):
            comments.append(stripped[2:].strip())

    # bindings: NAME = EXPR (top-level, column 0)
    bindings = []
    for line in lines:
        m = re.match(r"^([a-z][a-z0-9-]*)\s*=\s*(.+)", line)
        if m:
            bname = m.group(1)
            expr = m.group(2).strip()
            # truncate long expressions for summary
            summary = expr[:120] + "..." if len(expr) > 120 else expr
            bindings.append({"name": bname, "expr": summary})

    # return expression
    ret_match = re.search(r"^return\s+(.+)", source, re.MULTILINE)
    returns = ret_match.group(1).strip() if ret_match else None

    # count structural elements
    scan_count = len(re.findall(r"\bscan\s+\S+\s+\[", source))
    cond_count = source.count(" cond ") + source.count("(cond ")
    from_count = len(re.findall(r"\|\s*where\b", source))
    reduce_count = len(re.findall(r"\breduce\b", source))

    # extract calls: known tantra names and primitives
    # heuristic: any hyphenated identifier that appears as first token after =
    # or as a function call (name followed by args)
    # We'll collect all identifiers and filter later against known tantra names
    all_identifiers = set(re.findall(r"\b([a-z][a-z0-9]*(?:-[a-z0-9]+)+)\b", source))
    # Remove the tantra's own name, parameters, and binding names
    own_names = {name} | set(takes) | {b["name"] for b in bindings}
    # Known keywords/primitives to exclude
    keywords = {
        "tantra3",
        "takes",
        "return",
        "done",
        "otherwise",
        "cond",
        "let",
        "scan",
        "from",
        "where",
        "collect",
        "emit",
        "set",
        "fn",
        # primitives (not tantras)
        "to-string",
        "to-number",
        "string-length",
        "nth",
        "length",
        "append",
        "filter",
        "reduce",
        "map",
        "exists",
        "member",
        "unique",
        "gt",
        "lt",
        "eq",
        "neq",
        "and",
        "or",
        "not",
        "sub",
        "mul",
        "add",
        "div",
        "apply-op",
        "debug-print",
        "walk",
        "walk-in",
        "emit-node",
        "inspect-node",
        "shabda",
        "shabda-anveshana",
        "word-node",
        "call-tantra",
        "fixpoint",
        "ppr",
        "has-edge",
    }
    call_candidates = all_identifiers - own_names - keywords

    return {
        "name": name,
        "path": path,
        "group": tantra_group(path),
        "takes": takes,
        "bindings": bindings,
        "returns": returns,
        "comments": comments,
        "scans": scan_count,
        "conds": cond_count,
        "froms": from_count,
        "reduces": reduce_count,
        "lines": line_count,
        "calls": sorted(call_candidates),
        "source": source,
    }


def load_all_tantras():
    """Load and parse all tantras, return dict keyed by name."""
    tantras = OrderedDict()
    for path in find_all_tantras():
        parsed = parse_tantra(path)
        if parsed:
            tantras[parsed["name"]] = parsed
    return tantras


# ── call graph (refine using known tantra names) ──────────────────────────────


def build_call_graph(tantras):
    """Refine call candidates: only keep names that are actual tantra names."""
    known_names = set(tantras.keys())
    graph = {}  # name -> list of called tantra names
    for name, t in tantras.items():
        # filter calls to only known tantra names
        actual_calls = [c for c in t["calls"] if c in known_names and c != name]
        graph[name] = sorted(set(actual_calls))
    return graph


def build_reverse_graph(call_graph):
    """Reverse call graph: name -> list of tantras that call this one."""
    reverse = defaultdict(list)
    for caller, callees in call_graph.items():
        for callee in callees:
            reverse[callee].append(caller)
    return {k: sorted(v) for k, v in reverse.items()}


# ── output formatters ─────────────────────────────────────────────────────────


def fmt_separator(title, width=80):
    """Section separator."""
    return f"\n{'=' * width}\n  {title}\n{'=' * width}\n"


def fmt_file_header(t, width=80):
    """File header with metadata."""
    meta = f"[{t['group']}] {t['lines']} lines"
    if t["takes"]:
        meta += f" | takes: {', '.join(t['takes'])}"
    if t["scans"]:
        meta += f" | scans: {t['scans']}"
    if t["conds"]:
        meta += f" | conds: {t['conds']}"
    return f"\n{'─' * width}\n  {t['name']}  ({meta})\n  {t['path']}\n{'─' * width}"


def print_tantra(t, with_source=True):
    """Print a single tantra with optional source."""
    print(fmt_file_header(t))
    if with_source:
        print(t["source"])


def print_group(tantras, group_name):
    """Print all tantras in a group."""
    group_tantras = [t for t in tantras.values() if t["group"] == group_name]
    if not group_tantras:
        print(f"No tantras found in group '{group_name}'")
        print(f"Available groups: {', '.join(GROUPS.keys())}")
        return

    desc = GROUPS.get(group_name, "")
    total_lines = sum(t["lines"] for t in group_tantras)
    print(
        fmt_separator(
            f"{group_name}/ — {len(group_tantras)} files, {total_lines} lines — {desc}"
        )
    )

    for t in sorted(group_tantras, key=lambda x: x["name"]):
        print_tantra(t)


def print_all(tantras):
    """Print all tantras grouped by directory."""
    groups_seen = OrderedDict()
    for t in tantras.values():
        g = t["group"]
        if g not in groups_seen:
            groups_seen[g] = []
        groups_seen[g].append(t)

    for group_name, group_tantras in groups_seen.items():
        desc = GROUPS.get(group_name, "")
        total_lines = sum(t["lines"] for t in group_tantras)
        print(
            fmt_separator(
                f"{group_name}/ — {len(group_tantras)} files, {total_lines} lines — {desc}"
            )
        )
        for t in sorted(group_tantras, key=lambda x: x["name"]):
            print_tantra(t)


def print_summary(tantras):
    """One-line-per-tantra summary table."""
    # group tantras by group
    by_group = defaultdict(list)
    for t in tantras.values():
        by_group[t["group"]].append(t)

    total_lines = sum(t["lines"] for t in tantras.values())
    print(f"\n{'=' * 100}")
    print(f"  TANTRA SUMMARY — {len(tantras)} tantras, {total_lines} total lines")
    print(f"{'=' * 100}\n")

    for group_name in GROUPS:
        group_tantras = by_group.get(group_name, [])
        if not group_tantras:
            continue
        gl = sum(t["lines"] for t in group_tantras)
        print(
            f"  {group_name}/ ({len(group_tantras)} files, {gl} lines) — {GROUPS[group_name]}"
        )
        print(f"  {'─' * 96}")
        print(
            f"  {'Name':<30} {'Lines':>5} {'Takes':>5} {'Binds':>5} {'Calls':>5} {'Scans':>5} {'Conds':>5} {'Returns'}"
        )
        print(f"  {'─' * 96}")
        for t in sorted(group_tantras, key=lambda x: x["name"]):
            ret = (
                t["returns"][:30] + "..."
                if t["returns"] and len(t["returns"]) > 30
                else (t["returns"] or "—")
            )
            print(
                f"  {t['name']:<30} {t['lines']:>5} {len(t['takes']):>5} {len(t['bindings']):>5} {len(t['calls']):>5} {t['scans']:>5} {t['conds']:>5} {ret}"
            )
        print()

    # handle any groups not in GROUPS dict
    for group_name, group_tantras in by_group.items():
        if group_name not in GROUPS:
            gl = sum(t["lines"] for t in group_tantras)
            print(f"  {group_name}/ ({len(group_tantras)} files, {gl} lines)")
            print(f"  {'─' * 96}")
            for t in sorted(group_tantras, key=lambda x: x["name"]):
                ret = (
                    t["returns"][:30] + "..."
                    if t["returns"] and len(t["returns"]) > 30
                    else (t["returns"] or "—")
                )
                print(
                    f"  {t['name']:<30} {t['lines']:>5} {len(t['takes']):>5} {len(t['bindings']):>5} {len(t['calls']):>5} {t['scans']:>5} {t['conds']:>5} {ret}"
                )
            print()


def print_callgraph(tantras):
    """Print the static call graph."""
    cg = build_call_graph(tantras)
    rcg = build_reverse_graph(cg)

    print(fmt_separator("CALL GRAPH — who calls whom"))

    # sort by number of outgoing calls (most connected first)
    for name in sorted(cg.keys(), key=lambda n: (-len(cg[n]), n)):
        callees = cg[name]
        callers = rcg.get(name, [])
        if not callees and not callers:
            continue
        group = tantras[name]["group"]
        out = f"  {name:<35} [{group}]"
        if callees:
            out += f"\n    calls  → {', '.join(callees)}"
        if callers:
            out += f"\n    from   ← {', '.join(callers)}"
        print(out)
        print()

    # hub analysis
    print(fmt_separator("HUB TANTRAS — most called"))
    hubs = sorted(rcg.items(), key=lambda x: -len(x[1]))
    for name, callers in hubs[:15]:
        print(f"  {name:<35} called by {len(callers):>2}: {', '.join(callers)}")

    # leaf analysis
    leaves = [n for n, calls in cg.items() if not calls and n not in rcg]
    if leaves:
        print(fmt_separator("LEAF TANTRAS — neither call nor are called"))
        for name in sorted(leaves):
            print(f"  {name} [{tantras[name]['group']}]")


def print_search(tantras, pattern):
    """Search all tantra source for a regex pattern."""
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        print(f"Invalid regex: {e}")
        return

    total_matches = 0
    for t in tantras.values():
        matches = []
        for i, line in enumerate(t["source"].split("\n"), 1):
            if regex.search(line):
                matches.append((i, line.rstrip()))
        if matches:
            total_matches += len(matches)
            print(f"\n  {t['name']} [{t['group']}] — {len(matches)} matches")
            print(f"  {t['path']}")
            for lineno, line in matches:
                print(f"    {lineno:>4}: {line}")

    if total_matches == 0:
        print(f"No matches for '{pattern}' across {len(tantras)} tantras.")
    else:
        print(f"\n  Total: {total_matches} matches across {len(tantras)} tantras.")


def print_callers(tantras, name):
    """Show who calls a given tantra."""
    cg = build_call_graph(tantras)
    rcg = build_reverse_graph(cg)
    callers = rcg.get(name, [])
    if not callers:
        print(f"No tantras call '{name}'.")
        # check if it exists
        if name not in tantras:
            print(f"('{name}' is not a known tantra name)")
        return
    print(f"\n  Tantras that call '{name}' ({len(callers)}):\n")
    for caller in callers:
        t = tantras[caller]
        print(f"    {caller:<35} [{t['group']}] {t['lines']} lines")


def print_callees(tantras, name):
    """Show what a given tantra calls."""
    if name not in tantras:
        print(f"'{name}' is not a known tantra name.")
        return
    cg = build_call_graph(tantras)
    callees = cg.get(name, [])
    t = tantras[name]
    print(f"\n  '{name}' [{t['group']}] calls ({len(callees)}):\n")
    if not callees:
        print("    (no tantra calls)")
        return
    for callee in callees:
        ct = tantras[callee]
        print(f"    {callee:<35} [{ct['group']}] {ct['lines']} lines")


# ── JSON output ───────────────────────────────────────────────────────────────


def to_json_summary(tantras):
    """Structured JSON for all tantras (no source, for piping)."""
    result = {
        "total_tantras": len(tantras),
        "total_lines": sum(t["lines"] for t in tantras.values()),
        "groups": {},
        "tantras": {},
    }
    for group_name, desc in GROUPS.items():
        group_tantras = [t for t in tantras.values() if t["group"] == group_name]
        if group_tantras:
            result["groups"][group_name] = {
                "description": desc,
                "count": len(group_tantras),
                "total_lines": sum(t["lines"] for t in group_tantras),
                "tantras": [
                    t["name"] for t in sorted(group_tantras, key=lambda x: x["name"])
                ],
            }
    for t in tantras.values():
        result["tantras"][t["name"]] = {
            "group": t["group"],
            "path": t["path"],
            "lines": t["lines"],
            "takes": t["takes"],
            "bindings": [b["name"] for b in t["bindings"]],
            "calls": t["calls"],
            "returns": t["returns"],
            "scans": t["scans"],
            "conds": t["conds"],
            "froms": t["froms"],
            "reduces": t["reduces"],
            "comments": t["comments"],
        }
    return result


def to_json_callgraph(tantras):
    """JSON call graph."""
    cg = build_call_graph(tantras)
    rcg = build_reverse_graph(cg)
    return {
        "calls": cg,
        "called_by": rcg,
    }


def to_json_full(tantras):
    """Full JSON with source (for LLM ingestion)."""
    result = {}
    for t in tantras.values():
        result[t["name"]] = {
            "group": t["group"],
            "path": t["path"],
            "lines": t["lines"],
            "takes": t["takes"],
            "bindings": t["bindings"],
            "calls": t["calls"],
            "returns": t["returns"],
            "scans": t["scans"],
            "conds": t["conds"],
            "comments": t["comments"],
            "source": t["source"],
        }
    return result


# ── main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Read, group, search, and query all tantra3 files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tools/read_tantras.py --all                  # dump everything
  python3 tools/read_tantras.py --group pipeline       # just pipeline/
  python3 tools/read_tantras.py --summary              # one-line overview
  python3 tools/read_tantras.py --callgraph            # who calls whom
  python3 tools/read_tantras.py --search "viveka"      # find pattern
  python3 tools/read_tantras.py --tantra execute-mantra
  python3 tools/read_tantras.py --callers derive-chain
  python3 tools/read_tantras.py --callees anuvada-ganana
  python3 tools/read_tantras.py --summary --json | jq '.'
        """,
    )
    parser.add_argument(
        "--all", action="store_true", help="Dump all tantras grouped by directory"
    )
    parser.add_argument(
        "--group", type=str, help="Dump one group (pipeline, sankhya, avrti, ...)"
    )
    parser.add_argument("--tantra", type=str, help="Dump a single tantra by name")
    parser.add_argument(
        "--summary", action="store_true", help="One-line-per-tantra summary"
    )
    parser.add_argument("--callgraph", action="store_true", help="Static call graph")
    parser.add_argument("--search", type=str, help="Regex search across all tantras")
    parser.add_argument("--callers", type=str, help="Who calls this tantra?")
    parser.add_argument("--callees", type=str, help="What does this tantra call?")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--groups", action="store_true", help="List available groups")

    args = parser.parse_args()

    # default to --summary if no mode specified
    if not any(
        [
            args.all,
            args.group,
            args.tantra,
            args.summary,
            args.callgraph,
            args.search,
            args.callers,
            args.callees,
            args.groups,
        ]
    ):
        args.summary = True

    tantras = load_all_tantras()

    if args.groups:
        print(f"\nAvailable groups ({len(GROUPS)}):\n")
        by_group = defaultdict(list)
        for t in tantras.values():
            by_group[t["group"]].append(t)
        for name, desc in GROUPS.items():
            count = len(by_group.get(name, []))
            total = sum(t["lines"] for t in by_group.get(name, []))
            print(f"  {name:<12} {count:>2} files  {total:>4} lines  {desc}")
        return

    if args.json:
        if args.callgraph:
            print(json.dumps(to_json_callgraph(tantras), indent=2))
        elif args.all:
            print(json.dumps(to_json_full(tantras), indent=2))
        elif args.group:
            group_tantras = {
                k: v
                for k, v in to_json_full(tantras).items()
                if tantras[k]["group"] == args.group
            }
            print(json.dumps(group_tantras, indent=2))
        elif args.tantra:
            t = tantras.get(args.tantra)
            if t:
                print(
                    json.dumps(
                        {
                            "name": t["name"],
                            "group": t["group"],
                            "path": t["path"],
                            "lines": t["lines"],
                            "takes": t["takes"],
                            "bindings": t["bindings"],
                            "calls": t["calls"],
                            "returns": t["returns"],
                            "source": t["source"],
                        },
                        indent=2,
                    )
                )
            else:
                print(json.dumps({"error": f"tantra '{args.tantra}' not found"}))
        else:
            print(json.dumps(to_json_summary(tantras), indent=2))
        return

    if args.all:
        print_all(tantras)
    elif args.group:
        print_group(tantras, args.group)
    elif args.tantra:
        t = tantras.get(args.tantra)
        if t:
            print_tantra(t)
        else:
            print(f"Tantra '{args.tantra}' not found.")
            # suggest close matches
            matches = [n for n in tantras if args.tantra in n]
            if matches:
                print(f"Did you mean: {', '.join(matches)}?")
    elif args.summary:
        print_summary(tantras)
    elif args.callgraph:
        print_callgraph(tantras)
    elif args.search:
        print_search(tantras, args.search)
    elif args.callers:
        print_callers(tantras, args.callers)
    elif args.callees:
        print_callees(tantras, args.callees)


if __name__ == "__main__":
    main()
