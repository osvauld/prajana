"""ocaml.py — OCaml codebase analysis for vyakarana/.

Structural analysis of the 12-module vyakarana engine:
  modules, dependencies, functions, patterns, mutable state,
  shared helpers, coupling, and consolidation candidates.

No engine needed — reads .ml files directly.
"""

import os
import re
from collections import defaultdict
from upakarana.paths import ROOT

VYAKARANA_LIB = ROOT / "vyakarana" / "lib"
VYAKARANA_BIN = ROOT / "vyakarana" / "bin"

# darshana layers — philosophical grouping
DARSHANA = {
    "prakriti":  {"modules": ["prakriti"], "role": "substrate — types, graph, CSR, PPR"},
    "vakya":     {"modules": ["vakya"], "role": "parser — tokenizer, expressions, tantra4, arity"},
    "vidya":     {"modules": ["vidya"], "role": "reader — shabda, classification, graph walks"},
    "karma":     {"modules": ["karma"], "role": "editor — om5 parser, file I/O, edit operations"},
    "jnana":     {"modules": ["jnana"], "role": "index — tantra registration, graph enrichment"},
    "kriya":     {"modules": ["kriya", "kriya_types", "kriya_ops", "kriya_graph", "kriya_eval"],
                  "role": "evaluator — types, pure ops, graph ops, eval loop, facade"},
    "vak":       {"modules": ["vak"], "role": "voice — reasoning walks, English rendering"},
    "dvara":     {"modules": ["dvara"], "role": "gate — socket server, session management"},
}


# ── module parsing ──────────────────────────────────────────────────────────


def parse_module(path):
    """Parse one .ml file into structural features."""
    src = open(path).read()
    lines = src.split("\n")
    name = os.path.basename(path)[:-3]

    opens = re.findall(r"^open (\w+)", src, re.M)
    lets = re.findall(r"^let (?:rec )?(\w+)", src, re.M)
    types = re.findall(r"^type (\w+)", src, re.M)
    match_arms = len(re.findall(r"^\s*\|", src, re.M))

    refs = len(re.findall(r"\bref\b", src))
    hashtbls = len(re.findall(r"Hashtbl\.\w+", src))

    # module-level refs (top-level let ... = ref) vs local refs
    ref_names = re.findall(r"^let (\w+)\s*(?::\s*[^=]+)?\s*=\s*ref\b", src, re.M)
    ht_names = re.findall(r"^let (\w+)\s*(?::\s*[^=]+)?\s*=\s*Hashtbl\.create", src, re.M)

    # I/O: file operations
    has_io = bool(re.search(r"\bopen_in\b|\bopen_out\b|\bSys\.\w+\b|\bUnix\.\w+", src))

    # forward refs
    fwd_refs = re.findall(r"let (\w+)\s*(?::\s*[^=]+)?\s*=\s*ref\s*\(fun", src)

    return {
        "name": name,
        "path": path,
        "lines": len(lines),
        "opens": opens,
        "lets": lets,
        "types": types,
        "match_arms": match_arms,
        "refs": refs,
        "ref_names": ref_names,
        "hashtbls": hashtbls,
        "ht_names": ht_names,
        "has_io": has_io,
        "fwd_refs": fwd_refs,
        "source": src,
    }


def parse_all():
    """Parse all .ml files in vyakarana/lib/ and vyakarana/bin/."""
    modules = {}
    for d in [VYAKARANA_LIB, VYAKARANA_BIN]:
        if not d.exists():
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".ml"):
                m = parse_module(os.path.join(d, f))
                modules[m["name"]] = m
    return modules


# ── dependency graph ────────────────────────────────────────────────────────


def dependency_graph(modules):
    """Build module dependency graph from `open` statements."""
    deps = {}
    names = {m["name"].lower() for m in modules.values()}
    for m in modules.values():
        targets = []
        for o in m["opens"]:
            low = o.lower()
            if low in names:
                targets.append(low)
        deps[m["name"]] = targets
    return deps


def reverse_deps(deps):
    """Invert: who depends on me."""
    rev = defaultdict(list)
    for src, targets in deps.items():
        for t in targets:
            rev[t].append(src)
    return dict(rev)


def coupling(modules):
    """Coupling score: (in_degree, out_degree) per module."""
    deps = dependency_graph(modules)
    rdeps = reverse_deps(deps)
    result = {}
    for name in modules:
        result[name] = {
            "in": len(rdeps.get(name, [])),
            "out": len(deps.get(name, [])),
            "dependents": rdeps.get(name, []),
            "depends_on": deps.get(name, []),
        }
    return result


# ── function analysis ───────────────────────────────────────────────────────


def all_functions(modules):
    """Extract all top-level let definitions with signatures."""
    fns = {}
    for m in modules.values():
        for match in re.finditer(
            r"^let (?:rec )?([\w']+)\s*([^=]*?)\s*=", m["source"], re.M
        ):
            name = match.group(1)
            sig = match.group(2).strip()[:80]
            if name.startswith("_") and name not in ("_shabda_store",):
                continue
            fns.setdefault(name, []).append({
                "module": m["name"],
                "signature": sig,
                "line": m["source"][:match.start()].count("\n") + 1,
            })
    return fns


def duplicate_functions(modules):
    """Functions defined in 2+ modules (excluding facade re-exports)."""
    fns = all_functions(modules)
    dups = {}
    for name, locs in fns.items():
        mods = [l["module"] for l in locs]
        # filter out kriya facade (it just re-exports)
        real_mods = [m for m in mods if m != "kriya"]
        if len(real_mods) > 1:
            dups[name] = real_mods
    return dups


# ── pattern detection ───────────────────────────────────────────────────────


def detect_patterns(modules):
    """Detect code patterns across modules."""
    patterns = defaultdict(list)

    for m in modules.values():
        src = m["source"]
        name = m["name"]

        # json_escape / je definitions (not just uses)
        if re.search(r"^let (?:json_escape|je)\b", src, re.M):
            patterns["json-escape-def"].append(name)

        # with_node usage
        if "with_node" in src:
            patterns["with_node"].append(name)

        # env_copy usage (actual calls, not comments)
        if re.search(r'(?<![\w-])env_copy\b', src) and re.search(r'^let\s.*env_copy|[^(]\benv_copy\s', src, re.M):
            patterns["env_copy"].append(name)

        # Hashtbl.find_opt → match pattern
        ht_lookups = len(re.findall(r"Hashtbl\.find_opt", src))
        if ht_lookups > 3:
            patterns["hashtbl-heavy"].append((name, ht_lookups))

        # List.filter_map pattern (functional transforms)
        filter_maps = len(re.findall(r"List\.filter_map", src))
        if filter_maps > 3:
            patterns["filter-map-heavy"].append((name, filter_maps))

        # dir_walk / read_file usage (shared helpers from prakriti)
        if "dir_walk" in src and name != "prakriti":
            patterns["uses-dir_walk"].append(name)
        if "read_file" in src and name != "prakriti":
            patterns["uses-read_file"].append(name)

        # edges_by_rel usage (shared helper from vidya)
        if "edges_by_rel" in src and name != "vidya":
            patterns["uses-edges_by_rel"].append(name)

        # Printf.sprintf with je — JSON construction
        je_sprintf = len(re.findall(r'Printf\.sprintf.*\(je\b', src))
        if je_sprintf > 5:
            patterns["manual-json-building"].append((name, je_sprintf))

        # match op with | "name" -> ... dispatch tables
        op_arms = len(re.findall(r'^\s*\| "[\w-]+"', src, re.M))
        if op_arms > 5:
            patterns["string-dispatch"].append((name, op_arms))

    return dict(patterns)


# ── mutable state ───────────────────────────────────────────────────────────


def mutable_state(modules):
    """Map all refs and hashtbls across the codebase."""
    refs = []
    hashtbls = []
    for m in modules.values():
        for r in m["ref_names"]:
            refs.append({"name": r, "module": m["name"]})
        for h in m["ht_names"]:
            hashtbls.append({"name": h, "module": m["name"]})
    return {"refs": refs, "hashtbls": hashtbls}


# ── consolidation candidates ────────────────────────────────────────────────


def consolidation_candidates(modules):
    """Find things that could be further consolidated."""
    candidates = []

    # je defined in multiple modules
    je_defs = []
    for m in modules.values():
        if re.search(r"^let je\b", m["source"], re.M):
            je_defs.append(m["name"])
    if len(je_defs) > 1:
        candidates.append({
            "kind": "duplicate-helper",
            "name": "je",
            "modules": je_defs,
            "suggestion": "Use Prakriti.je everywhere — remove local je definitions",
        })

    # json_escape defined in multiple modules
    je2_defs = []
    for m in modules.values():
        if re.search(r"^let json_escape\b", m["source"], re.M):
            je2_defs.append(m["name"])
    if len(je2_defs) > 1:
        candidates.append({
            "kind": "duplicate-helper",
            "name": "json_escape",
            "modules": je2_defs,
            "suggestion": "Single json_escape in Prakriti — remove copies in " + ", ".join(je2_defs[1:]),
        })

    # env_copy defined in multiple modules
    ec_defs = []
    for m in modules.values():
        if re.search(r"^let env_copy\b", m["source"], re.M):
            ec_defs.append(m["name"])
    if len(ec_defs) > 1:
        candidates.append({
            "kind": "duplicate-helper",
            "name": "env_copy",
            "modules": ec_defs,
            "suggestion": "Single env_copy — define in Kriya_types, use from there",
        })

    # scan remnants (SEmit, SSet, SClear still in kriya_types)
    for m in modules.values():
        if any(x in m["source"] for x in ["SEmit", "SSet", "SClear"]):
            if "scan_stmt" in m["source"]:
                candidates.append({
                    "kind": "dead-code",
                    "name": "scan_stmt variants (SEmit/SSet/SClear)",
                    "modules": [m["name"]],
                    "suggestion": "Remove if no tantra uses scan — check with eval 'scan' grep",
                })

    # old format references
    for m in modules.values():
        old_refs = re.findall(r'"\.\w*tantra[23]?"', m["source"])
        if old_refs:
            candidates.append({
                "kind": "old-format-ref",
                "name": f"old format strings in {m['name']}",
                "modules": [m["name"]],
                "suggestion": f"Remove references to {old_refs}",
            })

    return candidates


# ── summary ─────────────────────────────────────────────────────────────────


def summary(modules=None):
    """Full codebase summary."""
    if modules is None:
        modules = parse_all()

    lib_modules = {n: m for n, m in modules.items() if "bin" not in m["path"]}
    bin_modules = {n: m for n, m in modules.items() if "bin" in m["path"]}

    total_lines = sum(m["lines"] for m in modules.values())
    lib_lines = sum(m["lines"] for m in lib_modules.values())

    deps = dependency_graph(modules)
    cp = coupling(modules)
    patterns = detect_patterns(modules)
    state = mutable_state(modules)
    candidates = consolidation_candidates(modules)
    dups = duplicate_functions(modules)

    return {
        "modules": len(lib_modules),
        "bin_modules": len(bin_modules),
        "total_lines": total_lines,
        "lib_lines": lib_lines,
        "darshana": {
            layer: {
                "role": info["role"],
                "modules": info["modules"],
                "lines": sum(modules[m]["lines"] for m in info["modules"] if m in modules),
            }
            for layer, info in DARSHANA.items()
        },
        "coupling_top": sorted(
            [(n, c["in"], c["out"]) for n, c in cp.items()],
            key=lambda x: -(x[1] + x[2])
        )[:8],
        "patterns": {k: v for k, v in patterns.items()},
        "mutable_state": {
            "refs": len(state["refs"]),
            "hashtbls": len(state["hashtbls"]),
            "details": state,
        },
        "duplicate_functions": dups,
        "consolidation_candidates": candidates,
    }


# ── CLI-friendly formatters ─────────────────────────────────────────────────


def print_darshana(modules=None):
    """Print darshana layer overview."""
    if modules is None:
        modules = parse_all()

    total = sum(m["lines"] for m in modules.values())
    print(f"\n{'=' * 80}")
    print(f"  DARSHANA — {len(modules)} modules, {total} lines in {len(DARSHANA)} layers")
    print(f"{'=' * 80}\n")

    for layer, info in DARSHANA.items():
        mods = [m for m in info["modules"] if m in modules]
        lines = sum(modules[m]["lines"] for m in mods)
        refs = sum(modules[m]["refs"] for m in mods)
        io_count = sum(1 for m in mods if modules[m]["has_io"])
        bar = "█" * int(lines / total * 25) + "░" * (25 - int(lines / total * 25))

        print(f"  {layer:12s} {info['role']}")
        print(f"                {lines:4d}L  state={refs:3d}  {io_count} I/O  {bar}")
        for m in mods:
            mod = modules[m]
            io = " [I/O]" if mod["has_io"] else ""
            fwd = f" fwd={len(mod['fwd_refs'])}" if mod["fwd_refs"] else ""
            print(f"    {m:24s} {mod['lines']:5d}L  {mod['match_arms']:3d} arms  ht={mod['hashtbls']:3d}{io}{fwd}")
        print()


def print_patterns(modules=None):
    """Print detected patterns."""
    if modules is None:
        modules = parse_all()

    patterns = detect_patterns(modules)
    print(f"\n{'=' * 80}")
    print(f"  PATTERNS — {len(patterns)} types detected")
    print(f"{'=' * 80}\n")

    for pname, data in sorted(patterns.items()):
        if isinstance(data[0], tuple):
            print(f"  {pname}:")
            for item in data:
                print(f"    {item[0]:20s} {item[1]}")
        else:
            print(f"  {pname}: {data}")
    print()


def print_consolidation(modules=None):
    """Print consolidation candidates."""
    if modules is None:
        modules = parse_all()

    candidates = consolidation_candidates(modules)
    print(f"\n{'=' * 80}")
    print(f"  CONSOLIDATION CANDIDATES — {len(candidates)} found")
    print(f"{'=' * 80}\n")

    for c in candidates:
        print(f"  [{c['kind']}] {c['name']}")
        print(f"    in: {', '.join(c['modules'])}")
        print(f"    → {c['suggestion']}")
        print()


def print_coupling(modules=None):
    """Print module coupling."""
    if modules is None:
        modules = parse_all()

    cp = coupling(modules)
    print(f"\n{'=' * 80}")
    print(f"  MODULE COUPLING")
    print(f"{'=' * 80}\n")

    for name, c in sorted(cp.items(), key=lambda x: -(x[1]["in"] + x[1]["out"])):
        if c["in"] + c["out"] > 0:
            print(f"  {name:20s} in={c['in']} out={c['out']}  ← {c['dependents']}  → {c['depends_on']}")
    print()


# ── parallelism readiness ──────────────────────────────────────────────────


def parallelism_audit(modules=None):
    """Audit the codebase for parallelism readiness.

    Checks:
    1. Mutable shared state (refs, hashtbls at module level)
    2. env_copy sites (→ must become immutable map)
    3. Global refs (eval_ctx, session_store, etc.)
    4. Forward refs (wire pattern — not domain-safe)
    5. Side-effecting primitives (emit-edge, write-signal)
    6. Pure vs impure function classification
    7. Domain/Thread/Eio usage (existing concurrency)
    8. Hashtbl.replace in evaluator (→ must become Map.add)
    """
    if modules is None:
        modules = parse_all()

    # 1. Module-level mutable state
    global_state = []
    for m in modules.values():
        for r in m["ref_names"]:
            global_state.append({"name": r, "module": m["name"], "kind": "ref"})
        for h in m["ht_names"]:
            global_state.append({"name": h, "module": m["name"], "kind": "hashtbl"})

    # 2. env_copy sites
    env_copies = []
    for m in modules.values():
        for match in re.finditer(r"env_copy\b", m["source"]):
            line = m["source"][:match.start()].count("\n") + 1
            env_copies.append({"module": m["name"], "line": line})

    # 3. Forward refs (ref (fun ...))
    fwd_refs = []
    for m in modules.values():
        for fr in m["fwd_refs"]:
            fwd_refs.append({"name": fr, "module": m["name"]})

    # 4. Hashtbl.replace in evaluator modules (kriya_*)
    ht_replace_sites = []
    for m in modules.values():
        for match in re.finditer(r"Hashtbl\.replace\b", m["source"]):
            line = m["source"][:match.start()].count("\n") + 1
            # Get context line
            lines = m["source"].split("\n")
            ctx = lines[line - 1].strip()[:100] if line <= len(lines) else ""
            ht_replace_sites.append({
                "module": m["name"], "line": line, "context": ctx,
            })

    # 5. Side-effecting string-dispatch arms (emit, write, set)
    side_effects = []
    for m in modules.values():
        for match in re.finditer(r'\| "(emit-\w+|write-\w+|set-\w+)"', m["source"]):
            op = match.group(1)
            side_effects.append({"op": op, "module": m["name"]})

    # 6. Concurrency imports
    concurrency = []
    for m in modules.values():
        for kw in ["Domain", "Thread", "Lwt", "Eio", "Mutex", "Atomic"]:
            if kw in m["source"]:
                concurrency.append({"keyword": kw, "module": m["name"]})

    # 7. Pure function candidates (no ref, no Hashtbl.replace, no global access)
    pure_fns = []
    impure_fns = []
    for m in modules.values():
        if m["name"] not in ("kriya_ops", "kriya_graph", "kriya_eval"):
            continue
        for match in re.finditer(r"^let (?:rec )?([\w']+)\s*([^=]*?)\s*=", m["source"], re.M):
            fn_name = match.group(1)
            start = match.start()
            # Find end (next top-level let or end of file)
            next_let = re.search(r"\n(?:let |$)", m["source"][start + 1:])
            end = start + 1 + next_let.start() if next_let else len(m["source"])
            body = m["source"][start:end]
            has_mutation = bool(re.search(
                r"Hashtbl\.replace|Hashtbl\.add|:=|ref\s|Buffer\.", body
            ))
            if has_mutation:
                impure_fns.append({"fn": fn_name, "module": m["name"]})
            else:
                pure_fns.append({"fn": fn_name, "module": m["name"]})

    # 8. Classify blockers
    blockers = []
    if env_copies:
        blockers.append({
            "blocker": "mutable env (Hashtbl)",
            "sites": len(env_copies),
            "fix": "Hashtbl.t → StringMap.t (immutable persistent map)",
            "effort": "medium",
        })
    if fwd_refs:
        blockers.append({
            "blocker": "forward refs (global mutable fn pointers)",
            "sites": len(fwd_refs),
            "fix": "pass eval_fn as parameter or use first-class modules",
            "effort": "medium",
        })
    global_hts = [s for s in global_state if s["kind"] == "hashtbl"
                  and s["module"] in ("kriya_graph", "kriya_eval", "kriya_ops")]
    if global_hts:
        blockers.append({
            "blocker": "global hashtbls in evaluator",
            "sites": len(global_hts),
            "fix": "thread-local or pass as parameter",
            "effort": "small",
        })
    if side_effects:
        blockers.append({
            "blocker": "side-effecting primitives",
            "sites": len(side_effects),
            "fix": "buffer effects in pmap, commit after join",
            "effort": "medium",
        })

    return {
        "global_state": global_state,
        "env_copy_sites": env_copies,
        "forward_refs": fwd_refs,
        "ht_replace_sites": ht_replace_sites,
        "side_effect_ops": side_effects,
        "concurrency_imports": concurrency,
        "evaluator_purity": {
            "pure": len(pure_fns),
            "impure": len(impure_fns),
            "pure_fns": pure_fns,
            "impure_fns": impure_fns,
        },
        "blockers": blockers,
    }


def print_parallelism(modules=None):
    """Print parallelism readiness report."""
    if modules is None:
        modules = parse_all()

    audit = parallelism_audit(modules)

    print(f"\n{'=' * 80}")
    print(f"  PARALLELISM READINESS AUDIT")
    print(f"{'=' * 80}\n")

    # Blockers
    print("  ── Blockers ──")
    for b in audit["blockers"]:
        print(f"    [{b['effort']:6s}] {b['blocker']} ({b['sites']} sites)")
        print(f"            fix: {b['fix']}")
    print()

    # Global state
    print(f"  ── Global mutable state ({len(audit['global_state'])}) ──")
    for s in audit["global_state"]:
        print(f"    {s['kind']:7s}  {s['module']:20s}  {s['name']}")
    print()

    # Forward refs
    if audit["forward_refs"]:
        print(f"  ── Forward refs ({len(audit['forward_refs'])}) ──")
        for fr in audit["forward_refs"]:
            print(f"    {fr['module']:20s}  {fr['name']}")
        print()

    # Hashtbl.replace sites
    print(f"  ── Hashtbl.replace ({len(audit['ht_replace_sites'])}) ──")
    for s in audit["ht_replace_sites"]:
        print(f"    {s['module']:20s}:{s['line']:4d}  {s['context']}")
    print()

    # env_copy sites
    print(f"  ── env_copy ({len(audit['env_copy_sites'])}) ──")
    for s in audit["env_copy_sites"]:
        print(f"    {s['module']:20s}:{s['line']:4d}")
    print()

    # Side effects
    if audit["side_effect_ops"]:
        print(f"  ── Side-effecting ops ({len(audit['side_effect_ops'])}) ──")
        for s in audit["side_effect_ops"]:
            print(f"    {s['module']:20s}  {s['op']}")
        print()

    # Purity
    p = audit["evaluator_purity"]
    print(f"  ── Evaluator purity: {p['pure']} pure, {p['impure']} impure ──")
    if p["impure_fns"]:
        print("    impure:")
        for f in p["impure_fns"]:
            print(f"      {f['module']:20s}  {f['fn']}")
    print()

    # Concurrency
    if audit["concurrency_imports"]:
        print(f"  ── Existing concurrency ──")
        for c in audit["concurrency_imports"]:
            print(f"    {c['module']:20s}  {c['keyword']}")
    else:
        print("  ── No concurrency imports found ──")
    print()


def print_report(modules=None):
    """Print full report."""
    if modules is None:
        modules = parse_all()
    print_darshana(modules)
    print_patterns(modules)
    print_coupling(modules)
    print_consolidation(modules)
