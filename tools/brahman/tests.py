"""
tests.py — static test discovery and metadata extraction.

Parses the v2 test files using Python's ast module (no imports, no server).
Returns structured metadata: name, layer, docstring, xfail gate, file, lineno.

Layer is derived from file name:
  test_evaluator.py  → evaluator
  test_graph.py      → graph
  test_pipeline.py   → pipeline
  test_answers.py    → answers
  test_xfail.py      → xfail

Gate is the xfail reason keyword (matches conftest._GATE_KEYWORDS):
  arithmetic, dvandva, inverse_math, sthita_viveka, motion_verb,
  compound_trigram, from_rest, total_compound, colour_classifier,
  article, relative_velocity, compute_compare, transitive, syllogism,
  proportional, ...
"""

import ast
import os
import re
from collections import OrderedDict

from .paths import ROOT

# ── paths ──────────────────────────────────────────────────────────────────────

V2_DIR = os.path.join(ROOT, "tools", "brahman", "v2")

# ── layer mapping ──────────────────────────────────────────────────────────────

FILE_TO_LAYER = {
    "test_evaluator.py": "evaluator",
    "test_graph.py": "graph",
    "test_pipeline.py": "pipeline",
    "test_answers.py": "answers",
    "test_xfail.py": "xfail",
}

# ── xfail gate extraction ──────────────────────────────────────────────────────

_GATE_KEYWORDS = {
    "dvandva": "dvandva",
    "inverse-math": "inverse_math",
    "invert-math": "inverse_math",
    "bound-vals": "inverse_math",
    "sthita-viveka": "sthita_viveka",
    "gravitational": "sthita_viveka",
    "coulomb": "sthita_viveka",
    "motion verb": "motion_verb",
    "moves at": "motion_verb",
    "moving at": "motion_verb",
    "trigram": "compound_trigram",
    "three-word": "compound_trigram",
    "from rest": "from_rest",
    "total kinetic": "total_compound",
    "total' still": "total_compound",
    "colour": "colour_classifier",
    "classifier": "colour_classifier",
    "article": "article",
    "'the'": "article",
    "relative-velocity": "relative_velocity",
    "compute-then-compare": "compute_compare",
    "compute then compare": "compute_compare",
    "transitiv": "transitive",
    "syllogism": "syllogism",
    "modus-ponens": "syllogism",
    "count addition": "arithmetic",
    "count subtraction": "arithmetic",
    "plain count": "arithmetic",
    "distance = speed": "arithmetic",
    "area =": "arithmetic",
    "proportional": "proportional",
}


def _gate_from_reason(reason: str) -> str:
    """Extract gate name from xfail reason string."""
    lower = reason.lower()
    for keyword, gate in _GATE_KEYWORDS.items():
        if keyword.lower() in lower:
            return gate
    return "other"


# ── AST parsing ────────────────────────────────────────────────────────────────


def _extract_xfail_reason(decorator: ast.expr) -> str | None:
    """Extract reason string from @pytest.mark.xfail(reason=...) decorator."""
    # handles both:
    #   @pytest.mark.xfail(strict=True, reason="...")
    #   @xfail(strict=True, reason="...")
    if not isinstance(decorator, ast.Call):
        return None
    for kw in decorator.keywords:
        if kw.arg == "reason":
            val = kw.value
            if isinstance(val, ast.Constant):
                return str(val.value)
            # concatenated strings: "foo" "bar" (JoinedStr or Constant+)
            if isinstance(val, ast.JoinedStr):
                return ""
    # also check positional args
    for arg in decorator.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    return None


def _is_xfail(decorator: ast.expr) -> tuple[bool, str]:
    """Return (is_xfail, reason) for a decorator node."""
    # @pytest.mark.xfail or @xfail
    if isinstance(decorator, ast.Attribute):
        # @pytest.mark.xfail  — no args
        if decorator.attr == "xfail":
            return True, ""
    if isinstance(decorator, ast.Call):
        func = decorator.func
        if isinstance(func, ast.Attribute) and func.attr == "xfail":
            return True, _extract_xfail_reason(decorator) or ""
        if isinstance(func, ast.Name) and func.id == "xfail":
            return True, _extract_xfail_reason(decorator) or ""
    return False, ""


def parse_file(path: str) -> list[dict]:
    """Parse one test file and return list of test metadata dicts."""
    fname = os.path.basename(path)
    layer = FILE_TO_LAYER.get(fname, fname.replace("test_", "").replace(".py", ""))

    try:
        source = open(path).read()
        tree = ast.parse(source, filename=path)
    except Exception:
        return []

    tests = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not node.name.startswith("test_"):
            continue

        # docstring
        doc = ast.get_docstring(node) or ""

        # xfail?
        is_xf = False
        xfail_reason = ""
        xfail_gate = ""
        for dec in node.decorator_list:
            found, reason = _is_xfail(dec)
            if found:
                is_xf = True
                xfail_reason = reason
                xfail_gate = _gate_from_reason(reason)
                break

        # extract inline assert patterns for search
        assert_texts = []
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                assert_texts.append(ast.unparse(child.test))

        tests.append(
            {
                "name": node.name,
                "layer": layer,
                "file": path,
                "lineno": node.lineno,
                "doc": doc,
                "xfail": is_xf,
                "xfail_reason": xfail_reason,
                "xfail_gate": xfail_gate if is_xf else "",
                "asserts": assert_texts,
                "nodeid": f"{os.path.relpath(path, ROOT)}/{node.name}",
            }
        )

    return tests


def find_test_files() -> list[str]:
    """Find all test files in v2/."""
    if not os.path.exists(V2_DIR):
        return []
    return sorted(
        os.path.join(V2_DIR, f)
        for f in os.listdir(V2_DIR)
        if f.startswith("test_") and f.endswith(".py")
    )


def load_all() -> list[dict]:
    """Load metadata for all v2 tests."""
    tests = []
    for path in find_test_files():
        tests.extend(parse_file(path))
    return tests


# ── query helpers ──────────────────────────────────────────────────────────────


def by_layer(tests: list[dict]) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for t in tests:
        result.setdefault(t["layer"], []).append(t)
    return result


def by_gate(tests: list[dict]) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for t in tests:
        if t["xfail"]:
            result.setdefault(t["xfail_gate"], []).append(t)
    return result


def filter_tests(
    tests: list[dict],
    layer: str | None = None,
    gate: str | None = None,
    pattern: str | None = None,
    xfail_only: bool = False,
    passing_only: bool = False,
) -> list[dict]:
    """Filter tests by layer, gate, name pattern, or xfail status."""
    result = tests
    if layer:
        result = [t for t in result if t["layer"] == layer]
    if gate:
        result = [t for t in result if t["xfail_gate"] == gate]
    if pattern:
        pat = re.compile(pattern, re.IGNORECASE)
        result = [t for t in result if pat.search(t["name"]) or pat.search(t["doc"])]
    if xfail_only:
        result = [t for t in result if t["xfail"]]
    if passing_only:
        result = [t for t in result if not t["xfail"]]
    return result


# ── summary ────────────────────────────────────────────────────────────────────


def summary(tests: list[dict]) -> dict:
    layers = by_layer(tests)
    gates = by_gate(tests)
    passing = [t for t in tests if not t["xfail"]]
    xfailing = [t for t in tests if t["xfail"]]
    return {
        "total": len(tests),
        "passing": len(passing),
        "xfail": len(xfailing),
        "layers": {k: len(v) for k, v in sorted(layers.items())},
        "gates": {k: len(v) for k, v in sorted(gates.items())},
    }
