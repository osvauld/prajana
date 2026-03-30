"""test_evaluator.py — the yantra instrument: does it execute correctly?

14 capabilities, ~20 tests. Each test covers one structural capability
of the evaluator (reduce, map, filter, cond, fn, let, from/where, fixpoint,
arithmetic, comparison, strings, lists, split-numeric, to-number).

These are the foundation — if anything here fails, nothing above can be trusted.
Protects: yantra_eval.ml, yantra_ops.ml, yantra_eval_primitives.ml
"""

import json
import pytest


# ── reduce ─────────────────────────────────────────────────────────────────────


def test_reduce_sum(vy):
    """reduce folds a list with an accumulator."""
    assert vy.approx_eq(vy.eval("reduce [1, 2, 3] 0 (fn a x -> add a x)"), 6.0)


def test_reduce_cond_max(vy):
    """reduce + cond: select maximum from a list."""
    assert vy.approx_eq(
        vy.eval("reduce [3, 1, 4, 1, 5] 0 (fn a x -> cond (gt x a) x a)"), 5.0
    )


def test_reduce_empty(vy):
    """reduce over empty list returns initial value."""
    assert vy.eval('reduce [] "init" (fn a x -> a)') == "init"


# ── map / filter ───────────────────────────────────────────────────────────────


def test_map_transform(vy):
    """map applies fn to each element."""
    result = vy.eval("map [1, 2, 3] (fn x -> mul x 2)")
    assert len(result) == 3
    assert vy.approx_eq(result[0], 2.0) and vy.approx_eq(result[2], 6.0)


def test_filter(vy):
    """filter keeps elements matching predicate."""
    result = vy.eval("filter [1, 2, 3, 4, 5] (fn x -> gt x 3)")
    assert len(result) == 2
    assert vy.approx_eq(result[0], 4.0)


# ── cond ───────────────────────────────────────────────────────────────────────


def test_cond_else_branch_in_reduce(vy):
    """Regression: else-branch inside fn inside reduce was broken."""
    result = vy.eval("reduce [1, 2, 3] 0 (fn acc x -> cond (gt x 1) acc x)")
    assert vy.approx_eq(result, 1.0)


def test_cond_inside_map(vy):
    """cond fires correctly for each map element."""
    result = vy.eval("map [-1, 2, -3] (fn x -> cond (gt x 0) x 0)")
    assert vy.approx_eq(result[0], 0.0) and vy.approx_eq(result[1], 2.0)


# ── fn / let / from-where / fixpoint ──────────────────────────────────────────


def test_let_binding(vy):
    """let x = expr in body."""
    assert vy.approx_eq(vy.eval("let x = add 1 2 in x"), 3.0)


def test_from_where_collect(vy):
    """from ... where ... collect comprehension."""
    result = vy.eval("from [1, 2, 3, 4] where [x] and (gt x 2) collect x")
    assert len(result) == 2
    assert vy.approx_eq(result[0], 3.0)


def test_fixpoint_stable(vy):
    """fixpoint terminates on stable input."""
    g = json.dumps([["a", "b", "c"]])
    result = vy.eval(f"fixpoint {g} (fn g -> g)")
    assert result == [["a", "b", "c"]]


# ── arithmetic + comparison ────────────────────────────────────────────────────


def test_arithmetic(vy):
    """add, sub, mul, div, sqrt, power, abs all work."""
    assert vy.approx_eq(vy.eval("add 3 4"), 7.0)
    assert vy.approx_eq(vy.eval("sub 10 3"), 7.0)
    assert vy.approx_eq(vy.eval("mul 6 7"), 42.0)
    assert vy.approx_eq(vy.eval("div 10 2"), 5.0)
    assert vy.approx_eq(vy.eval("sqrt 9"), 3.0)
    assert vy.approx_eq(vy.eval("power 2 10"), 1024.0)
    assert vy.approx_eq(vy.eval("abs -5"), 5.0)
    assert vy.approx_eq(vy.eval("div 5 0"), 0.0)  # div by zero → 0


def test_comparison(vy):
    """eq, neq, gt, lt, and, or, not all return correct booleans."""
    assert vy.eval("eq 5 5") is True
    assert vy.eval("neq 5 6") is True
    assert vy.eval("gt 5 3") is True
    assert vy.eval("lt 3 5") is True
    assert vy.eval("and true true") is True
    assert vy.eval("and true false") is False
    assert vy.eval("or false true") is True
    assert vy.eval("not false") is True


# ── strings ────────────────────────────────────────────────────────────────────


def test_strings(vy):
    """String primitives: split, substr, starts-with, ends-with, length."""
    assert vy.eval('split "a-b-c" "-"') == ["a", "b", "c"]
    assert vy.eval('substr "kilogram" 0 4') == "kilo"
    assert vy.eval('starts-with "kilogram" "kilo"') is True
    assert vy.eval('ends-with "velocities" "ies"') is True
    assert vy.approx_eq(vy.eval('string-length "mass"'), 4.0)


# ── lists ──────────────────────────────────────────────────────────────────────


def test_lists(vy):
    """List primitives: append, flatten, unique, range, sum, length, nth."""
    assert vy.eval('append ["a"] ["b", "c"]') == ["a", "b", "c"]
    assert vy.approx_eq(vy.eval("sum [1, 2, 3, 4]"), 10.0)
    assert vy.approx_eq(vy.eval('length ["a", "b", "c"]'), 3.0)
    assert vy.eval('nth ["x", "y"] 0') == "x"
    assert vy.eval('nth ["a", "b"] 99') is None  # out of bounds
    result = vy.eval('unique ["a", "b", "a", "c", "b"]')
    assert len(result) == 3


# ── split-numeric / to-number ──────────────────────────────────────────────────


def test_split_numeric(vy):
    """Parse '5kg' → (5.0, 'kg')."""
    result = vy.eval('split-numeric "5kg"')
    assert vy.approx_eq(result[0], 5.0)
    assert result[1] == "kg"


def test_split_numeric_bare_number(vy):
    """Parse '100' → (100.0, '')."""
    result = vy.eval('split-numeric "100"')
    assert vy.approx_eq(result[0], 100.0)
    assert result[1] == ""


def test_to_number(vy):
    """String to float conversion."""
    assert vy.approx_eq(vy.eval('to-number "42"'), 42.0)
    assert vy.eval('to-number "hello"') is None
