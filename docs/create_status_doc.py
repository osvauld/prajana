#!/usr/bin/env python3
"""Create the Agent-X Status Analysis sections in pathram2."""

import subprocess
import sys

def add_doc(title, body, parent="doc-51"):
    r = subprocess.run(
        [".venv/bin/python3", "-m", "pathram2", "add", "doc", title,
         "--body", body, "--parent", parent, "--tag", "active"],
        capture_output=True, text=True,
    )
    out = r.stdout.strip()
    print(out)
    if "Created:" in out:
        return out.split("Created:")[1].strip()
    return None

def link(src, tgt, rel, reason=""):
    args = [".venv/bin/python3", "-m", "pathram2", "link", src, tgt, rel]
    if reason:
        args += ["--reason", reason]
    subprocess.run(args, capture_output=True, text=True)

# --- Parent ---
r = subprocess.run(
    [".venv/bin/python3", "-m", "pathram2", "add", "doc",
     "Agent-X: Status Analysis",
     "--body", "Comprehensive analysis of where Agent-X stands today. Covers graph inventory, formula coverage, NLP capabilities, benchmark readiness, and the roadmap to full benchmark coverage.",
     "--tag", "active"],
    capture_output=True, text=True,
)
print(r.stdout.strip())

# --- Section 1: System Inventory ---
s1 = add_doc("System Inventory", r"""Current state of the Agent-X engine as of March 2026.

## Engine

| Component | Count | Description |
|-----------|-------|-------------|
| OCaml modules | 13 | Core engine code |
| OCaml lines | 6987 | Total lines of OCaml |
| Graph nodes | 1649 | Knowledge nodes across 4 layers |
| Tantras | 158 | Declarative computation rules |
| Shabda nodes | 1413 | Word/metadata entries |
| Word mappings | 783 | Words mapped to graph nodes |
| Eval primitives | 36 | OCaml-backed operations |
| Relation types | 62 | Typed edge dimensions |

## Graph Layers

| Layer | Nodes | Role |
|-------|-------|------|
| kosha | 1007 | Domain knowledge (physics, math, CS, biology) |
| sangati | 346 | Relations and connectors |
| bhasha | 166 | Language/grammar nodes |
| mantra | 130 | Formulas, operations, and computation rules |

## Edge Flow (Cross-Layer)

| From / To | bhasha | kosha | mantra | sangati |
|-----------|--------|-------|--------|---------|
| bhasha | 324 | 123 | 9 | 302 |
| kosha | 73 | 3621 | 169 | 2028 |
| mantra | 4 | 330 | 208 | 126 |
| sangati | 5 | 91 | 0 | 1882 |

Total graph edges: ~11,900. Density: 0.07% of possible cells in the 3D tensor.

## Test Suite

| Metric | Count |
|--------|-------|
| Total tests | 417 |
| Passing | 329 (78.9%) |
| Expected failures (xfail) | 81 (19.4%) |
| Actual failures | 7 (1.7%) |

## Test Coverage by Layer

| Layer | Tests |
|-------|-------|
| edges | 79 |
| grammar | 45 |
| gen_logic | 43 |
| physics | 38 |
| answers | 24 |
| pipeline | 22 |
| arithmetic | 19 |
| entity | 19 |
| evaluator | 17 |
| comparison | 16 |
| mixed | 16 |
| logic | 28 |
| graph | 10 |
| xfail | 41 |
""")

# --- Section 2: Formula Coverage ---
s2 = add_doc("Formula Coverage (Mantras)", r"""Agent-X has 23 physics/math mantras. Each mantra is a function stored in the graph with typed inputs (janya), output (phala), and a computation chain (krama).

## All 23 Mantras

| Mantra | Formula | Inputs $\to$ Output |
|--------|---------|---------------------|
| kinetic-energy-mantra | $KE = \frac{1}{2}mv^2$ | mass, velocity $\to$ kinetic-energy |
| potential-energy-mantra | $PE = mgh$ | mass, gravity, height $\to$ potential-energy |
| momentum-mantra | $p = mv$ | mass, velocity $\to$ momentum |
| newton-second-law-motion | $F = ma$ | mass, acceleration $\to$ force |
| velocity-mantra | $v = u + at$ | initial-velocity, acceleration, time $\to$ velocity |
| acceleration-mantra | $a = \frac{v-u}{t}$ | initial-velocity, final-velocity, time $\to$ acceleration |
| pressure-mantra | $P = \frac{F}{A}$ | force, area $\to$ pressure |
| mass-density-mantra | $\rho = \frac{m}{V}$ | mass, volume $\to$ mass-density |
| work-mantra | $W = Fd\cos\theta$ | force, displacement, angle $\to$ work |
| frequency-mantra | $f = \frac{1}{T}$ | period $\to$ frequency |
| period-mantra | $T = \frac{2\pi}{\omega}$ | angular-velocity $\to$ period |
| angular-velocity-mantra | $\omega = \frac{v}{r}$ | velocity, radius $\to$ angular-velocity |
| angular-momentum-mantra | $L = I\omega$ | moment-of-inertia, angular-velocity $\to$ angular-momentum |
| relative-velocity-mantra | $v_{rel} = v_{obs} - v_{observer}$ | observed-velocity, observer-velocity $\to$ relative-velocity |
| spring-force-mantra | $F = kx$ | spring-constant, displacement $\to$ spring-force |
| friction-force-mantra | $F = \mu N$ | coefficient, normal-force $\to$ friction-force |
| centripetal-force-mantra | $F = \frac{mv^2}{r}$ | mass, velocity, radius $\to$ centripetal-force |
| gravitational-force-mantra | $F = \frac{Gm_1m_2}{r^2}$ | gravitational-constant, mass1, mass2, radius $\to$ gravitational-force |
| ohm-law | $V = IR$ | current, resistance $\to$ voltage |
| electric-power-mantra | $P = VI$ | voltage, current $\to$ electric-power |
| capacitance-mantra | $C = \frac{Q}{V}$ | charge, voltage $\to$ capacitance |
| torque-mantra | $\tau = I\alpha$ | moment-of-inertia, angular-acceleration $\to$ torque |
| photon-energy-mantra | $E = hf$ | planck-constant, frequency $\to$ photon-energy |

## Inverse Computation

Every mantra with a krama chain supports automatic inversion. The pipeline reads each operation's inverse from the graph (pratipaksha edges on operation nodes):

| Operation | Inverse | How |
|-----------|---------|-----|
| half ($x \times 0.5$) | double ($x \times 2$) | pratipaksha edge |
| square ($x^2$) | square-root ($\sqrt{x}$) | pratipaksha edge |
| multiplication ($x \times y$) | division ($x / y$) | pratipaksha edge |
| addition ($x + y$) | subtraction ($x - y$) | pratipaksha edge |

No inverse formulas are hardcoded. The invert-krama tantra walks the krama tree and reverses each step using the graph.

## Constants (Auto-Supplied)

| Constant | Value | Used by |
|----------|-------|---------|
| gravitational-acceleration | 9.8 | potential-energy-mantra, gravitational-force-mantra |
| planck-constant | $6.626 \times 10^{-34}$ | photon-energy-mantra |
| speed-of-light | 299792458 | (available, not yet used) |
| pi | 3.14159265358979 | period-mantra |

Constants are stored as shabda entries on physics-constants and auto-supplied when a janya input has a constants-key in its shabda.
""")

# --- Section 3: NLP Pattern Coverage ---
s3 = add_doc("NLP Pattern Coverage", r"""The pipeline parses natural language questions into triples via mapping (shabda-anveshana), not string matching. Here is what patterns work today and what does not.

## Working Patterns (16/23)

| Pattern | Example | Status |
|---------|---------|--------|
| Direct: concept is N unit | "mass is 5 kg" | $\checkmark$ |
| Direct: concept is N (bare) | "force is 100" | $\checkmark$ |
| Separate sentences | "mass is 5 kg. velocity is 10 m/s." | $\checkmark$ |
| 'of' pattern | "a ball of mass 5 kg" | $\checkmark$ |
| 'with' pattern | "a ball with mass 5 kg" | $\checkmark$ |
| 'has' pattern | "a ball has mass 5 kg" | $\checkmark$ |
| 'has a X of N' | "has a mass of 5 kg" | $\checkmark$ |
| 'equals' copula | "mass equals 5 kg" | $\checkmark$ |
| 'the X is N' | "the mass is 5 kg" | $\checkmark$ |
| 'given' prefix | "given mass is 5 kg" | $\checkmark$ |
| 'what is' intent | "what is kinetic energy" | $\checkmark$ |
| 'calculate' intent | "calculate kinetic energy" | $\checkmark$ |
| 'determine' intent | "determine kinetic energy" | $\checkmark$ |
| 'compute' intent | "compute kinetic energy" | $\checkmark$ |
| Inverse solve | "kinetic energy is 250. find velocity" | $\checkmark$ |
| Decimal values | "mass is 0.5 kg" | $\checkmark$ |

## Failing Patterns (7/23)

| Pattern | Example | Why it fails | Impact |
|---------|---------|-------------|--------|
| N before concept | "a 5 kg ball" | BQG expects concept then number | HIGH -- very common in benchmarks |
| N unit concept | "5 kg mass" | Same -- number before concept | HIGH |
| Variable = N | "m = 5 kg" | "m" maps to metre, "=" not copula | MEDIUM |
| Multi-step chain | "height is 10. find velocity" | No PE $\to$ KE conservation chain | HIGH |
| Pronoun reference | "it has velocity 10" | No coreference resolution | MEDIUM |
| Scientific notation (partial) | "9.109e-31" | Works for some, edge cases | LOW |
| Units inline (partial) | "5 kilogram" | Works sometimes, inconsistent | LOW |

## Morphological Support

shabda-anveshana applies plural $\to$ singular normalization via graph-stored rules:

| Rule | Example | Method |
|------|---------|--------|
| english-plural-regular | "forces" $\to$ "force" | strip "s" |
| english-plural-ies | "energies" $\to$ "energy" | strip "ies", add "y" |
| english-plural-es | "masses" $\to$ "mass" | strip "es" |

Rules are graph nodes (under vachana-bahu), not hardcoded. New rules = new nodes.

## Intent Detection

5 dispatch modes, detected by signal analysis:

| Mode | Trigger | Example |
|------|---------|---------|
| derive | vidhi-kaala + numbers | "mass is 5. find KE" |
| anumana | "what is X" without numbers | "what is momentum" |
| viveka | "is X a Y" | "is velocity a vector" |
| count | "how many" | "how many forces act" |
| shunya | no intent, no data | (empty question) |
""")

# --- Section 4: Benchmark Coverage ---
s4 = add_doc("Benchmark Coverage", r"""We evaluated Agent-X against two standard physics QA benchmarks: TheoremQA (TIGER-Lab, 2023) and PhysReason (2024).

## TheoremQA

Source: TIGER-Lab/TheoremQA on HuggingFace. 800 questions across math, physics, CS, finance.

| Filter | Count |
|--------|-------|
| Total questions | 800 |
| Physics (text-only, no images) | 140 |
| Covered by existing mantras | ~95 |
| Solvable with current NLP | ~60 |

### Questions by Formula Category

| Category | Questions | Have Mantra? |
|----------|-----------|-------------|
| velocity/speed | 30 | $\checkmark$ velocity-mantra |
| electric/circuit | 32 | $\checkmark$ ohm-law, electric-power, capacitance |
| frequency/wave | 14 | $\checkmark$ frequency-mantra (partial) |
| thermal/heat | 10 | needs thermal-mantra |
| kinetic energy | 8 | $\checkmark$ kinetic-energy-mantra |
| density | 8 | $\checkmark$ mass-density-mantra |
| friction | 8 | $\checkmark$ friction-force-mantra |
| gravity | 7 | $\checkmark$ gravitational-force-mantra |
| acceleration | 7 | $\checkmark$ acceleration-mantra |
| power | 6 | needs power-mantra (general) |
| angular | 5 | $\checkmark$ angular-velocity-mantra |
| work | 5 | $\checkmark$ work-mantra |
| spring | 4 | $\checkmark$ spring-force-mantra |
| pressure | 4 | $\checkmark$ pressure-mantra |
| momentum | 2 | $\checkmark$ momentum-mantra |

### Coverage Gap

The 140 physics questions fall into three tiers:

**Tier 1 -- Directly solvable (~30 questions)**: Single-formula, values given explicitly. Example: "Calculate the momentum of an 80 kg person moving at 2 m/s." Our pipeline handles these today with minor NLP adjustments.

**Tier 2 -- Solvable with NLP fixes (~65 questions)**: Correct mantra exists, but values are embedded in natural language that our BQG cannot yet parse. Example: "A 5 kg ball is moving at 10 m/s. What is the kinetic energy?" Needs the N-before-concept pattern.

**Tier 3 -- Needs new mantras or multi-step (~45 questions)**: Requires formulas we do not have (thermal, wave, gas law, oscillation) or multi-step chains (conservation of energy).

## PhysReason

Source: PhysReason on HuggingFace. 1200 physics problems, 147 theorems.

| Filter | Count |
|--------|-------|
| Total problems | 1200 (mini: 200) |
| Text-only (no images) | 31 (mini) |
| Within our formula vocabulary | ~15 |
| Solvable with current NLP | ~5 |

PhysReason problems are harder: multi-step, symbolic answers, require context understanding. These represent our long-term target.

## GSM8K

8792 grade-school math problems. Zero physics formula questions. Not applicable.

## Benchmark Readiness Score

| Benchmark | Total applicable | Currently solvable | With NLP fixes | With new mantras |
|-----------|-----------------|-------------------|----------------|-----------------|
| TheoremQA | 140 | ~30 (21%) | ~95 (68%) | ~130 (93%) |
| PhysReason (mini) | 31 | ~5 (16%) | ~10 (32%) | ~20 (65%) |
| Our own tests | 417 | 329 (79%) | -- | -- |
""")

# --- Section 5: Missing Vocabulary ---
s5 = add_doc("Missing Vocabulary and Mantras", r"""To reach full benchmark coverage, we need to add these formulas and supporting nodes.

## Priority 1: Missing Mantras (unlocks ~55 benchmark questions)

| Mantra needed | Formula | Inputs $\to$ Output | Benchmark Qs |
|---------------|---------|---------------------|-------------|
| thermal-energy-mantra | $Q = mc\Delta T$ | mass, specific-heat, temperature-change $\to$ heat | 11 |
| wave-speed-mantra | $v = f\lambda$ | frequency, wavelength $\to$ wave-speed | 9 |
| power-mantra | $P = \frac{W}{t}$ | work, time $\to$ power | 9 |
| shm-period-mantra | $T = 2\pi\sqrt{\frac{m}{k}}$ | mass, spring-constant $\to$ period | 7 |
| pendulum-period-mantra | $T = 2\pi\sqrt{\frac{l}{g}}$ | length, gravity $\to$ period | 7 |
| ideal-gas-mantra | $PV = nRT$ | pressure, volume, moles, gas-constant $\to$ temperature | 6 |
| coulomb-mantra | $F = k\frac{q_1 q_2}{r^2}$ | charge1, charge2, distance $\to$ coulomb-force | 5 |
| electric-field-mantra | $E = \frac{F}{q}$ | force, charge $\to$ electric-field | 5 |
| magnetic-force-mantra | $F = qvB$ | charge, velocity, magnetic-field $\to$ magnetic-force | 3 |
| projectile-range-mantra | $R = \frac{v^2 \sin 2\theta}{g}$ | velocity, angle, gravity $\to$ range | 2 |
| conservation-energy | $PE = KE$ | via pratipaksha chain | 1 |

## Priority 2: Supporting Nodes Needed

| Node | Type | Shabda needed |
|------|------|--------------|
| specific-heat | kosha | word: "specific heat" |
| temperature-change | kosha | word: "temperature change", "delta t" |
| wavelength | kosha | word: "wavelength" |
| wave-speed | kosha | word: "wave speed" |
| moles | kosha | word: "moles", "mol" |
| gas-constant | kosha | constants-key: gas-constant (8.314) |
| charge | kosha | word: "charge" (already exists?) |
| electric-field | kosha | word: "electric field" |
| magnetic-field-strength | kosha | word: "magnetic field" |
| range | kosha | word: "range" |
| length | kosha | word: "length" |

## Priority 3: Constants to Add

| Constant | Value | Key in physics-constants |
|----------|-------|------------------------|
| gas-constant | 8.314 | gas-constant |
| coulomb-constant | $8.99 \times 10^9$ | coulomb-constant |
| boltzmann-constant | $1.381 \times 10^{-23}$ | boltzmann-constant |
| electron-charge | $1.602 \times 10^{-19}$ | electron-charge |

## Priority 4: Conservation Chain (pratipaksha)

The pratipaksha edge already exists: kinetic-energy $\leftrightarrow$ potential-energy. But dispatch-derive does not chain through pratipaksha to convert one to the other. Adding this unlocks "dropped from height, find velocity" questions.

Required: when solve-for has no direct mantra match, check if a pratipaksha concept has a matching mantra, compute that, then use pratipaksha to convert.
""")

# --- Section 6: NLP Roadmap ---
s6 = add_doc("NLP Roadmap", r"""The NLP gaps are more impactful than the mantra gaps. Fixing 3 patterns unlocks ~65 more benchmark questions with existing mantras.

## Fix 1: Number-Before-Concept (HIGH -- unlocks ~40 questions)

Current: "a 5 kg ball" $\to$ FAILS (5 binds to kilogram, not mass)
Target: "a 5 kg ball" $\to$ [mass, sankhya, 5.] + [mass, matra, kilogram]

The fix is in build-question-graph's emit-triples: when a number+unit appears before a concept, do a forward-lookahead to find the concept and bind to it.

Pattern variations that should work after fix:
- "a 5 kg ball"
- "a 0.60 kg basketball"
- "5 kg mass"
- "the 100 N force"
- "a 2 m height"

## Fix 2: Period-After-Bare-Number (MEDIUM -- unlocks ~15 questions)

Current: "area is 5." $\to$ "5" stays asprista-sankhya because "." consumed as viraam
Target: "area is 5." $\to$ [area, sankhya, 5.]

The fix is in BQG's punctuation handling: when a period follows a digit, it should be treated as a number terminator first, sentence boundary second.

## Fix 3: Multi-Step Chains via Pratipaksha (HIGH -- unlocks ~10 questions)

Current: "height is 10. find velocity" $\to$ NO MATCH
Target: compute PE = mgh, then KE = PE (conservation), then v = sqrt(2*KE/m)

Requires chaining through pratipaksha edges in dispatch-derive. When solve-for (velocity) is a janya of mantra-A (kinetic-energy-mantra), and mantra-A's phala (kinetic-energy) has a pratipaksha (potential-energy) that IS the phala of mantra-B (potential-energy-mantra) whose janya inputs ARE bound: compute mantra-B first, assign result to kinetic-energy, then inverse-solve mantra-A.

## Fix 4: Pronoun Resolution (MEDIUM -- unlocks ~5 questions)

Current: "a ball weighs 5 kg. it has velocity 10 m/s." $\to$ 5 binds to pronoun-it
Target: resolve "it" to the most recent entity (mass/ball)

Requires tracking the current entity in BQG and substituting pronoun-it with the antecedent.

## Fix 5: Variable Names (LOW -- unlocks ~5 questions)

Current: "m = 5 kg" $\to$ "m" maps to metre
Target: "m" in context of "mass m = 5" should bind to mass

Requires context-aware disambiguation: when a single letter follows a concept name, treat it as a variable alias, not a word lookup.

## Summary: Impact of Each Fix

| Fix | Effort | Questions Unlocked | Cumulative Coverage |
|-----|--------|-------------------|-------------------|
| Baseline (today) | -- | ~30 / 140 (21%) | 21% |
| + Fix 1 (N before concept) | Medium | +40 | 50% |
| + Fix 2 (period after number) | Small | +15 | 61% |
| + Fix 3 (pratipaksha chain) | Medium | +10 | 68% |
| + New mantras (11 formulas) | Medium | +35 | 93% |
| + Fix 4 (pronouns) | Medium | +5 | 96% |
| + Fix 5 (variables) | Small | +5 | 100% |
""")

# --- Section 7: Architecture Summary ---
s7 = add_doc("Architecture Summary", r"""A one-page overview of how Agent-X works, for someone seeing the project for the first time.

## What Agent-X Is

A proof-graph engine that answers physics and math questions by walking a 3D boolean tensor. No neural network, no LLM, no training data. All knowledge is a typed graph.

## The 3D Tensor

$$G \in \{0,1\}^{1649 \times 1649 \times 62}$$

1649 nodes (concepts, formulas, grammar), 62 relation types (identity, inverse, input-of, result-of, ...). Each edge is one cell set to 1.

## The Pipeline

A question enters as a string and exits as a computed answer:

$$\text{String} \xrightarrow{\text{BQG}} \text{Triples} \xrightarrow{\text{refine}} \text{Triples} \xrightarrow{\text{expand}} \text{Triples} \xrightarrow{\text{detect}} \text{Signals} \xrightarrow{\text{dispatch}} \text{Answer}$$

1. **build-question-graph**: map each word to graph nodes (not string matching). Emit triples.
2. **assertion-bandha**: detect "X is Y" patterns, add swarupa edges.
3. **avrti-refine-v2**: bind numbers to concepts, propagate, fixpoint.
4. **grade-split**: separate sentences into graded ring grades.
5. **kosha-expand**: PPR walk to discover nearby concepts.
6. **detect-signals**: classify question type (derive, count, viveka, anumana).
7. **dispatch-answer**: find matching formula, compute (forward or inverse), format proof.

## Key Properties

- **Monotonic**: triples only accumulate, never removed ($a \oplus b \geq a$)
- **Mapping, not matching**: every word lookup is a graph traversal via naama edges
- **Automatic inversion**: formulas inverted by reversing the krama chain using pratipaksha edges
- **Composable**: tantras are declarative s-expressions, not imperative code
- **Self-describing**: the pipeline's own stages are graph nodes

## Implementation

| Component | Technology | Lines |
|-----------|-----------|-------|
| Engine | OCaml | 6987 |
| Knowledge graph | .om5 files (s-expression) | 8743 |
| Computation rules | .tantra4 files (s-expression) | 2949 |
| Word/metadata | .shabda files (key-value) | ~3000 |
| Analysis tools | Python (upakarana) | ~5000 |
| Tests | Python (pytest) | ~3000 |
""")

# Link sections
sections = [s1, s2, s3, s4, s5, s6, s7]
for s in sections:
    if s:
        link("doc-51", s, "krama", "section ordering")

print("\nDone! Created sections:", sections)
