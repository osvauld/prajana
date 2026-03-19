#!/usr/bin/env python3
"""
analyze_graph_patterns.py — read /tmp/graph_patterns.json and report
structural patterns found by querying the live graph from test sentences.

Answers questions like:
  - Which words from test sentences never become concepts? (kosha gaps)
  - Which concepts are sought but never matchable? (mantra gaps)
  - Which two concepts always appear together but have no mantra between them?
  - What structural difference separates passing from failing sentences?
  - What new things are born from adjacency / retroactive / relational patterns?
  - Which sentence templates repeat — what is the canonical form?

Usage:
    python3 tools/analyze_graph_patterns.py
    python3 tools/analyze_graph_patterns.py --report gaps
    python3 tools/analyze_graph_patterns.py --report birth
    python3 tools/analyze_graph_patterns.py --report clusters
    python3 tools/analyze_graph_patterns.py --report anatomy

Reports: all, gaps, birth, clusters, anatomy
"""

import json, sys, os, argparse
from collections import Counter, defaultdict

DATA_PATH = "/tmp/graph_patterns.json"
SEP = "═" * 72


def load(path):
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Run: python3 tools/collect_graph_patterns.py")
        sys.exit(1)
    return json.load(open(path))


# ── reporters ──────────────────────────────────────────────────────────────────


def report_gaps(data):
    p = data["patterns"]
    print(SEP)
    print("  GAPS — things that should exist but don't")
    print(SEP)

    print(
        f"\n  Kosha gaps ({len(p['kosha_gaps'])} words never promoted from mithya to satya):"
    )
    print("  These words appear in test sentences but have no kosha entry.")
    print("  Adding them would let the pipeline resolve them to concepts.\n")
    for word, count in p["kosha_gaps"][:20]:
        print(f"    {word:<30} {count:>3}x in sentences")

    print(
        f"\n  Binding gaps ({len(p['binding_gaps'])} concepts that appear as satya but never get a value):"
    )
    print("  These concepts are recognized but the number never binds to them.\n")
    for concept, count in p["binding_gaps"][:15]:
        print(f"    {concept:<30} {count:>3}x unvalued")

    print(
        f"\n  Solve-for gaps (concepts sought but never matched — no mantra covers them):"
    )
    for sf, count in sorted(p["sf_gaps"].items(), key=lambda x: -x[1])[:15]:
        print(f"    {sf:<30} {count:>3}x sought, 0x matched")

    print(f"\n  Concept pair gaps (pairs that co-occur with intent but no match):")
    print("  These pairs appear together in sentences asking for something — a mantra")
    print(
        "  may be missing, or the janya concept names don't match what the mantra expects.\n"
    )
    for pair, count in p["mantra_gap_pairs"][:15]:
        print(f"    {pair[0]} + {pair[1]:<25} {count:>3}x co-occur, no match")


def report_birth(data):
    p = data["patterns"]
    print(SEP)
    print("  BIRTH — new things that emerge from combination")
    print(SEP)

    print(
        f"\n  Adjacency births ({len(p['adjacency_births'])} instances of mithya+satya → compound):"
    )
    print("  A mithya word (unrecognized) directly before a satya word (known concept)")
    print("  produces a new compound concept. Pattern: mithya+satya → new-satya.\n")

    # group by compound
    by_compound = defaultdict(list)
    for b in p["adjacency_births"]:
        by_compound[b["compound"]].append(b)

    for compound, instances in sorted(by_compound.items(), key=lambda x: -len(x[1])):
        contributing = set()
        for inst in instances:
            contributing.update(inst["mithya_from"])
        print(f"    '{compound}' born from: {sorted(contributing)}")
        print(f"      example: {instances[0]['sentence']!r}")

    print(f"\n  Edge types born in avrti-refine (not in raw graph):")
    print("  These edge types don't exist after word-by-word parsing —")
    print("  they emerge from the refinement passes.\n")
    born_counts = Counter()
    for tr in data["traces"]:
        for e in tr["born_in_refine"]:
            born_counts[e] += 1
    for e, n in born_counts.most_common():
        print(f"    {e:<30} {n:>3}x (born during refine)")

    print(f"\n  Edge types born in kosha-expand:")
    born_exp = Counter()
    for tr in data["traces"]:
        for e in tr["born_in_expand"]:
            born_exp[e] += 1
    for e, n in born_exp.most_common():
        print(f"    {e:<30} {n:>3}x (born during expand)")


def report_anatomy(data):
    p = data["patterns"]
    print(SEP)
    print("  ANATOMY — structural difference between passing and failing")
    print(SEP)

    print(
        f"\n  {p['passing_count']} passing sentences / {p['failing_count']} no-match sentences"
    )

    print(f"\n  Edge types that mark SUCCESS (appear in passing, absent from failing):")
    for e, f in sorted(p["success_markers"].items(), key=lambda x: -x[1])[:10]:
        print(f"    {e:<30} {f:.2f} avg freq in passing sentences")

    print(f"\n  Edge types that mark FAILURE (appear in failing, absent from passing):")
    for e, f in sorted(p["failure_markers"].items(), key=lambda x: -x[1])[:10]:
        print(f"    {e:<30} {f:.2f} avg freq in failing sentences")

    vp = p["viraam_patterns"]
    print(f"\n  Viraam (clause boundary) patterns:")
    print(f"    Passing sentences avg clauses:  {vp['pass_avg_clauses']}")
    print(f"    Failing sentences avg clauses:  {vp['no_match_avg_clauses']}")
    print(f"    Passing with multiple clauses:  {vp['pass_multi_clause']}")
    print(f"    Failing with multiple clauses:  {vp['no_match_multi_clause']}")

    # per-trace: what's different between pass and fail with same edge signature
    print(f"\n  Failing sentences with intent but no match (by missing piece):")
    has_intent_no_match = [
        tr for tr in data["traces"] if tr.get("no_match") and tr.get("has_intent")
    ]
    print(f"    Count: {len(has_intent_no_match)}")

    # group by what's missing
    missing_sankhya = [tr for tr in has_intent_no_match if not tr["sankhya_nodes"]]
    missing_entity = [tr for tr in has_intent_no_match if tr["entity_count"] == 0]
    has_kosha_gap = [tr for tr in has_intent_no_match if tr["mithya_still"]]
    has_binding_gap = [tr for tr in has_intent_no_match if tr["unvalued_satya"]]

    print(f"      no sankhya values at all:     {len(missing_sankhya)}")
    print(f"      no entities (no ownership):   {len(missing_entity)}")
    print(f"      has kosha gap (mithya stuck):  {len(has_kosha_gap)}")
    print(f"      has binding gap (unvalued):    {len(has_binding_gap)}")

    # show examples of each
    if has_kosha_gap:
        print(f"\n      Examples with kosha gap:")
        for tr in has_kosha_gap[:5]:
            print(f"        {tr['sentence'][:60]!r}")
            print(f"          mithya stuck: {tr['mithya_still']}")
    if has_binding_gap:
        print(f"\n      Examples with binding gap:")
        for tr in has_binding_gap[:5]:
            print(f"        {tr['sentence'][:60]!r}")
            print(f"          unvalued satya: {tr['unvalued_satya']}")


def report_clusters(data):
    p = data["patterns"]
    print(SEP)
    print("  CLUSTERS — sentence templates that share graph structure")
    print(SEP)
    print()
    print("  Sentences with the same edge-type signature in their refined graph")
    print("  are structurally equivalent — they follow the same template.")
    print("  Templates that are always passing vs always failing reveal which")
    print("  structural patterns the pipeline handles and which it doesn't.\n")

    traces_by_sentence = {tr["sentence"]: tr for tr in data["traces"]}

    for cluster in p["template_clusters"][:12]:
        sig = cluster["signature"]
        sentences = cluster["sentences"]
        count = cluster["count"]

        passing = sum(
            1 for s in sentences if traces_by_sentence.get(s, {}).get("has_value")
        )
        failing = sum(
            1 for s in sentences if traces_by_sentence.get(s, {}).get("no_match")
        )

        status = (
            "✓ all pass"
            if failing == 0 and passing > 0
            else "✗ all fail"
            if passing == 0 and failing > 0
            else f"mixed {passing}✓/{failing}✗"
        )

        print(f"  Template [{', '.join(sig)}]")
        print(f"    {count} sentences — {status}")
        for s in sentences[:3]:
            tr = traces_by_sentence.get(s, {})
            mark = "✓" if tr.get("has_value") else ("✗" if tr.get("no_match") else "?")
            sf = tr.get("solve_for", "")
            print(f"    {mark} {s[:60]!r}  sf={sf!r}")
        print()


def print_report(data, report="all"):
    if report in ("all", "gaps"):
        report_gaps(data)
    if report in ("all", "birth"):
        report_birth(data)
    if report in ("all", "anatomy"):
        report_anatomy(data)
    if report in ("all", "clusters"):
        report_clusters(data)
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--data", default=DATA_PATH)
    parser.add_argument(
        "--report",
        default="all",
        choices=["all", "gaps", "birth", "clusters", "anatomy"],
    )
    args = parser.parse_args()

    data = load(args.data)
    print_report(data, args.report)
