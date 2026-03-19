"""tests.py — static test discovery and metadata extraction.

Parses v2 test files using Python's ast module (no imports, no server).
Returns structured metadata: name, layer, docstring, xfail gate, file, lineno.
"""

import ast
import os
import re
from collections import OrderedDict

from .paths import ROOT, V2_DIR
from .gates import gate_from_reason

FILE_TO_LAYER = {
    "test_evaluator.py": "evaluator",
    "test_graph.py": "graph",
    "test_pipeline.py": "pipeline",
    "test_answers.py": "answers",
    "test_xfail.py": "xfail",
}


def _extract_xfail_reason(decorator: ast.expr) -> str | None:
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


def _is_xfail(decorator: ast.expr) -> tuple[bool, str]:
    if isinstance(decorator, ast.Attribute):
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
    fname = os.path.basename(path)
    layer = FILE_TO_LAYER.get(fname, fname.replace("test_", "").replace(".py", ""))
    try:
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source, filename=path)
    except Exception:
        return []

    tests = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not node.name.startswith("test_"):
            continue

        doc = ast.get_docstring(node) or ""
        is_xf = False
        xfail_reason = ""
        xfail_gate = ""
        for dec in node.decorator_list:
            found, reason = _is_xfail(dec)
            if found:
                is_xf = True
                xfail_reason = reason
                xfail_gate = gate_from_reason(reason)
                break

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
    if not os.path.exists(V2_DIR):
        return []
    return sorted(
        os.path.join(V2_DIR, f)
        for f in os.listdir(V2_DIR)
        if f.startswith("test_") and f.endswith(".py")
    )


def load_all() -> list[dict]:
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


def filter_tests(
    tests, layer=None, gate=None, pattern=None, xfail_only=False, passing_only=False
):
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
        "total": len(tests),
        "passing": len(passing),
        "xfail": len(xfailing),
        "layers": {k: len(v) for k, v in sorted(layers.items())},
        "gates": {k: len(v) for k, v in sorted(gates.items())},
    }
