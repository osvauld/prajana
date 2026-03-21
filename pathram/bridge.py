"""bridge.py — Live codebase data integration.

Wraps tools/ modules to pull live data from om nodes, tantras,
shabda, and test cache. All data is read fresh on each call.
"""

import sys
import os

# Ensure tools/ is importable
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)


class Bridge:
    """Lazy-loading bridge to tools/ modules."""

    def __init__(self):
        self._om_cache = None
        self._tantra_cache = None

    def _load_om(self):
        if self._om_cache is None:
            from tools import om
            self._om_cache = om.load_all()
        return self._om_cache

    def _load_tantras(self):
        if self._tantra_cache is None:
            from tools import tantras
            self._tantra_cache = tantras.load_all()
        return self._tantra_cache

    def om_summary(self):
        """Summary dict: total nodes, by domain, by layer."""
        from tools import om
        oms = self._load_om()
        return om.to_json_summary(oms)

    def tantra_summary(self):
        """Summary dict: total tantras, by group."""
        from tools import tantras
        ts = self._load_tantras()
        return tantras.to_json_summary(ts)

    def shabda_summary(self):
        """Shabda landscape summary."""
        from tools import shabda
        return shabda.summary()

    def test_baseline(self):
        """Current test results from cache."""
        from tools import cache
        summary, entries = cache.load()
        outcomes = cache.by_outcome(entries)
        return {
            "passed": len(outcomes.get("passed", [])),
            "xfailed": len(outcomes.get("xfailed", [])),
            "failed": len(outcomes.get("failed", [])),
        }

    def search_om(self, pattern):
        """Search om nodes for a pattern."""
        from tools import om
        oms = self._load_om()
        return om.search(oms, pattern)

    def search_tantras(self, pattern):
        """Search tantra sources for a pattern."""
        from tools import tantras
        ts = self._load_tantras()
        return tantras.search(ts, pattern)

    def search_shabda(self, pattern):
        """Search shabda word index for a pattern."""
        from tools import shabda
        return shabda.search_words(pattern=pattern)

    def om_node(self, name):
        """Get a single om node's details."""
        oms = self._load_om()
        node = oms.get(name)
        if node:
            from tools import om
            return om.to_json_node(node)
        return None

    def live_stats(self):
        """Compact live stats for glance/index."""
        stats = {}
        try:
            oms = self._load_om()
            stats["om_count"] = len(oms)
        except Exception:
            pass
        try:
            ts = self._load_tantras()
            stats["tantra_count"] = len(ts)
        except Exception:
            pass
        try:
            bl = self.test_baseline()
            stats.update(bl)
        except Exception:
            pass
        return stats

    def invalidate(self):
        """Clear caches to force fresh reads."""
        self._om_cache = None
        self._tantra_cache = None

    # --- Math extraction (the graph describes its own mathematics) ---

    def mantra_signatures(self):
        """Extract all mantra function signatures: f(janya) → phala via kriya."""
        oms = self._load_om()
        sigs = []
        for name, o in oms.items():
            if o.get("layer") != "mantra":
                continue
            edges = o.get("edges", [])
            janya = [e["target"] for e in edges if e["relation"] == "janya"]
            phala = [e["target"] for e in edges if e["relation"] == "phala"]
            kriya = [e["target"] for e in edges if e["relation"] == "kriya"]
            varga = [e["target"] for e in edges if e["relation"] == "varga"]
            sk = o.get("shabda_keys", {})
            if not janya and not phala:
                continue
            sigs.append({
                "name": name,
                "janya": janya,
                "phala": phala,
                "kriya": kriya,
                "varga": varga,
                "shabda": sk,
            })
        return sigs

    def operation_algebra(self):
        """Extract all fireable operations with eval, arity, inverse.

        Merges shabda from both .om inline shabda_keys AND external .shabda files,
        since eval/arity/pratipaksha-0 etc. live in the external shabda store.
        """
        oms = self._load_om()
        from tools import shabda as shabda_mod
        all_shabda = shabda_mod.load_all()
        ops = []
        for name, o in oms.items():
            # Merge: external shabda wins over inline
            sk = dict(o.get("shabda_keys", {}))
            ext = all_shabda.get(name)
            if ext:
                for k, v in ext.get("fields", {}).items():
                    if k not in sk:
                        sk[k] = v
            ev = sk.get("eval")
            if not ev:
                continue
            edges = o.get("edges", [])
            pratipaksha = [e["target"] for e in edges if e["relation"] == "pratipaksha"]
            ops.append({
                "name": name,
                "eval": ev,
                "arity": int(sk.get("arity", 0)),
                "word": sk.get("word", ""),
                "inverse": sk.get("inverse", ""),
                "pratipaksha": pratipaksha,
                "pratipaksha_0": sk.get("pratipaksha-0", ""),
                "pratipaksha_1": sk.get("pratipaksha-1", ""),
                "flip_1": bool(sk.get("pratipaksha-1-flip", "")),
            })
        return ops

    def algebraic_hierarchy(self):
        """Extract the algebraic structure hierarchy from kosha."""
        oms = self._load_om()
        structs = []
        for name in ["monoid", "group", "ring", "graded-ring", "distributivity",
                      "field-varga", "filtration", "associativity", "commutativity"]:
            o = oms.get(name)
            if not o:
                continue
            edges = o.get("edges", [])
            by_rel = {}
            for e in edges:
                by_rel.setdefault(e["relation"], []).append(e["target"])
            structs.append({"name": name, "edges": by_rel})
        return structs

    def pipeline_composition(self):
        """Extract the pipeline as a composition of tantras."""
        from tools import tantras
        ts = self._load_tantras()
        cg = tantras.call_graph(ts)
        rcg = tantras.reverse_call_graph(cg)
        composition = []
        for name, t in ts.items():
            composition.append({
                "name": name,
                "group": t.get("group", ""),
                "takes": t.get("takes", []),
                "returns": t.get("returns"),
                "calls": cg.get(name, []),
                "called_by": rcg.get(name, []),
                "lines": t.get("lines", 0),
                "scans": t.get("scans", 0),
                "reduces": t.get("reduces", 0),
                "conds": t.get("conds", 0),
            })
        return composition

    def visheshanam_dimensions(self):
        """Extract the edge type algebra (visheshanam ring dimensions)."""
        oms = self._load_om()
        vr = oms.get("visheshanam-ring")
        if not vr:
            return []
        edges = vr.get("edges", [])
        return [e["target"] for e in edges if e["relation"] == "yukta"]

    def emit_math(self):
        """Generate the full mathematical description of the system from the graph.

        Returns a markdown string with LaTeX describing:
        1. The operation algebra (Σ, with eval/arity/inverse)
        2. The mantra signatures (typed functions on the graph)
        3. The algebraic hierarchy (structural permissions)
        4. The pipeline as function composition
        5. The visheshanam ring (edge type algebra)
        """
        lines = []

        # 1. Operation Algebra
        ops = self.operation_algebra()
        lines.append("## The Operation Algebra")
        lines.append("")
        lines.append("The system has an operation set $\\Sigma$ with "
                      f"{len(ops)} operations, each declared in the kosha "
                      "with eval (primitive name), arity, and inverse:")
        lines.append("")
        lines.append("| Operation | $f$ | Arity | Word | $f^{-1}$ |")
        lines.append("|---|---|---|---|---|")
        for op in sorted(ops, key=lambda o: o["name"]):
            inv = op["inverse"] or (op["pratipaksha"][0] if op["pratipaksha"] else "—")
            word = op["word"] or "—"
            lines.append(f"| {op['name']} | `{op['eval']}` "
                         f"| {op['arity']} | {word} | {inv} |")
        lines.append("")

        # Invertibility detail
        invertible = [o for o in ops if o["pratipaksha_0"]]
        lines.append(f"**Invertible operations** ({len(invertible)}/{len(ops)}): "
                     "for binary $f(a, b) = c$, the inverse is declared per-argument:")
        lines.append("")
        lines.append("$$f^{-1}_0(c, b) = a \\quad\\text{and}\\quad f^{-1}_1(c, a) = b$$")
        lines.append("")
        for op in invertible:
            flip = " (flip)" if op["flip_1"] else ""
            lines.append(f"- `{op['name']}`: "
                         f"$p_0^{{-1}}$ = `{op['pratipaksha_0']}`, "
                         f"$p_1^{{-1}}$ = `{op['pratipaksha_1']}`{flip}")
        lines.append("")

        # 2. Mantra Signatures
        sigs = self.mantra_signatures()
        physics = [s for s in sigs if "physics-mantra" in s.get("varga", [])]
        lines.append("## Mantra Signatures")
        lines.append("")
        lines.append(f"The graph declares {len(sigs)} mantras as typed functions. "
                     f"{len(physics)} are physics mantras with complete "
                     "janya (input) → phala (output) signatures:")
        lines.append("")
        for s in sorted(physics, key=lambda x: x["name"]):
            j = ", ".join(s["janya"]) if s["janya"] else "∅"
            p = ", ".join(s["phala"]) if s["phala"] else "∅"
            k = ", ".join(s["kriya"]) if s["kriya"] else "direct"
            lines.append(f"$$\\text{{{s['name']}}}({j}) \\to {p} "
                         f"\\quad\\text{{via }}\\texttt{{{k}}}$$")
            lines.append("")

        # 3. Algebraic Hierarchy
        hierarchy = self.algebraic_hierarchy()
        lines.append("## Algebraic Hierarchy")
        lines.append("")
        lines.append("The kosha declares algebraic structures as **structural permissions**. "
                     "Each level adds guarantees that the pipeline reads to validate operations:")
        lines.append("")
        lines.append("$$\\text{field} \\supset \\text{ring} \\supset "
                     "\\text{group} \\supset \\text{monoid}$$")
        lines.append("")
        for s in hierarchy:
            sthita = s["edges"].get("sthita", [])
            kriya = s["edges"].get("kriya", [])
            siddha = s["edges"].get("siddha", [])
            drishthanta = s["edges"].get("drishthanta", [])
            yukta = s["edges"].get("yukta", [])
            parts = []
            if sthita:
                parts.append(f"rests on {', '.join(sthita)}")
            if kriya:
                parts.append(f"operates via {', '.join(kriya)}")
            if siddha:
                parts.append(f"proves {', '.join(siddha)}")
            if drishthanta:
                parts.append(f"witnessed by {', '.join(drishthanta)}")
            if yukta:
                parts.append(f"has {', '.join(yukta[:5])}" +
                             (f" +{len(yukta)-5} more" if len(yukta) > 5 else ""))
            lines.append(f"- **{s['name']}**: {'; '.join(parts)}")
        lines.append("")

        # Graded ring specifically
        lines.append("The **graded ring** is the input structure for paragraphs:")
        lines.append("")
        lines.append("$$R = \\bigoplus_{n \\geq 0} R_n$$")
        lines.append("")
        lines.append("where each $R_n$ is a sentence (grade), "
                     "the grade boundary is `viraam` (period/comma), "
                     "addition ($\\oplus$) is intra-sentence accumulation, "
                     "and multiplication ($\\otimes$) is cross-sentence entity selection.")
        lines.append("")

        # 4. Pipeline Composition
        comp = self.pipeline_composition()
        lines.append("## Pipeline as Function Composition")
        lines.append("")
        lines.append("The full pipeline is a composition of monotone endomorphisms "
                     "on the question graph $G$:")
        lines.append("")
        lines.append("$$\\text{answer} = (\\text{emit} \\circ \\text{pramana} "
                     "\\circ \\text{execute} \\circ \\text{match} "
                     "\\circ \\text{expand} \\circ \\text{refine} "
                     "\\circ \\text{build})(\\text{sentence})$$")
        lines.append("")

        # Show the actual pipeline stages
        groups = {}
        for c in comp:
            groups.setdefault(c["group"], []).append(c)
        for gname in ["pipeline", "avrti", "sankhya", "match",
                      "vishesa", "sandhi", "vibhakti", "anuvada"]:
            gs = groups.get(gname, [])
            if not gs:
                continue
            lines.append(f"**{gname}** ({len(gs)} tantras, "
                         f"{sum(c['lines'] for c in gs)} lines):")
            for c in sorted(gs, key=lambda x: -len(x["calls"])):
                takes = ", ".join(c["takes"]) if c["takes"] else "—"
                n_calls = len(c["calls"])
                if n_calls > 0:
                    lines.append(f"- $\\texttt{{{c['name']}}}({takes})$"
                                 f" — calls {n_calls} tantras")
            lines.append("")

        # 5. Visheshanam Ring
        dims = self.visheshanam_dimensions()
        lines.append("## Visheshanam Ring")
        lines.append("")
        lines.append(f"The edge type system is a {len(dims)}-element "
                     "non-commutative ring with 10 core dimensions "
                     "and extended grammatical dimensions:")
        lines.append("")
        lines.append("**Core** (the original 10): swarupa (IS), abheda (≡), "
                     "sthita (∈), yukta (+), siddha (⊢), kriya (×), "
                     "phala (→), janya (←), drishthanta (∃), pratipaksha (⁻¹)")
        lines.append("")
        extended = [d for d in dims if d not in [
            "visheshanam-swarupa", "visheshanam-abheda", "visheshanam-sthita",
            "visheshanam-yukta", "visheshanam-siddha", "visheshanam-kriya",
            "visheshanam-phala", "visheshanam-janya", "visheshanam-drishthanta",
            "visheshanam-pratipaksha", "visheshanam"
        ]]
        lines.append(f"**Extended** ({len(extended)} dimensions): "
                     f"{', '.join(extended)}")
        lines.append("")

        return "\n".join(lines)
