"""test_interpreter.py — yantra evaluator primitives.

Tests the evaluator in isolation: no domain knowledge, no kosha, no tantras.
Every test sends a pure yantra expression to the server and checks the result.

Protects against regressions in: yantra_eval.ml, yantra_ops.ml

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_interpreter.py -v --socket /tmp/vy.sock
"""

import json
import pytest


# ── reduce ────────────────────────────────────────────────────────────────────


def test_reduce_numeric_sum(vy):
    result = vy.eval("reduce [1, 2, 3] 0 (fn a x -> add a x)")
    assert vy.approx_eq(result, 6.0), f"expected 6.0, got {result!r}"


def test_reduce_empty_list_returns_init(vy):
    result = vy.eval('reduce [] "init" (fn a x -> a)')
    assert result == "init", f"expected 'init', got {result!r}"


def test_reduce_string_accumulator(vy):
    result = vy.eval('reduce ["a", "b", "c"] "" (fn acc x -> x)')
    # last element wins with this fn: returns "c"
    assert result == "c", f"expected 'c', got {result!r}"


def test_reduce_cond_select(vy):
    # select largest via cond inside reduce
    result = vy.eval("reduce [3, 1, 4, 1, 5] 0 (fn a x -> cond (gt x a) x a)")
    assert vy.approx_eq(result, 5.0), f"expected 5.0, got {result!r}"


# ── map ───────────────────────────────────────────────────────────────────────


def test_map_identity(vy):
    result = vy.eval('map ["a", "b", "c"] (fn x -> x)')
    assert result == ["a", "b", "c"], f"got {result!r}"


def test_map_empty_list(vy):
    result = vy.eval("map [] (fn x -> x)")
    assert result == [], f"expected [], got {result!r}"


def test_map_numeric_transform(vy):
    result = vy.eval("map [1, 2, 3] (fn x -> mul x 2)")
    assert len(result) == 3
    assert vy.approx_eq(result[0], 2.0)
    assert vy.approx_eq(result[1], 4.0)
    assert vy.approx_eq(result[2], 6.0)


# ── filter ────────────────────────────────────────────────────────────────────


def test_filter_keeps_matching(vy):
    result = vy.eval("filter [1, 2, 3, 4, 5] (fn x -> gt x 3)")
    assert len(result) == 2, f"expected 2 items, got {result!r}"
    assert vy.approx_eq(result[0], 4.0)
    assert vy.approx_eq(result[1], 5.0)


def test_filter_empty_result(vy):
    result = vy.eval("filter [1, 2, 3] (fn x -> gt x 100)")
    assert result == [], f"expected [], got {result!r}"


def test_filter_all_match(vy):
    result = vy.eval("filter [1, 2, 3] (fn x -> gt x 0)")
    assert len(result) == 3, f"expected 3, got {result!r}"


# ── nth ───────────────────────────────────────────────────────────────────────


def test_nth_in_bounds(vy):
    result = vy.eval('nth ["a", "b", "c"] 1')
    assert result == "b", f"expected 'b', got {result!r}"


def test_nth_first_element(vy):
    result = vy.eval('nth ["x", "y"] 0')
    assert result == "x", f"expected 'x', got {result!r}"


def test_nth_out_of_bounds(vy):
    result = vy.eval('nth ["a", "b"] 99')
    assert result is None, f"expected None for out-of-bounds, got {result!r}"


def test_nth_empty_list(vy):
    result = vy.eval("nth [] 0")
    assert result is None, f"expected None for empty list, got {result!r}"


# ── cond ──────────────────────────────────────────────────────────────────────


def test_cond_inside_reduce_ascending_list(vy):
    # cond with both branches firing — max of arbitrary list
    result = vy.eval("reduce [3, 1, 4, 1, 5] 0 (fn a x -> cond (gt x a) x a)")
    assert vy.approx_eq(result, 5.0), f"expected 5.0, got {result!r}"


def test_cond_inside_map_numeric(vy):
    # cond inside map — else-branch fires for non-positive inputs
    result = vy.eval("map [-1, 2, -3] (fn x -> cond (gt x 0) x 0)")
    assert vy.approx_eq(result[0], 0.0), f"expected 0.0 for -1, got {result[0]!r}"
    assert vy.approx_eq(result[1], 2.0), f"expected 2.0 for 2, got {result[1]!r}"
    assert vy.approx_eq(result[2], 0.0), f"expected 0.0 for -3, got {result[2]!r}"


def test_cond_else_branch_in_reduce(vy):
    # regression test for the parse_cond bug: else-branch inside fn inside reduce
    # was previously consuming ')' as the else value, returning ")" instead of acc.
    # reduce [1 2 3] 0 (fn acc x -> cond (gt x 1) acc x):
    #   x=1: gt 1 1 false → else → x=1    acc=1
    #   x=2: gt 2 1 true  → then → acc=1  acc=1
    #   x=3: gt 3 1 true  → then → acc=1  acc=1
    result = vy.eval("reduce [1, 2, 3] 0 (fn acc x -> cond (gt x 1) acc x)")
    assert vy.approx_eq(result, 1.0), f"expected 1.0, got {result!r}"


def test_cond_otherwise_branch(vy):
    # cond with explicit otherwise clause
    result = vy.eval("reduce [1, 2, 3] 0 (fn a x -> cond (gt x 2) x otherwise a)")
    assert vy.approx_eq(result, 3.0), f"expected 3.0, got {result!r}"


# ── fn / closures ─────────────────────────────────────────────────────────────
# Note: fn application only works inside primitive combinators (reduce/map/filter)
# or via `let x = expr in x`. Top-level anonymous fn application is not supported
# by eval-json (the top-level token must be a registered primitive or tantra name).


def test_fn_in_reduce(vy):
    # fn defined in reduce — closure used correctly
    result = vy.eval("reduce [1, 2, 3] 0 (fn a x -> add a x)")
    assert vy.approx_eq(result, 6.0), f"expected 6.0, got {result!r}"


def test_fn_in_map(vy):
    # map with fn — the fn applies to each element
    result = vy.eval("map [2, 3, 4] (fn x -> mul x x)")
    assert len(result) == 3
    assert vy.approx_eq(result[0], 4.0)
    assert vy.approx_eq(result[1], 9.0)
    assert vy.approx_eq(result[2], 16.0)


def test_let_in_binding(vy):
    # let x = expr in body — single-binding let expression
    result = vy.eval("let x = add 1 2 in x")
    assert vy.approx_eq(result, 3.0), f"expected 3.0, got {result!r}"


# ── from … where … collect ────────────────────────────────────────────────────


def test_from_where_collect_all(vy):
    result = vy.eval('from ["a", "b", "c"] where [x] collect x')
    assert result == ["a", "b", "c"], f"got {result!r}"


def test_from_where_collect_empty_input(vy):
    result = vy.eval("from [] where [x] collect x")
    assert result == [], f"expected [], got {result!r}"


def test_from_where_collect_with_guard(vy):
    # collect numbers greater than 2
    result = vy.eval("from [1, 2, 3, 4] where [x] and (gt x 2) collect x")
    assert len(result) == 2, f"expected 2 items, got {result!r}"
    assert vy.approx_eq(result[0], 3.0)
    assert vy.approx_eq(result[1], 4.0)


# ── fixpoint ──────────────────────────────────────────────────────────────────


def test_fixpoint_stable_fn_terminates(vy):
    # identity function: graph never changes → terminates in 1 pass
    g = json.dumps([["a", "b", "c"]])
    result = vy.eval(f"fixpoint {g} (fn g -> g)")
    assert result == [["a", "b", "c"]], f"got {result!r}"


def test_fixpoint_returns_non_empty_on_cap(vy):
    # A function that always appends — never converges.
    # fixpoint should cap at 20 iterations and return whatever it has.
    # We verify it terminates (no hang) and returns a list.
    g = json.dumps([])
    # append a triple each pass — will never stabilise
    result = vy.eval(f'fixpoint {g} (fn g -> append g [["x", "y", "z"]])')
    assert isinstance(result, list), f"expected list, got {result!r}"
    assert len(result) > 0, "expected non-empty result after cap"


# ── split-numeric ─────────────────────────────────────────────────────────────


def test_split_numeric_value_and_unit(vy):
    result = vy.eval('split-numeric "5kg"')
    assert vy.approx_eq(result[0], 5.0), f"value: {result[0]!r}"
    assert result[1] == "kg", f"unit: {result[1]!r}"


def test_split_numeric_bare_number(vy):
    result = vy.eval('split-numeric "100"')
    assert vy.approx_eq(result[0], 100.0), f"value: {result[0]!r}"
    assert result[1] == "", f"unit should be empty, got {result[1]!r}"


def test_split_numeric_negative(vy):
    result = vy.eval('split-numeric "-5m"')
    assert vy.approx_eq(result[0], -5.0), f"value: {result[0]!r}"
    assert result[1] == "m", f"unit: {result[1]!r}"


def test_split_numeric_decimal(vy):
    result = vy.eval('split-numeric ".5m"')
    assert vy.approx_eq(result[0], 0.5), f"value: {result[0]!r}"
    assert result[1] == "m", f"unit: {result[1]!r}"


def test_split_numeric_unit_only(vy):
    # no leading number → value is empty string (not null), unit is full string
    result = vy.eval('split-numeric "m/s"')
    assert result[0] == "" or result[0] is None, (
        f"expected empty/null value for unit-only, got {result[0]!r}"
    )
    assert "m" in str(result[1]), f"unit: {result[1]!r}"


def test_split_numeric_trailing_comma(vy):
    # "10," is a comma-suffixed number (appears in natural text)
    result = vy.eval('split-numeric "10,"')
    assert vy.approx_eq(result[0], 10.0), f"value: {result[0]!r}"


# ── string primitives ─────────────────────────────────────────────────────────


def test_ends_with_true(vy):
    result = vy.eval('ends-with "velocities" "ies"')
    assert result is True, f"expected True, got {result!r}"


def test_ends_with_false(vy):
    result = vy.eval('ends-with "velocity" "ies"')
    assert result is False, f"expected False, got {result!r}"


def test_starts_with_true(vy):
    result = vy.eval('starts-with "kilogram" "kilo"')
    assert result is True, f"expected True, got {result!r}"


def test_starts_with_false(vy):
    result = vy.eval('starts-with "gram" "kilo"')
    assert result is False, f"expected False, got {result!r}"


def test_substr(vy):
    result = vy.eval('substr "kilogram" 0 4')
    assert result == "kilo", f"expected 'kilo', got {result!r}"


def test_string_length(vy):
    result = vy.eval('string-length "mass"')
    assert vy.approx_eq(result, 4.0), f"expected 4, got {result!r}"


def test_split_on_delimiter(vy):
    result = vy.eval('split "a-b-c" "-"')
    assert result == ["a", "b", "c"], f"got {result!r}"


# ── to-number ─────────────────────────────────────────────────────────────────


def test_to_number_numeric_string(vy):
    result = vy.eval('to-number "42"')
    assert vy.approx_eq(result, 42.0), f"expected 42.0, got {result!r}"


def test_to_number_non_numeric_returns_null(vy):
    result = vy.eval('to-number "hello"')
    assert result is None, f"expected None for non-numeric, got {result!r}"


def test_to_number_float_string(vy):
    result = vy.eval('to-number "3.14"')
    assert vy.approx_eq(result, 3.14), f"expected 3.14, got {result!r}"


# ── list operations ───────────────────────────────────────────────────────────


def test_append(vy):
    result = vy.eval('append ["a"] ["b", "c"]')
    assert result == ["a", "b", "c"], f"got {result!r}"


def test_append_to_empty(vy):
    result = vy.eval('append [] ["x"]')
    assert result == ["x"], f"got {result!r}"


def test_flatten_nested(vy):
    result = vy.eval("flatten [[1, 2], [3, 4]]")
    assert len(result) == 4, f"expected 4 items, got {result!r}"
    assert vy.approx_eq(result[0], 1.0)
    assert vy.approx_eq(result[3], 4.0)


def test_unique_deduplicates(vy):
    result = vy.eval('unique ["a", "b", "a", "c", "b"]')
    assert len(result) == 3, f"expected 3 unique items, got {result!r}"
    assert "a" in result and "b" in result and "c" in result


def test_range(vy):
    # range takes a single count argument: range N → [0, 1, ..., N-1]
    result = vy.eval("range 4")
    assert len(result) == 4, f"expected 4 items, got {result!r}"
    assert all(vy.approx_eq(result[i], i) for i in range(4)), f"got {result!r}"


def test_sum_list(vy):
    result = vy.eval("sum [1, 2, 3, 4]")
    assert vy.approx_eq(result, 10.0), f"expected 10.0, got {result!r}"


def test_length(vy):
    result = vy.eval('length ["a", "b", "c"]')
    assert vy.approx_eq(result, 3.0), f"expected 3, got {result!r}"


def test_length_empty(vy):
    result = vy.eval("length []")
    assert vy.approx_eq(result, 0.0), f"expected 0, got {result!r}"


# ── comparison operators ──────────────────────────────────────────────────────


def test_eq_true(vy):
    assert vy.eval("eq 5 5") is True


def test_eq_false(vy):
    assert vy.eval("eq 5 6") is False


def test_neq_true(vy):
    assert vy.eval("neq 5 6") is True


def test_neq_false(vy):
    assert vy.eval("neq 5 5") is False


def test_lt_true(vy):
    assert vy.eval("lt 3 5") is True


def test_lt_false(vy):
    assert vy.eval("lt 5 3") is False


def test_gt_true(vy):
    assert vy.eval("gt 5 3") is True


def test_gt_false(vy):
    assert vy.eval("gt 3 5") is False


def test_and_both_true(vy):
    assert vy.eval("and true true") is True


def test_and_one_false(vy):
    assert vy.eval("and true false") is False


def test_or_one_true(vy):
    assert vy.eval("or false true") is True


def test_or_both_false(vy):
    assert vy.eval("or false false") is False


def test_not_true(vy):
    assert vy.eval("not false") is True


def test_not_false(vy):
    assert vy.eval("not true") is False


# ── arithmetic ────────────────────────────────────────────────────────────────


def test_add(vy):
    assert vy.approx_eq(vy.eval("add 3 4"), 7.0)


def test_sub(vy):
    assert vy.approx_eq(vy.eval("sub 10 3"), 7.0)


def test_mul(vy):
    assert vy.approx_eq(vy.eval("mul 6 7"), 42.0)


def test_div(vy):
    assert vy.approx_eq(vy.eval("div 10 2"), 5.0)


def test_div_by_zero_returns_zero(vy):
    result = vy.eval("div 5 0")
    assert vy.approx_eq(result, 0.0), f"expected 0.0, got {result!r}"


def test_abs_negative(vy):
    assert vy.approx_eq(vy.eval("abs -5"), 5.0)


def test_abs_positive(vy):
    assert vy.approx_eq(vy.eval("abs 5"), 5.0)


def test_sqrt(vy):
    assert vy.approx_eq(vy.eval("sqrt 9"), 3.0)


def test_pow(vy):
    # the primitive is named 'power', not 'pow'
    assert vy.approx_eq(vy.eval("power 2 10"), 1024.0)
