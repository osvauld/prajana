#!/usr/bin/env python3
"""Create the KE Pipeline Minimal Walkthrough sections in pathram2."""

import subprocess
import sys

def add_doc(title, body, parent="doc-36"):
    r = subprocess.run(
        [".venv/bin/python3", "-m", "pathram2", "add", "doc", title,
         "--body", body, "--parent", parent, "--tag", "active"],
        capture_output=True, text=True,
    )
    out = r.stdout.strip()
    print(out)
    # extract id
    if "Created:" in out:
        return out.split("Created:")[1].strip()
    return None

def link(src, tgt, rel, reason=""):
    args = [".venv/bin/python3", "-m", "pathram2", "link", src, tgt, rel]
    if reason:
        args += ["--reason", reason]
    subprocess.run(args, capture_output=True, text=True)


# --- Section 1: The Question ---
s1 = add_doc("The Question", r"""The input is a single string:

"mass is 5 kg and velocity is 10 m/s. find kinetic energy"

The expected answer is: kinetic-energy = 250

This is $\frac{1}{2} \times 5 \times 10^2 = \frac{1}{2} \times 5 \times 100 = 250$ joule.

The formula is: $KE = \frac{1}{2} m v^2$

The question has two sentences (separated by a period):
- Sentence 1: "mass is 5 kg and velocity is 10 m/s" (data)
- Sentence 2: "find kinetic energy" (intent)

The pipeline must: parse the words, bind numbers to concepts, find the right formula, compute, and return the answer. Every step works by adding triples to a growing graph.
""")

# --- Section 2: The Minimal Node Set ---
s2 = add_doc("The Minimal Node Set", r"""To answer this question, the pipeline touches exactly these nodes in the permanent graph. Each node is a row in the 3D tensor $G \in \{0,1\}^{N \times N \times R}$.

## Concept Nodes

| Node | What it is | Key edges (floor = 1) |
|------|-----------|----------------------|
| mass | a physical quantity | vishesa $\to$ linear-force-varga, matra $\to$ kilogram |
| velocity | a physical quantity | vishesa $\to$ linear-motion-varga, matra $\to$ metre-per-second |
| kinetic-energy | a physical quantity | vishesa $\to$ mechanical-energy-varga, pratipaksha $\to$ potential-energy |

These are the concepts the question talks about. Each lives in the kosha layer.

## Unit Nodes

| Node | shabda word: | shabda concepts-for-unit: | What it does |
|------|-------------|--------------------------|-------------|
| kilogram | kg, kilogram | mass, link-mass | When "kg" appears after a number, bind that number to mass |
| metre-per-second | m/s | velocity | When "m/s" appears after a number, bind that number to velocity |

Units are the bridge between human text ("5 kg") and graph concepts (mass = 5).

## The Formula Node (Mantra)

| Node | shabda | Edges |
|------|--------|-------|
| kinetic-energy-mantra | name: kinetic-energy, unit: joule | janya $\to$ mass, janya $\to$ velocity, phala $\to$ kinetic-energy |

The mantra also has krama (sequence) edges that encode the s-expression:

    (half (multiplication mass (square velocity)))

This reads: take velocity, square it, multiply by mass, halve the result.

## Operation Nodes

| Node | eval: | arity: | What it computes |
|------|-------|--------|-----------------|
| half | half | 1 | $x \mapsto x \times 0.5$ |
| multiplication | mul | 2 | $(x, y) \mapsto x \times y$ |
| square | square | 1 | $x \mapsto x^2$ |

These are pure functions. Their shabda carries the eval: key (the OCaml primitive name) and arity: (how many inputs).

## Grammar Nodes

| Node | shabda word: | Edge emitted | Role |
|------|-------------|-------------|------|
| copula | is, are, be, was, were | [word, copula, word] | Links subject to predicate |
| dvandva | and | [word, dvandva, dvandva] | Separates clauses (grade boundary) |
| vidhi-kaala | find, compute, calculate | [word, vidhi-kaala, solve-for] | Intent signal: "I want to find X" |

## Dimensions (Floors) Used

The 3D tensor has 62 floors. This question only uses a handful:

| Floor | Name | What it records |
|-------|------|----------------|
| satya | truth | "this word was found in the graph" |
| asprista-sankhya | untouched number | "a raw number, not yet bound" |
| sankhya | bound number | "number X is bound to concept Y" |
| matra | unit | "concept Y is measured in unit Z" |
| copula | linking verb | "is" connecting subject to predicate |
| dvandva | conjunction | "and" separating clauses |
| viraam | period/stop | sentence boundary |
| vidhi-kaala | imperative | "find" = intent to solve |
| swarupa | identity | X IS Y (from assertion-bandha) |
| kaala | tense | verb tense |
| vachana | number | singular/plural |
| janya | input-of | "mass is an input to the KE formula" |
| phala | result-of | "kinetic-energy is the output of the KE formula" |
| krama | sequence | "the formula steps in order" |
| kosha-janya | PPR-expanded | "nearby concept found by graph walk" |

That is 15 out of 62 floors. The rest are silent (all 0s) for this question.
""")

# --- Section 3: Step 1 build-question-graph ---
s3 = add_doc("Step 1: build-question-graph", r"""## What it does

Takes the raw sentence string. For each word:
1. Look up the word in the graph (shabda-anveshana: search naama edges)
2. If found: emit [concept, satya, concept]
3. If it is a number: emit [number, asprista-sankhya, number]
4. If a unit follows a number: emit [concept, sankhya, value] and [concept, matra, unit-node]
5. Grammar words emit their signal edge

## The input

"mass is 5 kg and velocity is 10 m/s. find kinetic energy"

Words processed left to right: mass, is, 5, kg, and, velocity, is, 10, m/s, ., find, kinetic energy

Note: "kinetic energy" is two words but the compound pre-pass merges them into "kinetic-energy" because the graph has a node with that name.

## Output: 14 triples

| # | Triple | Floor | Why |
|---|--------|-------|-----|
| 1 | [mass, satya, mass] | satya | "mass" found via naama lookup |
| 2 | [is, copula, is] | copula | "is" matches copula word: list |
| 3 | [5, asprista-sankhya, 5.] | asprista-sankhya | "5" is a number |
| 4 | [mass, sankhya, 5.] | sankhya | "kg" resolves to kilogram, concepts-for-unit = mass, so bind 5 to mass |
| 5 | [mass, matra, kilogram] | matra | unit annotation |
| 6 | [and, dvandva, dvandva] | dvandva | "and" is a conjunction |
| 7 | [velocity, satya, velocity] | satya | "velocity" found via naama lookup |
| 8 | [is, copula, is] | copula | second "is" |
| 9 | [10, asprista-sankhya, 10.] | asprista-sankhya | "10" is a number |
| 10 | [velocity, sankhya, 10.] | sankhya | "m/s" resolves to metre-per-second, concepts-for-unit = velocity |
| 11 | [velocity, matra, metre-per-second] | matra | unit annotation |
| 12 | [., viraam, .] | viraam | period = sentence boundary |
| 13 | [find, vidhi-kaala, solve-for] | vidhi-kaala | "find" = intent signal |
| 14 | [kinetic-energy, satya, kinetic-energy] | satya | compound "kinetic energy" found |

## Key mechanism: shabda-anveshana

This is a morphism from word-space to node-space. The graph has naama edges:

    kilogram --naama--> "kg"
    metre-per-second --naama--> "m/s"
    mass --naama--> "mass"

When "kg" appears, shabda-anveshana returns kilogram. Then concepts-for-unit on kilogram says "mass". So "5 kg" becomes: mass has value 5, measured in kilogram.

## What this step is in math terms

build-question-graph is a morphism: $\text{String} \to \text{Set of triples}$. Each triple is a point $(s, r, o)$ in the 3D tensor. This step activates 14 cells from 0 to 1.
""")

# --- Section 4: Step 2 assertion-bandha ---
s4 = add_doc("Step 2: assertion-bandha", r"""## What it does

Scans for subject-copula-object patterns within each grade (sentence). When it finds "X is Y" where both X and Y are graph nodes, it emits [X, swarupa, Y].

## Before (14 triples from Step 1)

## Pattern found

In sentence 1: mass ... is ... velocity. But wait --- "is" sits between "mass" (with its value) and "velocity" (next entity). The tantra sees:
- mass (satya) $\to$ is (copula) $\to$ ... $\to$ velocity (satya after copula)

So it emits: [mass, swarupa, velocity]

This is an IS-A assertion: "mass is [related to] velocity" in this sentence.

## After: 15 triples (14 + 1 new)

| # | New triple | Floor | Why |
|---|-----------|-------|-----|
| 15 | [mass, swarupa, velocity] | swarupa | copula pattern detected |

## What this step is in math terms

assertion-bandha reads the grammar structure and adds identity edges. In the boolean ring: swarupa is the multiplicative identity. If $G[\text{mass}][\text{velocity}][\text{swarupa}] = 1$, then mass and velocity are linked by identity in this question context.

Note: this swarupa edge is a question-local assertion, not a permanent graph edge. It says "in THIS question, mass and velocity are mentioned together as equals."
""")

# --- Section 5: Step 3 avrti-refine-v2 ---
s5 = add_doc("Step 3: avrti-refine-v2", r"""## What it does

Refines the question graph in two phases:

**Phase 1** (11 sub-passes, run once): sandhi-kosha, sandhi-avastha, sandhi-bandhana, vyakarana-sparsha, shashthi-possession, vibhakti-shashthi, vishesa-instance, rashi-viveka, vishesa-bandhana, rashi-anuvada.

**Phase 2** (fixpoint loop): sankhya-bandha-v2 $\to$ swarupa-anuvada $\to$ shunya-bandha-v2. Repeats until no new triples are added.

## For our question

Most Phase 1 passes are no-ops (nothing to refine --- no possessives, no rashi instances, no mithya words). The interesting work happens in Phase 2.

**vyakarana-sparsha** adds grammar annotations:
- [kinetic-energy, kaala, vartamana-kaala] --- present tense detected
- [kinetic-energy, vachana, eka-vachana] --- singular number detected

**sankhya-bandha-v2**: Already done by build-question-graph (mass=5, velocity=10 were bound at unit-recognition time). No new bindings.

**swarupa-anuvada**: No propagation needed (no chain of swarupa edges to follow).

**shunya-bandha-v2**: No unbound entities to mark as zero.

## After: 17 triples (15 + 2 new)

| # | New triple | Floor | Why |
|---|-----------|-------|-----|
| 16 | [kinetic-energy, kaala, vartamana-kaala] | kaala | grammar: present tense |
| 17 | [kinetic-energy, vachana, eka-vachana] | vachana | grammar: singular |

## What this step is in math terms

avrti-refine-v2 is a fixpoint operator: $f(G) = G$ when no new triples can be derived. It applies the ring operation $\oplus$ (OR / yukta) to accumulate triples monotonically. The graph can only grow, never shrink.
""")

# --- Section 6: Steps 4-5 grade-split + count-chain ---
s6 = add_doc("Steps 4-5: grade-split and count-chain", r"""## grade-split: What it does

Splits the flat list of triples into grades (sentences). The boundary markers are viraam (period) and dvandva (and).

## For our question

**Grade 0**: triples 1-5 (mass is 5 kg)
**Boundary**: triple 6 (and = dvandva = intra-grade boundary)
**Grade 0 continued**: triples 7-11 (velocity is 10 m/s)
**Boundary**: triple 12 (. = viraam = grade boundary)
**Grade 1**: triples 13-14 (find kinetic energy)
Plus: triples 15-17 (added by assertion-bandha and refine)

Grades are the graded ring structure: grade 0 = data, grade 1 = intent.

## count-chain: What it does

Looks for counting patterns (how many X, what is the number of Y). For our question: no counting is needed, so this is a no-op.

## After: still 17 triples (no change)

## What this step is in math terms

grade-split implements the grading of the ring: $R = R_0 \oplus R_1 \oplus R_2 \oplus \ldots$ Each grade is a sub-ring. The period (viraam) is the grade boundary --- it resets the additive index.
""")

# --- Section 7: Step 6 kosha-expand ---
s7 = add_doc("Step 6: kosha-expand (PPR)", r"""## What it does

Personalized PageRank walk from each satya node. Discovers nearby concepts in the permanent graph that might be relevant.

For each node with a satya triple, PPR walks outgoing edges with decaying probability. Nodes above a threshold get added as [seed, kosha-janya, nearby-node].

## For our question

Seeds: mass, velocity, kinetic-energy (the three satya nodes).

From mass, PPR discovers: momentum, kinetic-energy, gravitational-energy, force, kilogram, ...
From velocity, PPR discovers: momentum, kinetic-energy, acceleration, displacement, ...
From kinetic-energy, PPR discovers: potential-energy, mechanical-energy-varga, energy, momentum, velocity, mass, ...

## After: 17 + N kosha-janya triples

The exact count depends on the threshold and top-k settings. Typical: ~20-40 new triples. These are all on the kosha-janya floor.

Example new triples:
| Triple | Why |
|--------|-----|
| [mass, kosha-janya, momentum] | momentum is 1-hop from mass via yukta |
| [mass, kosha-janya, kinetic-energy] | kinetic-energy is 1-hop from mass via yukta |
| [velocity, kosha-janya, momentum] | momentum is 1-hop from velocity via yukta |
| [kinetic-energy, kosha-janya, potential-energy] | pratipaksha neighbor |
| [kinetic-energy, kosha-janya, velocity] | yukta neighbor |

## What this step is in math terms

PPR is a matrix operation on the adjacency matrix. Start with a seed vector $\mathbf{v}_0 = \mathbf{e}_{\text{mass}}$. At each step: $\mathbf{v}_{t+1} = \alpha \cdot A \cdot \mathbf{v}_t + (1-\alpha) \cdot \mathbf{v}_0$. The stationary distribution tells us which nodes are "close" to the seed. This is a cross-floor walk: it reads edges from ALL floors (yukta, swarupa, phala, janya, ...) to find neighbors.
""")

# --- Section 8: Step 7 detect-signals ---
s8 = add_doc("Step 7: detect-signals", r"""## What it does

Reads the question graph and detects what kind of answer is needed. There are 5 dispatch modes:

| Mode | When |
|------|------|
| shunya | No intent, no data --- empty question |
| anumana | "what is X" without numbers --- definition lookup |
| viveka | "is X a Y" --- yes/no classification |
| count | "how many X" --- counting |
| derive | numbers + "find X" --- computation (our case) |

## For our question

1. **extract-solve-for** scans for vidhi-kaala triples. Finds: [find, vidhi-kaala, solve-for]. The next satya node after "find" is kinetic-energy. So: solve-for = kinetic-energy.

2. **has-intent** = true (we have a vidhi-kaala edge).

3. **detect-shunya/viveka/anumana/count**: all return empty (we have numbers + intent).

4. **dispatch-mode = "derive"** (has-intent is true, no other mode matched first).

## After: 17+N triples + 3 signal triples

| Signal triple | What it means |
|--------------|---------------|
| [_signal, dispatch-mode, derive] | This is a computation question |
| [_signal, solve-for, kinetic-energy] | The target is kinetic-energy |
| [_signal, scope-entity, ""] | No scoping (e.g., "of the car") |

## What this step is in math terms

detect-signals is a classifier: it reads the boolean pattern of edges and maps to one of 5 categories. This is a morphism from the question graph to the dispatch lattice: $\text{Graph} \to \{\text{shunya}, \text{anumana}, \text{viveka}, \text{count}, \text{derive}\}$.
""")

# --- Section 9: Step 8 dispatch-answer ---
s9 = add_doc("Step 8: dispatch-answer (derive path)", r"""## What it does

Reads dispatch-mode = "derive" and calls dispatch-derive, which:

1. **propagate-derive**: Reactive propagation --- walks janya/phala edges from bound concepts to find matching mantras.

2. **match-mantra**: Finds the best mantra whose janya inputs match our bound concepts.

3. **execute-matched**: Evaluates the krama s-expression with the bound values.

4. **pramana-bandha + emit-reasoning**: Builds a proof graph (panchaavayava) and formats the answer.

## Step 8a: match-mantra

Inputs: graph with sankhya triples (mass=5, velocity=10) and solve-for=kinetic-energy.

1. **mantra-select("kinetic-energy")**: Looks for mantras with phala $\to$ kinetic-energy. Finds: kinetic-energy-mantra.

2. **forward-match**: Checks if all janya inputs of kinetic-energy-mantra have values:
   - janya $\to$ mass: has sankhya 5. $\checkmark$
   - janya $\to$ velocity: has sankhya 10. $\checkmark$
   - All inputs present. Forward match succeeds.

3. Returns: [kinetic-energy-mantra, [(mass, 5.), (velocity, 10.)], "forward"]

## Step 8b: execute-matched

The mantra has krama edges encoding: (half (multiplication mass (square velocity)))

**execute-chain** is a stack machine:

| Step | Operation | Stack before | Stack after |
|------|-----------|-------------|-------------|
| 1 | push velocity=10 | [] | [10] |
| 2 | square | [10] | [100] |
| 3 | push mass=5 | [100] | [100, 5] |
| 4 | multiplication | [100, 5] | [500] |
| 5 | half | [500] | [250] |

Result: 250

## Step 8c: format answer

phala of kinetic-energy-mantra is kinetic-energy.
Label = "kinetic-energy".
Answer = "kinetic-energy = 250"

## Step 8d: emit-reasoning (panchaavayava)

The proof is structured as 5 parts:

| Part | Sanskrit | English | Content |
|------|---------|---------|---------|
| 1 | pratijna | claim | we seek: kinetic-energy |
| 2 | hetu | reason | we know: kinetic-energy-mantra (velocity, mass $\to$ kinetic-energy) |
| 3 | udaharana | example | we see: velocity=10, mass=5 |
| 4 | upanaya | application | kinetic-energy = half(mul(mass, square(velocity))) = half(mul(5, square(10))) |
| 5 | nigamana | conclusion | kinetic-energy = 250 |

## Final output

"we have: mass=5. and velocity=10..we seek: kinetic-energy.we know: kinetic-energy-mantra (velocity, mass $\to$ kinetic-energy).we see: velocity=10., mass=5..we know: momentum-mantra (velocity, mass $\to$ momentum).we see: velocity=10., mass=5..we find: kinetic-energy = 250"
""")

# --- Section 10: The Complete Triple History ---
s10 = add_doc("The Complete Triple History", r"""Every triple that exists after each step. This is the full monotonic accumulation.

## After build-question-graph (14 triples)

| # | Subject | Edge | Object |
|---|---------|------|--------|
| 1 | mass | satya | mass |
| 2 | is | copula | is |
| 3 | 5 | asprista-sankhya | 5. |
| 4 | mass | sankhya | 5. |
| 5 | mass | matra | kilogram |
| 6 | and | dvandva | dvandva |
| 7 | velocity | satya | velocity |
| 8 | is | copula | is |
| 9 | 10 | asprista-sankhya | 10. |
| 10 | velocity | sankhya | 10. |
| 11 | velocity | matra | metre-per-second |
| 12 | . | viraam | . |
| 13 | find | vidhi-kaala | solve-for |
| 14 | kinetic-energy | satya | kinetic-energy |

## After assertion-bandha (+1 = 15)

| 15 | mass | swarupa | velocity |

## After avrti-refine-v2 (+2 = 17)

| 16 | kinetic-energy | kaala | vartamana-kaala |
| 17 | kinetic-energy | vachana | eka-vachana |

## After kosha-expand (+N kosha-janya triples)

PPR triples are additive --- they only help match-mantra find candidate formulas. They do not change the core binding logic.

## After detect-signals (+3 signal triples)

| S1 | _signal | dispatch-mode | derive |
| S2 | _signal | solve-for | kinetic-energy |
| S3 | _signal | scope-entity | (empty) |

## Total: 20 + N triples

The graph only grew. No triple was ever removed. This is the monotonicity property of the boolean ring: $a \oplus b \geq a$ (OR never removes 1s).
""")

# --- Section 11: Connecting to the Math ---
s11 = add_doc("Connecting to the Math Foundations", r"""## Sets

The graph is a set of nodes $N$ with $|N| = 1604$. For our question, the active set is just $\sim$12 nodes. The triples form a set of 3-tuples $(s, r, o) \in N \times R \times N$.

## Relations

Each edge type (satya, sankhya, matra, ...) is a binary relation on the node set. For example, sankhya is a relation: $\{(\text{mass}, 5), (\text{velocity}, 10)\}$.

## Operations

The pipeline applies operations on the triple set:
- $\oplus$ (yukta / OR): adding a new triple = setting a 0 to 1
- $\otimes$ (kriya / AND): matching requires all conditions true simultaneously

## Ring Structure

The question graph forms a boolean ring:
- Additive identity (0) = shunya (no edge)
- Multiplicative identity (1) = swarupa (identity edge)
- $a \oplus a = a$ (adding the same triple twice = no change, idempotent)
- $a \otimes a = a$ (matching the same condition twice = same result)

## Graded Ring

The sentences are grades: $R = R_0 \oplus R_1$
- $R_0$ = data grade: "mass is 5 kg and velocity is 10 m/s"
- $R_1$ = intent grade: "find kinetic energy"

The period (viraam) is the grade boundary. Each grade has its own additive indexing.

## Morphisms

The pipeline is a chain of morphisms (structure-preserving maps):

$\text{String} \xrightarrow{\text{BQG}} \text{Triples} \xrightarrow{\text{refine}} \text{Triples} \xrightarrow{\text{expand}} \text{Triples} \xrightarrow{\text{detect}} \text{Triples+Signals} \xrightarrow{\text{dispatch}} \text{Answer}$

Each arrow preserves monotonicity (never removes triples) and respects the ring structure.

## The 3D Tensor

For this question, we activated exactly these cells in $G \in \{0,1\}^{N \times N \times R}$:

- $G[\text{mass}][*][\text{satya}] = 1$ (mass exists)
- $G[\text{mass}][5][\text{sankhya}] = 1$ (mass = 5)
- $G[\text{mass}][\text{kilogram}][\text{matra}] = 1$ (mass measured in kg)
- $G[\text{velocity}][*][\text{satya}] = 1$ (velocity exists)
- $G[\text{velocity}][10][\text{sankhya}] = 1$ (velocity = 10)
- $G[\text{velocity}][\text{m/s}][\text{matra}] = 1$ (velocity measured in m/s)
- $G[\text{kinetic-energy}][*][\text{satya}] = 1$ (kinetic-energy exists)
- $G[\text{find}][*][\text{vidhi-kaala}] = 1$ (intent: solve)
- $G[\text{kinetic-energy-mantra}][\text{mass}][\text{janya}] = 1$ (mass is input)
- $G[\text{kinetic-energy-mantra}][\text{velocity}][\text{janya}] = 1$ (velocity is input)
- $G[\text{kinetic-energy-mantra}][\text{kinetic-energy}][\text{phala}] = 1$ (KE is output)

The pipeline walks these 1s to find the formula and compute the answer.

## Composition (Panchaavayava)

The final answer is a 5-part proof:
1. pratijna (claim): we seek kinetic-energy
2. hetu (reason): kinetic-energy-mantra connects mass, velocity $\to$ kinetic-energy
3. udaharana (evidence): mass=5, velocity=10
4. upanaya (application): half(mul(5, square(10))) = 250
5. nigamana (conclusion): kinetic-energy = 250

This is the composition $\Sigma$ from the ring: the pipeline stages are the operations, the answer is the composed result.
""")


# Link all to parent
sections = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11]
for s in sections:
    if s:
        link("doc-36", s, "krama", "section ordering")

# Link to learning notes
link("doc-36", "doc-14", "references", "math foundations")
link("doc-36", "doc-35", "references", "full pipeline trace")

print("\nDone! Created sections:", sections)
