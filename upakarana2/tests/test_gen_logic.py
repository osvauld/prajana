"""test_gen_logic.py — tests for generated logic and space-lift nodes.

Tests computation, inverse computation, and logic reasoning patterns
that exercise the 33 new nodes (11 logic + 22 space-lift).
"""

import re

import pytest

xfail = pytest.mark.xfail


# ── forward computation ──────────────────────────────────────────────────────


def test_ke_forward(vy):
    """mass=5 velocity=10 → KE=250"""
    r = vy.answer("mass is 5 and velocity is 10. find kinetic energy")
    assert "250" in r


def test_momentum_forward(vy):
    """mass=3 velocity=4 → p=12"""
    r = vy.answer("mass is 3 and velocity is 4. find momentum")
    assert "12" in r


def test_spring_force_forward(vy):
    """k=100 x=0.5 → F=50"""
    r = vy.answer("spring constant is 100 and displacement is 0.5. find spring force")
    assert "50" in r


def test_force_from_mass_accel(vy):
    """m=4 a=5 → F=20"""
    r = vy.answer("mass is 4 and acceleration is 5. find force")
    assert "20" in r


# ── inverse computation ──────────────────────────────────────────────────────


def test_inverse_mass_from_momentum(vy):
    """p=50 v=10 → m=5"""
    r = vy.answer("momentum is 50 and velocity is 10. find mass")
    assert "5" in r


def test_inverse_velocity_from_ke(vy):
    """KE=250 m=5 → v=10"""
    r = vy.answer("kinetic energy is 250 and mass is 5. find velocity")
    assert "10" in r


def test_inverse_mass_from_ke(vy):
    """KE=200 v=10 → m=4"""
    r = vy.answer("kinetic energy is 200 and velocity is 10. find mass")
    assert "4" in r


def test_inverse_accel_from_force(vy):
    """F=20 m=4 → a=5"""
    r = vy.answer("force is 20 and mass is 4. find acceleration")
    assert "5" in r


# ── zero / shunya ────────────────────────────────────────────────────────────


def test_at_rest_ke_zero(vy):
    """ball at rest, mass=5 → KE=0"""
    r = vy.answer("ball is at rest. mass is 5. find kinetic energy")
    assert "0" in r


def test_at_rest_momentum_zero(vy):
    """ball at rest, mass=5 → p=0"""
    r = vy.answer("ball is at rest. mass is 5. find momentum")
    assert "0" in r


# ── IS-A transitivity (uses transitive-swarupa node) ────────────────────────


@xfail(strict=True, reason="IS-A transitive: resolver checks terminal→terminal ('does animal inherit animal?'), not poodle→animal")
def test_transitive_two_hop(vy):
    """poodles→dogs→animals: is a poodle an animal"""
    r = vy.answer(
        "poodles are dogs. dogs are mammals. mammals are animals. "
        "is a poodle an animal"
    )
    rl = r.lower()
    yes_idx = rl.rfind("yes")
    assert yes_idx >= 0 and "poodle" in rl[yes_idx:]


def test_transitive_is_a_simple(vy):
    """a dog is an animal. a poodle is a dog. is a poodle an animal"""
    r = vy.answer("a dog is an animal. a poodle is a dog. is a poodle an animal")
    rl = r.lower()
    yes_idx = rl.rfind("yes")
    assert yes_idx >= 0 and "poodle" in rl[yes_idx:]


# ── modus tollens (uses modus-tollens node pattern) ──────────────────────────


def test_modus_tollens_ground_not_wet(vy):
    """if rain→wet, ground not wet → did not rain"""
    r = vy.answer(
        "if it rains the ground is wet. the ground is not wet. did it rain"
    )
    rl = r.lower()
    assert rl != "no match", "must be real inference, not 'no match'"
    assert re.search(r'\bno\b', rl) is not None
    assert "rain" in rl, "reasoning must reference rain"


# ── negation / double negation ───────────────────────────────────────────────


@xfail(strict=True, reason="negation+at-rest: response says 'no — velocity is absent' (checks velocity, not ball state); 'rest' only matches via 'at-rest' header")
def test_negation_not_moving_at_rest(vy):
    """the ball is not moving → ball is at rest"""
    r = vy.answer("the ball is not moving. is the ball at rest")
    assert "yes" in r.lower()


@xfail(strict=True, reason="double-negation: no cancellation logic; IS-A nonsense")
def test_double_negation_cancels(vy):
    """not-not-moving → moving"""
    r = vy.answer(
        "it is not true that the ball is not moving. is the ball moving"
    )
    rl = r.lower()
    assert "yes" in rl or "moving" in rl
    assert "is-a" not in rl, "must use negation logic, not IS-A"


# ── disjunctive syllogism ────────────────────────────────────────────────────


@xfail(strict=True, reason="disjunctive: 'blue' in pratijna not conclusion; no real elimination logic")
def test_disjunctive_red_or_blue(vy):
    """ball is red or blue. not red → blue"""
    r = vy.answer(
        "the ball is red or blue. the ball is not red. what color is the ball"
    )
    rl = r.lower()
    conclusion = rl.split(".")[-1] if "." in rl else rl
    assert "blue" in conclusion


# ── hypothetical syllogism (chained implication) ─────────────────────────────


@xfail(strict=True, reason="hypothetical syllogism chain not built in pipeline")
def test_hypothetical_chain(vy):
    """if A→B and B→C, given A → C"""
    r = vy.answer(
        "if temperature rises then ice melts. if ice melts then water appears. "
        "temperature rose. is water present"
    )
    rl = r.lower()
    # must show chain reasoning, not just echo question words
    assert "water" in rl, "must conclude about water"
    assert "is-a" not in rl, "must use implication logic, not IS-A"
    assert "we know" in rl or "we see" in rl, f"must show chain reasoning, not just echo: {r}"


# ── quantifier reasoning ────────────────────────────────────────────────────


@xfail(strict=True, reason="IS-A universal: response says 'sparrow has bird' (IS-A confirmed), not 'sparrow can fly'")
def test_universal_inheritance(vy):
    """all birds fly + sparrow is bird → sparrow flies"""
    r = vy.answer(
        "all birds can fly. a sparrow is a bird. can a sparrow fly"
    )
    rl = r.lower()
    assert re.search(r'\byes\b', rl) is not None and "fly" in rl


@xfail(strict=True, reason="existential quantifier reasoning not built in pipeline")
def test_existential_some(vy):
    """some metals are magnetic. is there a magnetic metal"""
    r = vy.answer("some metals are magnetic. is there a magnetic metal")
    assert "yes" in r.lower()


# ── graph structure: logic nodes connected ───────────────────────────────────


def test_modus_tollens_is_pratipaksha_of_ponens(vy):
    """modus-tollens and modus-ponens are inverses"""
    r = vy.eval('walk "modus-tollens" "pratipaksha"')
    assert "modus-ponens" in r


def test_de_morgan_connects_and_or(vy):
    """de-morgan-and links conjunction↔disjunction"""
    r = vy.eval('walk "de-morgan-and" "janya"')
    assert "conjunction" in r
    r2 = vy.eval('walk "de-morgan-and" "abheda"')
    assert "disjunction" in r2


def test_existential_universal_pratipaksha(vy):
    """existential and universal quantifiers are inverses"""
    r = vy.eval('walk "existential-quantifier" "pratipaksha"')
    assert "universal-quantifier" in r


def test_complex_log_exp_pratipaksha(vy):
    """complex-logarithm and complex-exponential are inverses"""
    r = vy.eval('walk "complex-logarithm" "pratipaksha"')
    assert "complex-exponential" in r


def test_mat_inverse_self_pratipaksha(vy):
    """mat-inverse is its own inverse"""
    r = vy.eval('walk "mat-inverse" "pratipaksha"')
    assert "mat-inverse" in r


def test_vec_sub_add_pratipaksha(vy):
    """vec-subtraction and vec-add are inverses"""
    r = vy.eval('walk "vec-subtraction" "pratipaksha"')
    assert "vec-add" in r


def test_set_membership_has_element(vy):
    """set-membership yukta includes element and set"""
    r = vy.eval('walk "set-membership" "yukta"')
    assert "element" in r
    assert "set" in r


def test_logic_varga_has_new_inference_rules(vy):
    """inference rules are reachable from logic-varga"""
    r = vy.eval('walk-in "inference" "swarupa"')
    assert "modus-tollens" in r
    assert "hypothetical-syllogism" in r
    assert "contrapositive" in r


# ── eval-typed: graph-native computation ─────────────────────────────────────
# The graph defines the algebra. eval-typed reads shabda metadata
# (krama-input, per-element, fold, krama) to decide how to compute.


class TestVectorOps:
    """Vector operations — graph drives the computation."""

    def test_vec_norm(self, vy):
        """‖[3,4]‖ = 5"""
        r = vy.eval('(call-tantra "eval-typed" ["vec-norm", [3, 4], []])')
        assert r == 5

    def test_vec_norm_3d(self, vy):
        """‖[1,2,2]‖ = 3"""
        r = vy.eval('(call-tantra "eval-typed" ["vec-norm", [1, 2, 2], []])')
        assert r == 3

    def test_vec_add(self, vy):
        """[1,2,3] + [4,5,6] = [5,7,9]"""
        r = vy.eval('(call-tantra "eval-typed" ["vec-add", [1, 2, 3], [4, 5, 6]])')
        assert r == [5, 7, 9]

    def test_vec_dot(self, vy):
        """[1,2,3] · [4,5,6] = 32"""
        r = vy.eval('(call-tantra "eval-typed" ["vec-dot", [1, 2, 3], [4, 5, 6]])')
        assert r == 32

    def test_vec_neg(self, vy):
        """-[3,-4] = [-3,4]"""
        r = vy.eval('(call-tantra "eval-typed" ["vec-neg", [3, -4], []])')
        assert r == [-3, 4]

    def test_vec_subtraction(self, vy):
        """[10,20] - [3,5] = [7,15]"""
        r = vy.eval('(call-tantra "eval-typed" ["vec-subtraction", [10, 20], [3, 5]])')
        assert r == [7, 15]


class TestSetOps:
    """Set operations — graph-native membership and subset."""

    def test_membership_true(self, vy):
        """3 ∈ {1,2,3}"""
        r = vy.eval('(call-tantra "eval-typed" ["set-membership", 3, [1, 2, 3]])')
        assert r is True

    def test_membership_false(self, vy):
        """5 ∉ {1,2,3}"""
        r = vy.eval('(call-tantra "eval-typed" ["set-membership", 5, [1, 2, 3]])')
        assert r is False

    def test_subset_true(self, vy):
        """{1,2} ⊆ {1,2,3,4}"""
        r = vy.eval('(call-tantra "eval-typed" ["set-subset", [1, 2], [1, 2, 3, 4]])')
        assert r is True

    def test_subset_false(self, vy):
        """{1,5} ⊄ {1,2,3,4}"""
        r = vy.eval('(call-tantra "eval-typed" ["set-subset", [1, 5], [1, 2, 3, 4]])')
        assert r is False

    def test_membership_zero(self, vy):
        """0 ∈ {0,1,2}"""
        r = vy.eval('(call-tantra "eval-typed" ["set-membership", 0, [0, 1, 2]])')
        assert r is True


# ── natural language: typed operations ───────────────────────────────────────
# The pipeline detects type words (set, vector) + operations from the graph,
# collects numbers into lists, and dispatches to eval-typed.


class TestNLSetOps:
    """Set operations via natural language."""

    def test_belong_yes(self, vy):
        r = vy.answer("does 3 belong to set 1 2 3")
        assert "yes" in r.lower()

    def test_belong_no(self, vy):
        r = vy.answer("does 5 belong to set 1 2 3")
        assert "no" in r.lower()


class TestNLVectorOps:
    """Vector operations via natural language."""

    @xfail(strict=True, reason="NL vector norm dispatch not wired")
    def test_norm(self, vy):
        r = vy.answer("find the norm of vector 3 4")
        assert "5" in r

    def test_add(self, vy):
        r = vy.answer("add vectors 1 2 3 and 4 5 6")
        assert "5" in r and "7" in r and "9" in r

    @xfail(strict=True, reason="NL vector dot-product dispatch not wired")
    def test_dot(self, vy):
        r = vy.answer("dot product of vector 1 2 3 and 4 5 6")
        assert "32" in r
