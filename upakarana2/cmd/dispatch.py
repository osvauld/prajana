"""dispatch.py — argparse parser + main() entry point."""

import argparse
import json
import sys

import upakarana2.store as store


def _print_json(data):
    print(json.dumps(data, indent=2, default=str))


def build_parser():
    p = argparse.ArgumentParser(prog="upakarana", description="Agent-X tooling")
    sub = p.add_subparsers(dest="command")

    # om
    s = sub.add_parser("om", help="Om5 queries")
    s.add_argument("action", choices=["summary", "search", "source", "domain", "with-relation"])
    s.add_argument("name", nargs="?")
    s.add_argument("--pattern", "-p")
    s.add_argument("--depth", type=int, default=2)
    s.add_argument("--relation", "-r")

    # tantra
    s = sub.add_parser("tantra", help="Tantra4 queries")
    s.add_argument("action", choices=["summary", "search", "source", "group", "callgraph", "reachability"])
    s.add_argument("name", nargs="?")
    s.add_argument("--pattern", "-p")

    # shabda
    s = sub.add_parser("shabda", help="Shabda queries")
    s.add_argument("action", choices=["summary", "search", "node", "gaps", "roles", "coverage"])
    s.add_argument("name", nargs="?")
    s.add_argument("--pattern", "-p")

    # vy (engine + live analysis)
    s = sub.add_parser("vy", help="Engine management + live analysis")
    s.add_argument("action", choices=[
        "start", "stop", "status", "reload",
        "eval", "ask", "walk", "inspect",
        "drift", "pratipaksha", "signal-trace", "panchaavayava",
    ])
    s.add_argument("name", nargs="?")
    s.add_argument("--expr", "-e")
    s.add_argument("--question", "-q")
    s.add_argument("--node")
    s.add_argument("--relation", "-r")
    s.add_argument("--incoming", "-i", action="store_true")
    s.add_argument("--sentence", "-s")

    # test
    s = sub.add_parser("test", help="Test operations")
    s.add_argument("action", choices=["list", "summary", "run", "failed"])
    s.add_argument("filter", nargs="?", help="layer name, gate:NAME, or test pattern")
    s.add_argument("--layer", "-l")
    s.add_argument("--gate", "-g")
    s.add_argument("--pattern", "-p")
    s.add_argument("--last-failed", action="store_true")
    s.add_argument("--failed", action="store_true",
                   help="Re-run only tests that failed in the last run")
    s.add_argument("--xfailed", action="store_true",
                   help="Re-run only xfailed tests from the last run")
    s.add_argument("--verbose", "-v", action="store_true")
    s.add_argument("--parallel", "-n", default="4",
                   help="Pytest-xdist workers: auto|off|N (default: 4)")

    # cache
    s = sub.add_parser("cache", help="Test result analysis")
    s.add_argument("action", choices=["summary", "gates", "slow", "trace", "compact"])
    s.add_argument("name", nargs="?", help="Test id for trace subcommand")

    # lint
    s = sub.add_parser("lint", help="Static lint")
    s.add_argument("target", choices=["om5", "tantra4", "all"], default="all", nargs="?")

    # health
    s = sub.add_parser("health", help="System health report")
    s.add_argument("--static-only", action="store_true")

    # search
    s = sub.add_parser("search", help="Cross-source pattern search")
    s.add_argument("pattern")
    s.add_argument("--scope", choices=["om", "tantra", "shabda", "all"], default="all")

    # ocaml
    s = sub.add_parser("ocaml", help="OCaml codebase analysis")
    s.add_argument("action", choices=["report", "darshana", "patterns", "coupling", "functions"])

    # a (graph analysis)
    s = sub.add_parser("a", help="Graph analysis (static)")
    s.add_argument("action", choices=[
        "ghosts", "incoming", "hubs", "orphans",
        "flow", "ring", "components", "swarupa",
        "signals", "signals-gap",
        "compose", "compose-gen", "compose-inverse",
        "gen-gaps", "gen-validate",
        "inherit-gaps",
    ])
    s.add_argument("name", nargs="?")
    s.add_argument("--layer", "-l")

    # usage
    s = sub.add_parser("usage", help="Command usage tracking")
    s.add_argument("action", choices=["report", "never", "reset"], default="report", nargs="?")

    return p


DISPATCH = {
    "om":     lambda args: _import_and_call("upakarana2.cmd.graph", "cmd_om", args),
    "tantra": lambda args: _import_and_call("upakarana2.cmd.graph", "cmd_tantra", args),
    "shabda": lambda args: _import_and_call("upakarana2.cmd.graph", "cmd_shabda", args),
    "search": lambda args: _import_and_call("upakarana2.cmd.graph", "cmd_search", args),
    "vy":     lambda args: _import_and_call("upakarana2.cmd.engine", "cmd_vy", args),
    "test":   lambda args: _import_and_call("upakarana2.cmd.test_cmd", "cmd_test", args),
    "cache":  lambda args: _import_and_call("upakarana2.cmd.test_cmd", "cmd_cache", args),
    "a":      lambda args: _import_and_call("upakarana2.cmd.analyze", "cmd_analyze", args),
    "health": lambda args: _import_and_call("upakarana2.cmd.meta", "cmd_health", args),
    "lint":   lambda args: _import_and_call("upakarana2.cmd.meta", "cmd_lint", args),
    "usage":  lambda args: _import_and_call("upakarana2.cmd.meta", "cmd_usage", args),
    "ocaml":  lambda args: _import_and_call("upakarana2.cmd.meta", "cmd_ocaml", args),
}


def _import_and_call(module, func, args):
    import importlib
    mod = importlib.import_module(module)
    getattr(mod, func)(args, store)


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    # Track usage
    action = getattr(args, "action", None) or getattr(args, "target", None)
    store.usage.track(args.command, action)

    handler = DISPATCH.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
