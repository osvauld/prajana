"""test_series.py — sequences, series, polynomials, and repeating patterns.

Tests progress from simple repeating cycles through standard
mathematical sequences to polynomial equations. Each test uses
natural language questions — the kind found in school textbooks.

Structure:
  cyclic      — repeating patterns, traffic lights, mod-based lookup
  arithmetic  — constant difference: a + n*d
  geometric   — constant ratio: a * r^n
  triangular  — handshakes, stacking: n*(n+1)/2
  powers      — doubling, binary, folding: 2^n
  fibonacci   — recursive: f(n) = f(n-1) + f(n-2)
  summation   — sum of first n terms
  linear      — ax + b = 0, word problems
  quadratic   — ax² + bx + c = 0, discriminant, projectile, area
  polynomial  — evaluation, higher degree
"""

import pytest

xfail = pytest.mark.xfail


# ══════════════════════════════════════════════════════════════════════════════
# CYCLIC / REPEATING PATTERNS
# ══════════════════════════════════════════════════════════════════════════════
# Pattern: (position - 1) mod period → index into label list.
# Graph: repeating-pattern concept with period + labels.


def test_repeating_color_pattern(vy):
    """Beads are strung in a repeating pattern: red, blue, green, yellow.
    What color is the 23rd bead? → (23−1) mod 4 = 2 → green (0-indexed)"""
    r = vy.answer(
        "Beads are strung in a repeating pattern: red, blue, green, yellow. "
        "What color is the 23rd bead?"
    )
    r_lower = r.lower()
    assert "no match" not in r_lower and r_lower.split("find")[-1].count("green") > 0


@xfail(strict=True, reason="series_cyclic: traffic light phase from elapsed time")
def test_traffic_light_phase(vy):
    """A traffic light cycles every 90 seconds: red for 40 seconds,
    yellow for 10 seconds, green for 40 seconds. What color is the
    light at 250 seconds? → 250 mod 90 = 70. 70 > 50 → green"""
    r = vy.answer(
        "A traffic light cycles every 90 seconds. It is red for 40 seconds, "
        "yellow for 10 seconds, and green for 40 seconds. "
        "What color is the light at 250 seconds?"
    )
    r_lower = r.lower()
    assert "no match" not in r_lower and r_lower.split("find")[-1].count("green") > 0


def test_repeating_number_pattern(vy):
    """A number pattern repeats: 3, 7, 1, 5. What is the 18th number
    in the pattern? → (18−1) mod 4 = 1 → 7"""
    r = vy.answer(
        "A number pattern repeats: 3, 7, 1, 5. "
        "What is the 18th number in the pattern?"
    )
    # must compute 7, not just echo — check "find" section
    r_find = r.lower().split("find")[-1] if "find" in r.lower() else r.lower()
    assert "7" in r_find and "no match" not in r.lower()


# ══════════════════════════════════════════════════════════════════════════════
# ARITHMETIC SERIES — constant difference
# ══════════════════════════════════════════════════════════════════════════════
# nth term: a + (n-1)*d
# sum of n terms: n*(2a + (n-1)*d) / 2


def test_arithmetic_nth_salary(vy):
    """A worker starts with a salary of 30000. The salary increases
    by 2000 each year. What is the salary after 5 years?
    → 30000 + (5−1)*2000 = 30000 + 8000 = 38000"""
    r = vy.answer(
        "A worker starts with a salary of 30000. The salary increases "
        "by 2000 each year. What is the salary after 5 years?"
    )
    assert "38000" in r


def test_arithmetic_nth_staircase(vy):
    """Each step of a staircase is 20 cm high. What is the height
    after climbing 12 steps? → 12 * 20 = 240 cm"""
    r = vy.answer(
        "Each step of a staircase is 20 cm high. "
        "What is the height after climbing 12 steps?"
    )
    assert "240" in r


@xfail(strict=True, reason="series_arithmetic: nth term — taxi fare")
def test_arithmetic_nth_taxi(vy):
    """A taxi charges a base fare of 3 dollars plus 2 dollars per
    kilometer. What is the cost for an 8 kilometer ride?
    → 3 + 8*2 = 19"""
    r = vy.answer(
        "A taxi charges a base fare of 3 dollars plus 2 dollars per kilometer. "
        "What is the cost for an 8 kilometer ride?"
    )
    assert "19" in r


def test_arithmetic_sum(vy):
    """A student saves 10 rupees in the first week, 15 in the second,
    20 in the third, and so on. How much has the student saved after
    8 weeks? → n*(2a+(n-1)*d)/2 = 8*(20+35)/2 = 8*55/2 = 220"""
    r = vy.answer(
        "A student saves 10 rupees in the first week, 15 in the second, "
        "20 in the third, increasing by 5 each week. "
        "How much has the student saved after 8 weeks?"
    )
    assert "220" in r


def test_arithmetic_find_difference(vy):
    """The 3rd term of an arithmetic sequence is 11 and the 7th term
    is 23. What is the common difference? → (23−11)/(7−3) = 12/4 = 3"""
    r = vy.answer(
        "The 3rd term of an arithmetic sequence is 11. "
        "The 7th term is 23. What is the common difference?"
    )
    # must compute 3, not just echo — check "find" section
    r_find = r.lower().split("find")[-1] if "find" in r.lower() else r.lower()
    assert "3" in r_find and "no match" not in r.lower()


# ══════════════════════════════════════════════════════════════════════════════
# GEOMETRIC SERIES — constant ratio
# ══════════════════════════════════════════════════════════════════════════════
# nth term: a * r^(n-1)
# sum of n terms: a * (r^n - 1) / (r - 1)


def test_geometric_nth_bacteria(vy):
    """A colony of 100 bacteria doubles every hour. How many bacteria
    are there after 8 hours? → 100 * 2^8 = 100 * 256 = 25600"""
    r = vy.answer(
        "A colony of 100 bacteria doubles every hour. "
        "How many bacteria are there after 8 hours?"
    )
    assert "25600" in r


def test_geometric_compound_interest(vy):
    """1000 dollars is deposited at 10 percent interest per year.
    What is the amount after 3 years?
    → 1000 * 1.1^3 = 1000 * 1.331 = 1331"""
    r = vy.answer(
        "1000 dollars is deposited at 10 percent interest per year. "
        "What is the amount after 3 years?"
    )
    assert "1331" in r


def test_geometric_depreciation(vy):
    """A car is worth 50000 dollars. It loses 20 percent of its
    value each year. What is its value after 3 years?
    → 50000 * 0.8^3 = 50000 * 0.512 = 25600"""
    r = vy.answer(
        "A car is worth 50000 dollars. It loses 20 percent of its value "
        "each year. What is its value after 3 years?"
    )
    assert "25600" in r


@xfail(strict=True, reason="series_geometric: paper folding — powers of 2")
def test_geometric_paper_folding(vy):
    """A piece of paper is folded in half 10 times. How many layers
    does it have? → 2^10 = 1024"""
    r = vy.answer(
        "A piece of paper is folded in half 10 times. "
        "How many layers does it have?"
    )
    assert "1024" in r


# ══════════════════════════════════════════════════════════════════════════════
# TRIANGULAR NUMBERS — n*(n+1)/2
# ══════════════════════════════════════════════════════════════════════════════


@xfail(strict=True, reason="series_triangular: handshakes")
def test_triangular_handshakes(vy):
    """There are 10 people in a room. Each person shakes hands with
    every other person exactly once. How many handshakes occur?
    → 10*9/2 = 45"""
    r = vy.answer(
        "There are 10 people in a room. Each person shakes hands with "
        "every other person exactly once. How many handshakes occur?"
    )
    assert "45" in r


@xfail(strict=True, reason="series_triangular: bowling pins")
def test_triangular_bowling_pins(vy):
    """Bowling pins are arranged in a triangle: 1 in the first row,
    2 in the second, 3 in the third, and so on. How many pins are
    in a triangle with 6 rows? → 6*7/2 = 21"""
    r = vy.answer(
        "Bowling pins are arranged in a triangle. The first row has 1 pin, "
        "the second has 2, the third has 3, and so on. "
        "How many pins are in a triangle with 6 rows?"
    )
    assert "21" in r


@xfail(strict=True, reason="series_triangular: diagonal count in polygon")
def test_triangular_diagonals(vy):
    """How many diagonals does a hexagon have?
    → n*(n-3)/2 = 6*3/2 = 9"""
    r = vy.answer("How many diagonals does a hexagon have?")
    assert "9" in r


# ══════════════════════════════════════════════════════════════════════════════
# POWERS OF 2 — doubling, binary
# ══════════════════════════════════════════════════════════════════════════════


@xfail(strict=True, reason="series_powers: binary — 8-bit combinations")
def test_powers_binary_combinations(vy):
    """How many different numbers can be represented with 8 binary
    digits? → 2^8 = 256"""
    r = vy.answer(
        "How many different numbers can be represented with 8 binary digits?"
    )
    assert "256" in r


@xfail(strict=True, reason="series_powers: chessboard grain doubling")
def test_powers_chessboard_grain(vy):
    """A king places 1 grain of rice on the first square of a
    chessboard, 2 on the second, 4 on the third, doubling each
    time. How many grains are on the 10th square? → 2^9 = 512"""
    r = vy.answer(
        "A king places 1 grain of rice on the first square of a chessboard, "
        "2 on the second, 4 on the third, doubling each time. "
        "How many grains are on the 10th square?"
    )
    assert "512" in r


@xfail(strict=True, reason="series_powers: total grains on chessboard — sum of geometric")
def test_powers_chessboard_total(vy):
    """A king places 1 grain of rice on the first square of a
    chessboard, doubling each time. How many total grains are on
    the first 10 squares? → 2^10 − 1 = 1023"""
    r = vy.answer(
        "A king places 1 grain of rice on the first square of a chessboard, "
        "doubling each time. How many total grains are on the first 10 squares?"
    )
    assert "1023" in r


# ══════════════════════════════════════════════════════════════════════════════
# FIBONACCI — f(n) = f(n-1) + f(n-2)
# ══════════════════════════════════════════════════════════════════════════════


def test_fibonacci_nth(vy):
    """The Fibonacci sequence starts 1, 1, 2, 3, 5, 8. Each number
    is the sum of the two before it. What is the 10th Fibonacci
    number? → 1,1,2,3,5,8,13,21,34,55 → 55"""
    r = vy.answer(
        "The Fibonacci sequence starts 1, 1, 2, 3, 5, 8. Each number is "
        "the sum of the two before it. What is the 10th Fibonacci number?"
    )
    assert "55" in r


@xfail(strict=True, reason="series_fibonacci: rabbit breeding")
def test_fibonacci_rabbits(vy):
    """A pair of rabbits produces a new pair every month. Each new pair
    also produces a pair starting from their second month. Starting with
    1 pair, how many pairs are there after 7 months?
    → 1,1,2,3,5,8,13 → 13"""
    r = vy.answer(
        "A pair of rabbits produces a new pair every month. Each new pair "
        "also produces a pair starting from their second month. Starting "
        "with 1 pair, how many pairs are there after 7 months?"
    )
    assert "13" in r


# ══════════════════════════════════════════════════════════════════════════════
# SUMMATION — sum of first n natural numbers, squares, cubes
# ══════════════════════════════════════════════════════════════════════════════


@xfail(strict=True, reason="series_summation: sum of first n natural numbers")
def test_sum_first_n(vy):
    """What is the sum of the first 100 natural numbers?
    → 100*101/2 = 5050 (Gauss formula)"""
    r = vy.answer("What is the sum of the first 100 natural numbers?")
    assert "5050" in r


@xfail(strict=True, reason="series_summation: sum of first n odd numbers")
def test_sum_first_n_odd(vy):
    """What is the sum of the first 7 odd numbers?
    → 1+3+5+7+9+11+13 = 49 = 7²"""
    r = vy.answer("What is the sum of the first 7 odd numbers?")
    assert "49" in r


@xfail(strict=True, reason="series_summation: sum of squares")
def test_sum_of_squares(vy):
    """What is the sum of the squares of the first 5 natural numbers?
    → 1+4+9+16+25 = 55 → n*(n+1)*(2n+1)/6 = 5*6*11/6 = 55"""
    r = vy.answer(
        "What is the sum of the squares of the first 5 natural numbers?"
    )
    assert "55" in r


# ══════════════════════════════════════════════════════════════════════════════
# EQUATIONS — samikarana (math notation)
# ══════════════════════════════════════════════════════════════════════════════
# Direct math notation: "solve 3x + 7 = 22" — parsed by samikarana-bandha.
# Variable detected structurally (any unresolved letter), degree by max power.


def test_samikarana_linear_basic(vy):
    """solve 3x + 7 = 22 → slope=3, intercept=7-22=-15, root=neg(-15/3)=5"""
    r = vy.answer("solve 3x + 7 = 22")
    assert "5" in r


def test_samikarana_linear_subtraction(vy):
    """solve 2x - 8 = 0 → slope=2, intercept=-8, root=neg(-8/2)=4"""
    r = vy.answer("solve 2x - 8 = 0")
    assert "4" in r


def test_samikarana_linear_rhs(vy):
    """solve 10 = 2x → x on RHS, root=10/2=5"""
    r = vy.answer("solve 10 = 2x")
    assert "5" in r


def test_samikarana_quadratic_two_roots(vy):
    """solve x^2 - 5x + 6 = 0 → disc=1, roots=3 and 2"""
    r = vy.answer("solve x^2 - 5x + 6 = 0")
    assert "2" in r and "3" in r


def test_samikarana_quadratic_repeated(vy):
    """solve x^2 - 6x + 9 = 0 → disc=0, root=3 (repeated)"""
    r = vy.answer("solve x^2 - 6x + 9 = 0")
    assert "3" in r


def test_samikarana_quadratic_no_real(vy):
    """solve x^2 + 2x + 5 = 0 → disc=4-20=-16 < 0 → no real solution"""
    r = vy.answer("solve x^2 + 2x + 5 = 0")
    r_lower = r.lower()
    assert "no real" in r_lower or "no solution" in r_lower


# ══════════════════════════════════════════════════════════════════════════════
# LINEAR EQUATIONS (word problems) — rekha (degree 1)
# ══════════════════════════════════════════════════════════════════════════════
# ax + b = c → x = (c - b) / a
# The simplest equation: one unknown, one solution, always solvable.


@xfail(strict=True, reason="series_linear: solve for x — direct")
def test_linear_solve_direct(vy):
    """If 3x + 7 = 22, what is x? → x = (22−7)/3 = 5"""
    r = vy.answer("if 3 times a number plus 7 equals 22. what is the number")
    assert "5" in r


@xfail(strict=True, reason="series_linear: word problem — doubled and increased")
def test_linear_word_problem(vy):
    """A number is doubled and then increased by 5. The result is 17.
    What is the number? → 2x + 5 = 17, x = 6"""
    r = vy.answer(
        "A number is doubled and then increased by 5. The result is 17. "
        "What is the number?"
    )
    assert "6" in r


@xfail(strict=True, reason="series_linear: two unknowns — sum and difference")
def test_linear_two_unknowns(vy):
    """The sum of two numbers is 20. Their difference is 6.
    What are the two numbers? → (20+6)/2=13 and (20−6)/2=7"""
    r = vy.answer(
        "The sum of two numbers is 20. Their difference is 6. "
        "What are the two numbers?"
    )
    assert "13" in r and "7" in r


@xfail(strict=True, reason="series_linear: age problem")
def test_linear_age_problem(vy):
    """A father is 3 times as old as his son. The sum of their ages
    is 48. How old is the son? → 3x + x = 48, x = 12"""
    r = vy.answer(
        "A father is 3 times as old as his son. The sum of their ages "
        "is 48. How old is the son?"
    )
    assert "12" in r


# ══════════════════════════════════════════════════════════════════════════════
# QUADRATIC EQUATIONS — varga-bahupada (degree 2)
# ══════════════════════════════════════════════════════════════════════════════
# ax² + bx + c = 0 → discriminant = b² - 4ac
# roots = (-b ± √discriminant) / 2a
# The first equation where STRUCTURE matters: discriminant determines
# whether solutions exist, are unique, or are complex.


@xfail(strict=True, reason="series_quadratic: factoring — two positive roots")
def test_quadratic_factor_positive(vy):
    """A number squared minus 5 times the number plus 6 equals 0.
    What are the possible values? → x²−5x+6=0 → (x−2)(x−3)=0 → x=2 or x=3"""
    r = vy.answer(
        "A number squared minus 5 times the number plus 6 equals 0. "
        "What are the possible values of the number?"
    )
    assert "2" in r and "3" in r


@xfail(strict=True, reason="series_quadratic: discriminant — no real roots")
def test_quadratic_no_real_roots(vy):
    """Does the equation x² + 2x + 5 = 0 have real solutions?
    → discriminant = 4 − 20 = −16 < 0 → no real solutions"""
    r = vy.answer(
        "A number squared plus 2 times the number plus 5 equals 0. "
        "Does this have a real solution?"
    )
    r_lower = r.lower()
    # must compute discriminant, not just echo "no match"
    assert "no match" not in r_lower and ("no" in r_lower or "not" in r_lower or "negative" in r_lower)


@xfail(strict=True, reason="series_quadratic: projectile — time to land")
def test_quadratic_projectile(vy):
    """A ball is thrown upward at 20 meters per second. Its height is
    given by 20t minus 5t squared. When does it hit the ground?
    → 20t − 5t² = 0 → t(20−5t) = 0 → t = 4 seconds"""
    r = vy.answer(
        "A ball is thrown upward at 20 meters per second. "
        "Its height is 20t minus 5t squared. "
        "When does the ball hit the ground?"
    )
    assert "4" in r


@xfail(strict=True, reason="series_quadratic: maximum area with fixed perimeter")
def test_quadratic_max_area(vy):
    """A farmer has 40 meters of fencing. He wants to enclose a rectangular
    garden along a wall. What is the maximum area he can enclose?
    → width=x, length=40-2x, area=x(40-2x)=40x-2x². Max at x=10 → area=200"""
    r = vy.answer(
        "A farmer has 40 meters of fencing to enclose a rectangular "
        "garden along a wall. What is the maximum area he can enclose?"
    )
    assert "200" in r


@xfail(strict=True, reason="series_quadratic: number puzzle — product and difference")
def test_quadratic_number_puzzle(vy):
    """Two numbers differ by 3. Their product is 40.
    What are the numbers? → x(x+3)=40 → x²+3x−40=0 → x=5, x+3=8"""
    r = vy.answer(
        "Two numbers differ by 3. Their product is 40. "
        "What are the two numbers?"
    )
    assert "5" in r and "8" in r


@xfail(strict=True, reason="series_quadratic: geometry — square side increase")
def test_quadratic_square_side(vy):
    """The side of a square is increased by 3. The area increases by 39.
    What was the original side length?
    → (x+3)² − x² = 39 → 6x+9=39 → x=5"""
    r = vy.answer(
        "The side of a square is increased by 3. The area increases by 39. "
        "What was the original side length?"
    )
    assert "5" in r


@xfail(strict=True, reason="series_quadratic: vertex — maximum height of projectile")
def test_quadratic_vertex_max(vy):
    """A ball is thrown upward. Its height in meters is 20t minus 5t squared.
    What is the maximum height reached?
    → vertex at t = -b/2a = -20/(2*-5) = 2. h(2) = 40−20 = 20"""
    r = vy.answer(
        "A ball is thrown upward. Its height in meters is 20t minus 5t squared. "
        "What is the maximum height the ball reaches?"
    )
    # must compute 20 as result, not just echo — check "find" section
    r_find = r.lower().split("find")[-1] if "find" in r.lower() else ""
    assert "20" in r_find and "no match" not in r.lower()


@xfail(strict=True, reason="series_quadratic: revenue optimization")
def test_quadratic_revenue(vy):
    """A company sells x items at a price of 100 minus 2x dollars each.
    The revenue is x times 100 minus 2x. How many items maximize revenue?
    → R = 100x − 2x², max at x = -100/(2*-2) = 25"""
    r = vy.answer(
        "A company sells items at a price of 100 minus 2 times the number "
        "of items dollars each. How many items should they sell to "
        "maximize revenue?"
    )
    assert "25" in r


# ══════════════════════════════════════════════════════════════════════════════
# POLYNOMIAL EVALUATION — bahupada
# ══════════════════════════════════════════════════════════════════════════════


@xfail(strict=True, reason="series_polynomial: evaluate cubic at a point")
def test_polynomial_evaluate(vy):
    """What is the value of 2x cubed minus 3x squared plus x minus 5
    when x is 3? → 2(27) − 3(9) + 3 − 5 = 54 − 27 + 3 − 5 = 25"""
    r = vy.answer(
        "What is the value of 2 times x cubed minus 3 times x squared "
        "plus x minus 5 when x is 3?"
    )
    assert "25" in r


# ══════════════════════════════════════════════════════════════════════════════
# ADDITIONAL SERIES — harmonic, alternating, mean inequalities
# ══════════════════════════════════════════════════════════════════════════════


@xfail(strict=True, reason="series_harmonic: bouncing ball total distance")
def test_harmonic_bouncing_ball(vy):
    """A ball is dropped from 10 meters. Each bounce reaches half the
    previous height. What is the total distance the ball travels before
    stopping? → 10 + 2*(5+2.5+1.25+...) = 10 + 2*5/(1-0.5) = 10+20 = 30"""
    r = vy.answer(
        "A ball is dropped from 10 meters. Each bounce reaches half the "
        "previous height. What is the total distance the ball travels?"
    )
    assert "30" in r


@xfail(strict=True, reason="series_mean: AM-GM inequality application")
def test_am_gm_inequality(vy):
    """The arithmetic mean of two positive numbers is 10. What is the
    maximum possible value of their product?
    → AM = (a+b)/2 = 10, max product when a=b=10 → product = 100"""
    r = vy.answer(
        "The arithmetic mean of two positive numbers is 10. "
        "What is the maximum possible value of their product?"
    )
    assert "100" in r


@xfail(strict=True, reason="series_geometric: infinite sum — convergent")
def test_geometric_infinite_sum(vy):
    """What is the sum of the infinite series 1 + 1/2 + 1/4 + 1/8 + ...?
    → a/(1-r) = 1/(1-0.5) = 2"""
    r = vy.answer(
        "What is the sum of the infinite series 1 plus one half plus "
        "one quarter plus one eighth and so on?"
    )
    r_lower = r.lower()
    find_section = r_lower.split("find")[-1] if "find" in r_lower else r_lower
    assert "2" in find_section and "no match" not in find_section


def test_arithmetic_find_position(vy):
    """An arithmetic sequence starts at 7 and increases by 4 each term.
    Which term equals 51? → 7 + (n-1)*4 = 51 → n = 12"""
    r = vy.answer(
        "An arithmetic sequence starts at 7 and increases by 4 each term. "
        "Which term in the sequence equals 51?"
    )
    assert "12" in r


@xfail(strict=True, reason="series_geometric: half-life decay")
def test_geometric_half_life(vy):
    """A substance has a half-life of 3 hours. Starting with 800 grams,
    how much remains after 9 hours?
    → 9/3 = 3 half-lives. 800 * (1/2)^3 = 100"""
    r = vy.answer(
        "A substance has a half-life of 3 hours. Starting with 800 grams, "
        "how much remains after 9 hours?"
    )
    assert "100" in r
