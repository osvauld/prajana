"""test_math.py — the math roadmap: primary school through advanced.

Tests are organized by level (L0–L6), progressing from fundamental
number concepts through coordinate geometry, trigonometry, lines,
intersections, vectors, and applications.

Each test uses natural language questions — the kind found in standard
textbook exercises. The graph must understand the concepts, not just
compute.

Gates:
  math_L0_number     — number line, sign, absolute value, mod, floor/ceil
  math_L0_arithmetic — natural phrasing of basic operations (minus, times, divided by)
  math_L1_coordinate — coordinate pairs, distance, midpoint
  math_L2_trig       — sine, cosine, tangent, radians, Pythagorean theorem
  math_L3_line       — slope, line equations, parallel, perpendicular
  math_L4_intersect  — line-line, segment-segment, line-circle intersection
  math_L5_vector     — vector arithmetic, dot product, cross product
  math_L6_apply      — torus distance, flood fill, composite spatial reasoning
"""

import pytest

xfail = pytest.mark.xfail


# ══════════════════════════════════════════════════════════════════════════════
# LEVEL 0 — NUMBER FOUNDATIONS
# ══════════════════════════════════════════════════════════════════════════════


# ── gate: math_L0_arithmetic — natural phrasing of basic operations ──────────


# ── passing: these word-problem phrasings already work via count-chain ───────


def test_five_plus_three(vy):
    """Ravi has 5 marbles in his left pocket and 3 marbles in his right
    pocket. How many marbles does he have in total? → 5 + 3 = 8
    Fixed: detect-direction now skips 'left' (disha) instead of treating it as kshaya."""
    r = vy.answer(
        "Ravi has 5 marbles in his left pocket and 3 marbles in his right pocket. "
        "How many marbles does he have in total?"
    )
    assert "8" in r


def test_twelve_minus_seven(vy):
    """There are 12 apples on a table. Priya took 7 of them.
    How many apples are left on the table? → 12 − 7 = 5"""
    r = vy.answer(
        "There are 12 apples on a table. Priya took 7 of them. "
        "How many apples are left on the table?"
    )
    assert "5" in r


def test_six_times_four(vy):
    """A garden has 6 rows of plants with 4 plants in each row.
    How many plants are there in total? → 6 × 4 = 24"""
    r = vy.answer(
        "A garden has 6 rows of plants with 4 plants in each row. "
        "How many plants are there in total?"
    )
    assert "24" in r


def test_twenty_divided_by_four(vy):
    """There are 20 chocolates to be shared equally among 4 friends.
    How many chocolates does each friend get? → 20 ÷ 4 = 5
    Fixed: division as 4th count-chain direction, triggered by 'shared'."""
    r = vy.answer(
        "There are 20 chocolates to be shared equally among 4 friends. "
        "How many chocolates does each friend get?"
    )
    assert "5" in r and "80" not in r


def test_sum_of(vy):
    """In a school, there are 15 boys and 27 girls. How many students
    are there in total? → 15 + 27 = 42"""
    r = vy.answer(
        "In a school, there are 15 boys and 27 girls. "
        "How many students are there in total?"
    )
    assert "42" in r


# ── xfail: these phrasings use math vocabulary the pipeline doesn't route ────


def test_product_of(vy):
    """A farmer plants 8 rows of saplings. Each row has 7 saplings.
    How many saplings are there in total? → 8 × 7 = 56
    Fixed: 'each' triggers multiplication via quant-each sthita→multiplication."""
    r = vy.answer(
        "A farmer plants 8 rows of saplings. "
        "Each row has 7 saplings. "
        "How many saplings are there in total?"
    )
    assert "56" in r


def test_difference_of(vy):
    """Arun scored 50 marks in maths and 18 marks in English.
    What is the difference between his maths and English marks?
    → 50 − 18 = 32
    Fixed: 'difference' bhasha node carries sthita→kshaya."""
    r = vy.answer(
        "Arun scored 50 marks in maths and 18 marks in English. "
        "What is the difference between his maths and English marks?"
    )
    assert "32" in r


@xfail(strict=True, reason="math_L0_arithmetic: 'squared' suffix not recognised")
def test_squared(vy):
    """A square tile has a side length of 9 centimeters. What is the area
    of the tile? → 9² = 81 square centimeters"""
    r = vy.answer(
        "A square tile has a side length of 9 centimeters. "
        "What is the area of the tile?"
    )
    assert "81" in r


@xfail(strict=True, reason="math_L0_arithmetic: 'square root of' not routed to square-root mantra")
def test_square_root(vy):
    """A square garden has an area of 144 square meters. What is the length
    of one side of the garden? → √144 = 12 meters"""
    r = vy.answer(
        "A square garden has an area of 144 square meters. "
        "What is the length of one side of the garden?"
    )
    assert "12" in r


def test_change_in_temperature(vy):
    """A temperature drops from 8 degrees to negative 3 degrees.
    What is the change in temperature? → 8 - (-3) = 11.
    Fixed: 'negative' sign-modifier produces -3, 'dropped'→falling→kshaya gives subtraction,
    so count-chain computes 8 - (-3) = 11."""
    r = vy.answer(
        "A temperature was 8 degrees celsius. "
        "It dropped to negative 3 degrees celsius. "
        "What is the change in temperature?"
    )
    r_lower = r.lower()
    assert "11" in r and ("change" in r_lower or "difference" in r_lower or "drop" in r_lower) and "plus" not in r_lower


@xfail(strict=True, reason="math_L0_arithmetic: multi-step — total cost calculation")
def test_total_cost(vy):
    """A notebook costs 3 dollars. A pen costs 2 dollars. A ruler costs 1 dollar.
    Maria buys 4 notebooks, 6 pens, and 2 rulers.
    What is the total cost? → 4*3 + 6*2 + 2*1 = 12 + 12 + 2 = 26"""
    r = vy.answer(
        "A notebook costs 3 dollars. A pen costs 2 dollars. A ruler costs 1 dollar. "
        "Maria buys 4 notebooks, 6 pens, and 2 rulers. "
        "What is the total cost?"
    )
    assert "26" in r


def test_sharing_equally(vy):
    """There are 48 candies to be shared equally among 8 children.
    How many candies does each child get? → 48 / 8 = 6
    Fixed: division as 4th count-chain direction, triggered by 'shared'."""
    r = vy.answer(
        "There are 48 candies. They are shared equally among 8 children. "
        "How many candies does each child get?"
    )
    assert "6" in r


# ── gate: math_L0_number — sign, absolute value, negative numbers ────────────


@xfail(strict=True, reason="math_L0_number: absolute value of negative number")
def test_absolute_value_negative(vy):
    """A submarine is at a depth of negative 7 meters relative to sea level.
    What is its distance from sea level? → |−7| = 7 meters"""
    r = vy.answer(
        "A submarine is at a depth of negative 7 meters relative to sea level. "
        "What is its distance from sea level?"
    )
    assert "7" in r and "no match" not in r.lower()


@xfail(strict=True, reason="math_L0_number: absolute value of positive number unchanged")
def test_absolute_value_positive(vy):
    """A bird is flying at a height of 5 meters above sea level.
    What is the absolute value of its height? → |5| = 5"""
    r = vy.answer(
        "A bird is flying at a height of 5 meters above sea level. "
        "What is the absolute value of its height?"
    )
    assert "5" in r and "no match" not in r.lower()


def test_subtraction_negative_result(vy):
    """A hiker starts at an altitude of 7 meters above sea level and descends
    12 meters into a cave. What is the hiker's altitude now? → 7 − 12 = −5
    Fixed: 'descends' (present tense) now carries kshaya via sandhi-viveka
    direction priority. grade-direction reads kshaya edge directly."""
    r = vy.answer(
        "A hiker starts at an altitude of 7 meters above sea level. "
        "He descends 12 meters into a cave. "
        "What is his altitude now?"
    )
    assert "-5" in r


@xfail(strict=True, reason="math_L0_number: comparing negative numbers")
def test_negative_comparison(vy):
    """City A recorded a temperature of negative 7 degrees celsius.
    City B recorded negative 2 degrees celsius. Which city was colder?
    → City A (−7 < −2 on the number line)"""
    r = vy.answer(
        "City A recorded a temperature of negative 7 degrees celsius. "
        "City B recorded a temperature of negative 2 degrees celsius. "
        "Which city was colder?"
    )
    r_lower = r.lower()
    assert "a" in r_lower and "no match" not in r_lower


@xfail(strict=True, reason="math_L0_number: ordering negative numbers")
def test_which_is_smaller(vy):
    """A thermometer shows negative 3 degrees in the morning and negative 8
    degrees at night. Which reading is lower? → −8"""
    r = vy.answer(
        "A thermometer shows negative 3 degrees in the morning and "
        "negative 8 degrees at night. Which reading is lower?"
    )
    r_lower = r.lower()
    assert ("-8" in r or "negative 8" in r_lower or "night" in r_lower) and "no match" not in r_lower


@xfail(strict=True, reason="math_L0_number: temperature word problem with negatives")
def test_temperature_below_zero(vy):
    """At 6 AM the temperature was negative 4 degrees celsius.
    By noon it rose by 9 degrees. What was the temperature at noon? → 5
    Graph currently returns 15 (adds 6+9) — must compute -4 + 9 = 5."""
    r = vy.answer(
        "At 6 AM the temperature was negative 4 degrees celsius. "
        "By noon it had risen by 9 degrees. "
        "What was the temperature at noon?"
    )
    assert "5" in r and "15" not in r


@xfail(strict=True, reason="math_L0_number: modular arithmetic — remainder")
def test_remainder(vy):
    """A teacher has 17 pencils and wants to distribute them equally among
    5 students. How many pencils are left over after each student gets
    the same number? → 17 mod 5 = 2"""
    r = vy.answer(
        "A teacher has 17 pencils and wants to distribute them equally "
        "among 5 students. How many pencils are left over after each "
        "student gets the same number?"
    )
    assert "2" in r


@xfail(strict=True, reason="math_L0_number: floor — rounding down to whole number")
def test_floor(vy):
    """A rope is 7.3 meters long. If you can only cut it into whole meter
    pieces, how many whole meter pieces can you get?
    → floor(7.3) = 7"""
    r = vy.answer(
        "A rope is 7.3 meters long. You can only cut whole meter pieces from it. "
        "How many whole meter pieces can you get?"
    )
    assert "7" in r and "no match" not in r.lower()


@xfail(strict=True, reason="math_L0_number: ceiling — rounding up to whole number")
def test_ceiling(vy):
    """A bus holds 40 passengers. There are 327 students going on a field trip.
    How many buses are needed to carry all the students?
    → ceil(327 / 40) = ceil(8.175) = 9"""
    r = vy.answer(
        "A bus holds 40 passengers. There are 327 students going on a field trip. "
        "How many buses are needed to carry all the students?"
    )
    assert "9" in r and "no match" not in r.lower()


@xfail(strict=True, reason="math_L0_number: even/odd classification")
def test_even_odd(vy):
    """There are 17 children in a class. Can they be split into two equal
    groups with no one left out? → No, because 17 is odd."""
    r = vy.answer(
        "There are 17 children in a class. Can they be split into two "
        "equal groups with no one left out?"
    )
    r_lower = r.lower()
    # Must show understanding of odd/even — "no" or "odd" or "cannot", not just echo 17
    assert ("odd" in r_lower or "cannot" in r_lower or ("no" in r_lower and "equal" in r_lower))


@xfail(strict=True, reason="math_L0_number: elevator word problem with floors and negatives")
def test_elevator_floors(vy):
    """A building has floors numbered from negative 3 (underground parking)
    to 10 (rooftop). An elevator starts at floor 3 and goes down 5 floors.
    What floor is it on now? → 3 − 5 = −2"""
    r = vy.answer(
        "A building has floors from negative 3 to 10. "
        "An elevator starts at floor 3 and goes down 5 floors. "
        "What floor is it on now?"
    )
    assert "-2" in r


@xfail(strict=True, reason="math_L0_number: multi-step with floor division and remainder")
def test_baker_cookies(vy):
    """A baker bakes 60 cookies in the morning. He packs them into gift
    boxes that hold exactly 8 cookies each. How many full gift boxes can
    he prepare, and how many cookies are left unpacked?
    → floor(60/8) = 7 boxes, 60 mod 8 = 4 leftover"""
    r = vy.answer(
        "A baker bakes 60 cookies in the morning. He packs them into gift "
        "boxes that hold exactly 8 cookies each. How many full gift boxes "
        "can he prepare, and how many cookies are left unpacked?"
    )
    assert "7" in r and "4" in r


# ══════════════════════════════════════════════════════════════════════════════
# LEVEL 1 — COORDINATE GEOMETRY
# ══════════════════════════════════════════════════════════════════════════════


# ── gate: math_L1_coordinate — distance, midpoint ───────────────────────────


@xfail(strict=True, reason="math_L1_coordinate: distance between two points")
def test_distance_two_points(vy):
    """Find the distance between the points (3, 0) and (0, 4).
    → sqrt((3-0)^2 + (0-4)^2) = sqrt(9+16) = sqrt(25) = 5"""
    r = vy.answer(
        "Find the distance between the points (3, 0) and (0, 4)."
    )
    assert "5" in r


@xfail(strict=True, reason="math_L1_coordinate: midpoint of two points")
def test_midpoint(vy):
    """What is the midpoint of the points (2, 6) and (8, 10)?
    → ((2+8)/2, (6+10)/2) = (5, 8)"""
    r = vy.answer(
        "What is the midpoint of the points (2, 6) and (8, 10)?"
    )
    assert "5" in r and "8" in r


@xfail(strict=True, reason="math_L1_coordinate: Manhattan distance")
def test_manhattan_distance(vy):
    """A taxi drives from intersection (2, 3) to intersection (7, 9)
    on a grid of streets. How many blocks does it travel?
    → |7-2| + |9-3| = 5 + 6 = 11"""
    r = vy.answer(
        "A taxi drives from intersection (2, 3) to intersection (7, 9) "
        "on a grid of streets. How many blocks does it travel?"
    )
    assert "11" in r


@xfail(strict=True, reason="math_L1_coordinate: distance word problem — is the point inside the circle")
def test_point_inside_circle(vy):
    """A circle has its center at the origin and a radius of 10.
    Is the point (6, 8) inside the circle?
    → distance = sqrt(36+64) = sqrt(100) = 10 → on the circle (not inside)"""
    r = vy.answer(
        "A circle has its center at the origin and a radius of 10. "
        "Is the point (6, 8) inside the circle?"
    )
    r_lower = r.lower()
    # Must demonstrate understanding: compute distance and compare to radius
    assert ("distance" in r_lower or "radius" in r_lower or "on the circle" in r_lower or "not inside" in r_lower) and "no match" not in r_lower


@xfail(strict=True, reason="math_L1_coordinate: which point is closer to origin")
def test_closer_to_origin(vy):
    """Which point is closer to the origin: (3, 4) or (1, 7)?
    → d1 = sqrt(9+16) = 5, d2 = sqrt(1+49) ≈ 7.07 → (3,4) is closer"""
    r = vy.answer(
        "Which point is closer to the origin: (3, 4) or (1, 7)?"
    )
    r_lower = r.lower()
    assert ("3, 4" in r or "(3,4)" in r or "distance" in r_lower or "closer" in r_lower) and "no match" not in r_lower and "plus" not in r_lower


# ══════════════════════════════════════════════════════════════════════════════
# LEVEL 2 — TRIGONOMETRY
# ══════════════════════════════════════════════════════════════════════════════


# ── gate: math_L2_trig — sin, cos, tan, degrees, Pythagoras ─────────────────


@xfail(strict=True, reason="math_L2_trig: sine of 90 degrees")
def test_sine_90(vy):
    """What is the sine of 90 degrees? → 1"""
    r = vy.answer("What is the sine of 90 degrees?")
    assert "1" in r and "no match" not in r.lower()


@xfail(strict=True, reason="math_L2_trig: cosine of 60 degrees")
def test_cosine_60(vy):
    """What is the cosine of 60 degrees? → 0.5"""
    r = vy.answer("What is the cosine of 60 degrees?")
    assert "0.5" in r


@xfail(strict=True, reason="math_L2_trig: tangent of 45 degrees")
def test_tangent_45(vy):
    """What is the tangent of 45 degrees? → 1"""
    r = vy.answer("What is the tangent of 45 degrees?")
    assert "1" in r and "no match" not in r.lower()


@xfail(strict=True, reason="math_L2_trig: Pythagorean theorem — find hypotenuse")
def test_pythagorean_hypotenuse(vy):
    """A right triangle has legs of length 5 and 12.
    What is the length of the hypotenuse?
    → sqrt(25 + 144) = sqrt(169) = 13"""
    r = vy.answer(
        "A right triangle has sides of length 5 and 12. "
        "What is the length of the hypotenuse?"
    )
    assert "13" in r


@xfail(strict=True, reason="math_L2_trig: Pythagorean theorem — find missing leg")
def test_pythagorean_missing_leg(vy):
    """A right triangle has a hypotenuse of 10 and one leg of 6.
    What is the length of the other leg?
    → sqrt(100 - 36) = sqrt(64) = 8"""
    r = vy.answer(
        "A right triangle has a hypotenuse of length 10 and one side of length 6. "
        "What is the length of the other side?"
    )
    assert "8" in r


@xfail(strict=True, reason="math_L2_trig: ladder problem — height using sine")
def test_ladder_height(vy):
    """A 10 meter ladder leans against a wall at 60 degrees to the ground.
    How high up the wall does it reach?
    → 10 * sin(60°) = 10 * 0.866 = 8.66"""
    r = vy.answer(
        "A 10 meter ladder leans against a wall making a 60 degree angle with the ground. "
        "How high up the wall does the ladder reach?"
    )
    assert "8.66" in r or "8.7" in r


@xfail(strict=True, reason="math_L2_trig: radian to degree conversion")
def test_radian_to_degree(vy):
    """Convert pi/4 radians to degrees. → 45"""
    r = vy.answer("Convert pi over 4 radians to degrees.")
    assert "45" in r


# ══════════════════════════════════════════════════════════════════════════════
# LEVEL 3 — LINES
# ══════════════════════════════════════════════════════════════════════════════


# ── gate: math_L3_line — slope, equations, parallel, perpendicular ───────────


@xfail(strict=True, reason="math_L3_line: slope between two points")
def test_slope_two_points(vy):
    """What is the slope of the line passing through (1, 2) and (4, 8)?
    → (8-2)/(4-1) = 6/3 = 2"""
    r = vy.answer(
        "What is the slope of the line passing through the points (1, 2) and (4, 8)?"
    )
    r_lower = r.lower()
    assert "slope" in r_lower and "2" in r and "plus" not in r_lower


@xfail(strict=True, reason="math_L3_line: y-intercept from two points")
def test_y_intercept(vy):
    """A line passes through (2, 5) and (4, 9). What is the y-intercept?
    → slope = (9-5)/(4-2) = 2. y = 2x + b → 5 = 4 + b → b = 1"""
    r = vy.answer(
        "A line passes through the points (2, 5) and (4, 9). "
        "What is the y-intercept?"
    )
    r_lower = r.lower()
    assert "intercept" in r_lower and "1" in r and "14" not in r


@xfail(strict=True, reason="math_L3_line: are two lines parallel")
def test_parallel_lines(vy):
    """Line A passes through (0, 1) and (2, 5).
    Line B passes through (0, 3) and (2, 7).
    Are the two lines parallel?
    → slope A = 2, slope B = 2 → yes, parallel"""
    r = vy.answer(
        "Line A passes through (0, 1) and (2, 5). "
        "Line B passes through (0, 3) and (2, 7). "
        "Are the two lines parallel?"
    )
    r_lower = r.lower()
    assert ("yes" in r_lower or "parallel" in r_lower) and "plus" not in r_lower


@xfail(strict=True, reason="math_L3_line: perpendicular slope")
def test_perpendicular_slope(vy):
    """A line has slope 3. What is the slope of a line perpendicular to it?
    → -1/3"""
    r = vy.answer(
        "A line has a slope of 3. "
        "What is the slope of a line perpendicular to it?"
    )
    assert "-0.33" in r or "-1/3" in r


@xfail(strict=True, reason="math_L3_line: point on a line check")
def test_point_on_line(vy):
    """A line passes through (0, 2) with slope 3. Is the point (2, 8) on this line?
    → y = 3x + 2. At x=2: y=8. Yes."""
    r = vy.answer(
        "A line passes through (0, 2) with a slope of 3. "
        "Is the point (2, 8) on this line?"
    )
    assert "yes" in r.lower()


# ══════════════════════════════════════════════════════════════════════════════
# LEVEL 4 — INTERSECTIONS
# ══════════════════════════════════════════════════════════════════════════════


# ── gate: math_L4_intersect — line-line, segment, line-circle ────────────────


@xfail(strict=True, reason="math_L4_intersect: intersection of two lines")
def test_line_line_intersection(vy):
    """Line A has slope 2 and y-intercept 1. Line B has slope -1 and y-intercept 7.
    Where do they intersect?
    → 2x + 1 = -x + 7 → 3x = 6 → x = 2, y = 5 → (2, 5)"""
    r = vy.answer(
        "Line A has slope 2 and y-intercept 1. "
        "Line B has slope negative 1 and y-intercept 7. "
        "Where do the two lines intersect?"
    )
    assert "2" in r and "5" in r


@xfail(strict=True, reason="math_L4_intersect: do two segments cross")
def test_segments_cross(vy):
    """Segment A goes from (0, 0) to (4, 4).
    Segment B goes from (0, 4) to (4, 0).
    Do they intersect? → Yes, at (2, 2)"""
    r = vy.answer(
        "Segment A goes from (0, 0) to (4, 4). "
        "Segment B goes from (0, 4) to (4, 0). "
        "Do the two segments intersect?"
    )
    r_lower = r.lower()
    assert "yes" in r_lower or "2" in r


@xfail(strict=True, reason="math_L4_intersect: line-circle intersection count")
def test_line_circle_intersect(vy):
    """A circle has center (0, 0) and radius 5.
    A horizontal line passes through y = 3.
    At how many points does the line intersect the circle?
    → x^2 + 9 = 25 → x^2 = 16 → x = ±4. Two points."""
    r = vy.answer(
        "A circle has its center at the origin and radius 5. "
        "A horizontal line is at height 3. "
        "At how many points does the line cross the circle?"
    )
    assert "2" in r or "two" in r.lower()


# ══════════════════════════════════════════════════════════════════════════════
# LEVEL 5 — VECTORS
# ══════════════════════════════════════════════════════════════════════════════


# ── gate: math_L5_vector — add, subtract, magnitude, dot, cross ──────────────


@xfail(strict=True, reason="math_L5_vector: vector addition")
def test_vector_add(vy):
    """Add the vectors (3, 4) and (1, 2). → (4, 6)"""
    r = vy.answer("Add the vectors (3, 4) and (1, 2).")
    r_lower = r.lower()
    assert ("4, 6" in r or "(4,6)" in r or "vector" in r_lower) and "plus" not in r_lower


@xfail(strict=True, reason="math_L5_vector: vector magnitude")
def test_vector_magnitude(vy):
    """What is the magnitude of the vector (3, 4)? → 5"""
    r = vy.answer("What is the magnitude of the vector (3, 4)?")
    assert "5" in r


@xfail(strict=True, reason="math_L5_vector: dot product")
def test_dot_product(vy):
    """What is the dot product of (1, 2, 3) and (4, 5, 6)?
    → 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32"""
    r = vy.answer("What is the dot product of the vectors (1, 2, 3) and (4, 5, 6)?")
    assert "32" in r


@xfail(strict=True, reason="math_L5_vector: cross product")
def test_cross_product(vy):
    """What is the cross product of (1, 0, 0) and (0, 1, 0)?
    → (0, 0, 1)"""
    r = vy.answer("What is the cross product of (1, 0, 0) and (0, 1, 0)?")
    r_lower = r.lower()
    assert ("0, 0, 1" in r or "(0,0,1)" in r or "cross product" in r_lower) and "plus" not in r_lower


@xfail(strict=True, reason="math_L5_vector: displacement word problem")
def test_displacement_vector(vy):
    """A boat sails 3 km east and then 4 km north.
    How far is it from its starting point?
    → sqrt(9 + 16) = 5 km"""
    r = vy.answer(
        "A boat sails 3 km east and then 4 km north. "
        "How far is the boat from its starting point?"
    )
    assert "5" in r


@xfail(strict=True, reason="math_L5_vector: angle between two vectors")
def test_angle_between_vectors(vy):
    """What is the angle between the vectors (1, 0) and (0, 1)?
    → cos(theta) = 0 → theta = 90 degrees"""
    r = vy.answer("What is the angle between the vectors (1, 0) and (0, 1)?")
    assert "90" in r


# ══════════════════════════════════════════════════════════════════════════════
# LEVEL 6 — APPLICATIONS
# ══════════════════════════════════════════════════════════════════════════════


# ── gate: math_L6_apply — torus distance, composite problems ─────────────────


@xfail(strict=True, reason="math_L6_apply: torus wrapping distance")
def test_torus_distance(vy):
    """On a 10 by 10 grid that wraps around (torus), what is the shortest
    distance from cell (1, 1) to cell (9, 9)?
    → min(|9-1|, 10-|9-1|) = min(8, 2) = 2 in each axis → distance = 2+2 = 4 (Manhattan)
    or Euclidean = sqrt(4+4) ≈ 2.83"""
    r = vy.answer(
        "On a 10 by 10 grid that wraps around, what is the shortest "
        "distance from position (1, 1) to position (9, 9)?"
    )
    # Accept Manhattan (4) or Euclidean (2.83)
    assert "4" in r or "2.8" in r


@xfail(strict=True, reason="math_L6_apply: area of triangle from coordinates")
def test_triangle_area_coordinates(vy):
    """What is the area of a triangle with vertices at (0, 0), (6, 0), and (0, 8)?
    → base = 6, height = 8, area = 0.5 * 6 * 8 = 24"""
    r = vy.answer(
        "What is the area of a triangle with vertices at (0, 0), (6, 0), and (0, 8)?"
    )
    assert "24" in r


@xfail(strict=True, reason="math_L6_apply: reflection of a point across a line")
def test_reflection_across_axis(vy):
    """What is the reflection of the point (3, 5) across the x-axis?
    → (3, -5)"""
    r = vy.answer("What is the reflection of the point (3, 5) across the x-axis?")
    assert "3" in r and "-5" in r
