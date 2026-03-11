# Bhasha Layer: English

`brahman/bhasha/english/` — surface forms in English. Every node here exists because
English has this word form. Nodes annotate with Sanskrit grammatical terms.

---

## Directory structure

```
brahman/bhasha/english/
  english.om                   -- bhasha anchor node for English
  grammar/
    articles.om                -- a, an, the (nipata)
    copula.om                  -- is, are, was, were, being (avyaya/tinanta)
    operators.om               -- +, -, *, /, = (nipata)
    questions.om               -- what, how, why, where, when, who, which (avyaya)
    conjunctions.om            -- and, or, but (nipata)
    prepositions.om            -- to, at, from, through, along, toward... (avyaya)
    modals.om                  -- must, should, can, cannot, may, will (avyaya)
    negation.om                -- no, not, without, never (avyaya / pratishedha)
    binding.om                 -- when, given, if, assuming, where, suppose (avyaya)
    sequence.om                -- then, next, after, first, finally (avyaya / krama)
    reference.om               -- it, that, previous, same, again (sarvanama)
    modifiers.om               -- kinetic, angular, potential (upasarga / samasa)
    scaling.om                 -- twice, half, squared, per, times (avyaya / sankhya)
    compute.om                 -- find, solve, calculate, compute, determine (tinanta)
    convert.om                 -- convert, express-in, change-to (tinanta)
  verbs/
    mechanics.om               -- drops/fell, travels/moved, stops/halted, vibrates...
    kinematics.om              -- reaches/reached, moves/moved, rotates/rotated...
    thermodynamics.om          -- heats/heated, cools/cooled, boils/boiled, melts...
    optics.om                  -- reflects/reflected, refracts/refracted, focuses...
    electrics.om               -- flows/flowed, charges/charged, resists/resisted...
    gravity.om                 -- attracts/attracted, orbits/orbited, escapes/escaped, weighs...
  context/
    direction.om               -- upward, downward, horizontal, vertical
    surface.om                 -- frictionless, rough, smooth
    state.om                   -- at-rest, thrown, decelerating
  queries/
    quantity.om                -- how-far, how-fast, how-heavy, how-hot, how-long, how-much
  scene/
    scene-types.om             -- projectile, pendulum, circuit, incline...
    goal-words.om              -- target, position, destination, goal, endpoint...
    unit-aliases.om            -- kg, m, s, N, J, W, V, A, Ω, rad...
    axis-words.om              -- x-axis, y-axis, z-axis, horizontal, vertical...
    joint-types.om             -- revolute, prismatic, spherical, fixed...
  defaults/
    scene-defaults-*.om        -- default parameters per scene type
```

---

## Node format: tinanta (verbal)

A verbal bhasha node declares:
- `tinanta-swarupa` (it is a verb form)
- `kala-yukta <value>` (its tense)
- `vachana-yukta <value>` (its number)
- `purusa-yukta <value>` (its person)
- `prayoga-yukta kartari-prayoga` or `karmani-prayoga`
- `dhatu <kosha-process-node>` (the bhave process it points to)
- `shabda` — only the surface word form(s) + description

```
bhasha reaches

  "tinanta-swarupa english-sthita"
  "kala-yukta vartamana-kala-sthita"
  "vachana-yukta eka-vachana-sthita"
  "purusa-yukta prathama-purusa-sthita"
  "prayoga-yukta kartari-prayoga-sthita"
  "dhatu reach-target-sthita"

  shabda reaches / third-person-singular-present-active

done


bhasha dropped

  "tinanta-swarupa english-sthita"
  "kala-yukta purva-kala-sthita"
  "prayoga-yukta kartari-prayoga-sthita"
  "dhatu free-fall-sthita"

  shabda dropped, fell, fell-from / simple-past-active-free-fall

done


bhasha is-dropped

  "tinanta-swarupa english-sthita"
  "kala-yukta purva-kala-sthita"
  "prayoga-yukta karmani-prayoga-sthita"
  "dhatu free-fall-sthita"

  shabda is-dropped, was-dropped / passive-free-fall

done
```

Note: `pos:verb` and `signal:ik=1.0` are NOT declared here — inherited from the kosha
process node via dhatu walk.

---

## Node format: subanta (nominal)

```
bhasha frictionless

  "subanta-swarupa english-sthita"
  "saptami-vibhakti-yukta"         -- describes the surface (locative context)
  "dhatu zero-friction-surface-sthita"

  shabda frictionless, smooth, frictionless-surface, no-friction / friction-coefficient-is-zero

done


bhasha upward

  "subanta-swarupa english-sthita"
  "panchami-vibhakti-yukta"        -- direction from which gravity acts (ablative)
  "dhatu vertical-motion-sthita"

  shabda upward, upwards, up / against-gravity-direction

done
```

---

## Node format: avyaya (indeclinable)

Grammar words, particles, prepositions — no inflection, no dhatu needed (or dhatu
to kosha avyaya concept).

```
bhasha to-preposition

  "avyaya-swarupa english-sthita"
  "chaturthi-vibhakti-yukta"       -- marks destination (dative)
  "dhatu toward-sthita"

  shabda to, toward, into, towards / destination-marker

done


bhasha must

  "avyaya-swarupa english-sthita"
  "kala-yukta sambhavana-kala-sthita"
  "dhatu hard-constraint-sthita"

  shabda must, has-to, needs-to / hard-constraint-marker

done


bhasha not-particle

  "avyaya-swarupa english-sthita"
  "pratishedha-kriya"
  "dhatu prohibition-sthita"

  shabda not, no, never, without, zero / negation-particle

done
```

---

## Tense-aware extraction

| Bhasha node kala | Extraction role |
|---|---|
| `vartamana-kala` | current state or ongoing constraint |
| `purva-kala` | initial condition, historical fact |
| `bhavishya-kala` | goal / target state |
| `vidhi-kala` | command → goal / target (highest priority) |
| `sambhavana-kala` | constraint (hard if must, soft if should, capability if can) |

```
"the arm reached [0.4, 0.3]"   → purva-kala  → initial-position
"the arm reaches [0.4, 0.3]"   → vartamana   → current constraint
"Reach [0.4, 0.3]"             → vidhi-kala  → target (goal)
```

---

## Voice-aware extraction (prayoga)

`karmani-prayoga` signals argument inversion:

```
active:  "the arm reaches [0.4, 0.3]"        coord is object  → ik-ahara direct
passive: "[0.4, 0.3] is reached by the arm"  coord is subject → argument order inverts
```

---

## Machine languages (future: Phase 9+)

`brahman/bhasha/ocaml/`, `brahman/bhasha/lua/`, `brahman/bhasha/strudel/`,
`brahman/bhasha/render/` — all moved, headers changed to `bhasha`. Content
rewrite deferred. Sanskrit grammatical annotations for programming constructs:

- A function: `tinanta-swarupa ahara-yukta phala-yukta`
- A type: `subanta-swarupa jati-abheda`
- A module: `subanta-swarupa vrnda-yukta`
- Pattern matching: `tinanta-swarupa vibhakti-yukta`
