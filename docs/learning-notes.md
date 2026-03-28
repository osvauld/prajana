# Learning Notes — Math Foundations of Agent-X

A ground-up guide to the math behind the proof graph.

---

A SET is a collection of distinct things.

## Rules

| Rule | Example | Explanation |
|------|---------|-------------|
| No duplicates | {1, 1, 2} = {1, 2} | Repeats collapse |
| Order irrelevant | {3, 1, 2} = {1, 2, 3} | Same elements = same set |
| In or not in | 3 ∈ {1,2,3}, 5 ∉ {1,2,3} | No "half in" |

## Operations on Sets

| Operation | Symbol | Example | Result |
|-----------|--------|---------|--------|
| Union | A ∪ B | {1,2} ∪ {2,3} | {1,2,3} |
| Intersection | A ∩ B | {1,2} ∩ {2,3} | {2} |
| Difference | A \ B | {1,2,3} \ {2} | {1,3} |
| Product | A × B | {1,2} × {x,y} | {(1,x),(1,y),(2,x),(2,y)} |

## Key Concepts

| Concept | Meaning | Example |
|---------|---------|---------|
| Subset | Every element of A is in B | {1,2} ⊆ {1,2,3} |
| Empty set (∅) | Nothing; subset of everything | ∅ ⊆ {anything} |
| Cardinality | How many elements | |{a,b,c}| = 3 |


---

A RELATION is a rule applied to two elements yielding yes or no. Properties describe the RULE, not the set.

## Three Key Properties

| Property | Question | = | < | ≤ | "is parent of" |
|----------|----------|---|---|---|-----------------|
| Reflexive | Every element relates to itself? | Yes (5=5) | No (5<5?) | Yes (5≤5) | No |
| Symmetric | If A→B, does B→A? | Yes | No (3<5 but 5≮3) | No | No |
| Transitive | If A→B and B→C, does A→C? | Yes | Yes | Yes | No |

## Combined Structures

| Structure | Properties | Example | In Agent-X |
|-----------|-----------|---------|------------|
| Equivalence relation | reflexive + symmetric + transitive | "=" (sameness) | abheda (non-difference) |
| Partial order | reflexive + antisymmetric + transitive | "⊆" (subset) | sthita (rests-on) |


---

An OPERATION takes inputs and produces an output.

| Type | Inputs | Example |
|------|--------|---------|
| Unary | one | neg(5)=-5, square(3)=9 |
| Binary | two | add(3,5)=8, mul(4,3)=12 |

## Properties of a Binary Operation

| Property | Rule | + example | - example |
|----------|------|-----------|-----------|
| Closure | Result stays in set | int+int=int ✓ | nat-nat=maybe negative ✗ |
| Associativity | (a∘b)∘c = a∘(b∘c) | (2+3)+4 = 2+(3+4) ✓ | (5-3)-1 ≠ 5-(3-1) ✗ |
| Identity | Element that does nothing | 0 (x+0=x) | — |
| Inverse | Element that undoes | -5 undoes 5 | — |
| Commutativity | a∘b = b∘a | 3+5=5+3 ✓ | 3-5≠5-3 ✗ |


---

Set + operation + properties = structure. Each level adds one requirement.

## Hierarchy

    Set + closure + associativity                = Semigroup
      + identity                                 = Monoid
        + inverses                               = Group
          + commutativity                        = Abelian Group
    Two ops: ⊕=abelian group, ⊗=monoid, distributive = Ring
      + layers                                   = Graded Ring

## Monoid (closure + associativity + identity)

| Set | Operation | Identity | Inverses? |
|-----|-----------|----------|-----------|
| {0,1,2,...} | + | 0 | No (-3 not in set) |
| {0,1,2,...} | × | 1 | No (1/5 not in set) |
| All strings | concatenation | "" | No |
| All lists | append | [] | No |

## Group (monoid + inverses)

| Set | Operation | Identity | Inverse of 5 |
|-----|-----------|----------|--------------|
| {...,-2,-1,0,1,2,...} | + | 0 | -5 |
| Rationals ≠ 0 | × | 1 | 1/5 |
| {0°,90°,180°,270°} | rotation | 0° | 270° |

## Ring (two interacting operations)

| | ⊕ (first) | ⊗ (second) |
|---|---|---|
| Structure | Abelian group | Monoid |
| Identity | 0 | 1 |
| Inverses | ✓ required | ✗ not required |
| Commutative | ✓ required | ✗ not required |
| Interaction | ⊗ distributes: a⊗(b⊕c) = (a⊗b)⊕(a⊗c) | |

In Agent-X:

| Ring element | Math | Sanskrit | Meaning |
|-------------|------|----------|---------|
| ⊕ | addition | yukta | connection/gathering |
| ⊗ | multiplication | kriya | action/transformation |
| 0 | zero | shunya | emptiness |
| 1 | one | swarupa | self-nature |
| ⁻¹ | negation | pratipaksha | opposition |

## Graded Ring (ring with layers)

R = R₀ ⊕ R₁ ⊕ R₂ ⊕ ... Each layer is a grade.

| | Polynomial example | Agent-X paragraph |
|---|---|---|
| Grade 0 | constants: 5, -3 | Sentence 1 facts |
| Grade 1 | linear: 2x, -x | Sentence 2 facts |
| Grade 2 | quadratic: 3x² | Sentence 3 (question) |
| ⊕ within grade | 3x²+5x²=8x² | "mass AND velocity" |
| ⊗ across grades | 2x×3x²=6x³ | "the second joint" |
| Grade boundary | degree changes | period (viraam) |
| Distributivity | — | "respectively" |


---

## Morphism (structure-preserving map)

Rule: f(a ⊕ b) = f(a) ⊕ f(b). Combine then map = map then combine.

| Function | Preserves? | Test | Morphism? |
|----------|-----------|------|-----------|
| f(x)=2x | addition | f(3+5)=16, f(3)+f(5)=16 ✓ | Yes |
| f(x)=x² | addition | f(3+5)=64, f(3)+f(5)=34 ✗ | No |
| length(s) | concat→add | len("ab"+"cd")=4=2+2 ✓ | Yes |
| log(x) | mul→add | log(a×b)=log(a)+log(b) ✓ | Yes |

Types: homomorphism (one-way), isomorphism (perfect two-way), endomorphism (to itself).

In Agent-X the lexical morphism δ maps English to graph concepts:

| Word | δ maps to | Meaning |
|------|-----------|---------|
| "heavier" | viveka-max | discrimination-maximum |
| "flew away" | kshaya | decrease |
| "find" | vidhi-kaala | seek/imperative |
| "more" | vriddhi | increase |

δ preserves structure: "more"→vriddhi, "flew away"→kshaya, and G[vriddhi][kshaya][pratipaksha]=1.

## Composition (chaining)

(g ∘ f)(x) = g(f(x)). Do f first, then g. Associative but NOT commutative.

In Agent-X a krama IS a composition:

| Formula | Krama | Steps |
|---------|-------|-------|
| K=½mv² | half ∘ mul ∘ square | square(v), mul(m,_), half(_) |
| p=mv | mul | mul(m,v) |
| Solve K for v | sqrt ∘ div ∘ double | double(K), div(_,m), sqrt(_) |

Inversion = reverse composition + pratipaksha each step.


---

G ∈ {0,1}^{N×N×R} — a 3D box of 0s and 1s.

| Axis | Size | Meaning |
|------|------|---------|
| Rows | N=1604 | FROM which node |
| Columns | N=1604 | TO which node |
| Depth | R=62 | WHICH relation type (floor) |

Visualize as 62 stacked grids, each 1604×1604:

    Floor 62 ┌─────────┐
    ...      │  1604   │
    Floor 2  │   ×     │
    Floor 1  └─1604────┘

## Edges and Nodes

An EDGE = a 1 in the tensor:
  G[addition][subtraction][pratipaksha] = 1  ← this IS the edge
  G[addition][multiplication][pratipaksha] = 0  ← no edge

A NODE = two vertical slices through all 62 floors:
  Outgoing: G[node][*][*] — what this node points TO
  Incoming: G[*][node][*] — what points AT this node
  Full identity = both slices combined.

## Sparsity

~37,000 ones in ~159 million cells = 0.023% filled.
CSR (Compressed Sparse Row) stores only the 1s.
Adding a node: O(edges on that node), typically 5-10. Microseconds.
Density decreases as nodes grow (edges~N, cells~N²).

## Boolean Ring

Elements are {0,1}. ⊕=OR, ⊗=AND:
  0 OR 0 = 0, 0 OR 1 = 1, 1 OR 1 = 1  (accumulate)
  0 AND 0 = 0, 0 AND 1 = 0, 1 AND 1 = 1  (select)
  a AND (b OR c) = (a AND b) OR (a AND c)  (distributivity)
  Identity for OR = 0 (shunya). Identity for AND = 1 (swarupa).


---

The visheshanam ring has 10 generators. Every dynamic dimension is composed from these.

| # | Name | English | Floor question | Algebraic role | Example |
|---|------|---------|---------------|---------------|---------|
| 1 | swarupa | self-nature / IS | What IS this? | 1⊗ (mul identity) | derivative IS jivamsha |
| 2 | abheda | non-difference / EQUALS | Same as what? | ≡ (equivalence) | addition EQUALS sankalana |
| 3 | drishthanta | example / WITNESS | Concrete instance? | ∃ (existential) | monoid EXEMPLIFIED BY addition |
| 4 | sthita | foundation / RESTS ON | Built on what? | ≤ (partial order) | ring RESTS ON group |
| 5 | yukta | connection / CONNECTED TO | Associated with? | ⊕ (addition) | ring CONNECTED TO monoid |
| 6 | siddha | established / PROVEN BY | What verifies? | ⊢ (provability) | ring PROVEN BY distributivity |
| 7 | kriya | action / ACTS THROUGH | What mechanism? | ⊗ (multiplication) | derivative ACTS THROUGH change |
| 8 | phala | fruit / PRODUCES | What result? | → (consequence) | derivative PRODUCES rate, slope |
| 9 | janya | born-from / ORIGINATES | What inputs? | ← (origin) | ideal BORN FROM ring |
| 10 | pratipaksha | opposite / INVERTS | What inverse? | ⁻¹ (group inverse) | addition INVERTS subtraction |

## Ring structure

| Property | ⊕ = yukta | ⊗ = kriya |
|----------|-----------|-----------|
| Closure | ✓ | ✓ |
| Associativity | ✓ | ✓ |
| Identity | shunya (0) | swarupa (1) |
| Inverses | rahita (absence) | not required |
| Commutative | ✓ (A connected to B = B connected to A) | ✗ ("A acts through B" ≠ "B acts through A") |

## Internal pratipaksha pairs among generators

| Generator | Pratipaksha | Meaning |
|-----------|------------|---------|
| phala (produces) | janya (born from) | output ←→ input |
| yukta (connection) | rahita (absence) | presence ←→ absence |
| kriya (action) | nirodha (cessation) | doing ←→ stopping |
| abheda (sameness) | vibheda (distinction) | unity ←→ difference |


---

Generated by composing the 10 static generators. Grouped by function.

## Grammar / Morphology

| # | Name | English | Captures | Example |
|---|------|---------|----------|---------|
| 11 | sandhi | joining | morpheme combination | "running" = run+-ing |
| 12 | dhatu | verb root | stripped inflection | "flew" → fly |
| 13 | vachana | number | singular/plural | "birds" = plural |
| 14 | purusa | person | 1st/2nd/3rd | "I" vs "he" |
| 15 | naama-mudra | name stamp | entity recognition | "ball-A" |
| 16 | naama-pratibodha | name awakening | resolved entity | ball-A→object |
| 17 | dvandva | pair compound | two concepts joined | "space-time" |

## Vibhakti (Case — WHO did WHAT to WHOM)

| # | Name | Case | Question | Example |
|---|------|------|----------|---------|
| 18 | prathama | nominative | WHO? | "THE CAR moves" |
| 19 | dvitiya | accusative | WHAT? | "Find THE ENERGY" |
| 20 | trtiya | instrumental | BY WHAT? | "with A RULER" |
| 21 | chaturthi | dative | FOR WHOM? | "for THE SYSTEM" |
| 22 | panchami | ablative | FROM WHERE? | "from REST" |
| 23 | shashthi | genitive | WHOSE? | "THE CAR'S velocity" |
| 24 | saptami | locative | WHERE/WHEN? | "at THE SURFACE" |

## Kaala (Tense — WHEN)

| # | Name | Tense | Signal | Example |
|---|------|-------|--------|---------|
| 25 | bhuta-kaala | past | was, flew | "the ball FLEW" |
| 26 | vartamana-kaala | present | is, moves | "the car IS moving" |
| 27 | bhavishya-kaala | future | will | "it WILL reach" |
| 28 | vidhi-kaala | imperative | find, calculate | "FIND the energy" |
| 29 | kala | time (general) | — | temporal reference |

## Quantity / Counting

| # | Name | English | Captures | Example |
|---|------|---------|----------|---------|
| 30 | sankhya | number | numeric value | "1000 kg"→1000 |
| 31 | asprista-sankhya | untouched number | unbound number | floating "5" |
| 32 | matra | unit | measurement unit | kg, m/s, joule |
| 33 | rashi-bandha | quantity binding | number→concept | 1000→mass |

## Structure / Ordering

| # | Name | English | Captures |
|---|------|---------|----------|
| 34 | krama | sequence | formula step chain |
| 35 | kramanusara | following order | dependency |
| 36 | poorva/purva | before | predecessor |
| 37 | paschat | after | successor |
| 38 | amsha | part | part-whole |
| 39 | adhikarana | container | locus |
| 40 | garbha | inner | nested |
| 41 | antya | end | terminal |

## Truth / Validity

| # | Name | English | Captures |
|---|------|---------|----------|
| 42 | satya | truth | how established |
| 43 | mithya | false | rejected/negated |
| 44 | viraam | stop/period | grade boundary |

## Classification / Taxonomy

| # | Name | English | Captures |
|---|------|---------|----------|
| 45 | vishesa | specialization | X is a kind of Y |
| 46 | lakshana | characteristic | X is a property of Y |
| 47 | karma | action/verb | node's action |
| 48 | vrnda | group | collection |
| 49 | avastha | state | condition |
| 50 | apeksha | dependency | depends on |

## Transformation / Philosophical

| # | Name | English | Captures |
|---|------|---------|----------|
| 51 | janaka | generator | what creates this |
| 52 | prayoga | application | usage |
| 53 | rahita | without | absence (yukta⁻¹) |
| 54 | atikrama | crossing | exceeding limit |
| 55 | nirodha | cessation | stopping (kriya⁻¹) |
| 56 | paripurna | full | completeness |
| 57 | atita | beyond | transcended |
| 58 | bhanga | breaking | rupture |
| 59 | daatri | giver | source |
| 60 | vibheda | distinction | splitting (abheda⁻¹) |
| 61 | ahara | input | what feeds in |

## Dynamic = Composed from Static

| Dynamic | Composition | Meaning |
|---------|------------|---------|
| karma | kriya ⊗ kriya | action of action |
| janaka | janya⁻¹ | reverse of born-from |
| vibheda | abheda⁻¹ | reverse of equivalence |
| rahita | yukta⁻¹ | reverse of connection |
| nirodha | kriya⁻¹ | reverse of action |
| mithya | pratipaksha ⊗ satya | inverse of truth |
| satya | siddha ⊗ siddha ⊗ ... | iterated proof |


---

The pratipaksha floor — one concrete grid from the tensor.

## Arithmetic Operations Grid (Floor 10)

|  | addition | subtraction | mul | division | square | sqrt | half | double |
|---|---|---|---|---|---|---|---|---|
| addition | 0 | **1** | 0 | 0 | 0 | 0 | 0 | 0 |
| subtraction | **1** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| multiplication | 0 | 0 | 0 | **1** | 0 | 0 | 0 | 0 |
| division | 0 | 0 | **1** | 0 | 0 | 0 | 0 | 0 |
| square | 0 | 0 | 0 | 0 | 0 | **1** | 0 | 0 |
| sqrt | 0 | 0 | 0 | 0 | **1** | 0 | 0 | 0 |
| half | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **1** |
| double | 0 | 0 | 0 | 0 | 0 | 0 | **1** | 0 |

Properties: symmetric (if A→B then B→A), sparse, clean pairs.

## Full Pratipaksha Pairs

| Operation | Pratipaksha | Domain |
|-----------|------------|--------|
| addition ←→ subtraction | add ←→ sub | arithmetic |
| multiplication ←→ division | mul ←→ div | arithmetic |
| square ←→ square-root | square ←→ sqrt | power |
| half ←→ double | half ←→ double | scaling |
| logarithm ←→ exponential | log ←→ exp | transcendental |
| sine ←→ arcsine | sin ←→ arcsin | trigonometry |
| cosine ←→ arccosine | cos ←→ arccos | trigonometry |
| derivative ←→ antiderivative | d/dx ←→ ∫dx | calculus |
| max ←→ min | — | comparison |
| ceil ←→ floor | — | rounding |
| vriddhi ←→ kshaya | increase ←→ decrease | signals |
| abheda ←→ vibheda | sameness ←→ difference | philosophy |
| yukta ←→ rahita | connection ←→ absence | philosophy |
| kriya ←→ nirodha | action ←→ cessation | philosophy |
| aarambham ←→ antya | beginning ←→ end | philosophy |
| phala ←→ janya | output ←→ input | structure |


---

Within a floor: ⊕ = OR (accumulate 1s).
Across floors: ⊗ = chain (output of one floor feeds as input to next).

The walker JUMPS to whichever floor it needs. Not sequential.

## Walk: "inverse of what addition acts through"

| Step | Floor | Row | Find 1s at |
|------|-------|-----|-----------|
| 1 | kriya (7) | addition | {matra, arithmetic, vriddhi} |
| 2 | pratipaksha (10) | vriddhi | {kshaya} |

Result: kshaya (decrease). Two jumps, 60 floors untouched.

## Walk: "solve K=½mv² for velocity"

| Step | Floor | Action | Result |
|------|-------|--------|--------|
| 1 | krama (34) | read formula | [half, mul, square] |
| 2 | pratipaksha (10) | invert each | [double, div, sqrt] |
| 3 | — | reverse order | [sqrt, div, double] |
| 4 | — | evaluate | v = sqrt(2K/m) |

## Non-commutativity

| Walk order | Path | Result |
|------------|------|--------|
| kriya ⊗ pratipaksha | addition→kriya→vriddhi→pratipaksha→kshaya | inverse of mechanism |
| pratipaksha ⊗ kriya | addition→pratipaksha→subtraction→kriya→??? | mechanism of inverse |

Different answers. Floor order matters.

## Janya + Phala Grids (formula inputs/outputs)

Janya floor (inputs):

|  | mass | velocity | acceleration |
|---|---|---|---|
| KE-mantra | **1** | **1** | 0 |
| momentum-mantra | **1** | **1** | 0 |
| force-mantra | **1** | 0 | **1** |

Phala floor (outputs):

|  | kinetic-energy | momentum | force |
|---|---|---|---|
| KE-mantra | **1** | 0 | 0 |
| momentum-mantra | 0 | **1** | 0 |
| force-mantra | 0 | 0 | **1** |

Both floors together: KE-mantra takes {mass,velocity} → produces {kinetic-energy}.


---

A question IS a tantra. Same structure as a mantra.

| | Mantra (formula) | Question |
|---|---|---|
| janya | mass, velocity | English words |
| krama | half ∘ mul ∘ square | construct ∘ assert ∘ refine ∘ expand ∘ detect ∘ dispatch ∘ emit |
| phala | 250 (number) | panchaavayava proof |
| temporary | variable bindings | 1s on dynamic floors |

## Pipeline Stages

| Stage | Input | Output | Mechanism | Type |
|-------|-------|--------|-----------|------|
| construct | sentence | raw-graph | materialize, shabda-anveshana | transducer |
| assert | raw-graph | asserted-graph | assertion-bandha | — |
| refine | asserted-graph | refined-graph | fixpoint ×13 sub-passes | endomorphism |
| expand | refined-graph | expanded-graph | PPR walk | morphism |
| detect | expanded-graph | intent-signals | signal detection | morphism |
| dispatch | intent-signals | answer | derive/count/viveka/anumana | — |
| emit | answer | proof | panchaavayava formatting | — |

Each stage only ADDS 1s. Monotonicity: question graph only grows.

## Discovery-97: Pipeline as Σ

Pipeline stages should have eval keys and pratipaksha:

| Stage | Pratipaksha | Meaning |
|-------|------------|---------|
| construct | generation | graph→sentence |
| refine | abstraction | richer→simpler |
| expand | compression | expanded→local |
| detect | synthesis | signals→graph |
| dispatch | question-generation | answer→question |
| emit | proof-checking | proof→answer |

Gap: execution is in OCaml, not graph-native. Closing this makes questions fully invertible tantras.


---

## Example 1: Physics — Kinetic Energy

Question: "mass is 5 and velocity is 10. find kinetic energy"
Answer: "we find: kinetic-energy = 250"

Graded ring:

| Grade | Sentence | Facts |
|-------|----------|-------|
| R₀ | "mass is 5 and velocity is 10" | sankhya: mass→5, velocity→10 |
| R₁ | "find kinetic energy" | vidhi-kaala: KE→seek |

Floor trace:

| Stage | Floors read | Floors written | Effect |
|-------|-------------|---------------|--------|
| construct | (text) | sankhya, vidhi-kaala | mass→5, vel→10, KE→seek |
| assert | satya | satya | mass=established, vel=established |
| refine | sankhya, matra, yukta | rashi-bandha | mass→5, vel→10 |
| expand | ALL (PPR) | janya, phala, krama | pulls in KE-mantra |
| detect | vidhi-kaala, rashi-bandha | intent | mode=derive, target=KE |
| dispatch | krama | sankhya, satya | evaluates formula |
| emit | all | (text) | panchaavayava proof |

Krama evaluation:

| Step | Operation | eval | Input | Output |
|------|-----------|------|-------|--------|
| 1 | square | square | velocity=10 | 100 |
| 2 | multiplication | mul | mass=5, 100 | 500 |
| 3 | half | half | 500 | **250** |

## Example 2: Count Addition (Graded Ring)

Question: "3 birds sat on a tree. 2 more came. how many birds are there in total"
Answer: "5 bird there total"

| Grade | Sentence | Signal | δ mapping |
|-------|----------|--------|-----------|
| R₀ | "3 birds sat on a tree" | sankhya=3 | δ("sat")→sthita |
| R₁ | "2 more came" | sankhya=2 | δ("more")→vriddhi (increase) |
| R₂ | "how many birds total" | prashna | δ("total")→sum |

Count fold:

| Step | acc | ⊕ direction | value | result |
|------|-----|-------------|-------|--------|
| start | 0 | — | shunya | 0 |
| R₀ | 0⊕3 | vriddhi→add | 3 | **3** |
| R₁ | 3⊕2 | vriddhi→add | 2 | **5** |

## Example 3: Count Subtraction (Pratipaksha)

Question: "10 birds sat on a tree. 3 flew away. how many birds are left"
Answer: "7 bird left"

| Grade | Sentence | Signal | δ mapping |
|-------|----------|--------|-----------|
| R₀ | "10 birds sat on a tree" | sankhya=10 | — |
| R₁ | "3 flew away" | sankhya=3 | δ("flew away")→**kshaya** |
| R₂ | "how many birds left" | prashna | — |

Critical edge: G[vriddhi][kshaya][pratipaksha] = 1

| Step | acc | ⊕ direction | value | result |
|------|-----|-------------|-------|--------|
| start | 0 | — | shunya | 0 |
| R₀ | 0⊕10 | vriddhi→add | 10 | **10** |
| R₁ | 10⊖3 | kshaya→sub | 3 | **7** |

One edge on floor 10 determines add vs subtract.

## Example 4: Comparison (Viveka)

Question: "ball-A has mass 5. ball-B has mass 3. which is heavier"
Answer: "ball-A is viveka-max"

| Grade | Sentence | Entity | Value |
|-------|----------|--------|-------|
| R₀ | "ball-A has mass 5" | ball-A | mass→5 |
| R₁ | "ball-B has mass 3" | ball-B | mass→3 |
| R₂ | "which is heavier" | — | δ("heavier")→viveka-max |

Cross-entity ⊗: select across grades, compare, return max.

## Example 5: Force (Chain Derivation)

Question: "mass is 10 and acceleration is 5. find force"
Answer: "we find: force = 50"

| Step | Operation | Input | Output |
|------|-----------|-------|--------|
| 1 | multiplication | mass=10, acceleration=5 | **50** |

Mantra: force-mantra, krama=(multiplication mass acceleration), F=ma.


---

## Ring Vocabulary

| Symbol | Sanskrit | English | Role |
|--------|----------|---------|------|
| ⊕ | yukta | connection | additive, commutative |
| ⊗ | kriya | action | multiplicative, non-commutative |
| 0 | shunya | emptiness | additive identity, fold seed |
| 1 | swarupa | self-nature | multiplicative identity |
| ⁻¹ | pratipaksha | opposition | group inverse |

## Graph Vocabulary

| Sanskrit | English | What it is |
|----------|---------|-----------|
| nigamana | conclusion | a node (truth-that-holds) |
| visheshanam | relation | edge type (one of 62 floors) |
| satya | truth | truth score |
| shabda | word | key-value metadata on nodes |
| tantra | program | declarative composition |
| mantra | formula | janya→phala via krama |
| krama | sequence | ordered operation chain |
| Σ | operation set | all nodes with eval keys |

## Panchaavayava (Five-Limbed Proof)

| Step | Sanskrit | English | Role |
|------|----------|---------|------|
| 1 | pratijna | thesis | states givens |
| 2 | hetu | reason | states sought |
| 3 | udaharana | example | shows formula |
| 4 | upanaya | application | substitutes values |
| 5 | nigamana | conclusion | states answer |


---

