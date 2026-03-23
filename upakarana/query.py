"""query.py — Composable query primitives for LLM and programmatic use.

Atomic queries that return structured data (dicts/lists).
Combines static file analysis + live engine when available.

Three source layers:
  1. static — reads .ml/.om5/.tantra4/.shabda files directly (always available)
  2. engine — queries the running vyakarana socket (available when server is up)
  3. combined — merges both for complete picture

Usage:
    from upakarana.query import Q
    q = Q()                          # auto-connects to engine if available
    q.module("prakriti")             # module overview
    q.function("join")              # find function across codebase
    q.node("velocity")             # graph node details
    q.tantra("anuvada-ganana")     # tantra structure
    q.shabda("mass")               # shabda metadata
    q.explain("prakriti")          # natural language summary
    q.deps("kriya_graph")          # dependency chain
    q.callers("join")              # who calls this function
    q.search("velocity", scope="all")  # cross-source search
"""

import os
import re
from upakarana.paths import ROOT


class Q:
    """Query interface — composable primitives for codebase + graph queries."""

    def __init__(self, client=None):
        """Initialize. Optionally pass an engine Client; otherwise auto-connects."""
        self._client = client
        self._client_tried = client is not None
        self._modules_cache = None
        self._om5_cache = None
        self._tantra_cache = None
        self._shabda_cache = None

    @property
    def _engine(self):
        """Lazy engine client — connects on first use, None if unavailable."""
        if not self._client_tried:
            self._client_tried = True
            try:
                from upakarana.engine.client import Client
                self._client = Client()
            except Exception:
                self._client = None
        return self._client

    @property
    def _modules(self):
        if self._modules_cache is None:
            from upakarana.analysis.ocaml import parse_all
            self._modules_cache = parse_all()
        return self._modules_cache

    @property
    def _om5(self):
        if self._om5_cache is None:
            from upakarana.parsers import om5
            self._om5_cache = om5.load_all()
        return self._om5_cache

    @property
    def _tantras(self):
        if self._tantra_cache is None:
            from upakarana.parsers import tantra4
            self._tantra_cache = tantra4.load_all()
        return self._tantra_cache

    @property
    def _shabda_nodes(self):
        if self._shabda_cache is None:
            from upakarana.parsers import shabda
            self._shabda_cache = shabda.load_all()
        return self._shabda_cache

    # ── module queries ────────────────────────────────────────────────────

    def modules(self):
        """List all OCaml modules with line counts."""
        return [
            {"name": m["name"], "lines": m["lines"], "has_io": m["has_io"],
             "opens": m["opens"], "match_arms": m["match_arms"]}
            for m in sorted(self._modules.values(), key=lambda x: -x["lines"])
        ]

    def module(self, name):
        """Full details of one OCaml module."""
        m = self._modules.get(name)
        if not m:
            return {"error": f"module not found: {name}"}

        from upakarana.analysis.ocaml import DARSHANA, coupling
        layer = next(
            (l for l, info in DARSHANA.items() if name in info["modules"]),
            "unknown"
        )
        cp = coupling(self._modules).get(name, {})

        fns = []
        for match in re.finditer(
            r"^let (?:rec )?([\w']+)\s*([^=]*?)\s*=", m["source"], re.M
        ):
            fn_name = match.group(1)
            sig = match.group(2).strip()[:100]
            line = m["source"][:match.start()].count("\n") + 1
            fns.append({"name": fn_name, "signature": sig, "line": line})

        types = []
        for match in re.finditer(r"^type ([\w']+)\s*=?\s*(.*)", m["source"], re.M):
            types.append({"name": match.group(1), "preview": match.group(2).strip()[:60]})

        return {
            "name": name,
            "layer": layer,
            "lines": m["lines"],
            "opens": m["opens"],
            "match_arms": m["match_arms"],
            "has_io": m["has_io"],
            "refs": m["ref_names"],
            "hashtbls": m["ht_names"],
            "fwd_refs": m["fwd_refs"],
            "functions": fns,
            "types": types,
            "dependents": cp.get("dependents", []),
            "depends_on": cp.get("depends_on", []),
        }

    # ── function queries ──────────────────────────────────────────────────

    def function(self, name):
        """Find a function across all modules. Returns definition sites + source."""
        results = []
        for m in self._modules.values():
            for match in re.finditer(
                rf"^(let (?:rec )?{re.escape(name)}\b.*?)(?=\n(?:let |type |\(\*|$))",
                m["source"], re.M | re.S
            ):
                line = m["source"][:match.start()].count("\n") + 1
                body = match.group(1)
                # trim to reasonable length
                lines = body.split("\n")
                results.append({
                    "module": m["name"],
                    "line": line,
                    "lines": len(lines),
                    "source": body[:2000] if len(body) > 2000 else body,
                })
        return results if results else {"error": f"function not found: {name}"}

    def callers(self, fn_name):
        """Find all call sites of a function across OCaml modules."""
        results = []
        for m in self._modules.values():
            # skip the module where it's defined (self-calls are obvious)
            lines = m["source"].split("\n")
            for i, line in enumerate(lines):
                # look for the function name used as a call (not a definition)
                if re.search(rf"\b{re.escape(fn_name)}\b", line):
                    if not re.match(rf"^let (?:rec )?{re.escape(fn_name)}\b", line):
                        results.append({
                            "module": m["name"],
                            "line": i + 1,
                            "text": line.strip()[:120],
                        })
        return results

    # ── dependency queries ────────────────────────────────────────────────

    def deps(self, name):
        """Full dependency chain for a module (what it needs, who needs it)."""
        from upakarana.analysis.ocaml import dependency_graph, reverse_deps
        dg = dependency_graph(self._modules)
        rdg = reverse_deps(dg)
        return {
            "module": name,
            "depends_on": dg.get(name, []),
            "depended_by": rdg.get(name, []),
        }

    # ── graph node queries ────────────────────────────────────────────────

    def node(self, name):
        """Graph node details — combines static om5 + live engine."""
        result = {}

        # static: from om5 file
        om5_node = self._om5.get(name)
        if om5_node:
            result["om5"] = {
                "name": om5_node["name"],
                "layer": om5_node["layer"],
                "domain": om5_node.get("domain", ""),
                "edges": om5_node["edges"],
                "path": om5_node.get("path", ""),
            }

        # static: shabda metadata
        shabda_node = self._shabda_nodes.get(name)
        if shabda_node:
            result["shabda"] = shabda_node.get("fields", {})

        # live: engine inspection
        if self._engine:
            try:
                result["live"] = self._engine.inspect(name)
            except Exception:
                pass
            try:
                result["triples"] = self._engine.triples_of(name)
            except Exception:
                pass

        if not result:
            return {"error": f"node not found: {name}"}
        result["name"] = name
        return result

    def walk(self, name, relation, incoming=False):
        """Walk edges from a node. Requires engine."""
        if not self._engine:
            return {"error": "engine not available"}
        try:
            if incoming:
                return self._engine.walk_in(name, relation)
            return self._engine.walk(name, relation)
        except Exception as e:
            return {"error": str(e)}

    def eval(self, expr):
        """Evaluate a tantra expression. Requires engine."""
        if not self._engine:
            return {"error": "engine not available"}
        try:
            return self._engine.eval(expr)
        except Exception as e:
            return {"error": str(e)}

    # ── tantra queries ────────────────────────────────────────────────────

    def tantra(self, name):
        """Tantra structure — params, bindings, calls, source."""
        t = self._tantras.get(name)
        if not t:
            return {"error": f"tantra not found: {name}"}
        return {
            "name": t["name"],
            "group": t["group"],
            "takes": t["takes"],
            "lines": t["lines"],
            "calls": t["calls"],
            "conds": t["conds"],
            "reduces": t["reduces"],
            "path": t.get("path", ""),
            "source": t["source"],
        }

    def tantra_calls(self, name):
        """What other tantras does this tantra call?"""
        t = self._tantras.get(name)
        if not t:
            return {"error": f"tantra not found: {name}"}
        return t["calls"]

    def tantra_callers(self, name):
        """What tantras call this one?"""
        from upakarana.parsers import tantra4
        cg = tantra4.call_graph(self._tantras)
        rcg = tantra4.reverse_call_graph(cg)
        return rcg.get(name, [])

    # ── shabda queries ────────────────────────────────────────────────────

    def shabda(self, name):
        """Shabda metadata for a node."""
        node = self._shabda_nodes.get(name)
        if not node:
            # try via engine
            if self._engine:
                try:
                    pairs = self._engine.eval(f'read-shabda "{name}"')
                    if pairs:
                        return {"name": name, "fields": pairs, "source": "engine"}
                except Exception:
                    pass
            return {"error": f"shabda not found: {name}"}
        return {"name": name, "fields": node.get("fields", {}), "source": "file"}

    # ── search ────────────────────────────────────────────────────────────

    def search(self, pattern, scope="all"):
        """Cross-source search: om5 nodes, tantras, shabda, OCaml functions."""
        results = []
        pat = re.compile(pattern, re.I)

        if scope in ("all", "om"):
            for name, node in self._om5.items():
                if pat.search(name) or pat.search(str(node.get("source", ""))):
                    results.append({"kind": "om5", "name": name,
                                    "layer": node["layer"]})

        if scope in ("all", "tantra"):
            for name, t in self._tantras.items():
                if pat.search(name) or pat.search(t.get("source", "")):
                    results.append({"kind": "tantra", "name": name,
                                    "group": t["group"]})

        if scope in ("all", "shabda"):
            for name in self._shabda_nodes:
                if pat.search(name):
                    results.append({"kind": "shabda", "name": name})

        if scope in ("all", "ocaml"):
            for m in self._modules.values():
                if pat.search(m["source"]):
                    # find matching lines
                    matches = []
                    for i, line in enumerate(m["source"].split("\n")):
                        if pat.search(line):
                            matches.append({"line": i + 1, "text": line.strip()[:100]})
                    results.append({"kind": "ocaml", "name": m["name"],
                                    "matches": matches[:5]})

        return results

    # ── explain ───────────────────────────────────────────────────────────

    def explain(self, name):
        """Gather all available context about a name — for LLM consumption.
        Checks: OCaml module, function, graph node, tantra, shabda."""
        context = {"name": name, "found_in": []}

        # OCaml module?
        if name in self._modules:
            context["found_in"].append("ocaml_module")
            context["module"] = self.module(name)

        # OCaml function?
        fn = self.function(name)
        if isinstance(fn, list) and fn:
            context["found_in"].append("ocaml_function")
            context["function"] = fn

        # Graph node?
        node = self.node(name)
        if "error" not in node:
            context["found_in"].append("graph_node")
            context["node"] = node

        # Tantra?
        t = self.tantra(name)
        if "error" not in t:
            context["found_in"].append("tantra")
            context["tantra"] = t

        # Shabda?
        s = self.shabda(name)
        if "error" not in s:
            context["found_in"].append("shabda")
            context["shabda"] = s

        if not context["found_in"]:
            context["error"] = f"nothing found for: {name}"

        return context

    # ── op queries (high-level: "does this op exist? who handles it?") ───

    def op(self, name):
        """Everything about an op: where it's dispatched, arity, graph node, shabda.
        Answers: "does op X exist?", "what handles it?", "what's its arity?" """
        result = {"name": name, "exists": False}

        # 1. check OCaml dispatch — which match arm handles it?
        for mod_name in ("kriya_graph", "kriya_ops", "dvara"):
            m = self._modules.get(mod_name)
            if not m:
                continue
            # find | "op-name" -> ... match arm
            pat = rf'^\s*\| "{re.escape(name)}"'
            for i, line in enumerate(m["source"].split("\n")):
                if re.match(pat, line):
                    result["exists"] = True
                    result.setdefault("dispatch", []).append({
                        "module": mod_name,
                        "line": i + 1,
                        "text": line.strip()[:120],
                    })

        # 2. check arity registration
        m = self._modules.get("kriya_graph")
        if m:
            pat = rf'r "{re.escape(name)}"\s+(-?\d+)'
            match = re.search(pat, m["source"])
            if match:
                result["arity"] = int(match.group(1))

        # 3. check graph node (op-<name>)
        op_node_name = f"op-{name}"
        om5_node = self._om5.get(op_node_name)
        if om5_node:
            result["exists"] = True
            result["graph_node"] = op_node_name
            result["edges"] = om5_node["edges"]

        # 4. check shabda for eval: key (what OCaml primitive implements it)
        shabda_node = self._shabda_nodes.get(op_node_name)
        if shabda_node:
            fields = shabda_node.get("fields", {})
            if "eval" in fields:
                result["eval_primitive"] = fields["eval"]
            if "parse-arity" in fields:
                result["parse_arity"] = fields["parse-arity"]
            if "degree" in fields:
                result["degree"] = fields["degree"]
            result["shabda"] = fields

        # 5. check if there's a tantra with this name
        t = self._tantras.get(name)
        if t:
            result["exists"] = True
            result["tantra"] = {
                "group": t["group"],
                "takes": t["takes"],
                "lines": t["lines"],
            }

        # 6. live engine check
        if self._engine and not result["exists"]:
            try:
                r = self._engine.eval(f'lookup "op-{name}"')
                if r and r != "none" and r is not None:
                    result["exists"] = True
                    result["live_node"] = True
            except Exception:
                pass

        return result

    def ops(self, pattern=None):
        """List all registered ops. Optional regex filter."""
        # collect from arity registration in kriya_graph
        m = self._modules.get("kriya_graph")
        if not m:
            return []
        ops = []
        for match in re.finditer(r'r "([^"]+)"\s+(-?\d+)', m["source"]):
            name = match.group(1)
            arity = int(match.group(2))
            if pattern and not re.search(pattern, name, re.I):
                continue
            ops.append({"name": name, "arity": arity})
        return sorted(ops, key=lambda x: x["name"])

    def dispatch_path(self, op_name):
        """Trace the full dispatch chain for an op call.
        Returns: which module handles it, fallback chain, tantra-by-name resolution."""
        chain = []

        # eval_call in kriya_graph chains: eval_graph_op → eval_pure_op → eval_pipeline_op → tantra fallback
        for step, mod_name, fn_name in [
            ("1. graph op", "kriya_graph", "eval_graph_op"),
            ("2. pure op", "kriya_ops", "eval_pure_op"),
            ("3. pipeline op", "kriya_graph", "eval_pipeline_op"),
        ]:
            m = self._modules.get(mod_name)
            if not m:
                continue
            pat = rf'^\s*\| "{re.escape(op_name)}"'
            hit = None
            for i, line in enumerate(m["source"].split("\n")):
                if re.match(pat, line):
                    hit = {"line": i + 1, "text": line.strip()[:120]}
                    break
            chain.append({
                "step": step,
                "module": mod_name,
                "function": fn_name,
                "matched": hit is not None,
                "match": hit,
            })
            if hit:
                break  # first match wins in the chain

        # 4. tantra-by-name fallback
        t = self._tantras.get(op_name)
        if t:
            chain.append({
                "step": "4. tantra fallback",
                "module": "(tantra file)",
                "function": op_name,
                "matched": True,
                "match": {"path": t.get("path", ""), "takes": t["takes"]},
            })

        return {"op": op_name, "chain": chain}

    def missing_ops(self):
        """Find ops registered in arity table but not handled in any dispatch."""
        registered = {o["name"] for o in self.ops()}
        handled = set()
        for mod_name in ("kriya_graph", "kriya_ops"):
            m = self._modules.get(mod_name)
            if not m:
                continue
            for match in re.finditer(r'^\s*\| "([^"]+)"', m["source"], re.M):
                handled.add(match.group(1))
        # also count tantras as handled
        for name in self._tantras:
            handled.add(name)
        return sorted(registered - handled)

    # ── batch / overview ──────────────────────────────────────────────────

    def overview(self):
        """System overview — counts and health."""
        result = {
            "ocaml_modules": len(self._modules),
            "ocaml_lines": sum(m["lines"] for m in self._modules.values()),
            "om5_nodes": len(self._om5),
            "tantras": len(self._tantras),
            "shabda_nodes": len(self._shabda_nodes),
        }
        if self._engine:
            try:
                result["engine"] = "connected"
                tantras = self._engine.list_tantras()
                result["loaded_tantras"] = len(tantras)
            except Exception:
                result["engine"] = "error"
        else:
            result["engine"] = "not available"
        return result
