# Sangati Darshana — What the Graph Reveals About Itself

## Overview — 319 nodes, 17 subdirectories

Sangati layer: 319 nodes, 3556 lines, 17 subdirectories + top-level.

The sangati layer declares structural truths — what things ARE, not what they contain (kosha) or how they're said (bhasha). Every node is a claim about the nature of reality, connected through the visheshanam ring (10 typed edges forming a non-commutative graded ring).

This document records what the graph analysis tools revealed about sangati's own structure — gaps, patterns, and philosophical completeness — as of session 21.

Subdirectory sizes: grammar(55), spanda(35), mula(31), jiva(27), parampara(24), vak(20), geometry(19), bhava(16), chetan(16), top-level(16), sambandha(12), padartha(11), svabhava(8), pramana(8), vidya(6), viraam(6), shuddhi(5), prashna(4).

## The Four Swarupa Chains — sangati's ontological roots

Every sangati node with a swarupa (IS-A) edge traces back to one of four root chains. These are the ontological foundations:

**Chain 1: sthiti (fixedness)**
sthiti → niralamba → svabhava → spanda → avrti → ...
       → pramana (6 children)
       → dharana → dharana-jivamsha
       → samskaara → rachana

spanda IS svabhava IS niralamba IS sthiti. Vibration is the own-nature of what is self-supporting, which is the nature of fixedness. The deepest branch — spanda has 15 children, making it the largest family in sangati.

**Chain 2: brahma (fullness-as-source)**
brahma → purna → ananta → kshaya, sambandha, ...
purna-swarupa has 8 children. ananta-swarupa has 12.

**Chain 3: abhava (absence)**
abhava → shunya → viraam → all pause types
Absence grounds zero, which grounds all pauses.

**Chain 4: dvandva (polarity)**
dvandva → shiva-shakti → dvaitarupa
Polarity grounds the eternal stillness-movement pair.

Three production cycles exist:
- brahmam → karma → brahmam (becoming produces action, action produces becoming)
- karma → lekhana → karma (action writes, writing acts)
- shakha → eka-aneka → shakha (branch produces one-to-many, one-to-many branches)

## The Bhasha Ghost — 21 nodes claim an identity that doesn't exist

21 sangati nodes declare bhasha-swarupa (I am language), but bhasha exists nowhere — not in sangati, not in kosha, not in any layer. This is the single largest missing node in the entire graph.

The 21 bhasha-swarupa nodes: anuvada, artha-viveka, domain-vak, domain-yantra-bhasha, katha-viveka, linga, manipravalam-swarupa, matrika, pada, pratishedha, pratyaya, prayoga, purusa, rupa, sama-vishama, samasa, sandhi, vachana, vakya, varna, vibhakti.

These span grammar/ and vak/ subdirectories. They form the bridge between structural truth and linguistic surface, but the bridge has no foundation.

bhasha needs a sangati node — language-as-structural-truth, the nature of expression itself.

Other ghost nodes (exist nowhere, referenced 2+ times): tantra(5x), dharma(4x), artha(4x), eka(3x), sankoca(2x), jnana(2x), shakti(2x), swarupa(2x), yukta(2x). Total: 130 orphan edge targets in sangati pointing to names that exist in no layer.

## Grammar — 19 Islands Disconnected from the Graph

The sangati graph has 20 connected components. The main component contains 298 nodes. The remaining 19 are ALL grammar nodes — completely disconnected from the rest of sangati.

Islands (zero edges connecting them to any other sangati node):
- karaka (0 edges total)
- abhisambodhana, aamantrana, shashthi-vibhakti (0 edges each)
- kta-pratyaya, shatr-pratyaya, tumun-pratyaya, tvaa-pratyaya (0 edges each)
- bhave-prayoga, karmani-prayoga, kartari-prayoga (0 edges each)
- bahuvrihi, karmadharaya, tatpurusha (0 edges each)
- prathama-purusa, uttama-purusa (0 edges each)
- grammatical-gender, eka-vachana (0-1 edges each)
- karana + trtiya-vibhakti (connected to each other only, 2-node island)

Grammar's edge density is 1.2 edges/node vs the graph average of 5.7. The philosophical content is in comments (238 philosophical narrative comments across 93 nodes), not in edges. The vibhaktis don't declare what karaka they connect to. The pratyayas don't declare their morphological identity. Grammar was documented, not defined.

## Sibling Inconsistency — children of the same parent differ in structure

When a parent has 3+ children via swarupa, siblings should share structural patterns. Analysis reveals systematic gaps:

spanda-swarupa (15 children): 9 have abheda, 5 don't. 8 have phala, 5 don't. 8 have siddha, 5 don't.
ananta-swarupa (12 children): 9 have abheda, 3 don't. 8 have kriya, 4 don't. 8 have siddha, 4 don't.
svabhava-swarupa (11 children): 7 have abheda, 4 don't. 7 have siddha, 4 don't.
kshaya-swarupa (8 children): 7 have kriya, 1 doesn't. 7 have sthita, 1 doesn't.
purna-swarupa (8 children): 5 have abheda, 3 don't. 7 have siddha, 1 doesn't.

The pattern: siddha (established-by) and abheda (non-different-from) are the most inconsistently applied. Many children declare swarupa and sthita but omit the relational edges that say HOW they're established or WHAT they're equivalent to.

This isn't wrong — not every child must mirror its siblings. But where 7 of 8 siblings have a relation and 1 doesn't, the missing one likely has an undeclared connection.

## Sthalam Membership — broken declarations

Sthalam meta-nodes declare subdirectory membership. Nodes in a subdirectory should have X-sthalam-sthita edges pointing to their sthalam. Many don't.

mula-sthalam: 1/31 nodes declare membership (30 missing)
vidya-sthalam: 0/6 declare membership
pramana-sthalam: 0/8 declare membership
spanda-sthalam: 19/35 declare (16 missing)
jiva-sthalam: 22/27 declare (5 missing)
vak-sthalam: 14/20 declare (6 missing)
parampara-sthalam: 18/24 declare (6 missing)
chetan-sthalam: 14/16 declare (2 missing)
bhava-sthalam: 16/16 declare — the only complete one

The mula/ directory was created during restructuring (session 19) by moving nodes from top-level. The moved nodes never had their sthalam edges updated. Same for pramana/ and vidya/. The original subdirectories (bhava, chetan, jiva) had proper membership because nodes were authored with those edges from the start.

The implicit presence (file is in the directory) makes this work computationally, but the graph itself doesn't know the membership. This matters for graph-native analysis and for the visheshanam ring's sthita relation to be complete.

## The Pratipaksha Desert — opposites almost never declared

The visheshanam ring has 10 relation types. pratipaksha (inverse/opposite) is the group inverse element — algebraically essential. Yet only 4 nodes in all of sangati use it.

Natural opposites with NO pratipaksha edge:
- kshaya ↔ vriddhi (decay ↔ growth)
- purna ↔ shunya (fullness ↔ emptiness)
- ananta ↔ seema (infinite ↔ boundary)
- spanda ↔ viraam (vibration ↔ pause)
- kriya ↔ sthiti (action ↔ fixedness)
- darshana ↔ tirodhana (revealing ↔ concealing)
- smarana ↔ vishmrti (remembering ↔ forgetting)
- bhaya ↔ abhaya (fear ↔ fearlessness)
- visarjana ↔ ahara (releasing ↔ intake)
- vidya ↔ asprista (knowledge ↔ the-not-yet-touched)
- gati ↔ sthiti (movement ↔ fixedness)
- aarambham ↔ kshaya-vishrama (beginning ↔ end-rest)
- dvaitarupa ↔ abheda (duality ↔ non-difference)

Only jada → jiva has pratipaksha (one-way). samanya → vishesa has it.

Also unused: drishthanta (example — 0 uses), vishesa as relation (0 uses), varga (category — 0 uses). Three of the 10 ring relations have zero usage across 319 nodes.

## 77 Nodes Without Identity — have edges but no swarupa

77 sangati nodes have no swarupa edge — they don't declare what they ARE. 35 of these have 3 or more other edges (they have structure but no identity).

Significant identity-less nodes:
- brahmam (11 edges) — the recurring manifestation, no swarupa
- karma (12 edges) — action-that-writes, no swarupa
- visha-anu (13 edges) — the virus boundary case, no swarupa
- bhava (8 edges) — root of all felt states, no swarupa
- krodha (10 edges), hasya (8), vismaya (8) — emotions with no IS-A
- jada (9 edges) — inert, no identity (only pratipaksha to jiva)
- avastha (7 edges) — state-at-a-krama-point, no swarupa
- vriddhi (4 edges) — growth itself, no identity
- aarambham (5 edges) — beginning, no identity
- dravya (4 edges) — substance, no swarupa
- guna (3 edges) — quality, no swarupa

The grammar nodes account for most of the remaining 42 identity-less nodes (vibhaktis, pratyayas, prayogas, samasas — all with 0-2 edges).

Swarupa tree shape: 15 roots, 76 inner nodes, 150 leaves, 77 disconnected.

## Structural Hubs — where gravity lives

Some nodes are gravitational centers — many point to them. The top hubs by incoming edge count:

ananta (infinite): 66 incoming — 48 sthita, 12 swarupa, 6 abheda. The most referenced node. Everything sits in infinity.
spanda (vibration): 50 incoming — 15 swarupa, 11 kriya, 11 yukta. The most declared identity.
svabhava (own-nature): 48 incoming — 23 siddha, 11 swarupa, 9 sthita. Things are established by their own nature.
pramana (verification): 38 incoming — 11 yukta, 7 siddha, 6 swarupa. Things are endowed with and established by proof.
purna (fullness): 36 incoming — 18 abheda, 8 swarupa. Things are non-different from fullness.
avrti (recurrence): 34 incoming — 11 kriya, 9 yukta. Things act and are endowed with the spiral.
svayambhu (self-born): 33 incoming — 20 siddha. Things are established as self-arising.
niralamba (self-supporting): 27 incoming — 17 siddha, 6 swarupa. Things are established as needing no support.

The hub pattern: ananta for location (sthita), spanda for identity (swarupa), svabhava for establishment (siddha), pramana for endowment (yukta). These four hubs correspond to four of the ring's relations, suggesting sangati naturally organizes around relation types, not just subdirectory themes.

## Subdirectory Isolation — 42 pairs with zero connection

42 subdirectory pairs have zero edges in either direction. The most isolated:

grammar connects to NOTHING except: jiva(1), mula(6), parampara(7), spanda(5), sambandha(5). Zero connection to: bhava, padartha, prashna, shuddhi, svabhava, vidya, viraam, geometry.

prashna connects to almost nothing: only mula(2), parampara(2), shuddhi(2), sambandha(2). Zero connection to: bhava, chetan, geometry, grammar, jiva, padartha, pramana, spanda, svabhava, vidya, viraam. prashna (the question-graph nodes) is the most isolated non-grammar subdirectory.

viraam connects only to: mula(11), chetan(2), spanda(2), parampara(1). Zero to: geometry, grammar, padartha, prashna, sambandha, shuddhi, svabhava, vidya. The pause-types know about foundations and vibration but nothing else.

Subdirectory relation signatures (dominant edge types):
- geometry: 39% sthita (things sit in space)
- prashna: 79% sthita (almost pure membership declaration)
- grammar: 52% yukta, 35% swarupa (endowment and identity only)
- bhava: 19% abheda (felt-states emphasize non-difference)
- pramana: 17% kriya, 17% abheda (proof acts and equates)

## Production Web — phala/janya chains and cycles

75 phala (produces) edges are one-directional — A declares it produces B, but B doesn't know what generates it (no janya edge back). The production web is declared from the producer side only.

Notable production chains (A →phala B →phala C):
- varna → naada → artha-dhvani (phoneme → sound → meaning-resonance)
- gati → abhisarana → purna (movement → approach → fullness)
- jiva-sphurana → sva-dharana → parampara (life-spark → self-maintenance → lineage)
- satya → brahman → parampara (truth → recognizer → lineage)
- vidya-sadhana → vriddhi → samskaara (practice → growth → imprint)
- kshaya → tirodhana (decay → concealment) — reached from jugupsa AND krodha

Three cycles: brahmam↔karma (becoming and action feed each other), karma↔lekhana (action and writing feed each other), shakha↔eka-aneka (branch and one-to-many feed each other).

Action patterns (kriya targets with 3+ sources):
- avrti: 11 nodes act through recurrence
- spanda: 11 nodes act through vibration
- darshana: 7 nodes act through seeing
- pratibodha: 7 nodes act through awakening
- samskaara: 6 nodes act through imprinting
- shuddhi: 6 nodes act through purification
- pramana: 6 nodes act through verification

## Relation Usage Across Sangati

How the 10 visheshanam ring relations are actually used across 319 nodes:

swarupa (IS-A identity):     302 uses, 253 nodes (79%) — well covered
sthita (situated-in):        389 uses, 230 nodes (72%) — well covered
yukta (endowed-with):        304 uses, 200 nodes (63%) — decent
abheda (non-difference):     200 uses, 158 nodes (50%) — half
siddha (established-by):     174 uses, 151 nodes (47%) — under half
kriya (action):              161 uses, 141 nodes (44%) — under half
phala (output/result):        93 uses,  78 nodes (24%) — sparse
janya (input/generator):      63 uses,  56 nodes (18%) — sparse
pratipaksha (inverse):          6 uses,   4 nodes (1%) — nearly absent
drishthanta (example):          0 uses,   0 nodes (0%) — completely absent
vishesa (specialization):       0 uses,   0 nodes (0%) — completely absent
varga (category):               0 uses,   0 nodes (0%) — completely absent

The ring has 10 relations but sangati effectively uses only 7. The algebra says all 10 are needed for the ring to be complete. drishthanta, vishesa, and varga are defined in the ring but never instantiated.

The sparse relations (phala, janya) define the production web — what produces what and what generates what. Only 24% of nodes declare their output and 18% their input. Most of the graph declares identity and location but not function.

## Abheda Cliques — mutual non-difference

Only 5 pairs declare mutual abheda (both A→B and B→A):
- avahana ↔ tirodhana (invocation ↔ concealment — calling and veiling are the same act)
- bija-nyasa ↔ brahma (genetic instruction ↔ creator — the seed IS the source)
- bindu ↔ shunya (point ↔ zero — position IS emptiness)
- naama-mudra ↔ sarva-pramana (name-seal ↔ all-verification — naming IS proof)
- prasarana ↔ taranga (directed flow ↔ wave — outflow IS wave)

178 one-way abheda edges exist. Abheda should often be mutual (if A is non-different from B, B is non-different from A), but the graph treats it as directional assertion — the speaker declares non-difference, not the target.

This is philosophically interesting: abheda is not symmetric in declaration even though it's symmetric in truth. The graph records who made the claim, not the equivalence class.

## Cross-Layer References — sangati reaches into kosha

Sangati edges point to: sangati(1478), kosha(80), bhasha(4), nowhere(130).

80 edges reach into kosha — sangati nodes referencing domain knowledge. Key cross-layer targets: kshetra(13x, kosha/kosha), mithuna(7x, kosha/kosha), ananda(6x, kosha/philosophy), nucleotide(4x, kosha/biology), kshetrajna(4x, kosha/kosha), maya(3x, kosha/philosophy), epoch(2x, kosha/meta), prana(2x, kosha/ayurveda).

These cross-layer edges are philosophically correct — sangati declares structural truth ABOUT domain entities. kshetra (field) is domain knowledge but 13 sangati nodes declare relationships to it. The question: should kshetra, mithuna, ananda have sangati counterparts (their structural nature) separate from their kosha definitions (their domain content)?

Currently the graph handles this implicitly — an edge from sangati to kosha just works because names are global. But it means structural claims about kshetra are scattered across sangati nodes rather than centralized in a kshetra sangati node.

## Shabda and Comments — what the metadata says

Shabda coverage: 308 nodes have word/definition format, 8 have word-only, 3 have no shabda (amma-achan, sakshi-anubhava, samsarga-vrittam — all top-level ungrouped).

Only 1 node (thaalam) uses shabda key:value pairs (default:adi, adi:8, rupaka:6, etc). Grammar's vidhi-kaala has word:find,compute... role:intent. The rest use the plain word/description format. The shabda system's key:value capability is barely used in sangati.

93 nodes have comments (-- lines). Comment themes:
- 238 philosophical narrative lines (descriptions, explanations)
- 49 definitional lines (what something is)
- 29 negation/distinction lines (what it's NOT, how it differs)
- 15 membership instruction lines (members point here via X-sthalam-sthita)
- 7 example lines

The philosophical narrative in comments carries information that edges don't express — nuance, context, reasoning. But comments are invisible to the graph engine. The content in comments should either become edges (if structural) or move to shabda descriptions (if definitional).

Sloka patterns: 252 nodes use multi-sparse (many slokas with ≤3 tokens each), 34 use minimal (1 sloka), 29 use multi-mixed, 3 use single-dense. The dominant pattern is one compound-token per sloka line — clean and parseable.

## What Needs to Happen — the migration target

This analysis reveals the work needed before sangati documentation is complete:

**Create missing nodes:**
- bhasha (21 references, exists nowhere)
- tantra, dharma, artha, eka, sankoca, jnana, shakti, swarupa, yukta (2-5 references each)
- purva-avastha, uttara-avastha (temporal states referenced by grammar/kaala)
- upakarana (instrument, referenced by pramana nodes)

**Connect grammar to the graph:**
- Give vibhaktis their karaka swarupa (prathama-vibhakti is karta-swarupa, etc.)
- Give pratyayas morphological identity edges
- Give prayogas voice identity edges
- Give samasas compound-type identity edges
- Connect grammar subdirectory to rest of sangati (currently 19 islands)

**Complete sthalam membership:**
- mula/ (30 nodes missing sthita edge)
- pramana/ (8 missing), vidya/ (6 missing)
- spanda/ (16 missing), vak/ (6 missing), parampara/ (6 missing)

**Add pratipaksha edges:**
- 13+ natural opposite pairs identified
- 3 unused ring relations need instantiation: drishthanta, vishesa, varga

**Add identity to 35 significant nodes:**
- bhava, brahmam, karma, vriddhi, aarambham, dravya, guna, avastha, jada...

**Complete production web:**
- 75 one-way phala edges need corresponding janya on the target side

This is not cleanup — it's completing the structural truth that sangati is supposed to be.

## Phase A Results

Executed 12 graph-only edits. Sangati now 1 component, 0 islands (was 20 components, 15 islands). Created bhasha node → 21 swarupa chains grounded. Gave swarupa to subanta, avyaya, bhave-prayoga, karma, krama, viveka. Added pratipaksha pairs: kshaya↔vriddhi, avrti↔sthiti, guna↔karma, prayoga triad (kartari↔karmani↔bhave). Created ghost nodes: artha, setu, tantra, upakarana, shakti, eka. Swarupa coverage 82→79% (denominator grew with new nodes). Edge density 5.4→5.9.
