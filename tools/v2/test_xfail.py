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


@xfail(
    strict=True,
    reason="bound-vals returns [] on fixpoint graph — invert-math cannot fire",
)
def test_inverse_ke_velocity(vy):
    """KE=50, m=2 → v≈7.07"""
    r = vy.answer("kinetic energy is 50 and mass is 2. find velocity")
    assert "7.07" in r


@xfail(strict=True, reason="bound-vals issue — same root cause")
def test_inverse_suvat_time(vy):
    """u=0, a=5, v=20 → t=4"""
    r = vy.answer(
        "initial velocity is 0. acceleration is 5. final velocity is 20. find time"
    )
    assert "4" in r


@xfail(strict=True, reason="bound-vals issue — same root cause")
def test_inverse_suvat_initial_velocity(vy):
    """v=30, a=5, t=4 → u=10"""
    r = vy.answer(
        "final velocity is 30. acceleration is 5. time is 4. find initial velocity"
    )
    assert "10" in r


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


@xfail(strict=True, reason="'total kinetic energy': avastha fires before kosha bigram")
def test_total_ke_resolves(vy):
    g = vy.bqg("find total kinetic energy given mass 2 and velocity 3")
    satya = vy.subjects(g, pred="satya")
    assert "total-kinetic-energy" in satya or "kinetic-energy" in satya
    assert "count" not in satya


@xfail(strict=True, reason="'total' resolves to count via shabda alias")
def test_total_momentum_resolves(vy):
    g = vy.bqg("find total momentum given mass 2 and velocity 3")
    assert "count" not in vy.subjects(g, pred="satya")


# ── gate: colour_classifier ───────────────────────────────────────────────────


@xfail(strict=True, reason="colour classifiers not treated as entity discriminators")
def test_red_blue_distinct(vy):
    g = vy.bqg("a box has 5 red balls and 3 blue balls")
    sankhya = [
        [t[0], t[2]]
        for t in g
        if isinstance(t, list) and len(t) >= 3 and t[1] == "sankhya"
    ]
    subjects = [s[0] for s in sankhya]
    assert len(set(subjects)) >= 2


@xfail(strict=True, reason="colour classifiers — full pipeline addition")
def test_red_blue_addition(vy):
    r = vy.answer("a box has 5 red balls and 3 blue balls. how many balls")
    assert "8" in r


# ── gate: article ──────────────────────────────────────────────────────────────


@xfail(strict=True, reason="'the' breaks scope detection: 'of the electron' fails")
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


@xfail(strict=True, reason="plain count addition not in pipeline")
def test_count_addition(vy):
    r = vy.answer(
        "3 birds sat on a tree. 2 more came. how many birds are there in total"
    )
    assert "5" in r


@xfail(strict=True, reason="plain count subtraction not in pipeline")
def test_count_subtraction(vy):
    r = vy.answer("10 birds sat on a tree. 3 flew away. how many birds are left")
    assert "7" in r


@xfail(strict=True, reason="distance = speed * time not in pipeline")
def test_distance_speed_time(vy):
    r = vy.answer("a train travels at 60 km per hour for 2 hours. how far does it go")
    assert "120" in r


@xfail(strict=True, reason="area = length * width not in pipeline")
def test_area_rectangle(vy):
    r = vy.answer("a rectangle has length 8 and width 5. find area")
    assert "40" in r


# ── gate: proportional ────────────────────────────────────────────────────────


@xfail(strict=True, reason="proportional reasoning: doubling velocity → 4x KE")
def test_proportional_ke_doubled(vy):
    r = vy.answer(
        "ball-A has mass 5 and velocity 10. ball-B has mass 5 and velocity 20. "
        "find kinetic energy of ball-A. find kinetic energy of ball-B"
    )
    assert "100" in r and "200" in r  # TODO: should be 250 and 1000
