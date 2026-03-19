#!/usr/bin/env python3
"""
analyze_abstractions.py — concrete before/after analysis of OCaml abstractions.

Tracks the six abstraction helpers extracted from the codebase:
  [A] make_eval_arg  (yantra_types.ml)        — eval + arg extraction
  [B] with_node      (yantra_eval_primitives)  — Proof_graph.find match in eval layer only
  [C] with_eval_ctx  (yantra_eval.ml)          — eval_ctx set/restore at call sites
  [D] opt_field      (socket.ml)               — Option.value ~default json_field
  [E] call_tantra_opt (yantra_eval_primitives) — find_opt by_name + eval_tantra inline
  [F] Category B     (yantra_ops.ml)           — ops pending tantra migration

False-positive exclusions applied:
  [A] yantra_types.ml lines inside make_eval_arg's OWN definition are excluded.
      yantra_pipeline_ops.ml variable-index loops (List.nth args i) are excluded.
  [B] Only eval-layer files counted (not proof_graph.ml, setu.ml, anuvada.ml etc
      which ARE the graph infrastructure and must use Hashtbl.find_opt k.nodes).
  [C] Only counts eval_ctx := at actual call sites, not inside with_eval_ctx /
      eval_tantra's own implementations.
  [E] Only counts the 3-line inline pattern (find_opt + Some t + eval_tantra inline),
      not top-level runner functions (run_anuvada_ganana etc).

Reports:
  - How many raw occurrences remain vs how many now use the helper
  - Which files still have raw patterns (migration not yet complete)
  - Category B migration status (which ops are in tantras, which in OCaml only)
  - Tantra-level patterns: sankhya-sparsha, shashthi-sparsha, agra, sattva, iccha-viveka

Does NOT require a running server — reads source files directly.

Usage:
    python3 tools/analyze_abstractions.py [--vyakarana ./vyakarana] [--brahman ./brahman]
    python3 tools/analyze_abstractions.py --report helpers
    python3 tools/analyze_abstractions.py --report category_b
    python3 tools/analyze_abstractions.py --report tantra_patterns
    python3 tools/analyze_abstractions.py --json
"""

import re, os, sys, json, glob, argparse
from collections import Counter, defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VYAKARANA_DEFAULT = os.path.join(REPO_ROOT, "vyakarana")
BRAHMAN_DEFAULT = os.path.join(REPO_ROOT, "brahman")

# ── file loading ──────────────────────────────────────────────────────────────

# Files that ARE graph infrastructure — with_node is not applicable there.
# These use Hashtbl.find_opt k.nodes correctly as part of the graph layer.
_GRAPH_INFRA_FILES = {
    "proof_graph.ml",
    "setu.ml",
    "setu_classify.ml",
    "setu_shabda.ml",
    "anuvada.ml",
}

# Files where with_eval_ctx's own definition lives — exclude from [C] raw count.
_WITH_EVAL_CTX_IMPL_FILE = "yantra_eval.ml"
# Line range (1-indexed) of with_eval_ctx's own body in yantra_eval.ml.
# The impl is at ~213-220; eval_tantra's internal set/restore at ~178-199.
# We exclude both since neither is a "call site" — they're implementations.
_EVAL_CTX_IMPL_LINES = set(range(175, 222))  # eval_tantra + with_eval_ctx bodies


def load_ml_sources(vyakarana_dir: str) -> dict[str, str]:
    """Load all .ml files (excluding _build) as {filename: source}."""
    files = {}
    for path in sorted(
        glob.glob(os.path.join(vyakarana_dir, "**", "*.ml"), recursive=True)
    ):
        if "/_build/" in path:
            continue
        name = os.path.basename(path)
        try:
            files[name] = open(path).read()
        except:
            pass
    return files


def load_tantra2_sources(brahman_dir: str) -> dict[str, str]:
    """Load all .tantra2 files as {rel-path: source}."""
    files = {}
    base = os.path.join(brahman_dir, "yantra")
    for path in sorted(
        glob.glob(os.path.join(base, "**", "*.tantra2"), recursive=True)
    ):
        rel = os.path.relpath(path, base)
        try:
            files[rel] = open(path).read()
        except:
            pass
    return files


# ── OCaml helper pattern analysis ─────────────────────────────────────────────


def _count_in_source_excluding_lines(
    src: str, pattern: re.Pattern, exclude_lines: set[int]
) -> int:
    """Count regex matches in src, skipping any match whose start line is in exclude_lines."""
    count = 0
    for m in pattern.finditer(src):
        line_no = src[: m.start()].count("\n") + 1  # 1-indexed
        if line_no not in exclude_lines:
            count += 1
    return count


def analyze_helpers(ml_files: dict[str, str]) -> dict:
    """Count raw pattern occurrences and helper usage per file, with false-positive exclusions."""

    # ── [A] raw arg_extract: e_eval k e (List.nth args N) with FIXED N ─────
    # Exclude: variable-index loops (List.nth args i where i is a variable)
    # Exclude: the make_eval_arg definition itself in yantra_types.ml
    A_rx = re.compile(r"e_eval k e \(List\.nth args \d+\)")
    A_var_rx = re.compile(
        r"e_eval k e \(List\.nth args [a-z]\b"
    )  # variable index — excluded

    # ── [A2] eval_str inline: as_string (e_eval k e (List.nth args N)) ──────
    A2_rx = re.compile(r"as_string \(e_eval k e \(List\.nth args \d+\)")

    # ── [B] with_node applicable: only in eval-layer files ──────────────────
    # The pattern in eval layer is: Proof_graph.find k name (NOT Hashtbl.find_opt k.nodes directly)
    # After migration, with_node wraps Proof_graph.find. Raw sites still use
    # `match Hashtbl.find_opt k.nodes name with` directly in eval files.
    B_rx = re.compile(r"Hashtbl\.find_opt k\.nodes\b")

    # ── [C] with_eval_ctx: eval_ctx := at call sites ─────────────────────────
    # Excludes: the with_eval_ctx and eval_tantra implementations themselves.
    C_rx = re.compile(r"eval_ctx :=")

    # ── [D] opt_field: Option.value ~default:"" (json_string_field ──────────
    D_rx = re.compile(r'Option\.value ~default:"" \(json_string_field')

    # ── [E] call_tantra_opt inline: the 3-line find_opt+by_name+eval_tantra ─
    # Real pattern (inline, not a top-level runner):
    #   match Hashtbl.find_opt ctx.ctx_index.by_name name with
    #   | Some t -> eval_tantra ...
    # Excludes: run_anuvada_ganana, run_session_anuvada, run_tantra_by_name
    # (those are top-level dispatch functions, not inline patterns).
    E_rx = re.compile(
        r"Hashtbl\.find_opt ctx\.ctx_index\.by_name\b.*?eval_tantra\b", re.DOTALL
    )

    raw_counts: dict[str, dict] = {
        "arg_extract": {"label": "[A] eval_arg", "total": 0, "by_file": {}},
        "as_string_coerce": {"label": "[A] eval_str inline", "total": 0, "by_file": {}},
        "node_lookup": {"label": "[B] with_node", "total": 0, "by_file": {}},
        "eval_ctx_set": {"label": "[C] with_eval_ctx", "total": 0, "by_file": {}},
        "json_field_opt": {"label": "[D] opt_field", "total": 0, "by_file": {}},
        "tantra_call_raw": {"label": "[E] call_tantra_opt", "total": 0, "by_file": {}},
    }

    for fname, src in ml_files.items():
        lines = src.split("\n")

        # [A] fixed-index arg_extract — exclude make_eval_arg definition lines
        # The definition of make_eval_arg in yantra_types.ml has the pattern too.
        # Detect by checking if the match is inside `let make_eval_arg` block.
        if fname == "yantra_types.ml":
            # Find the make_eval_arg definition block and exclude its lines
            make_eval_start = next(
                (i + 1 for i, l in enumerate(lines) if "let make_eval_arg" in l), None
            )
            if make_eval_start:
                # Block ends at next top-level `let` or end of file
                make_eval_end = next(
                    (
                        i + 1
                        for i, l in enumerate(lines)
                        if i >= make_eval_start and re.match(r"^let ", l)
                    ),
                    len(lines),
                )
                excl = set(range(make_eval_start, make_eval_end + 1))
            else:
                excl = set()
            a_count = _count_in_source_excluding_lines(src, A_rx, excl)
            a2_count = _count_in_source_excluding_lines(src, A2_rx, excl)
        elif fname == "yantra_pipeline_ops.ml":
            # Variable-index loops — all List.nth args here are non-fixed, skip [A]
            # BUT remember-bindings line 26 and print line 51 are fixed-index
            # and could use make_eval_arg — count those specifically
            a_count = len(A_rx.findall(src)) - len(A_var_rx.findall(src))
            a2_count = len(A2_rx.findall(src))
        else:
            a_count = len(A_rx.findall(src))
            a2_count = len(A2_rx.findall(src))

        if a_count > 0:
            raw_counts["arg_extract"]["by_file"][fname] = a_count
            raw_counts["arg_extract"]["total"] += a_count
        if a2_count > 0:
            raw_counts["as_string_coerce"]["by_file"][fname] = a2_count
            raw_counts["as_string_coerce"]["total"] += a2_count

        # [B] with_node — only in eval-layer files
        if fname not in _GRAPH_INFRA_FILES:
            b_count = len(B_rx.findall(src))
            if b_count > 0:
                raw_counts["node_lookup"]["by_file"][fname] = b_count
                raw_counts["node_lookup"]["total"] += b_count

        # [C] with_eval_ctx — exclude implementation lines in yantra_eval.ml
        if fname == _WITH_EVAL_CTX_IMPL_FILE:
            c_count = _count_in_source_excluding_lines(src, C_rx, _EVAL_CTX_IMPL_LINES)
        else:
            c_count = len(C_rx.findall(src))
        if c_count > 0:
            raw_counts["eval_ctx_set"]["by_file"][fname] = c_count
            raw_counts["eval_ctx_set"]["total"] += c_count

        # [D] opt_field
        d_count = len(D_rx.findall(src))
        if d_count > 0:
            raw_counts["json_field_opt"]["by_file"][fname] = d_count
            raw_counts["json_field_opt"]["total"] += d_count

        # [E] call_tantra_opt — inline pattern only
        e_count = len(E_rx.findall(src))
        if e_count > 0:
            raw_counts["tantra_call_raw"]["by_file"][fname] = e_count
            raw_counts["tantra_call_raw"]["total"] += e_count

    # Sort by_file
    for key in raw_counts:
        raw_counts[key]["by_file"] = sorted(
            raw_counts[key]["by_file"].items(), key=lambda x: x[1], reverse=True
        )

    # ── helper usage counts (unchanged) ──────────────────────────────────────
    HELPER_USAGE = {
        "eval_str": r"\beval_str\s+\d+",
        "eval_flt": r"\beval_flt\s+\d+",
        "eval_lst": r"\beval_lst\s+\d+",
        "eval_int": r"\beval_int\s+\d+",
        "eval_arg": r"\beval_arg\s+\d+",
        "with_node": r"\bwith_node\b",
        "with_eval_ctx": r"\bwith_eval_ctx\b",
        "opt_field": r"\bopt_field\b",
        "req_field": r"\breq_field\b",
        "call_tantra_opt": r"\bcall_tantra_opt\b",
        "make_eval_arg": r"\bmake_eval_arg\b",
    }
    helper_usage: dict[str, dict] = {}
    for h_name, h_rx in HELPER_USAGE.items():
        by_file: dict[str, int] = {}
        rx = re.compile(h_rx, re.MULTILINE)
        for fname, src in ml_files.items():
            count = len(rx.findall(src))
            if count > 0:
                by_file[fname] = count
        helper_usage[h_name] = {
            "total": sum(by_file.values()),
            "by_file": sorted(by_file.items(), key=lambda x: x[1], reverse=True),
        }

    # ── also report: files with remaining migration opportunities ────────────
    # [A] files where make_eval_arg is NOT yet set up but raw patterns exist
    migration_gaps: dict[str, list[str]] = {}
    for fname, count in raw_counts["arg_extract"]["by_file"]:
        has_setup = "make_eval_arg" in ml_files.get(fname, "")
        if not has_setup:
            migration_gaps[fname] = migration_gaps.get(fname, [])
            migration_gaps[fname].append(f"no make_eval_arg setup ({count} raw)")

    return {
        "raw": raw_counts,
        "helper_usage": helper_usage,
        "migration_gaps": migration_gaps,
    }


# ── Category B migration analysis ──────────────────────────────────────────────

CATEGORY_B_OPS = {
    "square": {"tantra": "mul x x", "score": 3},
    "half": {"tantra": "mul x 0.5", "score": 3},
    "double": {"tantra": "mul x 2", "score": 3},
    "reciprocal": {"tantra": "div 1 x", "score": 3},
    "to-english": {"tantra": "already a tantra", "score": 3},
    "domain-of": {"tantra": "already a tantra", "score": 3},
    "first-match": {"tantra": "nth (filter list fn) 0", "score": 2},
    "unique": {"tantra": "reduce with member check", "score": 2},
    "vec-scale": {"tantra": "map vec (fn x -> mul s x)", "score": 2},
    "vec-dot": {"tantra": "sum (map (zip a b) ...)", "score": 2},
    "vec-norm": {"tantra": "sqrt (sum (map ...))", "score": 2},
    "vec-add": {"tantra": "map (zip a b) ...", "score": 2},
    "vec-sub": {"tantra": "map (zip a b) ...", "score": 2},
    "sum": {"tantra": "reduce list 0 add", "score": 2},
    "zip": {"tantra": "map range ...", "score": 1},
    "reverse": {"tantra": "reduce with prepend", "score": 1},
    "range": {"tantra": "borderline — used as loop infra", "score": 1},
    "sort-desc": {"tantra": "needs comparison primitive", "score": 0},
    "frequencies": {"tantra": "needs dict/map value type", "score": 0},
    "take": {"tantra": "needs index tracking", "score": 0},
    "drop": {"tantra": "needs index tracking", "score": 0},
    "rot2d": {"tantra": "expressible but verbose", "score": 1},
    "mat-mul": {"tantra": "performance-sensitive nested loops", "score": 0},
}


def analyze_category_b(ml_files: dict[str, str], tantra_files: dict[str, str]) -> dict:
    """For each Category B op, count tantra call sites and OCaml arms remaining."""
    all_tantra_src = "\n".join(tantra_files.values())
    all_ocaml_src = "\n".join(ml_files.values())

    results = {}
    for op_name, info in CATEGORY_B_OPS.items():
        tantra_rx = re.compile(r"\b" + re.escape(op_name) + r"\b")
        ocaml_rx = re.compile(r'"' + re.escape(op_name) + r'"')

        tantra_calls = len(tantra_rx.findall(all_tantra_src))
        calling_tantras = [
            name for name, src in tantra_files.items() if tantra_rx.search(src)
        ]
        ocaml_arms = len(ocaml_rx.findall(all_ocaml_src))

        results[op_name] = {
            "tantra_calls": tantra_calls,
            "calling_tantras": calling_tantras,
            "ocaml_arms": ocaml_arms,
            "tantra_form": info["tantra"],
            "score": info["score"],
            "migrated": tantra_calls > 0 and info["score"] >= 3,
        }

    return dict(
        sorted(results.items(), key=lambda x: (-x[1]["score"], -x[1]["tantra_calls"]))
    )


# ── Tantra-level micro-pattern analysis ───────────────────────────────────────

TANTRA_MICRO_PATTERNS = {
    "sankhya-sparsha": {
        "desc": 'graph | where [s, e, o] | and (eq e "sankhya") | collect',
        "regex": r'eq e "sankhya"',
        "abstraction": "named tantra: sankhya-sparsha graph → [node-names]",
    },
    "shashthi-sparsha": {
        "desc": 'graph | where [s, e, o] | and (eq e "shashthi-vibhakti") | collect',
        "regex": r'eq e "shashthi-vibhakti"',
        "abstraction": "named tantra: shashthi-sparsha graph entity → [owned-concepts]",
    },
    "prathama-sparsha": {
        "desc": 'graph | where [s, e, o] | and (eq e "prathama-vibhakti") | collect',
        "regex": r'eq e "prathama-vibhakti"',
        "abstraction": "named tantra: prathama-sparsha graph → [entity-names]",
    },
    "exists-antipattern": {
        "desc": "gt (string-length (to-string X)) 0  — checks non-empty instead of (exists X)",
        "regex": r"gt \(string-length \(to-string",
        "abstraction": "(exists X) — already a primitive, replace antipattern",
    },
    "agra-pattern": {
        "desc": "cond (gt (length lst) 0) (nth lst 0) otherwise fallback",
        "regex": r"cond \(gt \(length",
        "abstraction": "agra-bandha — safe head-of-list with fallback",
    },
    "bandha-reduce": {
        "desc": "reduce triples [] (fn acc kv -> append acc [[...edge...]])",
        "regex": r"reduce.*\[\].*fn.*append.*acc",
        "abstraction": "emit-triples pattern — triple-list assembly",
    },
    "satya-check": {
        "desc": 'eq (shabda nd "satya") nd  — node is in kosha',
        "regex": r'shabda.*"satya"',
        "abstraction": "is-satya? predicate tantra",
    },
    "pipe-reduce-inline": {
        "desc": "let x = pipe in reduce x ... — now expressible as | reduce",
        "regex": r"\| where.*\| collect.*\n.*reduce",
        "abstraction": "use | reduce pipe continuation directly",
    },
}


def analyze_tantra_patterns(tantra_files: dict[str, str]) -> dict:
    """Count micro-pattern occurrences in tantra2 files."""
    results = {}
    for pat_name, pat in TANTRA_MICRO_PATTERNS.items():
        rx = re.compile(pat["regex"], re.MULTILINE | re.DOTALL)
        by_file: dict[str, int] = {}
        for fpath, src in tantra_files.items():
            count = len(rx.findall(src))
            if count > 0:
                by_file[fpath] = count
        results[pat_name] = {
            "total": sum(by_file.values()),
            "by_file": sorted(by_file.items(), key=lambda x: x[1], reverse=True),
            "desc": pat["desc"],
            "abstraction": pat["abstraction"],
        }
    return results


# ── reporting ─────────────────────────────────────────────────────────────────

SEP = "═" * 72


def print_helpers_report(helpers: dict):
    print(SEP)
    print("  OCaml HELPER ADOPTION")
    print("  (false positives excluded: make_eval_arg definition, graph infra files,")
    print("   with_eval_ctx/eval_tantra impl lines, variable-index loops)")
    print(SEP)

    raw = helpers["raw"]
    usage = helpers["helper_usage"]
    gaps = helpers.get("migration_gaps", {})

    print(f"\n  {'helper':<25} {'raw remaining':>14} {'uses':>6}  status")
    print("  " + "-" * 60)

    helper_map = {
        "arg_extract": ("eval_str", "eval_flt", "eval_lst", "eval_int", "eval_arg"),
        "as_string_coerce": ("eval_str",),
        "node_lookup": ("with_node",),
        "eval_ctx_set": ("with_eval_ctx",),
        "json_field_opt": ("opt_field", "req_field"),
        "tantra_call_raw": ("call_tantra_opt",),
    }

    for pat_name, pat in raw.items():
        raw_total = pat["total"]
        helper_names = helper_map.get(pat_name, ())
        use_total = sum(usage.get(h, {}).get("total", 0) for h in helper_names)
        label = pat["label"]
        if raw_total == 0:
            status = "✓ fully migrated"
        elif use_total > 0:
            status = f"⚡ partial ({use_total} uses)"
        else:
            status = "✗ not yet started"
        print(f"  {label:<25} {raw_total:>14} {use_total:>6}  {status}")

    print()
    print("  Helper call counts:")
    for h_name, h_data in sorted(
        usage.items(), key=lambda x: x[1]["total"], reverse=True
    ):
        if h_data["total"] > 0:
            files = ", ".join(f"{fn}({n})" for fn, n in h_data["by_file"][:3])
            print(f"    {h_name:<20} {h_data['total']:>4}×  {files}")

    print()
    print("  Remaining raw patterns by file:")
    file_totals: dict[str, int] = defaultdict(int)
    for pat in raw.values():
        for fname, count in pat["by_file"]:
            file_totals[fname] += count
    for fname, total in sorted(file_totals.items(), key=lambda x: x[1], reverse=True):
        if total > 0:
            gap_note = f"  ← {'; '.join(gaps[fname])}" if fname in gaps else ""
            print(f"    {fname:<40} {total} raw{gap_note}")

    if gaps:
        print()
        print("  Migration gaps (no make_eval_arg setup yet):")
        for fname, notes in gaps.items():
            print(f"    {fname}: {'; '.join(notes)}")


def print_category_b_report(cat_b: dict):
    print(f"\n{SEP}")
    print("  CATEGORY B — OCaml → Tantra migration")
    print(SEP)
    print(
        f"\n  {'op':<20} {'score':>5} {'ocaml-arms':>10} {'tantra-calls':>12}  status"
    )
    print("  " + "-" * 65)

    for op_name, info in cat_b.items():
        score = info["score"]
        ocaml = info["ocaml_arms"]
        calls = info["tantra_calls"]
        callers = (
            ", ".join(info["calling_tantras"][:2]) if info["calling_tantras"] else "—"
        )
        status = (
            "✓ tantras calling it"
            if calls > 0
            else ("ready" if score >= 2 else "deferred")
        )
        print(f"  {op_name:<20} {score:>5} {ocaml:>10} {calls:>12}  {status}")
        if calls > 0:
            print(f"    tantras: {callers}")
        print(f"    tantra form: {info['tantra_form']}")

    print()
    score3 = [op for op, info in cat_b.items() if info["score"] == 3]
    score2 = [op for op, info in cat_b.items() if info["score"] == 2]
    score0 = [op for op, info in cat_b.items() if info["score"] == 0]
    print(f"  Migrate now (score 3): {', '.join(score3)}")
    print(f"  Migrate next (score 2): {', '.join(score2)}")
    print(f"  Deferred (score 0): {', '.join(score0)}")


def print_tantra_patterns_report(tp: dict):
    print(f"\n{SEP}")
    print("  Tantra MICRO-PATTERNS (inline → named tantras)")
    print(SEP)
    print(f"\n  {'pattern':<25} {'occurrences':>12}  abstraction")
    print("  " + "-" * 75)

    for pat_name, pat in sorted(tp.items(), key=lambda x: x[1]["total"], reverse=True):
        total = pat["total"]
        if total > 0:
            print(f"  {pat_name:<25} {total:>12}  {pat['abstraction']}")
            for fpath, count in pat["by_file"][:4]:
                print(f"    {fpath:<50} {count}×")
            print(f"    pattern: {pat['desc']}")
            print()

    print("  Already abstracted (named tantras exist):")
    named = [
        "agra-bandha          — brahman/yantra/vishesa/agra-bandha.tantra2",
        "sought-bandha        — brahman/yantra/pipeline/sought-bandha.tantra2",
        "flush-pending-mithya — brahman/yantra/pipeline/flush-pending-mithya.tantra2",
        "bound-vals           — brahman/yantra/pipeline/bound-vals.tantra2",
        "bound-concepts       — brahman/yantra/pipeline/bound-concepts.tantra2",
        "satya-concepts       — brahman/yantra/pipeline/satya-concepts.tantra2",
        "emit-triples         — brahman/yantra/sankhya/emit-triples.tantra2",
    ]
    for n in named:
        print(f"    ✓ {n}")


def print_report(helpers, cat_b, tp, report="all"):
    if report in ("all", "helpers"):
        print_helpers_report(helpers)
    if report in ("all", "category_b"):
        print_category_b_report(cat_b)
    if report in ("all", "tantra_patterns"):
        print_tantra_patterns_report(tp)
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--vyakarana", default=VYAKARANA_DEFAULT)
    parser.add_argument("--brahman", default=BRAHMAN_DEFAULT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--report",
        default="all",
        choices=["all", "helpers", "category_b", "tantra_patterns"],
    )
    args = parser.parse_args()

    ml_files = load_ml_sources(args.vyakarana)
    tantra_files = load_tantra2_sources(args.brahman)

    helpers = analyze_helpers(ml_files)
    cat_b = analyze_category_b(ml_files, tantra_files)
    tp = analyze_tantra_patterns(tantra_files)

    if args.json:
        json.dump(
            {"helpers": helpers, "category_b": cat_b, "tantra_patterns": tp},
            sys.stdout,
            indent=2,
        )
    else:
        print_report(helpers, cat_b, tp, args.report)
