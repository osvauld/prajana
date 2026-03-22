"""vyakarana_analysis.py — static analysis of the OCaml vyakarana codebase.

Parses OCaml source to extract:
  - Primitive ops (from yantra_ops.ml, yantra_eval_primitives.ml, yantra_pipeline_ops.ml)
  - Registered arities
  - Module dependencies and dead code
  - Cross-reference with tantra4 usage

No server needed. Reads .ml and .tantra4 source directly from disk.
"""

import os
import re
from collections import defaultdict
from pathlib import Path

from .paths import ROOT, YANTRA

VYAKARANA_LIB = os.path.join(ROOT, "vyakarana", "lib")
DUNE_FILE = os.path.join(VYAKARANA_LIB, "dune")


# ── OCaml source parsing ────────────────────────────────────────────────────


def _read(path):
    """Read file contents, return empty string if missing."""
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        return ""


def parse_match_arms(source):
    """Extract all | "op-name" -> arms from an OCaml match expression."""
    # matches:  | "op-name" ->   or   | "op-name" | "op-name2" ->
    pattern = r'\|\s*"([a-z][a-z0-9_-]*)"\s*(?:\|\s*"[a-z][a-z0-9_-]*"\s*)*->'
    return re.findall(pattern, source)


def parse_combined_match_arms(source):
    """Extract combined match arms like | "a" | "b" | "c" -> as groups."""
    pattern = r'\|((?:\s*"[a-z][a-z0-9_-]*"\s*\|?)+)\s*->'
    results = []
    for m in re.finditer(pattern, source):
        names = re.findall(r'"([a-z][a-z0-9_-]*)"', m.group(1))
        if names:
            results.append(names)
    return results


def parse_arity_registrations(source):
    """Extract r "op-name" N; registrations from register_primitive_arities."""
    pattern = r'r\s+"([a-z][a-z0-9_-]*)"\s+(-?\d+)'
    return {name: int(arity) for name, arity in re.findall(pattern, source)}


def parse_boundary_keywords(source):
    """Extract boundary keyword registrations."""
    # List.iter b [")" ; "]" ; ...]
    pattern = r'List\.iter\s+b\s+\[([^\]]+)\]'
    keywords = []
    for m in re.finditer(pattern, source):
        keywords.extend(re.findall(r'"([^"]+)"', m.group(1)))
    return keywords


def ops_in_file(path):
    """Get all primitive op names defined in an OCaml file (match arms)."""
    source = _read(path)
    return parse_match_arms(source)


def ops_grouped_in_file(path):
    """Get combined match arm groups from an OCaml file."""
    source = _read(path)
    return parse_combined_match_arms(source)


# ── Tantra usage scanning ───────────────────────────────────────────────────


def all_tantra4_sources():
    """Read all .tantra4 files and return {name: source}."""
    tantras = {}
    for root, _, files in os.walk(YANTRA):
        for f in files:
            if f.endswith(".tantra4"):
                path = os.path.join(root, f)
                name = f[:-len(".tantra4")]
                tantras[name] = _read(path)
    return tantras


def ops_used_in_tantras(tantras=None):
    """Scan all tantra4 sources for operation names actually used.

    Returns {op_name: [tantra_names_that_use_it]}.
    """
    if tantras is None:
        tantras = all_tantra4_sources()
    usage = defaultdict(list)
    for tname, source in tantras.items():
        # find all hyphenated identifiers and single-word ops
        ids = set(re.findall(r'\b([a-z][a-z0-9]*(?:-[a-z0-9]+)*)\b', source))
        for ident in ids:
            usage[ident].append(tname)
    return dict(usage)


# ── Full analysis ────────────────────────────────────────────────────────────


def shabda_eval_ops():
    """Get all eval: primitive names referenced from om/shabda nodes.

    These are fired indirectly via apply-op: tantra calls apply-op "addition",
    which reads eval:add from the node's shabda, then dispatches to OCaml add.

    Returns {eval_name: [node_names]}.
    """
    from . import shabda as shabda_mod
    nodes = shabda_mod.load_all()
    eval_refs = defaultdict(list)
    for name, data in nodes.items():
        fields = data.get("fields", {})
        ev = fields.get("eval", "")
        if ev:
            eval_refs[ev.strip()].append(name)
    return dict(eval_refs)


def analyze_ops():
    """Cross-reference OCaml primitive ops with tantra4 + shabda eval: usage.

    Returns dict with:
      - pure_ops: ops in yantra_ops.ml
      - graph_ops: ops in yantra_eval_primitives.ml
      - pipeline_ops: ops in yantra_pipeline_ops.ml
      - arities: registered arities
      - tantra_usage: {op: [tantras using it]}
      - shabda_usage: {op: [om nodes with eval:op]}
      - unused_ops: ops defined in OCaml but not used by any tantra OR shabda eval:
      - unregistered_ops: ops defined but missing arity registration
    """
    pure_ops = ops_in_file(os.path.join(VYAKARANA_LIB, "yantra_ops.ml"))
    graph_ops = ops_in_file(os.path.join(VYAKARANA_LIB, "yantra_eval_primitives.ml"))
    pipeline_ops = ops_in_file(os.path.join(VYAKARANA_LIB, "yantra_pipeline_ops.ml"))

    prims_source = _read(os.path.join(VYAKARANA_LIB, "yantra_eval_primitives.ml"))
    arities = parse_arity_registrations(prims_source)
    boundaries = parse_boundary_keywords(prims_source)

    all_defined = set(pure_ops) | set(graph_ops) | set(pipeline_ops)

    tantras = all_tantra4_sources()
    usage = ops_used_in_tantras(tantras)

    # shabda eval: keys — ops fired indirectly via apply-op
    shabda_evals = shabda_eval_ops()

    # ops defined in OCaml but never referenced from tantra4 AND not in shabda eval:
    unused = sorted(op for op in all_defined
                    if op not in usage and op not in shabda_evals)

    # ops only reachable via shabda eval: (not directly in tantra source)
    shabda_only = sorted(op for op in all_defined
                         if op not in usage and op in shabda_evals)

    # ops defined in match arms but missing from arity table
    unregistered = sorted(op for op in all_defined if op not in arities)

    # ops used in tantras but not defined as OCaml primitives
    # (these are tantra-to-tantra calls, not missing primitives)
    tantra_only = sorted(op for op in usage if op not in all_defined
                         and op in tantras)  # it's a tantra name

    return {
        "pure_ops": sorted(set(pure_ops)),
        "graph_ops": sorted(set(graph_ops)),
        "pipeline_ops": sorted(set(pipeline_ops)),
        "all_defined": sorted(all_defined),
        "arities": arities,
        "boundaries": boundaries,
        "tantra_usage": usage,
        "shabda_usage": shabda_evals,
        "unused_ops": unused,
        "shabda_only_ops": shabda_only,
        "unregistered_ops": unregistered,
        "tantra_only_calls": tantra_only,
        "tantra_count": len(tantras),
    }


def analyze_modules():
    """Analyze OCaml module structure from dune file.

    Returns dict with module list, sizes, and dependency info.
    """
    dune_source = _read(DUNE_FILE)
    # extract module names from (modules ...) block
    m = re.search(r'\(modules\s+([\s\S]*?)\)', dune_source)
    modules = []
    if m:
        modules = re.findall(r'([a-z][a-z0-9_]*)', m.group(1))

    module_info = {}
    for mod_name in modules:
        path = os.path.join(VYAKARANA_LIB, mod_name + ".ml")
        source = _read(path)
        lines = len(source.split("\n")) if source else 0

        # extract open statements
        opens = re.findall(r'^open\s+(\w+)', source, re.MULTILINE)

        # extract module-level let bindings
        lets = re.findall(r'^let\s+(\w+)', source, re.MULTILINE)

        # count match arms (proxy for complexity)
        match_arms = len(re.findall(r'^\s*\|', source, re.MULTILINE))

        module_info[mod_name] = {
            "path": path,
            "lines": lines,
            "opens": opens,
            "let_count": len(lets),
            "match_arms": match_arms,
        }

    return {
        "modules": modules,
        "module_info": module_info,
        "total_lines": sum(m["lines"] for m in module_info.values()),
    }


def analyze_old_code():
    """Find tantra3/tantra2/scan-specific code that can be removed.

    Returns dict with:
      - old_extensions: files still referencing .tantra3/.tantra2/.tantra
      - scan_references: files referencing scan construct
      - tantra3_parser_refs: who calls yantra_tantra_file2 functions
    """
    results = {
        "old_extensions": [],
        "scan_references": [],
        "tantra3_parser_refs": [],
        "dead_functions": [],
    }

    for mod_file in Path(VYAKARANA_LIB).glob("*.ml"):
        source = mod_file.read_text()
        name = mod_file.stem

        # .tantra3, .tantra2, .tantra references
        old_exts = re.findall(r'\.tantra[23]?\b', source)
        if old_exts:
            results["old_extensions"].append({
                "file": name,
                "refs": list(set(old_exts)),
                "count": len(old_exts),
            })

        # scan construct references (eval_scan, ScanStmt, scan_state, etc.)
        scan_refs = re.findall(r'\b(eval_scan|ScanStmt|scan_state|scan_branch|scan_emit|SEmit|SSet|SClear)\b', source)
        if scan_refs:
            results["scan_references"].append({
                "file": name,
                "refs": list(set(scan_refs)),
                "count": len(scan_refs),
            })

        # yantra_tantra_file2 references
        t2_refs = re.findall(r'\b(Yantra_tantra_file2\.\w+|parse_tantra2_file|tokenise2|parse2_\w+)\b', source)
        if t2_refs:
            results["tantra3_parser_refs"].append({
                "file": name,
                "refs": list(set(t2_refs)),
                "count": len(t2_refs),
            })

    return results


def full_report():
    """Generate a complete vyakarana analysis report."""
    return {
        "ops": analyze_ops(),
        "modules": analyze_modules(),
        "old_code": analyze_old_code(),
    }
