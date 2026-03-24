"""test_edges.py — verify newly grounded relation dimensions.

These 15 sangati nodes were created to ground visheshanam suffixes that
were previously silently dropped by om_parser.ml. With the nodes +
ring entries in place, 188 edges become visible.

Three test levels:
  1. Graph: does the edge exist?
  2. Walk: can we traverse the dimension?
  3. Pipeline: can natural language trigger it? (xfail until tantras support it)
"""

import pytest

xfail = pytest.mark.xfail


# ── level 1: graph structure — edge exists ───────────────────────────────────


class TestJanakaEdges:
    """janaka (generator) — 69 edges."""

    def test_vector_space_generates_subspace(self, vy):
        r = vy.eval('walk "vector-space" "janaka"')
        assert "subspace" in r

    def test_aarambham_generates_krama(self, vy):
        r = vy.eval('walk "aarambham" "janaka"')
        assert "krama" in r


class TestRahitaEdges:
    """rahita (devoid-of) — 46 edges."""

    def test_jada_without_iccha(self, vy):
        r = vy.eval('walk "jada" "rahita"')
        assert "iccha" in r

    def test_jada_without_karma(self, vy):
        r = vy.eval('walk "jada" "rahita"')
        assert "karma" in r

    def test_primitive_type_without_vrnda(self, vy):
        r = vy.eval('walk "primitive-type" "rahita"')
        assert "vrnda" in r

    def test_nil_without_shunya(self, vy):
        r = vy.eval('walk "nil" "rahita"')
        assert "shunya" in r


class TestLakshanaEdges:
    """lakshana (characteristic/property-of) — 41 edges."""

    def test_associativity_is_property_of_algebra(self, vy):
        r = vy.eval('walk "associativity" "lakshana"')
        assert "algebra-varga" in r

    def test_commutativity_is_property_of_numbers(self, vy):
        r = vy.eval('walk "commutativity" "lakshana"')
        assert "number-varga" in r

    def test_capacity_is_property_of_information(self, vy):
        r = vy.eval('walk "capacity" "lakshana"')
        assert "information-varga" in r


class TestPoorvaEdges:
    """poorva (before/prior) — 18 edges."""

    def test_aarambham_preceded_by_abhava(self, vy):
        r = vy.eval('walk "aarambham" "poorva"')
        assert "abhava" in r

    def test_purnapara_preceded_by_shunya(self, vy):
        r = vy.eval('walk "purnapara" "poorva"')
        assert "shunya" in r


# ── level 2: walk queries — traversal works ──────────────────────────────────


class TestLakshanaWalk:
    """walk-in lakshana: 'what are the properties of X?'"""

    def test_algebra_properties(self, vy):
        r = vy.eval('walk-in "algebra-varga" "lakshana"')
        assert isinstance(r, list)
        assert len(r) >= 5  # associativity, commutativity, distributivity, ...
        assert "associativity" in r
        assert "commutativity" in r

    def test_number_properties(self, vy):
        r = vy.eval('walk-in "number-varga" "lakshana"')
        assert isinstance(r, list)
        assert "cardinality" in r

    def test_set_properties(self, vy):
        r = vy.eval('walk-in "set-varga" "lakshana"')
        assert isinstance(r, list)
        assert "cardinality" in r


class TestRahitaWalk:
    """walk-in rahita: 'what lacks X?'"""

    def test_who_lacks_iccha(self, vy):
        """Multiple nodes are devoid-of-iccha."""
        r = vy.eval('walk-in "iccha" "rahita"')
        assert isinstance(r, list)
        assert "jada" in r

    def test_who_lacks_vrnda(self, vy):
        r = vy.eval('walk-in "vrnda" "rahita"')
        assert isinstance(r, list)
        assert "primitive-type" in r


class TestJanakaWalk:
    """walk janaka: 'what does X generate?'"""

    def test_vector_space_generators(self, vy):
        r = vy.eval('walk "vector-space" "janaka"')
        assert isinstance(r, list)
        assert len(r) >= 2  # subspace, orthogonal


class TestKarmaWalk:
    """walk-in karma: 'what operations belong to class X?'"""

    def test_algebra_operations(self, vy):
        r = vy.eval('walk-in "algebra-varga" "karma"')
        assert isinstance(r, list)
        assert len(r) >= 5
        # morphism, composition, function, etc.

    def test_calculus_operations(self, vy):
        r = vy.eval('walk-in "calculus-varga" "karma"')
        assert isinstance(r, list)
        assert "derivative" in r


# ── level 3: pipeline — natural language triggers edge walk ──────────────────
# These require tantras that walk the new dimensions.
# Currently xfail until the tantras are built.


class TestKarmaClassification:
    """karma: operation belongs to its varga — enables op discovery."""

    def test_addition_is_number_op(self, vy):
        r = vy.eval('walk "addition" "karma"')
        assert "number-varga" in r

    def test_derivative_is_calculus_op(self, vy):
        r = vy.eval('walk "derivative" "karma"')
        assert "calculus-varga" in r

    def test_morphism_is_algebra_op(self, vy):
        r = vy.eval('walk "morphism" "karma"')
        assert "algebra-varga" in r

    def test_shortest_path_is_graph_op(self, vy):
        r = vy.eval('walk "shortest-path" "karma"')
        assert "graph-varga" in r

    def test_set_union_is_set_op(self, vy):
        r = vy.eval('walk "set-union" "karma"')
        assert "set-varga" in r

    def test_bayes_is_probability_op(self, vy):
        r = vy.eval('walk "bayes" "karma"')
        assert "probability-varga" in r


class TestKarmaDiscovery:
    """walk-in karma: discover all ops in a class — enables inverse search."""

    def test_number_ops_include_basics(self, vy):
        r = vy.eval('walk-in "number-varga" "karma"')
        for op in ["addition", "subtraction", "multiplication", "division"]:
            assert op in r, f"{op} missing from number-varga karma"

    def test_number_ops_include_trig(self, vy):
        r = vy.eval('walk-in "number-varga" "karma"')
        for op in ["sine", "cosine", "arcsine"]:
            assert op in r, f"{op} missing from number-varga karma"

    def test_calculus_ops(self, vy):
        r = vy.eval('walk-in "calculus-varga" "karma"')
        assert "derivative" in r
        assert "antiderivative" in r

    def test_geometry_ops_include_linear_algebra(self, vy):
        r = vy.eval('walk-in "geometry-varga" "karma"')
        for op in ["dot-product", "cross-product", "determinant"]:
            assert op in r, f"{op} missing from geometry-varga karma"


class TestLakshanaReasoning:
    """lakshana: verify structural properties of math classes."""

    def test_algebra_has_associativity(self, vy):
        r = vy.eval('walk-in "algebra-varga" "lakshana"')
        assert "associativity" in r

    def test_algebra_has_closure(self, vy):
        r = vy.eval('walk-in "algebra-varga" "lakshana"')
        assert "closure" in r

    def test_algebra_has_identity(self, vy):
        r = vy.eval('walk-in "algebra-varga" "lakshana"')
        assert "identity-element" in r

    def test_algebra_has_inverse_element(self, vy):
        r = vy.eval('walk-in "algebra-varga" "lakshana"')
        assert "inverse-element" in r

    def test_commutativity_shared(self, vy):
        """commutativity belongs to algebra, number, AND set vargas."""
        r = vy.eval('walk "commutativity" "lakshana"')
        assert "algebra-varga" in r
        assert "number-varga" in r


class TestInverseOps:
    """pratipaksha on math ops — used by invert-math tantra."""

    def test_addition_subtraction(self, vy):
        r = vy.eval('walk "addition" "pratipaksha"')
        assert "subtraction" in r

    def test_multiplication_division(self, vy):
        r = vy.eval('walk "multiplication" "pratipaksha"')
        assert "division" in r

    def test_derivative_antiderivative(self, vy):
        r = vy.eval('walk "derivative" "pratipaksha"')
        assert "antiderivative" in r


# ── level 3: inverse math — pratipaksha + karma for formula inversion ────────


class TestInversePipeline:
    """End-to-end inverse problems: given output + partial inputs, find missing."""

    def test_momentum_inverse_mass(self, vy):
        """p=50, v=10 → m=p/v=5. Simple division inverse."""
        r = vy.answer("momentum is 50 and velocity is 10. find mass")
        assert "5" in r

    def test_force_inverse_acceleration(self, vy):
        """F=50, m=10 → a=F/m=5. Simple division inverse."""
        r = vy.answer("force is 50 and mass is 10. find acceleration")
        assert "5" in r

    def test_ke_inverse_velocity(self, vy):
        """KE=250, m=5 → v=sqrt(2*KE/m)=10. Multi-step inversion."""
        r = vy.answer("kinetic energy is 250 and mass is 5. find velocity")
        assert "10" in r

    def test_ke_inverse_mass(self, vy):
        """KE=200, v=10 → m=2*KE/v²=4."""
        r = vy.answer("kinetic energy is 200 and velocity is 10. find mass")
        assert "4" in r


class TestInverseGraphStructure:
    """Verify the graph has enough info for an inverter to work."""

    def test_ke_mantra_knows_inputs_and_output(self, vy):
        janya = vy.eval('walk "kinetic-energy-mantra" "janya"')
        phala = vy.eval('walk "kinetic-energy-mantra" "phala"')
        assert "mass" in janya
        assert "velocity" in janya
        assert "kinetic-energy" in phala

    def test_half_double_inverse_pair(self, vy):
        assert "double" in vy.eval('walk "half" "pratipaksha"')
        assert "half" in vy.eval('walk "double" "pratipaksha"')

    def test_square_sqrt_inverse_pair(self, vy):
        assert "square-root" in vy.eval('walk "square" "pratipaksha"')
        assert "square" in vy.eval('walk "square-root" "pratipaksha"')

    def test_mul_div_inverse_pair(self, vy):
        assert "division" in vy.eval('walk "multiplication" "pratipaksha"')

    def test_all_inverse_ops_in_number_varga(self, vy):
        """All inverse pairs share number-varga — they compose."""
        for op in ["half", "double", "square", "square-root",
                    "multiplication", "division"]:
            karma = vy.eval(f'walk "{op}" "karma"')
            assert "number-varga" in karma, f"{op} not in number-varga"


# ── level 3: lakshana for entity classification + op validation ──────────────


class TestLakshanaEntityClassification:
    """lakshana separates operations from properties — entity identification."""

    def test_property_has_lakshana(self, vy):
        """associativity IS a property — it has lakshana edges."""
        assert len(vy.eval('walk "associativity" "lakshana"')) > 0

    def test_operation_has_no_lakshana(self, vy):
        """addition is NOT a property — no lakshana edges."""
        assert len(vy.eval('walk "addition" "lakshana"')) == 0

    def test_karma_vs_lakshana_cleanly_separates(self, vy):
        """Operations have karma. Properties have lakshana. Never both."""
        # Operation
        assert len(vy.eval('walk "addition" "karma"')) > 0
        assert len(vy.eval('walk "addition" "lakshana"')) == 0
        # Property
        assert len(vy.eval('walk "commutativity" "lakshana"')) > 0
        assert len(vy.eval('walk "commutativity" "karma"')) == 0

    def test_closure_implies_domain_closed(self, vy):
        """closure as lakshana of algebra-varga → ops produce same-domain results."""
        assert "algebra-varga" in vy.eval('walk "closure" "lakshana"')

    def test_inverse_element_implies_invertible(self, vy):
        """inverse-element as lakshana → ops in that varga can be inverted.
        This is the structural guarantee for invert-math."""
        assert "algebra-varga" in vy.eval('walk "inverse-element" "lakshana"')


class TestLakshanaOpValidation:
    """lakshana enables: 'can I safely transform this expression?'"""

    def test_addition_in_commutative_varga(self, vy):
        """addition is in number-varga which has commutativity →
        a+b = b+a is safe."""
        assert "number-varga" in vy.eval('walk "addition" "karma"')
        assert "commutativity" in vy.eval('walk-in "number-varga" "lakshana"')

    def test_subtraction_has_inverse(self, vy):
        """subtraction → pratipaksha → addition. The inverter can undo it."""
        assert "addition" in vy.eval('walk "subtraction" "pratipaksha"')

    def test_varga_with_associativity(self, vy):
        """associativity lakshana → (a op b) op c = a op (b op c).
        Enables regrouping in multi-step formulas."""
        assert "associativity" in vy.eval('walk-in "algebra-varga" "lakshana"')
        assert "associativity" in vy.eval('walk-in "number-varga" "lakshana"')


# ── level 3: graph self-reasoning — what the graph derives about a problem ────
# These test whether the graph contains enough structure for a tantra to
# REASON about a problem — not solve it, but plan the solution.


class TestGraphReasoningInverse:
    """Can the graph figure out HOW to invert a formula?
    Given a mantra and the sought quantity, derive the inversion plan."""

    def test_find_mantra_for_sought_quantity(self, vy):
        """'find velocity' → which mantras produce velocity?
        walk-in velocity phala → discovers mantra candidates."""
        r = vy.eval('walk-in "velocity" "phala"')
        assert "velocity-mantra" in r

    def test_mantra_missing_input(self, vy):
        """Given KE mantra, inputs are [mass, velocity]. If we have mass,
        the missing input is velocity — that's what we solve for."""
        janya = vy.eval('walk "kinetic-energy-mantra" "janya"')
        have = ["mass"]
        missing = [j for j in janya if j not in have]
        assert missing == ["velocity"]

    def test_inverse_plan_via_pratipaksha_chain(self, vy):
        """For KE = half(mul(mass, square(velocity))):
        To isolate velocity, reverse the chain:
          1. half → pratipaksha → double
          2. mul(mass, _) → pratipaksha → division(_, mass)
          3. square → pratipaksha → square-root
        The graph has all three inverse pairs."""
        assert "double" in vy.eval('walk "half" "pratipaksha"')
        assert "division" in vy.eval('walk "multiplication" "pratipaksha"')
        assert "square-root" in vy.eval('walk "square" "pratipaksha"')

    def test_all_krama_ops_have_inverses(self, vy):
        """Every op used in physics mantras should have a pratipaksha.
        If an op has no inverse, the formula can't be inverted through it."""
        krama_ops = ["half", "double", "square", "square-root",
                     "multiplication", "division", "addition", "subtraction"]
        for op in krama_ops:
            inv = vy.eval(f'walk "{op}" "pratipaksha"')
            assert len(inv) > 0, f"{op} has no pratipaksha — uninvertible"

    def test_inverse_ops_share_varga(self, vy):
        """An op and its inverse must be in the same varga for composition
        to be valid. karma dimension confirms this."""
        pairs = [("half", "double"), ("square", "square-root"),
                 ("multiplication", "division"), ("addition", "subtraction")]
        for fwd, rev in pairs:
            fwd_v = vy.eval(f'walk "{fwd}" "karma"')
            rev_v = vy.eval(f'walk "{rev}" "karma"')
            assert set(fwd_v) & set(rev_v), f"{fwd}/{rev} not in same varga"


class TestGraphReasoningClassification:
    """Can the graph classify a concept to decide how to handle it?"""

    def test_is_it_a_quantity_or_operation(self, vy):
        """mass has no karma edges → it's a quantity, not an operation.
        addition has karma → it's an operation."""
        assert len(vy.eval('walk "mass" "karma"')) == 0  # quantity
        assert len(vy.eval('walk "addition" "karma"')) > 0  # operation

    def test_is_it_computable(self, vy):
        """A concept is computable if some mantra has it as phala."""
        # kinetic-energy is computable — KE mantra outputs it
        r = vy.eval('walk-in "kinetic-energy" "phala"')
        assert "kinetic-energy-mantra" in r
        # time is a base quantity — no physics mantra outputs it
        r2 = vy.eval('walk-in "time" "phala"')
        assert not any("mantra" in str(x) for x in r2)

    def test_what_do_i_need_to_compute_it(self, vy):
        """To compute kinetic-energy: find its mantra, walk janya → [mass, velocity]."""
        mantras = vy.eval('walk-in "kinetic-energy" "phala"')
        assert "kinetic-energy-mantra" in mantras
        inputs = vy.eval('walk "kinetic-energy-mantra" "janya"')
        assert "mass" in inputs
        assert "velocity" in inputs

    def test_what_else_can_i_compute_from_same_inputs(self, vy):
        """Given mass and velocity, what else can I compute?
        walk-in mass janya → mantras that use mass as input.
        Intersect with mantras that use velocity."""
        mass_mantras = set(vy.eval('walk-in "mass" "janya"'))
        vel_mantras = set(vy.eval('walk-in "velocity" "janya"'))
        both = mass_mantras & vel_mantras
        # Should include KE and momentum at minimum
        assert "kinetic-energy-mantra" in both
        assert "momentum-mantra" in both


class TestGraphReasoningRobotics:
    """3-DOF robot arm: torque, angle, angular-velocity, moment-of-inertia."""

    def test_torque_mantra_exists(self, vy):
        """torque = moment-of-inertia * angular-acceleration."""
        r = vy.eval('walk-in "torque" "phala"')
        assert "torque-mantra" in r

    def test_torque_inputs(self, vy):
        """Torque mantra needs moment-of-inertia and angular-acceleration."""
        janya = vy.eval('walk "torque-mantra" "janya"')
        # moment-of-inertia and angular-acceleration should be inputs
        assert "moment-of-inertia" in janya or "angular-acceleration" in janya

    def test_angular_velocity_mantra_exists(self, vy):
        r = vy.eval('walk-in "angular-velocity" "phala"')
        assert "angular-velocity-mantra" in r

    def test_angular_chain(self, vy):
        """angular-acceleration → torque: the kinematic chain."""
        # angular-acceleration is janya (input) to torque-mantra
        assert "torque-mantra" in vy.eval('walk-in "angular-acceleration" "janya"')
        # angular-acceleration is kramanusara (derived from) angular-velocity
        assert "angular-velocity" in vy.eval('walk "angular-acceleration" "kramanusara"')

    def test_moment_of_inertia_in_rotational_varga(self, vy):
        """moment-of-inertia is in the rotational motion domain."""
        r = vy.eval('walk "moment-of-inertia" "vishesa"')
        assert any("rotational" in str(v) for v in r)

    @xfail(strict=True, reason="robotics: no 3DOF arm tantra yet")
    def test_3dof_arm_torque(self, vy):
        """3-DOF arm: given moment-of-inertia=2 and angular-acceleration=5,
        find torque. τ = I·α = 10."""
        r = vy.answer(
            "moment of inertia is 2 and angular acceleration is 5. find torque"
        )
        assert "10" in r


class TestGraphReasoningPureMath:
    """Pure math: the graph classifies mathematical objects."""

    def test_what_kind_of_thing_is_a_group(self, vy):
        """group → swarupa → tells us what kind of structure it is."""
        r = vy.eval('walk "group" "swarupa"')
        assert len(r) > 0  # has a classification

    def test_what_operations_does_set_theory_have(self, vy):
        """set-varga karma gives the full operation inventory."""
        r = vy.eval('walk-in "set-varga" "karma"')
        assert "set-union" in r
        assert "set-intersection" in r
        assert "set-difference" in r

    def test_set_operations_are_closed(self, vy):
        """set-varga has closure as lakshana → operations produce sets."""
        assert "closure" in vy.eval('walk-in "set-varga" "lakshana"')

    def test_distributivity_connects_two_vargas(self, vy):
        """distributivity is a property relating two operations.
        It's a lakshana of algebra-varga."""
        r = vy.eval('walk "distributivity" "lakshana"')
        assert "algebra-varga" in r

    def test_graph_ops_inventory(self, vy):
        """graph-varga has traversal operations."""
        r = vy.eval('walk-in "graph-varga" "karma"')
        assert "shortest-path" in r
        assert "breadth-first" in r

    def test_probability_ops(self, vy):
        """probability-varga operations include bayes."""
        r = vy.eval('walk-in "probability-varga" "karma"')
        assert "bayes" in r
        assert "marginalisation" in r


# ── level 3: pipeline xfails — NL triggers edge walk ─────────────────────────


@xfail(strict=True, reason="lakshana_query: no tantra walks lakshana yet")
def test_what_are_properties_of_algebra(vy):
    r = vy.answer("what are the properties of algebra")
    assert "associativity" in r or "commutativity" in r


@xfail(strict=True, reason="rahita_query: no tantra walks rahita yet")
def test_what_is_jada_without(vy):
    r = vy.answer("what is jada devoid of")
    assert "iccha" in r or "karma" in r


@xfail(strict=True, reason="janaka_query: no tantra walks janaka yet")
def test_what_does_vector_space_generate(vy):
    r = vy.answer("what does a vector space generate")
    assert "subspace" in r


@xfail(strict=True, reason="karma_query: no tantra walks karma yet")
def test_what_operations_in_calculus(vy):
    r = vy.answer("what operations belong to calculus")
    assert "derivative" in r
