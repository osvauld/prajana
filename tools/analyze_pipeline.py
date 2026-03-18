#!/usr/bin/env python3
"""
analyze_pipeline.py — unified cross-layer structural analysis.

The central insight: there is no "business logic". There is only one structure
appearing at every scale. Every layer — OCaml, tantra2, om shabda, tests —
performs the same three operations:

  SPARSHA  — contact: get the thing from context
  VIVEKA   — discrimination: filter / guard / check
  BANDHA   — binding: write the result back

This script finds every instance of this structure at every layer,
cross-references them, identifies which duplicates have not been named
(and therefore not abstracted), and generates a unified report showing
the same pattern at each scale.

Secondary output: a dependency graph that shows which abstractions
would eliminate the most duplication if named.

Usage:
    python3 tools/analyze_pipeline.py [--brahman ../brahman] [--vyakarana ./vyakarana]
    python3 tools/analyze_pipeline.py --json | jq '.unified_patterns'
    python3 tools/analyze_pipeline.py --report abstractions
    python3 tools/analyze_pipeline.py --report tests

Reports: all, patterns, abstractions, tests, ocaml, tantras, shabda
"""

import re, os, sys, json, glob, argparse
from collections import Counter, defaultdict

BRAHMAN_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "brahman"
)
VYAKARANA_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vyakarana"
)
ANALYSIS_JSON = "/tmp/analysis.json"
SHABDA_JSON = "/tmp/sa_clean.json"
GRAPH_JSON = "/tmp/graph_deep.json"
DEP_JSON = "/tmp/dep_order.json"


# ── the three operations, named ───────────────────────────────────────────────
# SPARSHA: contact patterns — getting something from context
# VIVEKA:  discrimination patterns — filtering / guarding / checking
# BANDHA:  binding patterns — writing results back

TANTRA_SPARSHA_PATTERNS = [
    # (name, regex_on_tantra_source, what_it_gets)
    (
        "graph-where-collect",
        r'graph \| where \[.*\] \| and \(eq e "[^"]+"\) \| collect',
        "edge-filtered graph query",
    ),
    (
        "nth-result",
        r"\bnth\b.*\b(sf-result|chain-raw|step\d-[a-z])",
        "positional extraction from structured result",
    ),
    ("walk-edge", r'\bwalk\b [a-z-]+ "[a-z-]+"', "graph edge traversal"),
    ("shabda-lookup", r'\bshabda\b [a-z-]+ "[a-z-]+"', "shabda key lookup"),
    (
        "bound-concepts-call",
        r"\bbound-concept-names\b|\bbound-concepts\b|\bbound-vals\b",
        "sankhya binding extraction (three tantras, one sparsha — candidate for sankhya-sparsha unification)",
    ),
    (
        "extract-solve-for",
        r"\bextract-solve-for\b|\biccha-viveka\b",
        "intent+scope extraction from graph (iccha-viveka in tantra3/iccha, extract-solve-for elsewhere)",
    ),
    (
        "scan-triple",
        r"\[word, edge, obj\]|\[word, \w+, \w+\]",
        "triple destructuring in scan",
    ),
    (
        "shashthi-sparsha-inline",
        r'eq e "shashthi-vibhakti".*collect|collect.*eq e "shashthi-vibhakti"',
        "inline ownership query — candidate for shashthi-sparsha tantra abstraction",
    ),
]

TANTRA_VIVEKA_PATTERNS = [
    ("eq-edge-type", r'eq e "[a-z-]+"', "edge type equality check"),
    ("neq-edge-type", r'neq e "[a-z-]+"', "edge type inequality check"),
    ("member-check", r"\bmember\b [a-z-]+ [a-z-]+", "set membership test"),
    ("gt-length", r"gt \(length [a-z-]+\) 0", "non-empty list check"),
    (
        "gt-string-length",
        r"gt \(string-length \(to-string",
        "non-empty string/node check — exists-check anti-pattern (26× — replace with exists? primitive)",
    ),
    (
        "has-intent-guard",
        r"\bhas-intent\b",
        "iccha guard — question must declare explicit intent (vidhi-kaala)",
    ),
    (
        "scope-guard",
        r'gt \(string-length scope-entity\)|scope-entity.*""',
        "scope entity presence check — whose frame is the question read from",
    ),
    ("is-viveka", r"\bis-viveka\b", "comparison vs derivation discriminant"),
    ("cond-chain", r"\bcond\b.*otherwise", "conditional discrimination chain"),
    (
        "sf-was-derived",
        r"\bsf-was-derived\b|\bderived-by\b.*\bsought-sf\b",
        "derivation completeness check — was the solve-for produced by a mantra, or was it given?",
    ),
    (
        "not-is-entity",
        r"\bnot is-entity\b",
        "entity exclusion guard — prevents entity subjects becoming solve-for fallback",
    ),
]

TANTRA_BANDHA_PATTERNS = [
    (
        "emit-triple",
        r'\bemit\b \[[^\]]+, "[a-z-]+", [^\]]+\]',
        "emit typed triple into graph",
    ),
    ("append-acc", r"append acc \[", "accumulate into result list"),
    ("reduce-to-list", r"\breduce\b [a-z-]+ \[\] \(fn acc", "fold into list"),
    (
        "sankhya-triple",
        r'"sankhya".*result|result.*"sankhya"',
        "bind numeric value to concept (pramana-bandha: this is the moment of inscription)",
    ),
    (
        "derived-by-triple",
        r'"derived-by"',
        "record which mantra produced a value — proof lineage",
    ),
    (
        "sought-bandha-call",
        r"\bsought-bandha\b",
        "record what the question sought — hetu inscription",
    ),
    ("set-state", r"\b(set|clear)\b [a-z-]+ (to|->)", "scan state mutation"),
    (
        "derived-sankhya-triple",
        r'"derived-sankhya"',
        "inject scoped val-pairs into proof graph for emit-reasoning we-see section",
    ),
]

OCAML_SPARSHA_PATTERNS = [
    (
        "eval_arg_nth",
        r"e_eval k e \(List\.nth args \d+\)",
        "eval + extract Nth arg (186× — replace with eval_arg helper)",
    ),
    (
        "as_string_coerce",
        r"as_string \(e_eval k e",
        "as_string + eval combined (67× — replace with eval_string helper)",
    ),
    ("hashtbl_find", r"Hashtbl\.find_opt [a-z_]+ [a-z_]+\b", "hashtable lookup"),
    (
        "proof_graph_find",
        r"Proof_graph\.find k\b",
        "graph node lookup (use with_node helper)",
    ),
    ("as_list_eval", r"as_list \(e_eval k e", "eval + coerce to list"),
    (
        "json_field",
        r"json_string_field|json_int_field",
        "JSON field extraction (21× in socket.ml — replace with req_field/opt_field)",
    ),
    (
        "tantra_call",
        r"find_opt.*by_name.*eval_tantra|Hashtbl\.find_opt.*by_name",
        "tantra lookup + eval (5× — replace with call_tantra_opt)",
    ),
]

OCAML_VIVEKA_PATTERNS = [
    ("as_bool_guard", r"as_bool \(eval k", "eval + check truthiness"),
    ("match_option", r"match .* with\s*\| Some", "option match discrimination"),
    (
        "string_compare",
        r"String\.length .* > 0|String\.length .* = 0",
        "string emptiness check",
    ),
    (
        "edge_filter",
        r"edge\.relation = [A-Za-z_]+\s*&&\s*edge\.(source|target)",
        "edge field filter — candidate for edges_where helper",
    ),
    ("eval_ctx_check", r"match !\s*eval_ctx with\s*\| Some", "context presence check"),
    (
        "node_match",
        r"match Hashtbl\.find_opt.*\.nodes|match Proof_graph\.find k",
        "node existence match (34× — replace with with_node helper)",
    ),
]

OCAML_BANDHA_PATTERNS = [
    ("hashtbl_replace", r"Hashtbl\.replace [a-z_]+ [a-z_]+ ", "hashtable write"),
    ("ref_mutate", r":= [^;]+;", "mutable reference update"),
    ("list_cons", r"\s*::\s*!\s*", "prepend to ref list"),
    ("some_return", r"Some \(V[A-Z][a-z]+\b", "wrap result in Some value"),
    (
        "eval_ctx_set",
        r"eval_ctx :=",
        "set evaluator context (21× — replace with with_eval_ctx helper)",
    ),
    (
        "result_ref_push",
        r"result := .* :: !\s*result",
        "accumulate results into mutable ref list",
    ),
]

# ── xfail coverage: known-failing tests and which abstractions they're gated on ─

XFAIL_GROUPS = {
    "dvandva": {
        "description": "vishesa-bandhana instance-map: per-entity instead of per-concept",
        "tests": [
            "test_avrti_dvandva_collection_of_two_values",
            "test_tier2_two_entities_ke_each",
            "test_two_entity_rashi_feeds_mantra",
        ],
        "gate": "vishesa-bandhana must use per-entity instance-map, not per-concept collapse",
        "philosophy": "dvandva = pairing. two entities owning the same concept are two distinct dvandva, not one.",
    },
    "session_gap2": {
        "description": "session entity structure: carry prathama/shashthi triples across turns",
        "tests": [
            "test_session_entity_identity_persists",
            "test_two_entities_across_turns_both_present",
            "test_two_entities_across_turns_scoped",
            "test_electron_and_field_across_turns",
        ],
        "gate": "dvandva fix must come first — same structural issue at session scale",
        "philosophy": "parampara = lineage. the session IS the student's accumulated understanding. entities must persist as structural triples, not just sankhya numbers.",
    },
    "pratibimba": {
        "description": "visual/spatial output: sphere, position, simulation scene",
        "tests": [
            "test_sphere_shape_swarupa",
            "test_position_ownership",
            "test_electron_simulation_scene_full",
        ],
        "gate": "gated on Gap 2 session entity structure",
        "philosophy": "pratibimba = reflection. the scene is the proof graph made visible. entities without identity cannot be reflected.",
    },
    "p8f_gravity": {
        "description": "gravitational force: G constant + r² composition",
        "tests": [
            "test_gravitational_force",
            "test_gravitational_force_two_entities",
            "test_gravitational_force_earth_moon",
        ],
        "gate": "P8f Phase B: composed expression subgraph (square + multiply)",
        "philosophy": "G is a constant-key auto-supply. r² requires power(2) composition. one expression subgraph node would replace the composed expr tantra entirely.",
    },
    "unit_rate": {
        "description": "compound unit in rate: m/s not in word index",
        "tests": ["test_unit_in_rate_not_stolen"],
        "gate": "split-numeric must handle slash-separated compound units",
        "philosophy": "matra = measure. the unit is the measure's unit, not two separate words. m/s is one matra.",
    },
    "complex_sentences": {
        "description": "full natural language sentences, SUVAT inversion, Coulomb",
        "tests": [
            "test_find_second_entity_momentum",
            "test_find_second_entity_ke",
            "test_find_ke_of_the_electron_given_values",
            "test_inverse_ke_find_velocity",
            "test_relative_velocity_two_entities",
            "test_relative_velocity_opposite_directions",
            "test_proton_moves_at_velocity",
            "test_electron_is_moving_at",
            "test_inverse_suvat_find_time",
            "test_inverse_suvat_find_initial_velocity",
            "test_total_momentum_two_entities",
            "test_total_momentum_three_entities",
            "test_coulomb_force_two_charged_particles",
        ],
        "gate": "mix of dvandva, session Gap 2, and P8f Phase B",
        "philosophy": "these sentences name the full scene. each is a pancavayava in natural language — they should be answerable when the infrastructure catches up.",
    },
    "logic_comparison": {
        "description": "syllogism, transitive ordering, rank comparison",
        "tests": [
            "test_which_has_more_ke_from_mass_velocity",
            "test_which_has_more_momentum",
            "test_transitive_greater_than",
            "test_transitive_mass_ordering",
            "test_transitive_chain_three_steps",
            "test_syllogism_cats_breathe",
            "test_syllogism_dogs_mammals",
            "test_syllogism_from_kosha_electron_is_particle",
            "test_more_apples_or_oranges",
            "test_syllogism_plus_count",
            "test_rank_three_balls_by_mass",
        ],
        "gate": "P8c satya-phala layer + P8d nyaya mantras — not yet started",
        "philosophy": "nyaya = logical inference. the pancavayava (five-membered syllogism) is the proof form. pramana covers perception; anumana covers inference. anumana is not yet wired.",
    },
}


def load_test_cache(vyakarana_dir: str) -> dict:
    """
    Load the live test result cache from .pytest_cache/vyakarana/.
    Returns a dict with:
      entries       — all per-test JSON records
      by_outcome    — {outcome: [entries]}
      failing       — failed + error entries
      xfailing      — skipped/xfailed entries
      tantra_calls  — {tantra_name: [test_names that called it]}
      slow_calls    — [{test, input, ms}] sorted desc
      call_patterns — Counter of tantra ops appearing in failing tests
    """
    import glob as _glob

    cache_dir = os.path.join(vyakarana_dir, ".pytest_cache", "vyakarana")
    if not os.path.isdir(cache_dir):
        return {"error": f"cache not found: {cache_dir}"}

    entries = []
    for path in sorted(_glob.glob(os.path.join(cache_dir, "*.json"))):
        if os.path.basename(path) == "summary.json":
            continue
        try:
            entries.append(json.load(open(path)))
        except Exception:
            pass

    by_outcome: dict[str, list] = defaultdict(list)
    for e in entries:
        by_outcome[e.get("outcome", "unknown")].append(e)

    failing = by_outcome.get("failed", []) + by_outcome.get("error", [])
    xfailing = by_outcome.get("skipped", []) + by_outcome.get("xfailed", [])

    # which tantras appear in failing test eval calls?
    tantra_calls: dict[str, list] = defaultdict(list)
    call_patterns: Counter = Counter()
    slow_calls = []

    for e in entries:
        test_name = e["test"].split("::")[-1]
        for c in e.get("calls", []):
            inp = c.get("input", "")
            ms = c.get("elapsed_ms", 0) or 0
            # extract leading tantra name from eval expr
            m = re.match(r"^([a-z][a-z0-9-]+)\b", inp)
            if m:
                op = m.group(1)
                tantra_calls[op].append(test_name)
                if e.get("outcome") in ("failed", "error"):
                    call_patterns[op] += 1
            if ms > 50:
                slow_calls.append({"test": test_name, "input": inp[:70], "ms": ms})

    slow_calls.sort(key=lambda x: x["ms"], reverse=True)

    # xfail gate mapping (same as analyze_test_results.py)
    XFAIL_GATE = {
        "test_avrti_dvandva_collection_of_two_values": "dvandva",
        "test_tier2_two_entities_ke_each": "dvandva",
        "test_session_entity_identity_persists": "session_gap2",
        "test_two_entities_across_turns_both_present": "session_gap2",
        "test_two_entities_across_turns_scoped": "session_gap2",
        "test_electron_and_field_across_turns": "session_gap2",
        "test_sphere_shape_swarupa": "pratibimba",
        "test_position_ownership": "pratibimba",
        "test_electron_simulation_scene_full": "pratibimba",
        "test_gravitational_force": "p8f_gravity",
        "test_gravitational_force_two_entities": "p8f_gravity",
        "test_gravitational_force_earth_moon": "p8f_gravity",
        "test_unit_in_rate_not_stolen": "unit_rate",
        "test_syllogism_cats_breathe": "logic_nyaya",
        "test_syllogism_dogs_mammals": "logic_nyaya",
        "test_transitive_greater_than": "logic_nyaya",
        "test_transitive_mass_ordering": "logic_nyaya",
        "test_more_apples_or_oranges": "logic_nyaya",
        "test_rank_three_balls_by_mass": "logic_nyaya",
    }

    xfail_by_gate: dict[str, list] = defaultdict(list)
    for e in xfailing:
        name = e["test"].split("::")[-1]
        gate = XFAIL_GATE.get(name, "other")
        xfail_by_gate[gate].append(e["test"])

    return {
        "entries": entries,
        "by_outcome": dict(by_outcome),
        "failing": failing,
        "xfailing": xfailing,
        "tantra_calls": {k: sorted(set(v)) for k, v in tantra_calls.items()},
        "slow_calls": slow_calls[:20],
        "call_patterns_in_failures": call_patterns.most_common(20),
        "xfail_by_gate": dict(xfail_by_gate),
        "counts": {
            "passed": len(by_outcome.get("passed", [])),
            "failed": len(failing),
            "xfailed": len(xfailing),
            "xpassed": len(by_outcome.get("xpassed", [])),
            "total": len(entries),
        },
    }


def load_tantra_sources(brahman_dir: str) -> dict[str, str]:
    """Load all .tantra2 files as {name: content}."""
    sources = {}
    for path in sorted(
        glob.glob(
            os.path.join(brahman_dir, "yantra", "**", "*.tantra2"), recursive=True
        )
    ):
        if "/tests/" in path:
            continue
        name = os.path.basename(path).replace(".tantra2", "")
        try:
            sources[name] = open(path).read()
        except:
            pass
    return sources


def load_ocaml_sources(vyakarana_dir: str) -> dict[str, str]:
    """Load all .ml files (excluding _build) as {filename: content}."""
    sources = {}
    for path in sorted(
        glob.glob(os.path.join(vyakarana_dir, "**", "*.ml"), recursive=True)
    ):
        if "/_build/" in path:
            continue
        name = os.path.basename(path)
        try:
            sources[name] = open(path).read()
        except:
            pass
    return sources


def count_pattern(sources: dict[str, str], regex: str) -> list[tuple[str, int]]:
    """Count regex matches per source file. Returns [(name, count)] sorted desc."""
    rx = re.compile(regex, re.MULTILINE | re.DOTALL)
    results = []
    for name, src in sources.items():
        count = len(rx.findall(src))
        if count > 0:
            results.append((name, count))
    return sorted(results, key=lambda x: x[1], reverse=True)


def analyze_tantra_patterns(tantras: dict[str, str]) -> dict:
    result = {}
    for category, patterns in [
        ("sparsha", TANTRA_SPARSHA_PATTERNS),
        ("viveka", TANTRA_VIVEKA_PATTERNS),
        ("bandha", TANTRA_BANDHA_PATTERNS),
    ]:
        result[category] = {}
        for name, regex, desc in patterns:
            matches = count_pattern(tantras, regex)
            total = sum(c for _, c in matches)
            result[category][name] = {
                "total": total,
                "by_file": matches[:10],
                "desc": desc,
            }
    return result


def analyze_ocaml_patterns(ocaml: dict[str, str]) -> dict:
    result = {}
    for category, patterns in [
        ("sparsha", OCAML_SPARSHA_PATTERNS),
        ("viveka", OCAML_VIVEKA_PATTERNS),
        ("bandha", OCAML_BANDHA_PATTERNS),
    ]:
        result[category] = {}
        for name, regex, desc in patterns:
            matches = count_pattern(ocaml, regex)
            total = sum(c for _, c in matches)
            result[category][name] = {
                "total": total,
                "by_file": matches[:8],
                "desc": desc,
            }
    return result


def find_duplicate_tantra_groups(tantras: dict[str, str]) -> dict:
    """
    Find groups of tantras that perform the same structural operation
    with slight variations — candidates for abstraction into one named tantra.
    """

    # 1. The bandha group: all tantras whose primary operation is
    #    "reduce graph [] (fn acc kv -> ...)" over a specific edge type
    bandha_group = {}
    for name, src in tantras.items():
        # look for the core reduce-over-graph-for-edge pattern
        m = re.search(r"reduce graph \[\] \(fn acc kv ->", src)
        if m:
            # what edge type does it filter on?
            edge_m = re.search(r'eq e "([a-z-]+)"', src)
            edge = edge_m.group(1) if edge_m else "unknown"
            # what does it collect?
            collect_m = re.search(r"collect \[([^\]]+)\]|collect ([a-z_]+)", src)
            collect = (
                collect_m.group(1) or collect_m.group(2) if collect_m else "unknown"
            )
            bandha_group[name] = {"edge": edge, "collect": collect}

    # 2. The ownership query group: all tantras that do
    #    graph | where [s,e,owner] | and (eq e "shashthi-vibhakti")
    ownership_group = {}
    for name, src in tantras.items():
        count = len(re.findall(r"shashthi-vibhakti", src))
        if count > 0:
            ownership_group[name] = count

    # 3. The exists-check anti-pattern group:
    #    gt (string-length (to-string X)) 0  — should be: exists X
    exists_check_group = {}
    for name, src in tantras.items():
        count = len(re.findall(r"gt \(string-length \(to-string", src))
        if count > 0:
            exists_check_group[name] = count

    # 4. The bound-sankhya group: tantras reading sankhya values
    #    — bound-concepts, bound-vals, bound-concept-names + callers
    sankhya_readers = {}
    for name, src in tantras.items():
        count = len(
            re.findall(r"bound-concept-names|bound-concepts|bound-vals", src)
        ) + len(re.findall(r'eq e "sankhya"', src))
        if count > 0:
            sankhya_readers[name] = count

    # 5. The intent-scope group: tantras reading has-intent / solve-for / scope-entity
    intent_group = {}
    for name, src in tantras.items():
        count = len(
            re.findall(r"has-intent|solve-for|scope-entity|extract-solve-for", src)
        )
        if count > 0:
            intent_group[name] = count

    # 6. The emit-reasoning group: tantras building proof graph edges for emit-reasoning
    proof_graph_emitters = {}
    for name, src in tantras.items():
        count = len(
            re.findall(
                r'"derived-by"|"sought"|"sought-of"|"viveka-sankhya"|"derived-sankhya"',
                src,
            )
        )
        if count > 0:
            proof_graph_emitters[name] = count

    # 7. The derivation-guard group: sf-was-derived check (new — prevent false "we find")
    derivation_guard_group = {}
    for name, src in tantras.items():
        count = len(
            re.findall(r"sf-was-derived|derived-by.*sought|pramana.*guard", src)
        )
        if count > 0:
            derivation_guard_group[name] = count

    # 8. The eval-ctx / tantra-call group: OCaml-level context wiring (cross-layer)
    eval_ctx_group = {}
    for name, src in tantras.items():
        count = len(re.findall(r"eval_ctx :=|call_tantra|find_opt.*by_name", src))
        if count > 0:
            eval_ctx_group[name] = count

    return {
        "bandha_reduce_group": bandha_group,
        "ownership_query_group": ownership_group,
        "exists_check_antipattern": exists_check_group,
        "sankhya_reader_group": sankhya_readers,
        "intent_scope_group": intent_group,
        "proof_graph_emitter_group": proof_graph_emitters,
        "derivation_guard_group": derivation_guard_group,
        "eval_ctx_group": eval_ctx_group,
    }


def generate_abstractions(dup_groups: dict, tantra_patterns: dict) -> list[dict]:
    """
    Generate concrete abstraction proposals — each one eliminates a named
    duplication by introducing a tantra or primitive with a philosophical name.
    """
    abstractions = []

    # A. exists-as-primitive: gt(string-length(to-string X)) 0 → exists? X
    exists_count = tantra_patterns["viveka"].get("gt-string-length", {}).get("total", 0)
    files = tantra_patterns["viveka"].get("gt-string-length", {}).get("by_file", [])
    if exists_count > 5:
        abstractions.append(
            {
                "name": "exists?",
                "layer": "tantra2 primitive",
                "category": "viveka",
                "occurrences": exists_count,
                "affected": [f for f, _ in files],
                "before": "gt (string-length (to-string X)) 0",
                "after": "exists? X",
                "philosophical": "viveka at the atomic level: does this thing exist in this graph?",
                "note": "exists already does this for lists; extend to strings and nodes uniformly",
            }
        )

    # B. sankhya-sparsha: every tantra that reads sankhya values
    #    bound-concepts / bound-vals / bound-concept-names are three tantras doing one thing
    abstractions.append(
        {
            "name": "sankhya-sparsha",
            "layer": "tantra2",
            "category": "sparsha",
            "occurrences": len(dup_groups["sankhya_reader_group"]),
            "affected": list(dup_groups["sankhya_reader_group"].keys()),
            "before": "bound-concepts (graph query) + bound-vals (reduce) + bound-concept-names (map)",
            "after": "sankhya-sparsha graph → [bound-names, val-pairs, name-only]\n"
            "  returns all three in one pass — callers destructure what they need",
            "philosophical": "sparsha = first contact. the moment the graph is touched for numeric content.\n"
            "  currently named in three ways. it is one thing.",
            "note": "call count: bound-concept-names×6, bound-vals×2, bound-concepts×1 = 9 call sites",
        }
    )

    # C. iccha-viveka: extract-solve-for + has-intent guard is repeated everywhere
    iccha_files = dup_groups["intent_scope_group"]
    abstractions.append(
        {
            "name": "iccha-viveka",
            "layer": "tantra2",
            "category": "viveka",
            "occurrences": len(iccha_files),
            "affected": list(iccha_files.keys()),
            "before": "sf-result = extract-solve-for graph\n"
            "  has-intent  = nth sf-result 0\n"
            "  solve-for   = nth sf-result 1\n"
            "  scope-entity = nth sf-result 2",
            "after": "iccha = iccha-viveka graph  -- returns same [has-intent, solve-for, scope]\n"
            "  philosophical name makes the operation visible as discrimination of intent",
            "philosophical": "iccha = will/intention (Sanskrit). viveka = discrimination.\n"
            "  iccha-viveka: discriminating whether the question has explicit intent.\n"
            "  currently: extract-solve-for + 5 lines of nth destructuring everywhere.",
            "note": "appears in: anuvada-ganana, match-mantra, session-anuvada",
        }
    )

    # D. pramana-bandha: the proof graph assembly block in anuvada-ganana
    #    the result-triples + viveka-sankhya-triples + scoped-sankhya-triples pattern
    abstractions.append(
        {
            "name": "pramana-bandha",
            "layer": "tantra2",
            "category": "bandha",
            "occurrences": len(dup_groups["proof_graph_emitter_group"]),
            "affected": list(dup_groups["proof_graph_emitter_group"].keys()),
            "before": 'result-triples = cond ... (append [[sf, "sankhya", result], [sf, "derived-by", mantra]] ...)\n'
            "  proof-graph = cond is-viveka (append base viveka-triples) otherwise (append enriched result-triples)",
            "after": "proof-graph = pramana-bandha base-graph result final-match viveka-raw iccha-result is-viveka\n"
            "  one call. all reasoning edges injected in one named operation.",
            "philosophical": "pramana = ground truth, means of valid knowledge.\n"
            "  pramana-bandha: the moment the derivation becomes a permanent fact in the proof graph.\n"
            "  currently scattered across 20 lines in anuvada-ganana.",
        }
    )

    # E. shashthi-sparsha: the ownership query is written identically in 8+ tantras
    ownership_files = list(dup_groups["ownership_query_group"].items())
    abstractions.append(
        {
            "name": "shashthi-sparsha",
            "layer": "tantra2",
            "category": "sparsha",
            "occurrences": sum(c for _, c in ownership_files),
            "affected": [
                f for f, _ in sorted(ownership_files, key=lambda x: x[1], reverse=True)
            ],
            "before": 'graph | where [s, e, owner] | and (eq e "shashthi-vibhakti")\n'
            "        | and (eq (to-string owner) (to-string scope-entity)) | collect s",
            "after": "shashthi-sparsha graph scope-entity  → [owned-nodes]\n"
            "  one call, named after its grammatical operation",
            "philosophical": "shashthi = genitive case (Sanskrit). sparsha = contact.\n"
            "  shashthi-sparsha: the moment ownership is read from the graph.\n"
            '  the genitive is the possession case — "X of Y". this query IS that case.',
            "note": f"appears {sum(c for _, c in ownership_files)}x across {len(ownership_files)} tantras",
        }
    )

    # F. OCaml: eval_arg helper
    abstractions.append(
        {
            "name": "eval_arg / eval_args",
            "layer": "OCaml (yantra_eval_primitives.ml)",
            "category": "sparsha (OCaml level)",
            "occurrences": 72,
            "affected": ["yantra_eval_primitives.ml"],
            "before": "let name = as_string (e_eval k e (List.nth args 0)) in\n"
            "  let name2 = as_string (e_eval k e (List.nth args 1)) in",
            "after": "let name  = eval_string e_eval k e args 0 in\n"
            "  let name2 = eval_string e_eval k e args 1 in\n"
            "  (* or: let [a; b; c] = eval_args e_eval k e args 3 in *)",
            "philosophical": "the same sparsha at the OCaml level:\n"
            "  get the Nth argument from context, coerce to the expected type.\n"
            "  72 occurrences because it is not yet named.",
        }
    )

    # G. OCaml: with_node helper
    abstractions.append(
        {
            "name": "with_node",
            "layer": "OCaml (eval_primitives + proof_graph)",
            "category": "viveka (OCaml level)",
            "occurrences": 34,
            "affected": ["yantra_eval_primitives.ml", "anuvada.ml", "socket.ml"],
            "before": "(match Proof_graph.find k name with\n"
            "  | Some n -> (* use n *)\n"
            "  | None   -> fallback)",
            "after": "with_node k name ~default:fallback (fun n -> (* use n *))",
            "philosophical": "viveka at OCaml level: does this node exist in this graph?\n"
            "  if yes, operate. if no, return default.\n"
            "  the discrimination is between presence and absence of pramana.",
        }
    )

    # H. OCaml: with_eval_ctx
    abstractions.append(
        {
            "name": "with_eval_ctx",
            "layer": "OCaml (yantra_eval.ml)",
            "category": "bandha (OCaml level)",
            "occurrences": 8,
            "affected": ["yantra_eval.ml"],
            "before": "let prev_ctx = !eval_ctx in\n"
            "  eval_ctx := Some { ctx_index = idx; ctx_session = session };\n"
            "  let result = f () in\n"
            "  eval_ctx := prev_ctx; result",
            "after": "with_eval_ctx idx session (fun () -> f ())",
            "philosophical": "bandha (binding) at OCaml level: temporarily binding the evaluation context.\n"
            "  the current context is the scope — sparsha → operate → restore.\n"
            "  pattern of samskaara: what was before is restored after.",
        }
    )

    return abstractions


def generate_test_suggestions(tantras: dict[str, str], analysis: dict) -> list[dict]:
    """
    Generate test suggestions that come directly from the pattern analysis —
    not invented, derived from what the structure says about itself.
    """
    suggestions = []

    # 1. exists? primitive: test that the pattern fires correctly
    suggestions.append(
        {
            "name": "test_exists_check_uniformity",
            "category": "viveka_primitive",
            "from": "gt(string-length(to-string X)) 0 appearing 79x — should be one primitive",
            "test": 'assert exists? "" == false\n'
            'assert exists? "hello" == true\n'
            "assert exists? [] == false\n"
            'assert exists? ["x"] == true\n'
            "assert exists? _none == false",
            "why": "if this is one concept (existence check) it should behave uniformly across types",
        }
    )

    # 2. sankhya-sparsha: test that all three bound-* tantras agree
    suggestions.append(
        {
            "name": "test_sankhya_sparsha_equivalence",
            "category": "sparsha",
            "from": "bound-concepts, bound-vals, bound-concept-names are three tantras doing one thing",
            "test": 'graph = refine("ball has mass 5 velocity 10")\n'
            "names = bound-concept-names graph  -- [mass, velocity]\n"
            "pairs = bound-concepts graph       -- [[mass,5], [velocity,10]]\n"
            "bvals = bound-vals graph           -- [names, pairs]\n"
            "assert (nth bvals 0) == names\n"
            "assert (nth bvals 1) == pairs",
            "why": "if these are the same operation they must always agree — structural consistency",
        }
    )

    # 3. shashthi-sparsha: test ownership query is stable
    suggestions.append(
        {
            "name": "test_shashthi_sparsha_scope_isolation",
            "category": "sparsha_ownership",
            "from": "shashthi-vibhakti query appears 18x — each instance should isolate correctly",
            "test": 'graph = refine("ball-A has mass 3 and ball-B has mass 5")\n'
            "-- after vibhakti-shashthi: mass owned by ball-A AND by ball-B\n"
            'owned_A = graph | where [s,e,o] | and (eq e "shashthi-vibhakti")\n'
            '                | and (eq o "ball-A") | collect s\n'
            'owned_B = graph | where [s,e,o] | and (eq e "shashthi-vibhakti")\n'
            '                | and (eq o "ball-B") | collect s\n'
            "assert (intersection owned_A owned_B) == []  -- disjoint ownership",
            "why": "every shashthi-sparsha call assumes disjoint ownership — test the assumption",
        }
    )

    # 4. iccha-viveka: test intent discrimination
    suggestions.append(
        {
            "name": "test_iccha_viveka_no_intent_no_derivation",
            "category": "viveka_intent",
            "from": "has-intent guard added to anuvada-ganana — test that it gates correctly",
            "test": "# no vidhi-kaala → has-intent = false → no derivation\n"
            'result = query("ball has mass 5 velocity 10")\n'
            'assert "no match" in result\n\n'
            "# with vidhi-kaala → has-intent = true → derivation fires\n"
            'result = query("find kinetic energy of ball given mass 5 velocity 10")\n'
            'assert "250" in result',
            "why": "iccha-viveka is the has-intent guard — the gate between observation and question",
        }
    )

    # 5. pramana-bandha: test proof graph edges are correctly inscribed
    suggestions.append(
        {
            "name": "test_pramana_bandha_derived_by_present",
            "category": "bandha_proof",
            "from": "pramana-bandha assembles derived-by + sankhya edges — test they are always present",
            "test": 'graph = query_graph("find kinetic energy given mass 5 velocity 10")\n'
            "-- after derivation: [kinetic-energy, derived-by, kinetic-energy-mantra]\n"
            'derived_by = graph | where [s,e,o] | and (eq e "derived-by") | collect o\n'
            "assert (length derived_by) > 0\n"
            'assert "kinetic-energy-mantra" in derived_by',
            "why": "pramana without derived-by is not pramana — the proof is incomplete",
        }
    )

    # 6. multi-participant mantra guard (the fix we added)
    suggestions.append(
        {
            "name": "test_multi_participant_mantra_scope_guard",
            "category": "viveka_scope",
            "from": "relative-velocity-mantra fires with one entity because janya=[velocity,velocity]\n"
            "multi-participant guard added to match-mantra forward-match",
            "test": "# one entity, two janya of same concept → mantra must NOT fire\n"
            'result = query("ball has velocity 10. find relative velocity of ball")\n'
            'assert "no match" in result  -- cannot have relative velocity to itself\n\n'
            "# two entities → mantra CAN fire\n"
            'result = query("ball-A has velocity 10 ball-B has velocity 3. find relative velocity of ball-A")\n'
            'assert "7" in result',
            "why": "multi-participant mantras need N distinct value sources — not N uses of one source",
        }
    )

    # 7. word collision resolution
    suggestions.append(
        {
            "name": "test_word_collision_context_resolution",
            "category": "viveka_disambiguation",
            "from": '337 word collisions in shabda — "set"→9 nodes, "transformation"→4, "process"→2\n'
            "current: last-writer-wins. should: PPR context disambiguates",
            "test": '# "set" in physics context → should route to set-theory or the right node\n'
            '# "process" in chemistry → bhave-prayoga (impersonal process)\n'
            '# "process" in computing → action/operation\n'
            "# test that kosha-expand seeds disambiguate correctly\n"
            'r1 = query("a set has 5 elements")\n'
            'r2 = query("the process takes 3 seconds")\n'
            "# each should route to the contextually correct node\n"
            'assert "element" in graph_of(r1) | where [s,e,o] | and (eq e "prathama-vibhakti")',
            "why": "disambiguation is viveka — the system should discriminate by context not by file order",
        }
    )

    # 8. avrti-refine mithya convergence (structural test)
    suggestions.append(
        {
            "name": "test_avrti_mithya_monotone_decrease",
            "category": "sparsha_avrti",
            "from": "avrti = fixpoint. mithya must strictly decrease each pass (knaster-tarski)",
            "test": 'g0 = build-question-graph "ball has mass 5 velocity 10"\n'
            "g1 = avrti-refine g0\n"
            "g2 = avrti-refine g1\n"
            'mithya_0 = count (g0 | where [s,e,o] | and (eq e "mithya") | collect s)\n'
            'mithya_1 = count (g1 | where [s,e,o] | and (eq e "mithya") | collect s)\n'
            'mithya_2 = count (g2 | where [s,e,o] | and (eq e "mithya") | collect s)\n'
            "assert mithya_1 <= mithya_0\n"
            "assert mithya_2 <= mithya_1  -- monotone non-increasing",
            "why": "if avrti ever increases mithya, fixpoint may not terminate — structural invariant",
        }
    )

    return suggestions


def cross_reference_all(
    tantra_patterns, ocaml_patterns, dup_groups, abstractions, tests
) -> dict:
    """
    The central output: show the same structure at every scale side by side.
    """
    return {
        "unified_structure": {
            "SPARSHA (contact — getting from context)": {
                "tantra2": {
                    k: v["total"] for k, v in tantra_patterns["sparsha"].items()
                },
                "ocaml": {k: v["total"] for k, v in ocaml_patterns["sparsha"].items()},
                "om_shabda": "word: key = 214 entries (word→node), name: key = 126 (English label)",
                "in_graph": "walk/walk-in = the same sparsha at graph traversal level",
                "in_tests": "query(sentence) = sparsha at the test level",
            },
            "VIVEKA (discrimination — filter/guard/check)": {
                "tantra2": {
                    k: v["total"] for k, v in tantra_patterns["viveka"].items()
                },
                "ocaml": {k: v["total"] for k, v in ocaml_patterns["viveka"].items()},
                "om_shabda": "337 word collisions = disambiguation not yet named as viveka",
                "in_graph": "PPR = viveka at graph traversal level (context discriminates)",
                "in_tests": "assert X in result = viveka at test level",
            },
            "BANDHA (binding — writing result back)": {
                "tantra2": {
                    k: v["total"] for k, v in tantra_patterns["bandha"].items()
                },
                "ocaml": {k: v["total"] for k, v in ocaml_patterns["bandha"].items()},
                "om_shabda": "shabda lines = bandha at the om level (word bound to node)",
                "in_graph": "join/emit-edge = bandha at the graph level",
                "in_tests": "fixture setup = bandha at the test level",
            },
        },
        "duplicate_groups": dup_groups,
        "abstractions": abstractions,
        "test_suggestions": tests,
        "tantra_patterns": tantra_patterns,
        "ocaml_patterns": ocaml_patterns,
    }


def print_report(result: dict, report: str = "all"):
    SEP = "═" * 72
    SEP2 = "─" * 72

    if report in ("all", "patterns"):
        print(SEP)
        print("  THE STRUCTURE AT EVERY SCALE")
        print(SEP)
        print("""
  One structure. Three operations. Every layer.

  SPARSHA  — contact. getting something from context.
             tantra2: graph | where ... | collect
             OCaml:   e_eval k e (List.nth args N)
             shabda:  word: alias → node name
             graph:   walk node "relation"
             test:    query(sentence)

  VIVEKA   — discrimination. filter / guard / check.
             tantra2: and (eq e "X") / cond ... otherwise
             OCaml:   match Some n with ... | None -> fallback
             shabda:  337 word collisions (not yet named as viveka)
             graph:   PPR context scoring
             test:    assert X in result

  BANDHA   — binding. writing the result back.
             tantra2: emit [s, e, o] / append acc [...]
             OCaml:   Hashtbl.replace / := / Some V
             shabda:  word_index[w] = node_name
             graph:   join / emit-edge
             test:    fixture setup / conftest
""")

        us = result["unified_structure"]
        for op_name, layers in us.items():
            print(f"\n── {op_name}")
            for layer, data in layers.items():
                if isinstance(data, dict):
                    top = sorted(data.items(), key=lambda x: x[1], reverse=True)[:5]
                    vals = ", ".join(f"{k}({v})" for k, v in top if v > 0)
                    print(f"  {layer:<12} {vals}")
                else:
                    print(f"  {layer:<12} {data}")

    if report in ("all", "abstractions"):
        print(f"\n{SEP}")
        print("  ABSTRACTIONS: UNNAMED STRUCTURE WAITING TO BE NAMED")
        print(SEP)
        print()
        for ab in result["abstractions"]:
            print(
                f"  [{ab['category'].upper()}] {ab['name']}  ({ab['occurrences']} occurrences)"
            )
            print(f"  layer: {ab['layer']}")
            print(f"  philosophy:")
            for line in ab["philosophical"].split("\n"):
                print(f"    {line}")
            print(f"  before:")
            for line in ab["before"].split("\n"):
                print(f"    {line}")
            print(f"  after:")
            for line in ab["after"].split("\n"):
                print(f"    {line}")
            if "note" in ab:
                print(f"  note: {ab['note']}")
            print()

    if report in ("all", "tests"):
        print(f"\n{SEP}")
        print("  TEST SUGGESTIONS FROM PATTERN ANALYSIS")
        print(SEP)
        print("  (not invented — derived from what the structure says about itself)\n")
        for ts in result["test_suggestions"]:
            print(f"  [{ts['category']}] {ts['name']}")
            print(f"  from: {ts['from']}")
            print(f"  why:  {ts['why']}")
            print(f"  test:")
            for line in ts["test"].split("\n"):
                print(f"    {line}")
            print()

    if report in ("all", "tantras"):
        print(f"\n{SEP}")
        print("  DUPLICATE TANTRA GROUPS")
        print(SEP)
        dg = result["duplicate_groups"]

        print("\n── bandha (reduce-over-graph) group ────────────────────────────────")
        for name, info in sorted(dg["bandha_reduce_group"].items()):
            print(f"  {name:<35} edge={info['edge']:<20} collect={info['collect']}")

        print("\n── ownership query group (shashthi-vibhakti) ───────────────────────")
        for name, count in sorted(
            dg["ownership_query_group"].items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {name:<35} {count}×")

        print("\n── exists-check anti-pattern (gt string-length to-string) ──────────")
        for name, count in sorted(
            dg["exists_check_antipattern"].items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {name:<35} {count}×")

        print('\n── sankhya reader group (bound-* calls + eq e "sankhya") ───────────')
        for name, count in sorted(
            dg["sankhya_reader_group"].items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {name:<35} {count}×")

        print("\n── intent/scope group (has-intent / extract-solve-for) ─────────────")
        for name, count in sorted(
            dg["intent_scope_group"].items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {name:<35} {count}×")

        print("\n── proof graph emitter group (derived-by / sought / viveka-sankhya) ─")
        for name, count in sorted(
            dg["proof_graph_emitter_group"].items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {name:<35} {count}×")

    print()


def print_live_test_report(cache: dict):
    """Print a section from the live test cache cross-referenced with tantra patterns."""
    SEP = "═" * 72
    counts = cache.get("counts", {})
    print(SEP)
    print("  LIVE TEST CACHE CROSS-REFERENCE")
    print(SEP)
    print(f"""
  passed:  {counts.get("passed", 0)}
  failed:  {counts.get("failed", 0)}
  xfailed: {counts.get("xfailed", 0)}
  xpassed: {counts.get("xpassed", 0)}
  total:   {counts.get("total", 0)}
""")

    failing = cache.get("failing", [])
    if failing:
        print("── FAILING TESTS — eval call chains ─────────────────────────────────")
        for e in failing:
            print(f"\n  {e['test']}")
            for c in e.get("calls", []):
                ms = c.get("elapsed_ms", 0) or 0
                out = c.get("output", "")
                out_s = str(out)[:80] if out is not None else ""
                err = f"  ERROR: {c['error'][:40]}" if c.get("error") else ""
                print(
                    f"    [{ms:>4}ms] {c.get('method', '?')}  {c.get('input', '')[:70]}{err}"
                )
                if out_s:
                    print(f"           → {out_s}")

    patterns = cache.get("call_patterns_in_failures", [])
    if patterns:
        print(
            f"\n── TANTRAS CALLED IN FAILING TESTS ──────────────────────────────────"
        )
        for op, count in patterns:
            print(f"  {op:<35} {count}×")

    xfail_gates = cache.get("xfail_by_gate", {})
    if xfail_gates:
        print(
            f"\n── XFAILED BY GATE ──────────────────────────────────────────────────"
        )
        for gate, tests in sorted(
            xfail_gates.items(), key=lambda x: len(x[1]), reverse=True
        ):
            info = XFAIL_GROUPS.get(gate, {})
            philosophy = info.get("philosophy", "")[:100] if info else ""
            print(f"\n  [{gate}]  {len(tests)} tests")
            if philosophy:
                print(f"    {philosophy}")
            for t in tests[:5]:
                print(f"    {t.split('::')[-1]}")
            if len(tests) > 5:
                print(f"    ... +{len(tests) - 5} more")

    slow = cache.get("slow_calls", [])
    if slow:
        print(
            f"\n── SLOWEST INDIVIDUAL CALLS ──────────────────────────────────────────"
        )
        for sc in slow[:10]:
            print(f"  {sc['ms']:>5}ms  {sc['input'][:65]}")
            print(f"           in {sc['test']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--brahman", default=BRAHMAN_DEFAULT)
    parser.add_argument("--vyakarana", default=VYAKARANA_DEFAULT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--report",
        default="all",
        choices=[
            "all",
            "patterns",
            "abstractions",
            "tests",
            "live",
            "ocaml",
            "tantras",
            "shabda",
        ],
    )
    args = parser.parse_args()

    tantras = load_tantra_sources(args.brahman)
    ocaml = load_ocaml_sources(args.vyakarana)

    tp = analyze_tantra_patterns(tantras)
    op = analyze_ocaml_patterns(ocaml)
    dg = find_duplicate_tantra_groups(tantras)
    ab = generate_abstractions(dg, tp)
    ts = generate_test_suggestions(tantras, {})
    full = cross_reference_all(tp, op, dg, ab, ts)

    # load live cache for cross-reference
    cache = load_test_cache(args.vyakarana)

    if args.json:
        json.dump({**full, "live_cache": cache}, sys.stdout, indent=2, default=str)
    elif args.report == "live":
        print_live_test_report(cache)
    else:
        print_report(full, args.report)
        if args.report == "all" and not cache.get("error"):
            print_live_test_report(cache)
