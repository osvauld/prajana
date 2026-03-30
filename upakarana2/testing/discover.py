"""discover.py — Static test discovery using Python AST.

Parses test files without importing them. No server needed.
"""

import ast
import os
import re

from upakarana2.paths import ROOT, TESTS_DIR
from upakarana2.testing.gates import gate_from_reason

FILE_TO_LAYER = {
    "test_evaluator.py": "evaluator",
    "test_graph.py": "graph",
    "test_pipeline.py": "pipeline",
    "test_answers.py": "answers",
    "test_xfail.py": "xfail",
    "test_edges.py": "edges",
    "test_grammar.py": "grammar",
    "test_tantras.py": "tantras",
    "test_physics.py": "physics",
    "test_entity.py": "entity",
    "test_comparison.py": "comparison",
    "test_arithmetic.py": "arithmetic",
    "test_logic.py": "logic",
    "test_mixed.py": "mixed",
}


def _layer_from_path(path):
    fname = os.path.basename(path)
    if fname in FILE_TO_LAYER:
        return FILE_TO_LAYER[fname]
    rel = os.path.relpath(path, str(TESTS_DIR))
    parts = rel.replace(os.sep, "/").split("/")
    parts[-1] = parts[-1].replace("test_", "").replace(".py", "")
    return "/".join(parts)


def _extract_xfail_reason(decorator):
    if not isinstance(decorator, ast.Call):
        return None
    for kw in decorator.keywords:
        if kw.arg == "reason":
            val = kw.value
            if isinstance(val, ast.Constant):
                return str(val.value)
            if isinstance(val, ast.JoinedStr):
                return ""
    for arg in decorator.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    return None


def _is_xfail(decorator):
    if isinstance(decorator, ast.Attribute) and decorator.attr == "xfail":
        return True, ""
    if isinstance(decorator, ast.Call):
        func = decorator.func
        if isinstance(func, ast.Attribute) and func.attr == "xfail":
            return True, _extract_xfail_reason(decorator) or ""
        if isinstance(func, ast.Name) and func.id == "xfail":
            return True, _extract_xfail_reason(decorator) or ""
    return False, ""


def parse_file(path):
    """Parse test functions from a file using AST."""
    layer = _layer_from_path(path)
    try:
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source, filename=path)
    except Exception:
        return []

    tests = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
            continue

        doc = ast.get_docstring(node) or ""
        is_xf, xfail_reason, xfail_gate = False, "", ""
        for dec in node.decorator_list:
            found, reason = _is_xfail(dec)
            if found:
                is_xf = True
                xfail_reason = reason
                xfail_gate = gate_from_reason(reason)
                break

        assert_texts = [ast.unparse(child.test) for child in ast.walk(node)
                        if isinstance(child, ast.Assert)]

        tests.append({
            "name": node.name, "layer": layer, "file": path,
            "lineno": node.lineno, "doc": doc,
            "xfail": is_xf, "xfail_reason": xfail_reason,
            "xfail_gate": xfail_gate if is_xf else "",
            "asserts": assert_texts,
            "nodeid": f"{os.path.relpath(path, str(ROOT))}/{node.name}",
        })
    return tests


def find_test_files():
    if not os.path.exists(str(TESTS_DIR)):
        return []
    results = []
    for dirpath, _, filenames in os.walk(str(TESTS_DIR)):
        for f in filenames:
            if f.startswith("test_") and f.endswith(".py"):
                results.append(os.path.join(dirpath, f))
    return sorted(results)


def load_all():
    tests = []
    for path in find_test_files():
        tests.extend(parse_file(path))
    return tests


def by_layer(tests):
    result = {}
    for t in tests:
        result.setdefault(t["layer"], []).append(t)
    return result


def by_gate(tests):
    result = {}
    for t in tests:
        if t["xfail"]:
            result.setdefault(t["xfail_gate"], []).append(t)
    return result


def filter_tests(tests, layer=None, gate=None, pattern=None,
                 xfail_only=False, passing_only=False):
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


def summary(tests):
    layers = by_layer(tests)
    gates = by_gate(tests)
    passing = [t for t in tests if not t["xfail"]]
    xfailing = [t for t in tests if t["xfail"]]
    return {
        "total": len(tests), "passing": len(passing), "xfail": len(xfailing),
        "layers": {k: len(v) for k, v in sorted(layers.items())},
        "gates": {k: len(v) for k, v in sorted(gates.items())},
    }
