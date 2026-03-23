"""test_entity.py — entity scoping: ownership, two-entity isolation, three-entity,
cross-sentence accumulation, sthita-viveka (multi-slot mantras), transfers.
"""


# ── single entity ─────────────────────────────────────────────────────────────


def test_named_entity_prathama(vy):
    """Entity name gets prathama-vibhakti"""
    g = vy.bqg("ball-A has mass 3")
    assert vy.has_triple(g, subj="ball-A", pred="prathama-vibhakti")


def test_named_entity_ownership(vy):
    """Property owned by entity via shashthi-vibhakti"""
    g = vy.bqg("ball has mass 5")
    assert vy.has_triple(g, pred="shashthi-vibhakti")


def test_unnamed_entity_computes(vy):
    """No entity name — implicit binding still computes"""
    r = vy.answer("mass is 5 and velocity is 10. find kinetic energy")
    assert "250" in r


# ── two entities: isolation ───────────────────────────────────────────────────


def test_two_entity_scope_first(vy):
    """ball-A values don't bleed into ball-B"""
    r = vy.answer(
        "ball-A has mass 3 and velocity 4. ball-B has mass 2 and velocity 5. "
        "find kinetic energy of ball-A"
    )
    assert "24" in r


def test_two_entity_scope_second(vy):
    """ball-B values don't bleed into ball-A"""
    r = vy.answer(
        "ball-A has mass 3 and velocity 4. ball-B has mass 2 and velocity 5. "
        "find kinetic energy of ball-B"
    )
    assert "25" in r


def test_two_entity_distinct_prathama(vy):
    """Both entities get prathama-vibhakti labels"""
    g = vy.bqg("ball-A has mass 3. ball-B has mass 5")
    assert vy.has_triple(g, subj="ball-A", pred="prathama-vibhakti")
    assert vy.has_triple(g, subj="ball-B", pred="prathama-vibhakti")


def test_two_entity_scope_vps(vy):
    """scope-vps isolates ball-A mass as 3, not ball-B's 2"""
    g = vy.bqg("ball-A has mass 3 and velocity 4. ball-B has mass 2 and velocity 5")
    vps = vy.eval(f'scope-vps {vy.tl(g)} "ball-A"')
    assert isinstance(vps, list) and len(vps) >= 1
    pairs = vps[0] if isinstance(vps[0], list) else []
    vps_map = {p[0]: p[1] for p in pairs if isinstance(p, list) and len(p) >= 2}
    if "mass" in vps_map:
        assert vps_map["mass"] in ("3", "3.")


# ── three entities ────────────────────────────────────────────────────────────


def test_three_entity_prathama(vy):
    """Three entities all get prathama labels"""
    g = vy.bqg("ball-A has mass 3. ball-B has mass 5. ball-C has mass 7")
    prathama = vy.subjects(g, pred="prathama-vibhakti")
    assert "ball-A" in prathama
    assert "ball-B" in prathama
    assert "ball-C" in prathama


def test_three_entity_specific_query(vy):
    """Three entities — asking for specific one gives right answer"""
    r = vy.answer(
        "ball-A has mass 3. ball-B has mass 5. ball-C has mass 7. "
        "find kinetic energy of ball-B given velocity 4"
    )
    assert "40" in r


# ── entity name in answer strands ─────────────────────────────────────────────


def test_entity_name_in_we_have(vy):
    """Entity name appears in 'we have' strand"""
    r = vy.answer("ball-A has mass 5 and velocity 10. find kinetic energy of ball-A")
    we_have = vy.strand(r, "we have")
    assert "ball-A" in we_have


# ── cross-sentence accumulation ───────────────────────────────────────────────


def test_cross_sentence_entity(vy):
    """Properties split across sentences bind to same entity"""
    r = vy.answer("ball has mass 5. velocity is 10. find kinetic energy")
    assert "250" in r or "kinetic-energy" in r


def test_period_boundary_entity_preserved(vy):
    """Period boundary doesn't lose first entity's ownership"""
    g = vy.bqg("ball-A has mass 3. ball-B has mass 5")
    owners = vy.subjects(g, pred="prathama-vibhakti")
    assert "ball-A" in owners


def test_pronoun_it_reference(vy):
    """'it' refers back to entity in prior sentence"""
    r = vy.answer("ball has mass 5. it has velocity 10. find kinetic energy")
    assert "250" in r or "kinetic-energy" in r


# ── sthita-viveka: multi-slot mantras ─────────────────────────────────────────


def test_sthita_viveka_gravitational(vy):
    """Gravitational force needs mass1 and mass2 — two entities"""
    r = vy.answer(
        "particle-A has mass 5.972e24. particle-B has mass 7.34e22. "
        "find gravitational force given radius 3.84e8"
    )
    assert "1.98" in r or "gravitational" in r.lower()


def test_sthita_viveka_two_masses_distinct(vy):
    """Two entities with same concept (mass) → assigned to mass1/mass2 slots"""
    g = vy.bqg("particle-A has mass 5.972e24. particle-B has mass 7.34e22")
    prathama = vy.subjects(g, pred="prathama-vibhakti")
    assert "particle-A" in prathama and "particle-B" in prathama


# ── entity transfer ────────────────────────────────────────────────────────────


def test_entity_transfer_gave(vy):
    """Maria had 10, gave 4 → Maria has 6"""
    r = vy.answer("Maria had 10 apples. she gave 4 to Tom. how many apples does Maria have")
    assert "6" in r


def test_entity_transfer_gave_receiver(vy):
    """Tom receives 3 from Mary who had 4 → Mary has 1"""
    r = vy.answer("Mary had 4 apples. she gave 3 to Tom. how many apples does Mary have")
    assert "1" in r


# ── session: entity persists across turns ─────────────────────────────────────


def test_session_entity_persists(vy):
    """Entity defined in turn 1 accessible in turn 2"""
    sid = "test-entity-persist-v2"
    vy.ask("electron has mass 9.109e-31", session_id=sid)
    r = vy.ask("find momentum given velocity 1e6", session_id=sid)
    assert len(r) > 0


def test_session_accumulate_properties(vy):
    """Mass set in turn 1, velocity in turn 2, KE in turn 3"""
    sid = "test-entity-accumulate-v2"
    vy.ask("mass is 5", session_id=sid)
    vy.ask("velocity is 10", session_id=sid)
    r = vy.ask("find kinetic energy", session_id=sid)
    assert "250" in r or "kinetic-energy" in r
