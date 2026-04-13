"""test_arithmetic.py — count chains: add, subtract, dvandva, long chains,
multiplication via 'each', named entity totals, transfer.
"""

import pytest

xfail = pytest.mark.xfail


# ── two-sentence chains ───────────────────────────────────────────────────────


def test_add_two_sentences(vy):
    """3 birds + 2 more = 5"""
    r = vy.answer("3 birds sat on a tree. 2 more came. how many birds are there")
    assert "5" in r


def test_subtract_two_sentences(vy):
    """10 birds - 3 flew away = 7"""
    r = vy.answer("10 birds sat on a tree. 3 flew away. how many birds are left")
    assert "7" in r


def test_add_comma_boundary(vy):
    """Comma is viraam boundary: 10 birds, 3 flew away = 7"""
    r = vy.answer("10 birds sat on a tree, 3 flew away. how many birds are left")
    assert "7" in r


def test_number_before_noun(vy):
    """3 birds - 2 flew = 1"""
    r = vy.answer("3 birds sat on a tree. 2 flew away. how many birds are left")
    assert "1" in r


# ── three-sentence chains ─────────────────────────────────────────────────────


def test_three_sentence_chain(vy):
    """10 - 3 + 2 = 9"""
    r = vy.answer("10 birds sat on a tree. 3 flew away. 2 more came. how many birds are there")
    assert "9" in r


# ── long chains ───────────────────────────────────────────────────────────────


def test_long_chain_five_ops(vy):
    """10 - 2 + 5 - 3 + 1 = 11"""
    r = vy.answer(
        "there are 10 birds on a tree. 2 flew away. 5 more came. "
        "3 flew away. 1 more came. how many birds are there"
    )
    assert "11" in r


# ── dvandva: two numbers in one sentence ──────────────────────────────────────


def test_dvandva_cats_dogs(vy):
    """5 cats and 3 dogs → 8 animals"""
    r = vy.answer("there are 5 cats and 3 dogs. how many animals are there")
    assert "8" in r


def test_dvandva_basket_fruits(vy):
    """8 apples + 6 oranges → 14 fruits"""
    r = vy.answer("a basket has 8 apples and 6 oranges. how many fruits are there in total")
    assert "14" in r


def test_dvandva_three_kinds(vy):
    """3 + 4 + 5 = 12"""
    r = vy.answer("a bag has 3 apples, 4 oranges and 5 bananas. how many fruits are there")
    assert "12" in r


# ── named entity totals ───────────────────────────────────────────────────────


def test_named_total_two_boxes(vy):
    """box-A has 5, box-B has 3. total = 8"""
    r = vy.answer("box-A has 5 apples. box-B has 3 apples. how many apples are there in total")
    assert "8" in r


def test_named_gave_away(vy):
    """Maria had 10, gave 4. Maria has 6"""
    r = vy.answer("Maria had 10 apples. she gave 4 to Tom. how many apples does Maria have")
    assert "6" in r


# ── multiplication via 'each' ─────────────────────────────────────────────────


def test_multiplication_tables_legs(vy):
    """4 tables × 4 legs = 16"""
    r = vy.answer(
        "there are 4 tables. each table has 4 legs. how many legs are there in total"
    )
    assert "16" in r


def test_multiplication_bags_apples(vy):
    """3 bags × 5 apples = 15"""
    r = vy.answer("there are 3 bags. each bag has 5 apples. how many apples are there in total")
    assert "15" in r


def test_multiplication_children_coins(vy):
    """6 children × 4 coins = 24"""
    r = vy.answer("6 children each have 4 coins. how many coins are there in total")
    assert "24" in r


def test_distribution_per(vy):
    """'per' as distribution: 5 km per hour for 3 hours = 15"""
    r = vy.answer("a train travels at 60 km per hour for 2 hours. how far does it go")
    assert "120" in r


# ── physics + count ───────────────────────────────────────────────────────────


def test_physics_count_total_mass(vy):
    """3 balls each of mass 5 → total mass = 15"""
    r = vy.answer("there are 3 balls. each ball has mass 5. what is the total mass")
    assert "15" in r


# ── per-entity scoped count ───────────────────────────────────────────────────


def test_entity_scope_apples_sold(vy):
    """10 apples, 3 sold → 7 apples left (not 17)"""
    r = vy.answer("a shop has 10 apples. 3 apples were sold. how many apples are left")
    assert " 7 " in r or r.endswith(" 7") or "is 7" in r


@xfail(strict=True, reason="entity-scope: scope bug produces '77' (8 mixed into apple count); '7' and '8' only appear as intermediate values not as the stated answers")
def test_entity_scope_two_fruits(vy):
    """10 apples, 8 oranges, 3 apples sold → 7 apples, 8 oranges"""
    r = vy.answer(
        "a shop has 10 apples and 8 oranges. 3 apples were sold. how many of each are left"
    )
    assert "7" in r and "8" in r and "77" not in r


# ── multiple questions ────────────────────────────────────────────────────────


@xfail(strict=True, reason="multi-question: only answers last question with wrong value (8 not 7); '4' and '7' only appear as intermediate derivation values, not stated answers")
def test_multi_question_two_answers(vy):
    """Two questions in one paragraph → two answers"""
    r = vy.answer(
        "Tom has 7 apples. he gave 3 to Mary. Mary had 4 apples. "
        "how many apples does Tom have. how many apples does Mary have"
    )
    # must contain two separate answer sections (two "we find" or two answer lines)
    rl = r.lower()
    assert rl.count("we find") >= 2, f"expected two answers but got: {r}"


# ── complex: multi-step count chains ─────────────────────────────────────────


def test_three_op_chain(vy):
    """20 - 5 + 3 = 18"""
    r = vy.answer(
        "a bag has 20 apples. 5 were eaten. 3 more were added. how many apples are in the bag"
    )
    assert "18" in r


def test_multiplication_each(vy):
    """4 × 6 = 24 via 'each'"""
    r = vy.answer("there are 4 boxes. each box has 6 balls. how many balls are there")
    assert "24" in r
