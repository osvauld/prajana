#!/usr/bin/env python3
"""
collect_graph_patterns.py — query the live graph from test sentences to find
structural patterns the static analyzers cannot see.

This is the data-collection layer. It:
  1. Reads every sentence that was ever sent to anuvada-ganana / build-question-graph
     from the pytest cache.
  2. Runs each unique sentence through the pipeline at every stage.
  3. Records what exists at each stage, what changed, what was born from what.
  4. Queries the graph directly for structural patterns:
       - which edge types co-occur
       - which mithya words never become satya (kosha gaps)
       - which satya concepts never get a sankhya value (binding gaps)
       - which concept pairs co-occur but have no mantra between them (mantra gaps)
       - which sentences produce identical graph structure (template clusters)
       - which words appear adjacent but produce nothing new (dead adjacency)
       - what the graph looks like right before a no-match vs a pass

Output: /tmp/graph_patterns.json
Read by: tools/analyze_graph_patterns.py

Usage:
    python3 tools/collect_graph_patterns.py [--socket /tmp/vy.sock] [--cache PATH]
    python3 tools/collect_graph_patterns.py --only nouns    # just mithya analysis
    python3 tools/collect_graph_patterns.py --only gaps     # just binding gaps
    python3 tools/collect_graph_patterns.py --only clusters # just template clusters
    python3 tools/collect_graph_patterns.py --only birth    # just emergence patterns
"""

import json, sys, os, glob, re, socket as socket_mod, argparse
from collections import defaultdict, Counter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "vyakarana", "tests"))

SOCKET_DEFAULT = "/tmp/vy.sock"
CACHE_DEFAULT = os.path.join(REPO_ROOT, "vyakarana", ".pytest_cache", "vyakarana")
OUT_PATH = "/tmp/graph_patterns.json"


# ── socket ─────────────────────────────────────────────────────────────────────


def q(sock_path, expr):
    """Eval a tantra2 expression, return the result."""
    with socket_mod.socket(socket_mod.AF_UNIX, socket_mod.SOCK_STREAM) as s:
        s.connect(sock_path)
        cmd = json.dumps({"command": "eval-json", "expr": expr})
        s.sendall((cmd + "\n").encode())
        data = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
            try:
                r = json.loads(data)
                return r.get("result")
            except Exception:
                continue
    return None


def safe_q(sock_path, expr):
    try:
        return q(sock_path, expr)
    except Exception:
        return None


# ── sentence extraction from test cache ────────────────────────────────────────


def load_test_sentences(cache_dir):
    """Return list of {sentence, test, outcome, output} from pytest cache."""
    entries = []
    seen = set()
    for f in sorted(glob.glob(os.path.join(cache_dir, "*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        test = d.get("test", "").split("::")[-1]
        outcome = d.get("outcome", "")
        for c in d.get("calls", []):
            inp = c.get("input", "")
            out = str(c.get("output", ""))
            # extract sentence from anuvada-ganana or build-question-graph call
            for fn in ("anuvada-ganana", "build-question-graph"):
                if fn not in inp:
                    continue
                parts = inp.split('"')
                if len(parts) >= 2:
                    sentence = parts[1]
                    if len(sentence) > 3 and sentence not in seen:
                        seen.add(sentence)
                        entries.append(
                            {
                                "sentence": sentence,
                                "test": test,
                                "outcome": outcome,
                                "output": out[:120],
                                "fn": fn,
                                "no_match": "no match" in out,
                                "has_value": ("we find" in out or " = " in out),
                            }
                        )
    return entries


# ── stage-by-stage graph trace ─────────────────────────────────────────────────


def trace_sentence(sock_path, sentence):
    """
    Run sentence through every pipeline stage.
    Return dict with edge sets and node sets at each stage,
    and what was BORN (newly appeared) at each transition.
    """
    j = json.dumps(sentence)

    raw = safe_q(sock_path, f"build-question-graph {j}") or []
    refined = (
        safe_q(
            sock_path, f"fixpoint (build-question-graph {j}) (fn g -> avrti-refine g)"
        )
        or []
    )
    expanded = safe_q(sock_path, f"kosha-expand {json.dumps(refined)}") or []

    def edges(g):
        return {t[1] for t in g if isinstance(t, list) and len(t) == 3}

    def nodes_by_edge(g, edge):
        return [t[0] for t in g if isinstance(t, list) and len(t) == 3 and t[1] == edge]

    def triples_by_edge(g, edge):
        return [t for t in g if isinstance(t, list) and len(t) == 3 and t[1] == edge]

    raw_edges = edges(raw)
    ref_edges = edges(refined)
    exp_edges = edges(expanded)

    # what was born at each stage
    born_in_refine = ref_edges - raw_edges
    born_in_expand = exp_edges - ref_edges

    # mithya words that are still mithya after refine (never promoted)
    mithya_before = set(nodes_by_edge(raw, "mithya"))
    satya_after = set(nodes_by_edge(refined, "satya"))
    mithya_still = mithya_before - satya_after  # kosha gap candidates

    # satya concepts that have no sankhya (bound but unvalued)
    satya_nodes = set(nodes_by_edge(refined, "satya"))
    sankhya_nodes = set(
        t[0]
        for t in refined
        if isinstance(t, list) and len(t) == 3 and t[1] == "sankhya"
    )
    unvalued_satya = satya_nodes - sankhya_nodes

    # co-occurring concept pairs in sankhya
    sankhya_pairs = sorted(sankhya_nodes)
    co_pairs = []
    for i in range(len(sankhya_pairs)):
        for j in range(i + 1, len(sankhya_pairs)):
            co_pairs.append((sankhya_pairs[i], sankhya_pairs[j]))

    # what the solve-for is
    sf_result = safe_q(sock_path, f"extract-solve-for {json.dumps(refined)}") or [
        False,
        "",
        "",
    ]
    solve_for = sf_result[1] if len(sf_result) > 1 else ""
    scope_entity = sf_result[2] if len(sf_result) > 2 else ""
    has_intent = sf_result[0] if len(sf_result) > 0 else False

    # did match-mantra find something?
    mm = safe_q(sock_path, f"match-mantra {json.dumps(refined)}") or []
    matched = bool(mm)
    matched_mantra = mm[0] if mm else ""

    # entity count
    entities = nodes_by_edge(refined, "prathama-vibhakti")

    # viraam count (sentence boundary count — how many clauses)
    viraam_count = len(
        [t for t in raw if isinstance(t, list) and len(t) == 3 and t[1] == "viraam"]
    )

    return {
        "sentence": sentence,
        "raw_edges": sorted(raw_edges),
        "ref_edges": sorted(ref_edges),
        "exp_edges": sorted(exp_edges),
        "born_in_refine": sorted(born_in_refine),
        "born_in_expand": sorted(born_in_expand),
        "mithya_words": sorted(mithya_before),
        "mithya_still": sorted(mithya_still),  # kosha gaps
        "satya_nodes": sorted(satya_nodes),
        "unvalued_satya": sorted(unvalued_satya),  # binding gaps
        "sankhya_nodes": sorted(sankhya_nodes),
        "co_pairs": co_pairs,  # concept co-occurrence
        "solve_for": solve_for,
        "scope_entity": scope_entity,
        "has_intent": has_intent,
        "entity_count": len(entities),
        "entities": entities,
        "viraam_count": viraam_count,
        "matched": matched,
        "matched_mantra": matched_mantra,
    }


# ── pattern aggregation ────────────────────────────────────────────────────────


def aggregate_patterns(traces, test_sentences):
    """
    Find patterns across all traces:
    - kosha gaps: mithya words never promoted
    - binding gaps: satya concepts never valued
    - mantra gaps: concept pairs that co-occur but no mantra bridges them
    - adjacency birth: what mithya word + what satya word produced a new concept
    - template clusters: sentences with identical edge-type signature
    - no-match anatomy: what is structurally different about no-match sentences
    """

    # build lookup by sentence
    by_sentence = {t["sentence"]: t for t in traces}
    outcome_by_sentence = {s["sentence"]: s for s in test_sentences}

    # ── kosha gaps ─────────────────────────────────────────────────────────────
    kosha_gaps = Counter()
    for tr in traces:
        for w in tr["mithya_still"]:
            kosha_gaps[w] += 1

    # ── binding gaps ───────────────────────────────────────────────────────────
    binding_gaps = Counter()
    for tr in traces:
        for c in tr["unvalued_satya"]:
            binding_gaps[c] += 1

    # ── mantra gaps: co-occurring concepts with no mantra match ────────────────
    mantra_gap_pairs = Counter()
    for tr in traces:
        s_info = outcome_by_sentence.get(tr["sentence"], {})
        if s_info.get("no_match") and tr["has_intent"]:
            for pair in tr["co_pairs"]:
                mantra_gap_pairs[pair] += 1

    # ── template clusters: group by edge-type signature ────────────────────────
    clusters = defaultdict(list)
    for tr in traces:
        sig = tuple(sorted(tr["ref_edges"]))
        clusters[sig].append(tr["sentence"])

    cluster_report = []
    for sig, sentences in sorted(clusters.items(), key=lambda x: -len(x[1])):
        cluster_report.append(
            {
                "signature": list(sig),
                "count": len(sentences),
                "sentences": sentences[:5],
            }
        )

    # ── adjacency birth: mithya+satya → new concept ────────────────────────────
    # if a sentence has mithya words AND satya nodes that contain a hyphen,
    # the hyphenated satya is likely the compound born from adjacency
    adjacency_births = []
    for tr in traces:
        compound_satya = [c for c in tr["satya_nodes"] if "-" in c]
        if compound_satya and tr["mithya_words"]:
            for c in compound_satya:
                parts = c.split("-")
                # which mithya word contributed?
                contributing = [
                    w
                    for w in tr["mithya_words"]
                    if any(p.startswith(w[:4]) for p in parts)
                ]
                adjacency_births.append(
                    {
                        "compound": c,
                        "mithya_from": contributing,
                        "sentence": tr["sentence"][:60],
                    }
                )

    # ── no-match anatomy: structural diff between passing and failing ──────────
    passing_traces = [
        tr
        for tr in traces
        if outcome_by_sentence.get(tr["sentence"], {}).get("has_value")
    ]
    failing_traces = [
        tr
        for tr in traces
        if outcome_by_sentence.get(tr["sentence"], {}).get("no_match")
    ]

    def avg_edge_types(trs):
        if not trs:
            return {}
        counts = Counter()
        for tr in trs:
            for e in tr["ref_edges"]:
                counts[e] += 1
        return {e: round(c / len(trs), 2) for e, c in counts.most_common()}

    passing_edge_freq = avg_edge_types(passing_traces)
    failing_edge_freq = avg_edge_types(failing_traces)

    # edges that appear in passing but not failing (structural markers of success)
    success_markers = {
        e: f
        for e, f in passing_edge_freq.items()
        if failing_edge_freq.get(e, 0) < f * 0.5
    }
    # edges that appear in failing but not passing (structural markers of failure)
    failure_markers = {
        e: f
        for e, f in failing_edge_freq.items()
        if passing_edge_freq.get(e, 0) < f * 0.5
    }

    # ── viraam patterns: how many clauses per sentence type ────────────────────
    viraam_by_outcome = defaultdict(list)
    for tr in traces:
        info = outcome_by_sentence.get(tr["sentence"], {})
        if info.get("has_value"):
            viraam_by_outcome["pass"].append(tr["viraam_count"])
        elif info.get("no_match"):
            viraam_by_outcome["no_match"].append(tr["viraam_count"])

    def avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else 0

    viraam_patterns = {
        "pass_avg_clauses": avg(viraam_by_outcome["pass"]),
        "no_match_avg_clauses": avg(viraam_by_outcome["no_match"]),
        "pass_multi_clause": sum(1 for v in viraam_by_outcome["pass"] if v > 0),
        "no_match_multi_clause": sum(1 for v in viraam_by_outcome["no_match"] if v > 0),
    }

    # ── solve-for gaps: what concepts are sought but never matched ─────────────
    sf_no_match = Counter()
    sf_matched = Counter()
    for tr in traces:
        sf = tr["solve_for"]
        if not sf:
            continue
        info = outcome_by_sentence.get(tr["sentence"], {})
        if info.get("no_match"):
            sf_no_match[sf] += 1
        elif info.get("has_value"):
            sf_matched[sf] += 1

    # concepts frequently sought but never matched = structural gap
    sf_gaps = {sf: n for sf, n in sf_no_match.items() if sf_matched.get(sf, 0) == 0}

    return {
        "kosha_gaps": kosha_gaps.most_common(40),
        "binding_gaps": binding_gaps.most_common(30),
        "mantra_gap_pairs": [(list(p), n) for p, n in mantra_gap_pairs.most_common(20)],
        "adjacency_births": adjacency_births[:50],
        "template_clusters": cluster_report[:20],
        "success_markers": success_markers,
        "failure_markers": failure_markers,
        "viraam_patterns": viraam_patterns,
        "sf_gaps": sf_gaps,
        "passing_count": len(passing_traces),
        "failing_count": len(failing_traces),
        "total_traces": len(traces),
    }


# ── main ───────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--socket", default=SOCKET_DEFAULT)
    parser.add_argument("--cache", default=CACHE_DEFAULT)
    parser.add_argument("--out", default=OUT_PATH)
    parser.add_argument(
        "--only", default=None, choices=["nouns", "gaps", "clusters", "birth", "all"]
    )
    parser.add_argument(
        "--limit", type=int, default=200, help="max sentences to trace (default 200)"
    )
    args = parser.parse_args()

    if not os.path.exists(args.socket):
        print(f"ERROR: socket not found: {args.socket}")
        sys.exit(1)

    print(f"Loading test sentences from {args.cache}...")
    test_sentences = load_test_sentences(args.cache)
    print(
        f"  {len(test_sentences)} sentence entries ({len(set(s['sentence'] for s in test_sentences))} unique)"
    )

    unique = list({s["sentence"]: s for s in test_sentences}.values())
    unique = unique[: args.limit]

    print(f"Tracing {len(unique)} sentences through pipeline...")
    traces = []
    for i, s_info in enumerate(unique):
        sentence = s_info["sentence"]
        if i % 20 == 0:
            print(f"  [{i}/{len(unique)}] {sentence[:50]!r}")
        tr = trace_sentence(args.socket, sentence)
        tr["test"] = s_info["test"]
        tr["outcome"] = s_info["outcome"]
        tr["no_match"] = s_info["no_match"]
        tr["has_value"] = s_info["has_value"]
        traces.append(tr)

    print("Aggregating patterns...")
    patterns = aggregate_patterns(traces, test_sentences)

    result = {
        "traces": traces,
        "patterns": patterns,
    }

    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)

    size = os.path.getsize(args.out)
    print(f"\nWritten: {args.out} ({size:,} bytes)")
    print(f"  {patterns['total_traces']} traces")
    print(
        f"  {patterns['passing_count']} passing / {patterns['failing_count']} failing"
    )
    print(f"  {len(patterns['kosha_gaps'])} kosha gaps")
    print(f"  {len(patterns['binding_gaps'])} binding gaps")
    print(f"  {len(patterns['adjacency_births'])} adjacency birth instances")
    print(f"  {len(patterns['template_clusters'])} template clusters")
    print(f"\nRun: python3 tools/analyze_graph_patterns.py")


if __name__ == "__main__":
    main()
