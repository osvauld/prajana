"""test_math.py — the math roadmap: primary school through advanced.

Tests are organized by level (L0–L6), progressing from fundamental
number concepts through coordinate geometry, trigonometry, lines,
intersections, vectors, and applications.

Each test uses natural language questions — the kind found in standard
textbook exercises. The graph must understand the concepts, not just
compute.

Gates:
  math_L0_sankhya    — number words, ordinals, fractions, multipliers, base conversion
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
# LEVEL 0 — NUMBER WORDS & TYPES (sankhya)
# ══════════════════════════════════════════════════════════════════════════════


# ── gate: math_L0_sankhya — number words as values ──────────────────────────


def test_number_word_apples(vy):
    """Tom picked twenty-two apples. How many apples does Tom have?
    → twenty-two = 22"""
    r = vy.answer(
        "Tom picked twenty-two apples. How many apples does Tom have?"
    )
    assert "22" in r


def test_number_word_mixed(vy):
    """A school has 5 classrooms with thirty students each.
    How many students are there in total?
    → 5 × 30 = 150"""
    r = vy.answer(
        "A school has 5 classrooms with thirty students each. "
        "How many students are there in total?"
    )
    assert "150" in r


def test_number_word_large(vy):
    """The village has two thousand three hundred people.
    A nearby town has 1500 people. How many people total?
    → 2300 + 1500 = 3800"""
    r = vy.answer(
        "The village has two thousand three hundred people. "
        "A nearby town has 1500 people. How many people total?"
    )
    assert "3800" in r


# ── gate: math_L0_sankhya — multipliers ─────────────────────────────────────


def test_multiplier_double(vy):
    """A recipe needs 3 cups of flour. If you double the recipe,
    how many cups of flour do you need?
    → 3 × 2 = 6"""
    r = vy.answer(
        "A recipe needs 3 cups of flour. If you double the recipe, "
        "how many cups of flour do you need?"
    )
    assert "6" in r


def test_multiplier_triple(vy):
    """A painter charges 200 dollars per room. He triples the rate.
    How much does he charge?
    → 200 × 3 = 600"""
    r = vy.answer(
        "A painter charges 200 dollars per room. "
        "He triples the rate. How much does he charge?"
    )
    assert "600" in r


def test_multiplier_half(vy):
    """A tank holds 80 liters of water. It is now half full.
    How many liters of water are in the tank?
    → 80 × 0.5 = 40"""
    r = vy.answer(
        "A tank holds 80 liters of water. It is now half full. "
        "How many liters of water are in the tank?"
    )
    assert "40" in r


def test_multiplier_quarter(vy):
    """A pizza has 12 slices. Maria ate a quarter of the pizza.
    How many slices did she eat?
    → 12 × 0.25 = 3"""
    r = vy.answer(
        "A pizza has 12 slices. Maria ate a quarter of the pizza. "
        "How many slices did she eat?"
    )
    assert "3" in r


# ── gate: math_L0_sankhya — fractions ───────────────────────────────────────


def test_fraction_one_third(vy):
    """A farmer has 90 acres of land. He plants wheat on one third
    of his land. How many acres of wheat does he have?
    → 90 × (1/3) = 30"""
    r = vy.answer(
        "A farmer has 90 acres of land. He plants wheat on one third "
        "of his land. How many acres of wheat does he have?"
    )
    assert "30" in r


def test_fraction_two_thirds(vy):
    """A class has 45 students. Two thirds of them passed the exam.
    How many students passed?
    → 45 × (2/3) = 30"""
    r = vy.answer(
        "A class has 45 students. Two thirds of them passed the exam. "
        "How many students passed?"
    )
    assert "30" in r


def test_fraction_three_quarters(vy):
    """A journey is 200 kilometers. The bus has covered three quarters
    of the journey. How many kilometers has it traveled?
    → 200 × (3/4) = 150"""
    r = vy.answer(
        "A journey is 200 kilometers. The bus has covered three quarters "
        "of the journey. How many kilometers has it traveled?"
    )
    assert "150" in r


# ── gate: math_L0_sankhya — ordinals as positions ──────────────────────────


@xfail(strict=True, reason="gate:sankhya — ordinal: third in line")
def test_ordinal_position(vy):
    """Students are standing in a line. Their heights are 140, 135,
    150, 145, and 160 centimeters. What is the height of the third student?
    → position 3 = 150"""
    r = vy.answer(
        "Students are standing in a line. Their heights are "
        "140, 135, 150, 145, and 160 centimeters. "
        "What is the height of the third student?"
    )
    r_lower = r.lower()
    assert r_lower.split("find")[-1].count("150") > 0


# ── gate: math_L0_sankhya — base conversion ─────────────────────────────────


# ── gate: math_L0_sankhya — number in words (output) ────────────────────────


@xfail(strict=True, reason="gate:sankhya — output: number to word")
def test_number_to_word_simple(vy):
    """What is 7 in words?
    → seven"""
    r = vy.answer("What is 7 in words?")
    assert "seven" in r.lower()


@xfail(strict=True, reason="gate:sankhya — output: composed number to words")
def test_number_to_word_composed(vy):
    """What is 42 in words?
    → forty-two"""
    r = vy.answer("What is 42 in words?")
    r_lower = r.lower()
    assert "forty" in r_lower and "two" in r_lower


@xfail(strict=True, reason="gate:sankhya — output: large number to words")
def test_number_to_word_large(vy):
    """What is 350 in words?
    → three hundred fifty"""
    r = vy.answer("What is 350 in words?")
    r_lower = r.lower()
    assert "three" in r_lower and "hundred" in r_lower and "fifty" in r_lower


@xfail(strict=True, reason="gate:sankhya — output: compute and answer in words")
def test_compute_answer_in_words(vy):
    """A baker has 8 eggs. He uses 3 eggs. How many eggs are left?
    Answer in words.
    → 8 - 3 = 5 → five"""
    r = vy.answer(
        "A baker has 8 eggs. He uses 3 eggs. "
        "How many eggs are left? Answer in words."
    )
    assert "five" in r.lower()


@xfail(strict=True, reason="gate:sankhya — output: fraction to words")
def test_fraction_to_words(vy):
    """A rope is 12 meters long. It is cut into 4 equal pieces.
    What is the length of each piece in words?
    → 12 / 4 = 3 → three"""
    r = vy.answer(
        "A rope is 12 meters long. It is cut into 4 equal pieces. "
        "What is the length of each piece in words?"
    )
    assert "three" in r.lower()


# ── gate: math_L0_sankhya — base conversion ─────────────────────────────────


@xfail(strict=True, reason="gate:sankhya — base conversion: decimal to binary")
def test_base_decimal_to_binary(vy):
    """What is 13 in binary?
    → 13 = 1101 in base 2"""
    r = vy.answer("What is 13 in binary?")
    assert "1101" in r


@xfail(strict=True, reason="gate:sankhya — base conversion: decimal to hex")
def test_base_decimal_to_hex(vy):
    """What is 255 in hexadecimal?
    → 255 = FF in base 16"""
    r = vy.answer("What is 255 in hexadecimal?")
    r_upper = r.upper()
    assert "FF" in r_upper


@xfail(strict=True, reason="gate:sankhya — base conversion: binary to decimal")
def test_base_binary_to_decimal(vy):
    """What is 10110 in decimal?
    → 10110 binary = 16+4+2 = 22"""
    r = vy.answer("What is 10110 in binary converted to decimal?")
    assert "22" in r


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


# ── gate: math_xkyu — verb-connector-quantity binding (x k y u) ──────────────
# The (x k y u) pattern: verb/action x, connector k (by/to/from/at/into),
# quantity y, qualifier u. The connector determines HOW y relates to x.
# Same structure as physics "moves at 5 m/s" but in math domain.


def test_xkyu_increases_by(vy):
    """a number is 5. it increases by 3. what is the number? → 5+3=8
    Works: count-chain detects vriddhi from 'increases' verb."""
    r = vy.answer("a number is 5. it increases by 3. what is the number")
    assert "8" in r


def test_xkyu_decreases_by(vy):
    """a number is 10. it decreases by 4. what is the number? → 10-4=6
    Works: dhatu-decrease has sthita→kshaya, count-chain uses subtraction."""
    r = vy.answer("a number is 10. it decreases by 4. what is the number")
    assert "6" in r


def test_xkyu_multiplied_by(vy):
    """a number is 7. it is multiplied by 3. what is the result? → 7*3=21
    Works: dhatu-multiply has sthita→multiplication, count-chain uses mul."""
    r = vy.answer("a number is 7. it is multiplied by 3. what is the result")
    assert "21" in r


def test_xkyu_divided_by(vy):
    """a number is 20. it is divided by 4. what is the result? → 20/4=5
    Works: count-chain detects division from 'divided' verb."""
    r = vy.answer("a number is 20. it is divided by 4. what is the result")
    assert "5" in r


def test_xkyu_divided_into(vy):
    """a rope of length 12 m is divided into 4 equal parts. what is the length of each part? → 12/4=3
    Works: count-chain detects division from 'divided' verb."""
    r = vy.answer(
        "a rope has length 12. it is divided into 4 equal parts. "
        "what is the length of each part"
    )
    assert "3" in r


def test_xkyu_increases_by_percent(vy):
    """a number is 200. it increases by 10 percent. what is the number? → 200+20=220
    Works: shatamana scales nv as acc*nv/100, then vriddhi adds."""
    r = vy.answer("a number is 200. it increases by 10 percent. what is the number")
    assert "220" in r


@xfail(strict=True, reason="math_xkyu: 'from X to Y' — apadana+sampradana range")
def test_xkyu_from_to_range(vy):
    """the sum of numbers from 1 to 5 → 1+2+3+4+5=15"""
    r = vy.answer("what is the sum of numbers from 1 to 5")
    assert "15" in r


@xfail(strict=True, reason="math_xkyu: 'grows by X each step' — karana+parimana iterative")
def test_xkyu_grows_by_each(vy):
    """a plant is 10 cm tall. it grows by 2 cm each day. what is the height after 5 days? → 10+2*5=20"""
    r = vy.answer(
        "a plant is 10 cm tall. it grows by 2 cm each day. "
        "what is the height after 5 days"
    )
    assert "20" in r


def test_xkyu_reduced_to(vy):
    """a quantity is 50. it is reduced to 30. what is the decrease? → 50-30=20
    Works: dhatu-reduce has sthita→kshaya, count-chain uses subtraction."""
    r = vy.answer("a quantity is 50. it is reduced to 30. what is the decrease")
    assert "20" in r


# ── gate: math_percentage — percentage arithmetic ────────────────────────────
# Percentage is a scaling operation: "X percent of Y" = X/100 * Y.
# Needs: percent bhasha node, percentage mantra, count-chain awareness.


def test_percent_of_basic(vy):
    """what is 25 percent of 200? → 25/100 * 200 = 50
    Works: shatamana-bandha binds percentage=25, whole-value=200 → inverse percentage-mantra."""
    r = vy.answer("what is 25 percent of 200")
    assert "50" in r


def test_percent_of_number(vy):
    """a number is 300. what is 20 percent of the number? → 60
    Works: shatamana-bandha cross-grade binding, percentage=20, whole-value=300 → inverse."""
    r = vy.answer("a number is 300. what is 20 percent of the number")
    assert "60" in r


def test_percent_decrease(vy):
    """a number is 80. it decreases by 25 percent. what is the number? → 80 - 20 = 60
    Works: shatamana scales nv as acc*nv/100, then kshaya subtracts."""
    r = vy.answer("a number is 80. it decreases by 25 percent. what is the number")
    assert "60" in r


def test_percent_find_percentage(vy):
    """a class has 40 students. 10 students failed. what percent failed? → 10/40*100 = 25
    Works: shatamana-bandha maps larger→whole-value, smaller→part-value, forward percentage-mantra."""
    r = vy.answer("a class has 40 students. 10 students failed. what percent failed")
    assert "25" in r


def test_percent_increase_from_values(vy):
    """a price was 80. it increased to 100. what is the percent increase? → (100-80)/80*100 = 25
    Works: shatamana-bandha detects bhuta-kaala+direction → percent-change-mantra(initial=80,final=100)."""
    r = vy.answer("a price was 80. it increased to 100. what is the percent increase")
    assert "25" in r


def test_percent_decrease_from_values(vy):
    """a price was 200. it decreased to 150. what is the percent decrease? → (200-150)/200*100 = 25
    Works: percent-change-mantra gives -25, assertion matches substring."""
    r = vy.answer("a price was 200. it decreased to 150. what is the percent decrease")
    assert "25" in r


def test_percent_successive(vy):
    """a number is 100. it increases by 10 percent. it increases by 20 percent. what is the number?
    → 100 * 1.1 * 1.2 = 132
    Works: shatamana scales from current accumulator, so chained percentages compound correctly."""
    r = vy.answer(
        "a number is 100. it increases by 10 percent. "
        "it increases by 20 percent. what is the number"
    )
    assert "132" in r


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


@xfail(strict=True, reason="math_cyclic: '6 AM' must not leak standalone 6 into count-chain")
def test_temperature_below_zero(vy):
    """At 6 AM the temperature was negative 4 degrees celsius.
    By noon it rose by 9 degrees. What was the temperature at noon? → 5
    Graph currently returns 15 (adds 6+9) — must compute -4 + 9 = 5.
    Blocked by: '6 AM' time-point parsing — 6 enters count-chain as standalone number."""
    r = vy.answer(
        "At 6 AM the temperature was negative 4 degrees celsius. "
        "By noon it had risen by 9 degrees. "
        "What was the temperature at noon?"
    )
    assert "5" in r and "15" not in r


def test_remainder(vy):
    """A teacher has 17 pencils and wants to distribute them equally among
    5 students. How many pencils are left over after each student gets
    the same number? → 17 mod 5 = 2
    Fixed: shesha detection in count-chain — "left" + division context → mod op.
    mod mantra walks ganana→mod, OCaml Float.rem computes remainder."""
    r = vy.answer(
        "A teacher has 17 pencils and wants to distribute them equally "
        "among 5 students. How many pencils are left over after each "
        "student gets the same number?"
    )
    assert "2" in r


def test_floor(vy):
    """A rope is 7.3 meters. You can only cut whole meter pieces from it.
    How many whole meter pieces can you get? → floor(7.3) = 7
    Fixed: purna detection in count-chain — "whole" (swarupa→purna) in question
    grade → floor applied to count result. Avoids 'long' which triggers viveka."""
    r = vy.answer(
        "A rope is 7.3 meters. You can only cut whole meter pieces from it. "
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
    find_section = r_lower.split("find")[-1] if "find" in r_lower else r_lower
    # Must show understanding of odd/even — "no" or "odd" or "cannot" in answer
    assert ("odd" in find_section or "cannot" in find_section or "no" in find_section)


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


# ── gate: math_cyclic — modular / cyclic arithmetic ────────────────────────
# Cyclic domains share one pattern: (base + offset) mod period → result.
# Graph: cyclic-domain concept with (siddha period), labels via yukta.
# Unlocks: clock, calendar, compass, repeating patterns.


# ── clock arithmetic ──────────────────────────────────────────────────────


def test_clock_add_hours(vy):
    """It is 10 PM. What time will it be in 3 hours? → (22+3) mod 24 = 1 → 1 AM"""
    r = vy.answer("it is 10 PM. what time will it be in 3 hours")
    r_lower = r.lower()
    assert ("1" in r and "am" in r_lower) and "13" not in r


@xfail(strict=True, reason="math_cyclic: clock — hours between two times")
def test_clock_difference(vy):
    """A movie starts at 9 AM and ends at 2 PM. How many hours long is the
    movie? → 14 − 9 = 5 hours"""
    r = vy.answer(
        "A movie starts at 9 AM and ends at 2 PM. "
        "How many hours long is the movie?"
    )
    assert "5" in r


def test_clock_subtract_wrap(vy):
    """It is 2 AM. What time was it 5 hours ago? → (2−5+24) mod 24 = 21 → 9 PM"""
    r = vy.answer("it is 2 AM. what time was it 5 hours ago")
    r_lower = r.lower()
    assert ("9" in r and "pm" in r_lower) and "no match" not in r_lower


@xfail(strict=True, reason="math_cyclic: clock — minutes wrapping")
def test_clock_add_minutes(vy):
    """A class starts at 10:45 AM. The class is 50 minutes long.
    What time does it end? → 10:45 + 50 min = 11:35 AM"""
    r = vy.answer(
        "A class starts at 10:45 AM. The class is 50 minutes long. "
        "What time does it end?"
    )
    assert "11" in r and "35" in r


# ── day-of-week arithmetic ────────────────────────────────────────────────


def test_day_of_week_add(vy):
    """Today is Wednesday. What day will it be in 10 days?
    → (3 + 10) mod 7 = 6 → Saturday"""
    r = vy.answer("today is Wednesday. what day will it be in 10 days")
    r_lower = r.lower()
    assert "saturday" in r_lower


def test_day_of_week_subtract(vy):
    """Today is Monday. What day was it 3 days ago?
    → (1 − 3 + 7) mod 7 = 5 → Friday"""
    r = vy.answer("today is Monday. what day was it 3 days ago")
    r_lower = r.lower()
    assert "friday" in r_lower


def test_day_of_week_large(vy):
    """Today is Friday. What day will it be in 100 days?
    → (5 + 100) mod 7 = 0 → Sunday"""
    r = vy.answer("today is Friday. what day will it be in 100 days")
    r_lower = r.lower()
    assert "sunday" in r_lower


# ── compass / angle arithmetic ────────────────────────────────────────────


@xfail(strict=True, reason="math_cyclic: compass — turn degrees from direction")
def test_compass_turn(vy):
    """A ship is heading North. It turns 270 degrees clockwise.
    What direction is it heading now? → (0 + 270) mod 360 = 270 → West"""
    r = vy.answer(
        "A ship is heading North. It turns 270 degrees clockwise. "
        "What direction is it heading now?"
    )
    r_lower = r.lower()
    assert "west" in r_lower


# ── temperature with time (the motivating test) ──────────────────────────


@xfail(strict=True, reason="math_cyclic: time-point parsing — '6 AM' should not be standalone number")
def test_temperature_with_time(vy):
    """At 6 AM the temperature was negative 4 degrees celsius.
    By noon it rose by 9 degrees. What was the temperature at noon?
    → −4 + 9 = 5 (the '6' from '6 AM' must not enter count-chain)"""
    r = vy.answer(
        "At 6 AM the temperature was negative 4 degrees celsius. "
        "By noon it had risen by 9 degrees. "
        "What was the temperature at noon?"
    )
    assert "5" in r and "15" not in r


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
    # must compute slope=2, not just echo — check "find" section
    r_find = r_lower.split("find")[-1] if "find" in r_lower else ""
    assert "slope" in r_find and "2" in r_find and "no match" not in r_lower


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
    assert "yes" in r_lower or (r_lower.split("find")[-1].count("2") > 0)


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
    assert "0, 0, 1" in r or "(0,0,1)" in r


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
