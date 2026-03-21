# Kosha Darshana — What Domain Knowledge Reveals About Its Structure

## Overview — 1072 nodes across 17 subdomains

Kosha layer: 1072 nodes, 15250 lines, 17 subdomains + 126 top-level nodes.

Kosha is domain knowledge — what things CONTAIN, how they work, what they're made of. Unlike sangati (structural truth), kosha describes the world's content. The biggest subdomains: math(186), physics(191), yantra(110), chemistry(84), computation(71), biology(50), common-sense(48).

Key numbers:
- 456 nodes (43%) have no swarupa — nearly half lack identity declaration
- 1516 orphan edge targets (738 unique names exist nowhere)
- 69 connected components (main: 966 nodes, 68 islands)
- 600 varga edges across 57 categories — varga is heavily used in kosha (vs 0 in sangati)
- Edges point to: kosha(3542), sangati(2007), bhasha(296), mantra(149), nowhere(1516)

Relation usage differs from sangati:
- yukta dominates: 2618 uses, 78% of nodes (kosha nodes say what they're endowed with)
- varga used: 600 uses, 44% (category membership — absent in sangati)
- pratipaksha slightly better: 16 uses vs sangati's 6
- drishthanta, vishesa still at 0

## The 126 English Bridge Nodes — top-level kosha

126 kosha nodes sit at the top level (no subdirectory). 101 have no swarupa, 107 have no shabda. But 114 have abheda edges — they are English-to-Sanskrit bridges.

Pattern: each top-level node is an English concept that declares abheda (non-difference) with a sangati or deeper kosha node:
- aging → abheda → kshaya (decay)
- conservation → abheda → purna (fullness)
- entropy → abheda → kshaya
- evolution → abheda → vivartana (transformation)
- zero → abheda → shunya
- infinity → abheda → ananta
- wave-particle → abheda → shiva-shakti
- logic → abheda → nyaya
- growth → abheda → vriddhi

These are NOT orphans — they're the concept-mapping layer. English words finding their sangati ground. But they have no swarupa (they don't declare what kind of thing they are), no shabda (no metadata), and no varga (no category). They exist only to say "this English word IS that Sanskrit concept."

This is functionally similar to what bhasha/english does, but these are in kosha layer. The question: should these be bhasha nodes instead? Or does kosha correctly hold them because they're domain-knowledge bridges rather than linguistic surface?

## Math — 186 nodes, the operations/properties/structures pattern

Math has 186 nodes organized by: algebra(27), calculus(11), complexity(12), geometry(52), graph(19), logic(21), number(76), probability(13), set(15), + 17 direct nodes.

Each subdomain uses a consistent three-category split:
- structures (88 nodes, 6.9 avg edges) — what exists: group, ring, field, vector-space, graph, set
- operations (35 nodes, 5.1 avg edges) — what acts: addition, multiplication, union, composition
- properties (30 nodes, 5.9 avg edges) — what holds: commutativity, associativity, continuity
- domain-root (32 nodes, 5.2 avg edges) — category headers and uncategorized

Identity gaps: 87 nodes (47%) have no swarupa. The structures are well-defined but operations and properties often lack IS-A declaration. The domain-root nodes (17 direct under kosha/math/) are mostly category headers with no swarupa.

Swarupa chains: float ← 10 children (the numeric tower). eka-eka(bijection) ← 5 children. morphism ← 4 children. set ← 3 children. The math IS-A hierarchy is thin compared to sangati's.

Hubs: number(50 incoming), float(41), set(38), matra(38). Everything in math points to number and float. set is the second gravitational center. matra (measure) bridges math↔physics.

Shabda key usage is minimal: only 4 nodes use word:, only 1 uses eval:/arity:. The graded-ring.om node uniquely uses grade-boundary, fold-identity, and all the op keys (add, sub, mul, etc.) — it's the algebraic backbone.

Only 7 math nodes connect to physics directly (amplitude, inverse-square-law, phase, topology, vector, trigonometry-varga, corruption-in-math). The math↔physics bridge is surprisingly thin — most physics nodes reference math concepts that resolve to sangati roots, not math kosha nodes.

Only 3 math nodes have mantra counterparts (executable formulas).

## Physics — 191 nodes, the subanta/tinanta grammar bridge

Physics has 191 nodes across: kinematics(28), electromagnetism(28), quantum(27), dynamics(22), thermodynamics(16), fluid(15), energy(14), oscillation(12), processes(10), ik(9), orbital(4), constraints(4), + 25 direct.

The most striking pattern: physics nodes declare grammatical identity.
- 47 nodes declare subanta-swarupa (nominal form — these are quantities: force, energy, mass, velocity)
- 39 nodes declare tinanta-swarupa (verbal form — these are processes: collision, diffusion, escape)
- 39 also declare bhave-prayoga-swarupa (impersonal voice — processes happen, no agent acts)

This is a deep insight: physics quantities ARE nouns (subanta) and physics processes ARE verbs (tinanta) in impersonal voice (bhave-prayoga). The grammar IS the physics ontology. A force is a noun. A collision is a verb that happens without an agent.

Swarupa chains: subanta ← 47, tinanta ← 39, float ← 18 (constants), sandhi ← 7 (processes as joinings), scalar ← 6, wave ← 5, energy ← 3, spanda ← 3. The grammar roots (subanta, tinanta) are the real parents of physics, not physics concepts themselves.

The -varga pattern: 18 nodes use the suffix (circuit-varga, dynamics-varga, thermodynamics-varga...). These are category containers — subanta-swarupa nodes that organize subdomain membership. They bridge the varga system to physics subdomain hierarchy.

Hubs: velocity(29 incoming — everything needs speed), force(23), energy(20), wave(12), displacement(12). velocity dominates because kinematics+dynamics+oscillation all reference it.

54 physics nodes (28%) have no swarupa — mostly quantities in kinematics/linear (9 of 9 have no swarupa!) and quantum (12 of 27).

## Sangeetham — 30 nodes, the swara hierarchy

Sangeetham (music) has 30 nodes, only 4 without swarupa. This is one of the best-connected kosha subdomains.

The swara hierarchy: 7 individual swaras (shadja, rishabha, gandhara, madhyama, panchama, dhaivata, nishada) all declare swara-swarupa. saptaswara collects them. swara itself is naada-swarupa (primordial sound). This forms a clean tree rooted in sangati's naada.

Music concepts bridge to sangati naturally:
- andolan → spanda-swarupa (vibration)
- nyasa → viraam-swarupa (pause/rest)
- gamaka → naada-swarupa (sound ornament)
- kan-swara → sparsha-swarupa (touch/grace note)
- sangeetham → samsarga-swarupa (contact — music IS contact)

The laya (rhythm/tempo) branch: laya, kshaya-laya, vriddhi-laya. Rhythm has decay and growth forms — this maps to sangati's kshaya/vriddhi pair. laya itself has no swarupa (one of the 4 gaps).

raga is the richest node (14 edges): setu-swarupa, eka-aneka-swarupa (one-to-many — one raga yields many compositions). raga-varga is subanta-swarupa + krama (ordered sequence).

The -varga pattern appears here too: sangeetham-varga, raga-varga, swara-varga, laya-varga — all subanta-swarupa category containers.

Missing: shruti (microtone) has no swarupa, akshara (syllable/beat) has no swarupa.

## Philosophy — 26 nodes, where kosha meets sangati

Philosophy has 26 nodes, 9 without swarupa. This subdomain is the bridge between kosha (domain content) and sangati (structural truth).

Nodes like ananda, dampati, kama, maya, moksha, navarasa, rasa — these are concepts that exist as domain knowledge but carry philosophical weight that bleeds into sangati.

ananda → recognition-swarupa (6 edges). Not bliss-as-feeling but bliss-as-recognition.
dampati → samsarga-swarupa (10 edges). The couple as a form of contact.
kama → darshana-swarupa + sambandha-swarupa (12 edges). Desire is seeing + connection.
maya → 8 edges but NO swarupa. Illusion has no declared identity — philosophically apt or a gap?
ishvara → love-swarupa + truth-swarupa + purna-swarupa (9 edges). The divine is love, truth, and fullness.
moksha → ananta-swarupa (7 edges). Liberation IS the infinite.
rasa → sakshi-pratibodha-swarupa (8 edges). Aesthetic experience IS witness-awakening.
navarasa → rasa-swarupa (12 edges). The nine moods are aesthetic experience.

Several philosophy nodes have no swarupa: absolute, maya, faultless, independent, proof, self, truth, proven-knowledge. These are English-concept nodes without Sanskrit grounding — similar to the top-level bridge nodes but sitting in philosophy/.

sex → mithuna-swarupa (11 edges). shiva-mooli → rasayana-swarupa (13 edges, most in philosophy).

## English Bhasha — 106 nodes, the surface layer

English bhasha has 106 nodes across: direct(50), grammar(50), grammar/morphology(6).

60 nodes (57%) have no swarupa. The direct nodes (50) are the worst — 49 have no swarupa. These are word-mapping nodes with shabda word: keys but no graph identity.

The grammar nodes (50) are better connected: only 5 lack swarupa. Their swarupas bridge to sangati grammar:
- 16 nodes → avyaya-swarupa (indeclinable words: articles, prepositions, conjunctions)
- 11 nodes → preposition-swarupa
- 6 nodes → copula-swarupa
- 4 nodes → nipata-swarupa (particles)
- 4 nodes → conjunction-swarupa

Role distribution: 68 nodes have no role key, 29 have role:grammar, 3 have role:possession, 3 have role:pronoun, 2 have role:intent, 1 has role:rashi-bandha.

The morphology sub-subdirectory (6 nodes) has all 6 without swarupa — these are the kta-pratyaya (-ed), shatr-pratyaya (-ing) mapping nodes added recently. They link English morphology to sangati grammar pratyayas but don't declare their own nature.

Average edge density: 2.4 across English (vs 8.1 in physics, 6.1 in math). English nodes are sparse — mostly just word: key + a few edges. This is expected: bhasha IS the surface, not the depth. But the direct nodes being 98% identity-less suggests they're lookup entries, not graph citizens.

## The Varga System — category membership in kosha

varga (category membership) is used 600 times across 473 kosha nodes — 44% of all kosha. This is kosha's dominant organizational pattern, completely absent from sangati.

Top categories by membership:
- number: 39 members
- common-sense: 34
- physics: 33
- algebra: 29
- chemistry: 25
- engineering: 22
- geometry: 22
- math: 20
- thermodynamics: 19
- set: 19
- oscillation: 17
- graph: 17
- organic: 15
- materials: 15
- quantum: 15
- linear-motion: 15

The varga targets are often orphans — physics(39x), common-sense(34x), algebra(29x), geometry(29x), chemistry(28x) are referenced as varga targets but these exact names don't exist as nodes. They're implicit category labels.

The -varga suffix nodes (like circuit-varga, dynamics-varga) serve as explicit category containers — they declare subanta-swarupa and hold yukta edges to their domain's key concepts. These ARE the category infrastructure.

sangati uses sthita for membership (X-sthalam-sthita), kosha uses varga. Two different patterns for the same concept — directory membership. Neither is complete.

## Yantra — 110 nodes, the operation algebra

Yantra (machine/instrument) has 110 nodes with the lowest edge density in kosha: 2.4 avg edges. 96 have no swarupa.

These are the operation nodes — op-add, op-mul, op-sin, op-map, op-reduce, op-filter, op-bind, etc. Each declares a single edge: op-class-X-kriya (action through its operation class).

The operation classes: op-class-monoid (add, mul, and, or, append, concat — associative binary ops), op-class-projection (abs, acos, sin, sqrt — unary transforms), op-class-binary (atan2, pow, mod — non-associative binary), op-class-keyed (avrti, shabda — lookup operations), op-class-reduce (reduce, map, filter — higher-order).

The visheshanam sub-subdirectory (11 nodes) holds the ring-theoretic infrastructure: visheshanam-ring, op-class nodes, and their algebraic properties.

These 110 nodes are the executable vocabulary — what tantras can call. They're sparse because their identity IS their operation class. op-add doesn't need to say what it IS beyond op-class-monoid-kriya. But they have no varga, no sthita, no connection to the math kosha nodes they implement.

Missing link: op-add implements addition (kosha/math/number/operations/addition), but there's no edge saying so. The operation algebra and the math concepts are disconnected.

## The 738 Ghost Names — orphan targets that exist nowhere

1516 kosha edge targets (738 unique names) point to names that exist in no layer. The most referenced:

Category labels used as varga targets (don't exist as nodes):
yantra(39x), physics(39x), common-sense(34x), geometry(29x), algebra(29x), chemistry(28x), math(23x), engineering(22x), organic(15x), materials(15x), linear-motion(15x), complexity(11x), taxonomy(10x), civil(10x).

These are directory names being used as category labels. When a node says X-varga, X is often just the subdirectory name.

Infrastructure names:
setu(18x), artha(18x), upakarana(11x), domain-yantra(11x), satya-ganana(9x), conductor(9x), structures(9x), structure(8x), dynamics(8x), map(7x), cs(7x), calculus(7x).

Physics/chemistry specifics:
rotation(7x), valence-two(7x), valence-three(5x), valence-one(5x), charge(5x), particle-a(5x), particle-b(5x), horizontal(5x), distance(5x), scalar-multiplication(5x), optics(5x), shakti(5x).

Many orphans are subdirectory segments used as category names, English words without nodes, or intermediate concepts that were referenced but never defined. The 738 unique missing names vs 1072 existing nodes means kosha references almost as many concepts as it defines.

## Connected Components — 69 fragments

Kosha has 69 connected components. The main component holds 966 of 1072 nodes (90%). The 68 islands are:

Multi-node islands:
- op-bind, op-class-constructor, op-pair (3 nodes, yantra — constructor ops form their own group)
- action, knowledge-action, service (3 nodes, top-level English bridges)
- isthmus + separation-union (2 nodes)
- intrinsic-nature + self-born (2 nodes — English bridges not connecting to main graph)
- armor + fearlessness (2 nodes)
- intractable + tractable (2 nodes, complexity properties)
- humanity + society (2 nodes)

54 single-node islands including: induction, specular-reflection, identity-signature, genetics-varga, computation-varga, macro-varga, quantum-varga.

The -varga nodes form many islands because they declare subanta-swarupa but subanta resolves to sangati (not kosha), so within-kosha they're disconnected. The English bridge pairs (armor↔fearlessness, intrinsic-nature↔self-born) are connected to each other but to nothing else in kosha.

Compared to sangati (20 components, 298 in main), kosha is more connected proportionally (90% vs 93%) but has far more tiny islands. Most islands are isolated English bridges or category-only nodes.

## Cross-Layer Flow — kosha reaches everywhere

Kosha edges point to: kosha(3542), sangati(2007), bhasha(296), mantra(149), nowhere(1516).

Kosha → sangati (2007 edges): Domain knowledge declaring structural relationships. Physics quantities saying subanta-swarupa (grammar), processes saying tinanta-swarupa + bhave-prayoga (grammar+voice). This is the deepest cross-layer pattern: kosha grounds itself in sangati's grammar.

Kosha → bhasha (296 edges): Domain nodes referencing linguistic surface. Mostly via shabda word-mappings resolved through English bhasha.

Kosha → mantra (149 edges): Domain concepts linking to executable formulas. This is the computation bridge — kosha says what a concept IS, mantra says how to calculate it.

Cross-subdomain within kosha:
- biology ↔ chemistry: 70+51 = 121 edges (strongest connection)
- common-sense → physics: 82 edges (common-sense is heavily physics-grounded)
- physics → math: 32 edges (surprisingly sparse for how intertwined they should be)
- yantra → math: 48 edges (operations reference their mathematical foundations)
- 3d → physics: 39 edges (spatial reasoning needs mechanics)
- engineering → physics: 26 edges
- robotics → 3d: 23 edges, → physics: 14 edges

Weakest links: meta connects to almost nothing. finance connects only to physics(3). sangeetham connects to philosophy(5) and physics(5) equally.

## Patterns Across Layers — what the full picture shows

Comparing kosha and sangati reveals structural principles:

**Relation signatures differ by layer:**
- sangati: swarupa(79%), sthita(72%), yukta(63%) — identity and location dominate
- kosha: yukta(78%), sthita(58%), swarupa(57%) — endowment dominates, identity weaker
- kosha emphasizes what things HAVE (yukta); sangati emphasizes what things ARE (swarupa)

**Category systems:**
- sangati uses sthita (X-sthalam-sthita) for membership — philosophical: you SIT in a space
- kosha uses varga for membership — categorical: you BELONG to a class
- Neither is complete. Both are partially applied.

**The grammar bridge:**
- Physics uses sangati grammar nodes as swarupa targets: subanta (47x), tinanta (39x), bhave-prayoga (39x)
- This means physics defines itself THROUGH grammar — quantities are nouns, processes are verbs
- But the grammar nodes in sangati are the most disconnected (19 islands). The bridge's foundation is weak.

**The bhasha ghost spans all layers:**
- 21 sangati nodes claim bhasha-swarupa
- bhasha/english has 60 nodes with no swarupa
- Top-level kosha has 126 English bridge nodes
- bhasha itself exists NOWHERE. The concept of language-as-nature has no node in any layer.

**Edge density gradient:**
- sangati average: 5.7 edges/node
- kosha average: 7.0 edges/node (but yantra drags this down at 2.4)
- kosha/physics: 8.1, kosha/biology: 12.5, kosha/chemistry: 10.0
- bhasha/english: 2.4, sangati/grammar: 1.2
- The linguistic layers are sparse; the scientific layers are dense.

**What exists nowhere but is heavily referenced across ALL layers:**
bhasha(21x), tantra(9x), dharma(4x), artha(22x), shakti(7x), eka(7x), upakarana(11x), setu(18x). These are foundational concepts that every layer assumes but nobody defines.

## What Needs to Happen — the kosha migration target

**Top-level bridge nodes (126):**
- Decide: should English concept bridges be kosha or bhasha?
- If kosha: add swarupa, shabda, varga to all 126
- If bhasha: move them to bhasha/english/ with word: keys
- Either way, 107 missing shabda and 101 missing swarupa need filling

**Create missing foundational nodes:**
- bhasha — the root of all language nodes (21+ references, exists nowhere)
- artha — meaning (18+ references)
- setu — bridge/connection (18+ references)
- upakarana — instrument (11+ references)
- tantra — the concept of recipe/process (9+ references)

**Math gaps:**
- 87 of 186 nodes lack swarupa (47%)
- operations/properties nodes need identity (what kind of operation? what kind of property?)
- Connect op-add↔addition, op-mul↔multiplication etc. (yantra↔math bridge)
- Only 7 math→physics connections — this bridge needs filling
- Only 3 mantra counterparts for 186 math concepts

**Physics gaps:**
- 54 of 191 lack swarupa (28%)
- kinematics/linear/quantities: ALL 9 have no swarupa
- quantum: 12 of 27 have no swarupa
- Direct physics nodes (25): 14 have no swarupa

**Grammar bridge:**
- sangati/grammar nodes (physics' swarupa foundation) are the most disconnected in sangati
- Fix sangati grammar first → physics swarupa chains become grounded

**Varga system:**
- 57 varga category targets, many are orphan directory names
- Either create nodes for these categories or change edges to point to existing nodes

**English bhasha:**
- 49 of 50 direct english nodes lack swarupa
- 6 morphology nodes lack swarupa
- These need connection to sangati grammar roots

**Sangeetham and philosophy:**
- Relatively well-connected (4 and 9 missing swarupa respectively)
- sangeetham: shruti, laya, akshara, domain-music need swarupa
- philosophy: maya, absolute, truth, self, proof need identity

## Shabda Extraction Design

80 English bridge nodes (abheda+yukta only) at kosha root extracted to sangati-english.shabda and moved to history/kosha-english-bridge/. 34 richer nodes remain at root (cell, mithuna, pravesa, etc. — have swarupa/kriya/phala edges, carry real domain knowledge). Design decision: shabda (surface words) separates from .om node definitions. New directory brahman/shabda/ with composable .shabda files by domain. Same format as existing parse_shabda_file. Bridge resolution via synthetic abheda edges at load time — no .om rewrites needed. Health after extraction: 1577 nodes, 7.0 density (target hit), kosha 21 components (from 69), 64% swarupa.
