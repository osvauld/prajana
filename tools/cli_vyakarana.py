"""cli_vyakarana.py — CLI commands for vyakarana OCaml codebase analysis.

Handles: vyakarana (ops|modules|old-code|unused|report)
"""

from . import vyakarana_analysis as VA


def _sep(title, width=80):
    return f"\n{'=' * width}\n  {title}\n{'=' * width}\n"


def cmd_vyakarana(args):
    sub = args.subcmd or "report"

    if sub == "ops":
        _ops()
    elif sub == "unused":
        _unused()
    elif sub == "modules":
        _modules()
    elif sub == "old-code":
        _old_code()
    elif sub == "report":
        _report()
    else:
        print(f"Unknown vyakarana command: {sub}")
        print("Available: ops, unused, modules, old-code, report")


def _ops():
    """Show all primitive ops grouped by file."""
    r = VA.analyze_ops()
    print(_sep(f"OCAML PRIMITIVE OPS — {len(r['all_defined'])} defined"))

    print(f"  yantra_ops.ml (pure):")
    for op in r["pure_ops"]:
        arity = r["arities"].get(op, "?")
        users = r["tantra_usage"].get(op, [])
        status = f"{len(users)} tantras" if users else "UNUSED"
        print(f"    {op:<25} arity={arity:<4} {status}")

    print(f"\n  yantra_eval_primitives.ml (graph):")
    for op in r["graph_ops"]:
        arity = r["arities"].get(op, "?")
        users = r["tantra_usage"].get(op, [])
        status = f"{len(users)} tantras" if users else "UNUSED"
        print(f"    {op:<25} arity={arity:<4} {status}")

    print(f"\n  yantra_pipeline_ops.ml (pipeline):")
    for op in r["pipeline_ops"]:
        arity = r["arities"].get(op, "?")
        users = r["tantra_usage"].get(op, [])
        status = f"{len(users)} tantras" if users else "UNUSED"
        print(f"    {op:<25} arity={arity:<4} {status}")
    print()


def _unused():
    """Show ops defined in OCaml but not used by any tantra or shabda eval:."""
    r = VA.analyze_ops()
    unused = r["unused_ops"]
    shabda_only = r["shabda_only_ops"]

    print(_sep(f"UNUSED OPS — {len(unused)} defined, unreferenced by tantra or shabda"))

    for op in unused:
        loc = "pure" if op in r["pure_ops"] else \
              "graph" if op in r["graph_ops"] else "pipeline"
        arity = r["arities"].get(op, "?")
        print(f"    {op:<25} [{loc}]  arity={arity}")

    if shabda_only:
        print(f"\n  SHABDA-ONLY OPS — {len(shabda_only)} (reachable only via apply-op + eval: key):")
        for op in shabda_only:
            loc = "pure" if op in r["pure_ops"] else \
                  "graph" if op in r["graph_ops"] else "pipeline"
            nodes = r["shabda_usage"].get(op, [])
            arity = r["arities"].get(op, "?")
            print(f"    {op:<25} [{loc}]  arity={arity}  <- {', '.join(nodes)}")

    if r["unregistered_ops"]:
        print(f"\n  MISSING ARITY ({len(r['unregistered_ops'])}):")
        for op in r["unregistered_ops"]:
            print(f"    {op}")
    print()


def _modules():
    """Show OCaml module structure and sizes."""
    r = VA.analyze_modules()
    print(_sep(f"OCAML MODULES — {len(r['modules'])} modules, {r['total_lines']} lines"))

    print(f"  {'Module':<30} {'Lines':>6} {'Lets':>5} {'Arms':>5} {'Opens'}")
    print(f"  {'─' * 80}")
    for mod_name in r["modules"]:
        info = r["module_info"][mod_name]
        opens = ", ".join(info["opens"][:4])
        if len(info["opens"]) > 4:
            opens += f" +{len(info['opens'])-4}"
        print(f"  {mod_name:<30} {info['lines']:>6} {info['let_count']:>5} "
              f"{info['match_arms']:>5} {opens}")
    print()


def _old_code():
    """Show tantra3/scan-specific code that can be removed."""
    r = VA.analyze_old_code()
    print(_sep("OLD CODE — tantra3/scan remnants"))

    if r["old_extensions"]:
        print(f"  Files referencing .tantra3/.tantra2/.tantra:")
        for item in r["old_extensions"]:
            print(f"    {item['file']:<30} {item['refs']}  ({item['count']}x)")

    if r["scan_references"]:
        print(f"\n  Files with scan construct references:")
        for item in r["scan_references"]:
            print(f"    {item['file']:<30} {item['refs']}")

    if r["tantra3_parser_refs"]:
        print(f"\n  Files calling tantra3 parser (yantra_tantra_file2):")
        for item in r["tantra3_parser_refs"]:
            print(f"    {item['file']:<30} {item['refs']}")
    print()


def _report():
    """Full analysis report."""
    _unused()
    _old_code()
    _modules()
