"""test_xfail.py — the roadmap: features not yet built.

Every test here represents a structural capability that the pipeline
needs but doesn't have. They are grouped by gate (what must be built first).
When a gate is implemented, its tests should start passing and get moved
to the appropriate passing test file.

Gates:
  dvandva           — per-entity instance-map, dvandva collection
  inverse_math      — bound-vals / invert-math path
  sthita_viveka     — multi-slot entity assignment (gravitational, coulomb)
  motion_verb       — 'moves at' / 'moving at' → velocity signal
  compound_trigram  — three-word compounds (electric-field-strength)
  from_rest         — 'from rest' → initial-velocity=0
  total_compound    — 'total kinetic energy' compound resolution
  colour_classifier — colour words as entity discriminators
  article           — 'the electron' article transparency
  relative_velocity — relative-velocity concept
  compute_compare   — compute-then-compare viveka
  transitive        — transitive chain inference
  syllogism         — modus ponens / assertion chain
  arithmetic        — plain count addition/subtraction
  proportional      — proportional reasoning
  sentence_scope    — grade-sparsha: sentence-local binding via graded-ring partitioning
  dvandva_count     — multiple numbers in one sentence summed (5 cats and 3 dogs)
  entity_scope      — per-entity scoped count (paragraph answer)
  multi_question    — multiple questions in one paragraph (multiple answers)
  multiplication    — 'each' triggers multiply (4 tables × 4 legs)
  count_compare     — count then viveka comparison
  long_chain        — 4+ grade count chains with mixed operations
"""

import pytest

xfail = pytest.mark.xfail


# ── gate: dvandva ──────────────────────────────────────────────────────────────


@xfail(
    strict=True,
    reason="dvandva collection: consecutive asprista-sankhya under "
    "a satya concept should form a dvandva group",
)
def test_dvandva_collection(vy):
    g = vy.eval(
        f"fixpoint {vy.tl([['mass', 'satya', 'mass'], ['3', 'asprista-sankhya', '3.'], ['5', 'asprista-sankhya', '5.']])} avrti-refine"
    )
    dvandva = vy.all_triples(g, subj="mass", pred="dvandva")
    assert len(dvandva) == 2


@xfail(
    strict=True,
    reason="dvandva: total-momentum requires iterating over entity-owned momenta and summing",
)
def test_total_momentum_two(vy):
    r = vy.answer(
        "ball-A has mass 3 and velocity 4. ball-B has mass 2 and velocity 5. find total momentum"
    )
    assert "22" in r


@xfail(strict=True, reason="dvandva: same pattern, three entities")
def test_total_momentum_three(vy):
    r = vy.answer(
        "ball-A has mass 3 and velocity 4. ball-B has mass 2 and velocity 5. ball-C has mass 5 and velocity 6. find total momentum"
    )
    assert "52" in r


# ── gate: inverse_math ─────────────────────────────────────────────────────────


## inverse_ke_velocity, inverse_suvat_time, inverse_suvat_initial_velocity
## moved to test_physics.py — these now pass after invert-krama work


# ── gate: sthita_viveka ────────────────────────────────────────────────────────


@xfail(
    strict=True,
    reason="sthita-viveka: flat concept lookup can't assign two masses to mass1/mass2 slots",
)
def test_gravitational_force(vy):
    r = vy.answer(
        "particle-A has mass 5.972e24. particle-B has mass 7.34e22. find gravitational force given radius 3.84e8"
    )
    assert "1.98" in r


@xfail(
    strict=True, reason="sthita-viveka: same slot assignment gap for charge1/charge2"
)
def test_coulomb_force(vy):
    r = vy.answer(
        "particle-A has charge 1.6e-19. particle-B has charge 1.6e-19. find coulomb force given radius 1e-10"
    )
    assert "2.3" in r


# ── gate: motion_verb ──────────────────────────────────────────────────────────


@xfail(strict=True, reason="'moves at' not recognised as velocity signal")
def test_moves_at_velocity(vy):
    g = vy.bqg("a proton moves at 2e6 m/s")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert "velocity" in sankhya


@xfail(strict=True, reason="'moving at' not recognised as velocity signal")
def test_moving_at_ke(vy):
    r = vy.answer(
        "the electron has mass 9.109e-31 kg. it is moving at 1e6 m/s. find kinetic energy"
    )
    assert "4.5545e-19" in r


@xfail(strict=True, reason="motion verb 'moves' not in sandhi-viveka")
def test_proton_moves_momentum(vy):
    r = vy.answer("a proton moves at 2e6 m/s. it has mass 1.67e-27 kg. find momentum")
    assert "3.34e-21" in r


# ── gate: compound_trigram ─────────────────────────────────────────────────────


@xfail(
    strict=True,
    reason="sandhi-kosha only handles bigrams; electric-field-strength is a trigram",
)
def test_electric_field_strength(vy):
    g = vy.bqg("electric field strength is 0.1")
    assert vy.subjects(g, pred="satya") == ["electric-field-strength"]


@xfail(strict=True, reason="trigram: orbital-radius not in kosha")
def test_orbital_radius(vy):
    g = vy.bqg("find orbital radius")
    assert "orbital-radius" in vy.subjects(g, pred="satya")


# ── gate: from_rest ────────────────────────────────────────────────────────────


@xfail(strict=True, reason="'from rest' should mean initial-velocity=0")
def test_from_rest(vy):
    g = vy.bqg("accelerates from rest at 3 m/s2")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert sankhya.get("initial-velocity") in ("0", "0.")


@xfail(strict=True, reason="'from rest' confusion: 'rest' maps to count-remaining")
def test_car_from_rest_force(vy):
    r = vy.answer("a car of mass 1200 accelerates from rest at 3 m/s2. find force")
    assert "force =" in r and "no match" not in r


# ── gate: total_compound ───────────────────────────────────────────────────────


def test_total_ke_resolves(vy):
    g = vy.bqg("find total kinetic energy given mass 2 and velocity 3")
    satya = vy.subjects(g, pred="satya")
    assert "total-kinetic-energy" in satya or "kinetic-energy" in satya
    assert "count" not in satya


def test_total_momentum_resolves(vy):
    g = vy.bqg("find total momentum given mass 2 and velocity 3")
    assert "count" not in vy.subjects(g, pred="satya")


# ── gate: colour_classifier ───────────────────────────────────────────────────


def test_red_blue_distinct(vy):
    g = vy.bqg("a box has 5 red balls and 3 blue balls")
    sankhya = [
        [t[0], t[2]]
        for t in g
        if isinstance(t, list) and len(t) >= 3 and t[1] == "sankhya"
    ]
    subjects = [s[0] for s in sankhya]
    assert len(set(subjects)) >= 2


def test_red_blue_addition(vy):
    r = vy.answer("a box has 5 red balls and 3 blue balls. how many balls")
    assert "8" in r


# ── gate: article ──────────────────────────────────────────────────────────────


def test_article_before_entity(vy):
    r = vy.answer(
        "find kinetic energy of the electron given mass 9.109e-31 and velocity 1e6"
    )
    assert "4.5545e-19" in r


# ── gate: relative_velocity ────────────────────────────────────────────────────


@xfail(strict=True, reason="relative-velocity concept not in kosha")
def test_relative_velocity(vy):
    r = vy.answer(
        "ball-A has velocity 10. ball-B has velocity 3. find relative velocity of ball-A with respect to ball-B"
    )
    assert "7" in r


# ── gate: compute_compare ──────────────────────────────────────────────────────


@xfail(
    strict=True,
    reason="compute-then-compare not implemented: viveka compares raw values, not derived",
)
def test_which_more_ke_computed(vy):
    r = vy.answer(
        "ball-A has mass 2 and velocity 3. ball-B has mass 2 and velocity 5. which has more kinetic energy."
    )
    assert "9" in r and "25" in r


@xfail(strict=True, reason="compute-then-compare: two seeks needed")
def test_which_more_ke_two_seeks(vy):
    r = vy.answer(
        "ball-A has mass 2 and velocity 3. ball-B has mass 2 and velocity 5. which has more kinetic energy."
    )
    assert r.count("we seek") >= 2


# ── gate: transitive ──────────────────────────────────────────────────────────


@xfail(strict=True, reason="transitivity not implemented: needs graph walk chain")
def test_transitive_chain(vy):
    r = vy.answer("a is greater than b. b is greater than c. is a greater than c.")
    assert "yes" in r.lower()


@xfail(strict=True, reason="transitivity emission: two we-know strands")
def test_transitive_two_knows(vy):
    r = vy.answer("a is greater than b. b is greater than c. is a greater than c.")
    assert r.count("we know") >= 2


# ── gate: syllogism ───────────────────────────────────────────────────────────


@xfail(
    strict=True, reason="syllogism not implemented: needs assertion-bandha + chain walk"
)
def test_syllogism(vy):
    r = vy.answer("all cats are animals. all animals breathe. do cats breathe.")
    assert "yes" in r.lower()
    assert "cat" in r and "animal" in r and "breathe" in r


# ── gate: arithmetic ──────────────────────────────────────────────────────────


# ── gate: sentence_scope ───────────────────────────────────────────────────────
# These tests require deeper grade-sparsha capabilities beyond basic count:
# three-sentence chaining, or entity-scoped arithmetic + viveka comparison.


def test_count_three_sentence_chain(vy):
    """10 birds. 3 flew away. 2 came back. → 10 - 3 + 2 = 9."""
    r = vy.answer(
        "10 birds sat on a tree. 3 flew away. 2 more came. how many birds are there"
    )
    assert "9" in r


def test_viveka_after_count(vy):
    """box-A starts with 5 and gains 3 → 8. box-B has 6. which has more → box-A."""
    r = vy.answer(
        "box-A has 5 items. 3 more were added to box-A. box-B has 6 items. which has more items"
    )
    assert "box-A" in r or "box-a" in r.lower()


@xfail(strict=True, reason="distance = speed * time not in pipeline")
def test_distance_speed_time(vy):
    r = vy.answer("a train travels at 60 km per hour for 2 hours. how far does it go")
    assert "120" in r


@xfail(strict=True, reason="rectangle area mantra not in pipeline")
def test_area_rectangle(vy):
    """rectangle area mantra: A = length × width."""
    r = vy.answer("a rectangle has length 8 and width 5. find area")
    assert "40" in r


# ── gate: proportional ────────────────────────────────────────────────────────


# ── gate: dvandva_count ───────────────────────────────────────────────────────
# multiple numbers in one sentence — dvandva within a grade


def test_dvandva_count_cats_dogs(vy):
    """5 cats and 3 dogs → 8 animals."""
    r = vy.answer("there are 5 cats and 3 dogs. how many animals are there")
    assert "8" in r


def test_dvandva_count_basket(vy):
    """8 apples + 6 oranges → 14 fruits."""
    r = vy.answer(
        "a basket has 8 apples and 6 oranges. how many fruits are there in total"
    )
    assert "14" in r


def test_dvandva_count_three(vy):
    """3 + 4 + 5 = 12."""
    r = vy.answer(
        "a bag has 3 apples, 4 oranges and 5 bananas. how many fruits are there"
    )
    assert "12" in r


# ── gate: entity_scope ────────────────────────────────────────────────────────
# per-entity scoped count — paragraph answer


@xfail(strict=True, reason="entity_scope: per-entity count after subtraction")
def test_entity_scope_each_fruit(vy):
    """10 apples, 8 oranges, 3 apples sold → 7 apples, 8 oranges."""
    r = vy.answer(
        "a shop has 10 apples and 8 oranges. 3 apples were sold. how many of each are left"
    )
    assert "7" in r and "8" in r



@xfail(strict=True, reason="entity_scope: two-entity transfer")
def test_entity_scope_transfer(vy):
    """Tom: 7-3=4, Mary: 4+3=7."""
    r = vy.answer(
        "Tom has 7 apples. he gave 3 to Mary. Mary had 4 apples. how many apples does Tom have"
    )
    found = vy.strand(r, "we find")
    assert "4" in found


# ── gate: multi_question ──────────────────────────────────────────────────────
# multiple questions in one paragraph — multiple answers


@xfail(strict=True, reason="multi_question: two questions, two answers")
def test_multi_question_tom_mary(vy):
    """Tom gives to Mary → answer both."""
    r = vy.answer(
        "Tom has 7 apples. he gave 3 to Mary. Mary had 4 apples. "
        "how many apples does Tom have. how many apples does Mary have"
    )
    found = vy.strand(r, "we find")
    assert "4" in found and "7" in found


@xfail(strict=True, reason="multi_question: intermediate and final count")
def test_multi_question_intermediate(vy):
    """10 - 3 = 7 (first q), then +5 = 12 (second q)."""
    r = vy.answer(
        "there are 10 birds on a tree. 3 flew away. how many birds are left. "
        "5 more came. how many birds are there now"
    )
    found = vy.strand(r, "we find")
    assert "7" in found and "12" in found


# ── gate: multiplication ─────────────────────────────────────────────────────
# "each" triggers multiplication, not addition


@xfail(strict=True, reason="multiplication: 'each' should trigger multiply")
def test_multiplication_tables_legs(vy):
    """4 tables × 4 legs = 16."""
    r = vy.answer(
        "there are 4 tables. each table has 4 legs. how many legs are there in total"
    )
    assert "16" in r


@xfail(strict=True, reason="multiplication: bags with items")
def test_multiplication_bags(vy):
    """3 bags × 5 apples = 15."""
    r = vy.answer(
        "there are 3 bags. each bag has 5 apples. how many apples are there in total"
    )
    assert "15" in r


@xfail(strict=True, reason="multiplication: people with coins")
def test_multiplication_people(vy):
    """6 children × 4 coins = 24."""
    r = vy.answer(
        "6 children each have 4 coins. how many coins are there in total"
    )
    assert "24" in r


# ── gate: count_compare ──────────────────────────────────────────────────────
# count then viveka comparison


def test_count_compare_jars(vy):
    """jar-A=8, jar-B=12 → jar-B has more."""
    r = vy.answer(
        "jar-A has 8 marbles. jar-B has 12 marbles. which jar has more marbles"
    )
    assert "jar-B" in r or "jar-b" in r.lower()


def test_count_compare_after_change(vy):
    """box-A: 5+3=8, box-B: 6 → box-A has more."""
    r = vy.answer(
        "box-A has 5 items. 3 more were added to box-A. box-B has 6 items. which has more items"
    )
    assert "box-A" in r or "box-a" in r.lower()


# ── gate: long_chain ─────────────────────────────────────────────────────────
# 4+ grade chains with mixed operations


def test_long_chain_six_grades(vy):
    """10 - 2 + 5 - 3 + 1 = 11."""
    r = vy.answer(
        "there are 10 birds on a tree. 2 flew away. 5 more came. "
        "3 flew away. 1 more came. how many birds are there"
    )
    assert "11" in r


# ── gate: proportional ────────────────────────────────────────────────────────


@xfail(strict=True, reason="proportional reasoning: doubling velocity → 4x KE")
def test_proportional_ke_doubled(vy):
    r = vy.answer(
        "ball-A has mass 5 and velocity 10. ball-B has mass 5 and velocity 20. "
        "find kinetic energy of ball-A. find kinetic energy of ball-B"
    )
    assert "100" in r and "200" in r  # TODO: should be 250 and 1000
