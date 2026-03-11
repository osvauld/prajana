# Kosha Inheritance Architecture — Varga, Vishesa, Amsha

## Core principle

Every kosha subdomain has a **varga** (cluster) node at its root. Varga nodes are pure
organisational anchors — they carry what is universal to all members: domain identity,
unit family, and sangati root connections. Leaf nodes point to their varga via `vishesa`
edges and inherit everything above them transitively.

The directory structure IS the inheritance topology. The varga node lives at the root of
its subdir. The directory path is invisible to the graph — only node names matter — but the
subdir organises the files so human navigation and graph walk agree.

---

## The subdir pattern (physics: quantities/processes)

Every physics subdomain dir follows the same internal structure, recursively:

```
<subdomain>/
  <subdomain>-varga.om     ← varga node: units + sangati roots + domain identity
  quantities/              ← subanta nodes: what exists, what is measured
  processes/               ← tinanta bhave nodes: what happens, what is done
  <sub-subdomain>/         ← if large enough, recurse with same pattern
    <sub-subdomain>-varga.om
    quantities/
    processes/
```

The `quantities/` vs `processes/` split IS the grammatical pada distinction:
- `quantities/` = `subanta` nodes (nouns — things that exist and are measured)
- `processes/` = `tinanta bhave` nodes (verbs — pure processes with no agent)

## The subdir pattern (math: structures/properties/operations)

Math is NOT physics. Math has no measured quantities and no temporal processes.
Math uses three subdir types with distinct edge suffixes:

| subdir | edge suffix | meaning |
|---|---|---|
| `structures/` | `X-varga-vishesa` | leaf IS a particular of that structural class |
| `properties/` | `X-varga-lakshana` | leaf IS a characterising property/axiom of that class |
| `operations/` | `X-varga-karma` | leaf IS an operation/map within that class |

The `lakshana` suffix is math-specific. Properties/axioms are not quantities (subanta)
nor processes (tinanta). They are characterising marks that hold over structures.

---

## Three IS-A edge types (Nyaya framework)

| Edge | Sanskrit | Meaning | Walk? | Example |
|---|---|---|---|---|
| `swarupa` | essential nature | identity — this node IS that, completely | yes | `bhave-prayoga-swarupa` |
| `vishesa` | particular | this is a particular instance of a universal (samanya) | yes | `collision` is a `sandhi-karma-vishesa` |
| `amsha` | portion/member | one member of a set that together constitutes the whole | yes | `prathama-vibhakti` is a `vibhakti-amsha` |
| `dhatu` | root/stem | this word form has this concept as its morphological root | yes | `reaches` has `reach-target` as dhatu |

**`swarupa`** — identity. No distinction between the node and what it points to. Cannot be inverted.

**`vishesa`** — particular of a universal (samanya). The child adds specificity that the
parent does not have. Multiple vishesas of the same samanya are distinct. Walk upward
finds the class; walk downward enumerates all particulars.

**`amsha`** — member of a constituted set. The amshas together *make up* the whole. The eight
vibhaktis are amshas of vibhakti — remove one and the case system is incomplete. Unlike
vishesa, amshas are exhaustive: the set of amshas is the set.

**Old `abheda` conflated all three.** Going forward:
- Replace `X-abheda` meaning "X is a kind of Y" → `Y-vishesa`
- Replace `X-abheda` meaning "X is a member of set Y" → `Y-amsha`
- Keep `abheda` only for genuine non-difference / synonymy

---

## What varga nodes carry

Each varga node carries three things and nothing else:

1. **Vishesa edges upward** — `X-varga-vishesa` pointing to parent varga(s)
2. **Unit family** — the SI units that all members are measured in
3. **Sangati root connections** — the philosophical/structural anchors

```
kosha linear-motion-varga
  "kinematics-varga-vishesa"  ← points up
  "metre-matra second-matra"  ← units
  "gati-swarupa kramanusara-yukta avastha-yukta kshetra-sthita"  ← sangati roots
```

What varga nodes do NOT carry: specific physics content, equations, relationships between
quantities. Those belong on the leaf nodes only.

---

## What leaves carry (after restructure)

A leaf node carries only what makes it distinct from all other vishesas of its varga:

```
kosha velocity                     BEFORE              AFTER
  "subanta-swarupa"                inherited           removed
  "domain-physics-sthita"          inherited           removed
  "kaala-yukta"                    inherited           removed
  "kshetra-sthita"                 inherited           removed
  "physics-time-apeksha"           inherited           removed
  "avastha-sthita"                 inherited           removed
  "metre-matra"                    inherited           removed
  ──────────────────────────────────────────────────────────────
  "linear-motion-varga-vishesa"    NEW                 added
  "vega-abheda direction-yukta"    specific            kept
  "displacement-kramanusara"       specific            kept
  "acceleration-kramanusara-phala" specific            kept
```

---

## Cross-cluster membership — multiple vishesa edges

A node can be a vishesa of multiple vargas simultaneously:

```
torque
  "rotational-force-varga-vishesa"    ← causes angular acceleration
  "mechanical-energy-varga-vishesa"   ← torque × angle = work (joules)

angular-velocity
  "rotational-motion-varga-vishesa"   ← in the rotational derivative chain
  "oscillation-varga-vishesa"         ← omega IS angular frequency

energy
  "mechanical-energy-varga-vishesa"
  "thermodynamics-varga-vishesa"      ← thermal energy is energy
  "electromagnetism-varga-vishesa"    ← electrical energy is energy
```

---

## Cross-domain math properties — multiple varga-lakshana edges

Cross-domain math properties do NOT get duplicated per-subdir. One node, multiple edges:

```
commutativity   → "algebra-varga-lakshana" "set-varga-lakshana" "number-varga-lakshana"
                  "sama-yukta"
closure         → "algebra-varga-lakshana" "set-varga-lakshana"
                  "purna-yukta"
identity-element→ "algebra-varga-lakshana" "set-varga-lakshana"
                  "shunya-yukta" "sama-yukta"
inverse-element → "algebra-varga-lakshana" "set-varga-lakshana"
                  "viparita-yukta"
associativity   → "algebra-varga-lakshana" "number-varga-lakshana"
                  "sama-yukta"
equivalence-rel → "algebra-varga-lakshana" "set-varga-lakshana"
                  "sama-yukta" "sambandha-yukta"
partial-order   → "set-varga-lakshana" "algebra-varga-lakshana"
                  "sambandha-yukta" "krama-yukta"
morphism        → "algebra-varga-karma" "set-varga-karma"
                  "sambandha-yukta" "rachana-yukta"
```

---

## Full varga hierarchy tree

```
math-varga                     brahman/kosha/math/
    algebra-varga
    geometry-varga
    calculus-varga
    number-varga
    set-varga
    graph-varga                (NEW Phase 2.9)
    logic-varga                (NEW Phase 2.9)
    probability-varga          (NEW Phase 2.9)
    complexity-varga           (NEW Phase 2.9 — also cs-varga-vishesa)

cs-varga → math-varga          brahman/kosha/computation/concepts/
    type-varga
    computation-varga
    memory-varga
    information-varga          (NEW Phase 2.9 — also probability-varga-vishesa)

physics-varga → math-varga     brahman/kosha/physics/
    kinematics-varga
        linear-motion-varga
            quantities/        displacement, velocity, acceleration, jerk, speed, momentum
            processes/         free-fall, projectile-motion, decelerate-to-rest,
                               horizontal-motion, vertical-motion
        rotational-motion-varga
            quantities/        angular-displacement, angular-velocity, angular-acceleration,
                               angular-momentum
    dynamics-varga
        linear-force-varga
            quantities/        force, net-force, friction-force, normal-force, spring-force,
                               tension-force, drag-force, gravitational-force, centripetal-force,
                               mass, gravity
            processes/         force-apply, collision
        rotational-force-varga
            quantities/        torque, moment-of-inertia
    energy-varga
        mechanical-energy-varga
            quantities/        kinetic-energy, potential-energy, work, path-energy
            processes/         position-step, velocity-step, velocity-decay, velocity-plan
    oscillation-varga → math-varga
        quantities/            frequency, period, wave, sound, vibration, harmonic,
                               damped-oscillation, constructive, destructive, diffraction,
                               sine, cosine, spectrum
    thermodynamics-varga → energy-varga
        quantities/            temperature, absolute-zero, entropy
        processes/             heat-transfer, phase-change-boil, phase-change-freeze, alpha-cooling
        laws/                  zeroth-law, first-law, second-law, third-law
    electromagnetism-varga → energy-varga
        circuit-varga
            quantities/        current, voltage, resistance, capacitance, inductance, circuit
            processes/         current-flow, charge-accumulate
        field-varga
            quantities/        electric-field, magnetic-field, electromagnetism
        optics-varga → oscillation-varga
            quantities/        photon, spectrum, light
            processes/         specular-reflection, refraction, diffraction
    quantum-varga → math-varga
        quantities/            entanglement, planck-relation, planck-scale, standard-model,
                               string-theory, electron, atom, nuclear-force, photon
        processes/             tunneling, collapse
    fluid-varga → math-varga   brahman/kosha/physics/fluid/
        quantities/            pressure, viscosity, turbulence, vortex, advection, diffusion
    ik/                        (robotics/physics bridge)
        quantities/            jacobian, joint-space, task-space
        processes/             reach-target, locate, move-to, rotate-by, dls-pseudoinverse
    constraints/
        processes/             hard-constraint, soft-constraint, capability-bound, prohibition
    units/                     kilogram, metre, second, newton, radian, physics-constants

chemistry-varga → physics + math    brahman/kosha/chemistry/
biology-varga → chemistry           brahman/kosha/biology/
robotics-varga → physics + cs       brahman/kosha/robotics/
sangeetham-varga → physics + math   brahman/kosha/sangeetham/
finance-varga → math                brahman/kosha/finance/
```

---

## Walk cost model

IS-A edges (`swarupa`, `vishesa`, `amsha`, `dhatu`) are walked as cheaper than relational
edges (`yukta`, `kriya`, `phala`, `janya`). This gives the graph metric structure:

- Two vishesas of the same samanya: distance 2 (up to parent, down to sibling)
- Two nodes in different subtrees: distance 4+

Semantic similarity is inversely proportional to path length through IS-A edges.

```
velocity ↔ acceleration    distance 2  (both kramanusara-matra-vishesa)
velocity ↔ current         distance 4+ (different subtrees)
vartamana-kaala ↔ bhuta-kaala  distance 2  (both kaala-amsha)
```

**Non-inheritance edges** (not walked for shabda merging):
`yukta`, `kriya`, `phala`, `janya`, `pratipaksha`, `apeksha`, `sthita`

---

## Samanya node naming — Sanskrit domain identities

| subdir | samanya node | Sanskrit meaning |
|---|---|---|
| `physics/electrical/` | `vidyut-matra` | electrical measure |
| `physics/kinematics/` | `kramanusara-matra` | derivative-chain measure |
| `physics/thermodynamics/` | `ushna-matra` | thermal measure |
| `physics/waves/` | `taranga-matra` | wave measure |
| `physics/orbital/` | `bhramana-matra` | orbital/revolving measure |
| `physics/forces/` | `bala-matra` | force measure |
| `physics/ik/` | `ik-karma` | IK computation process |
| `physics/simulation/` | `anukrana-karma` | simulation-step process |
| `physics/constraints/` | `niyama-karma` | constraint process |
| `physics/processes/` | `sandhi-karma` | scenario/contact process |
| `physics/quantum/` | `svayambhu-matra` | fundamental constant |
| `physics/fluid/` | `pravaha-matra` | flow/fluid measure |
| `robotics/actuator/` | `chalana-seema` | actuator limit |
| `robotics/links/` | `bandha-matra` | link property |
| `robotics/target/` | `lakshya-sthana` | target pose |
