# Visheshanam Algebra Plan

Status: Draft v1.0
Owner: OpenCode + user
Scope: Encode the algebraic properties of the 10 edge relation types as first-class graph
objects, enforce structural consequences at load time, weight satya convergence by
epistemic strength, upgrade chain_resolve to scored beam search, and connect the
op-class monoid to the math-domain algebraic tower (monoid → ring → field).

---

## Background and Motivation

The 10 visheshanam (edge types: Swarupa, Abheda, Drishthanta, Sthita, Yukta, Siddha,
Kriya, Phala, Janya, Pratipaksha) are currently opaque OCaml enum tags. Their algebraic
properties — symmetry, transitivity, duality, involution, congruence — are implicit in the
code (e.g. setu.ml treats Abheda bidirectionally) but not encoded anywhere, not enforced
structurally, and not exploited computationally.

Additionally:
- The math kosha encodes up to groups but has no monoid/ring/field tower.
- The op-class monoid (built in the arity plan) is disconnected from the math-domain
  concept of a monoid.
- chain_resolve uses a plain FIFO BFS — path quality is not considered.
- join() in proof_graph.ml silently overwrites nodes instead of merging edges.

---

## CS/Math Analysis Summary

### The 10 visheshanam as algebraic objects

| Relation   | CS mapping                        | Key properties                              |
|------------|-----------------------------------|---------------------------------------------|
| Swarupa    | Subtype / identity morphism       | symmetric, transitive, reflexive, congruence, composable |
| Abheda     | Equivalence class / quotient type | symmetric, transitive, congruence, composable |
| Pratipaksha| Group inverse / involution        | symmetric, involutive                       |
| Phala      | Function codomain / return type   | antisymmetric, dual=Janya                   |
| Janya      | Generator / left adjoint          | antisymmetric, dual=Phala                   |
| Yukta      | Product component / conjunction   | symmetric, ring-op=add                      |
| Sthita     | Dependency / partial order        | antisymmetric, transitive, composable       |
| Kriya      | Morphism / function application   | antisymmetric, composable, ring-op=mul      |
| Siddha     | Entailment / proof certification  | antisymmetric                               |
| Drishthanta| Witness / proof term              | antisymmetric                               |

Ring-op interpretation: Yukta = additive join (commutative), Kriya = multiplicative
composition (directional). The relation algebra of the graph is ring-like: Yukta joins,
Kriya composes, Pratipaksha inverts.

### Graph structure facts

- Typed directed unweighted multigraph (no weight field on typed_edge).
- Scale-free topology: hub nodes (domain-math, ananta, svabhava, spanda, avrti).
- NOT a DAG: 6 Sthita 2-cycles, 5 Yukta 2-cycles, 3 Phala 2-cycles.
- Yukta edges are unidirectional in .om files despite being semantically symmetric
  (2265 edges, reverse almost never written).
- Pratipaksha in math files IS already bidirectional (authors write both directions).
- Phala/Janya dual relationship almost never complete (465 Phala, 161 Janya — most
  missing their inverse direction).
- satya_ganana uses Jacobi iteration, contraction rate 0.70 — always converges in ≤20
  steps regardless of cycles.

### chain_resolve analysis

- Plain FIFO Queue — no cost, no score, no priority.
- First-found wins. No comparison of alternative paths.
- 4-hop max depth, fixed candidate set (from_target + from_knowns + bridge tantras).
- Optimizing for: reachability only.
- Correct algorithm: NOT Dijkstra (no single target, no additive cost).
  NOT pure BFS (we want epistemically better paths, not just shorter ones).
  RIGHT algorithm: beam search — expand highest-scored states first, stop at first
  found. This is exploratory (no fixed goal cost) but guided (satya + relation weight).

### Math kosha gap

- group.om encodes all 4 group axioms via edge types.
- No monoid.om, ring.om, field.om, distributivity.om.
- op-class-monoid (from arity plan) is disconnected from the math concept.
- polynomial.om and vector-space.om implicitly encode ring structure but unnamed.

---

## Property Table (source of truth — lives in .om files, not OCaml constants)

| Node                       | sym | antisym | trans | refl | invol | cong | comp | dual  | ring-op | weight |
|----------------------------|-----|---------|-------|------|-------|------|------|-------|---------|--------|
| visheshanam-swarupa        | yes | —       | yes   | yes  | —     | yes  | yes  | —     | —       | 0.90   |
| visheshanam-abheda         | yes | —       | yes   | —    | —     | yes  | yes  | —     | —       | 0.85   |
| visheshanam-pratipaksha    | yes | —       | —     | —    | yes   | —    | —    | —     | —       | 0.70   |
| visheshanam-phala          | —   | yes     | —     | —    | —     | —    | —    | janya | —       | 0.75   |
| visheshanam-janya          | —   | yes     | —     | —    | —     | —    | —    | phala | —       | 0.75   |
| visheshanam-yukta          | yes | —       | —     | —    | —     | —    | —    | —     | add     | 0.50   |
| visheshanam-sthita         | —   | yes     | yes   | —    | —     | —    | yes  | —     | —       | 0.80   |
| visheshanam-kriya          | —   | yes     | —     | —    | —     | —    | yes  | —     | mul     | 0.80   |
| visheshanam-siddha         | —   | yes     | —     | —    | —     | —    | —    | —     | —       | 0.85   |
| visheshanam-drishthanta    | —   | yes     | —     | —    | —     | —    | —    | —     | —       | 0.55   |

All weights and properties are stored ONLY in the .om files. No OCaml constants for weights.
The property table is populated at startup by scan_visheshanam_properties.

---

## Three-Layer Architecture

```
Layer 1 (data):    brahman/kosha/yantra/visheshanam/   — 10 property nodes
                   brahman/kosha/math/                 — 4 new algebraic structure nodes

Layer 2 (schema):  proof_graph.ml                      — vish_props type, property table,
                                                          join() merge fix, weighted satya

Layer 3 (compute): yantra_index.ml                     — scan_visheshanam_properties,
                                                          apply_relation_axioms,
                                                          build_index call order
                   yantra_resolver.ml                  — beam search in chain_resolve
```

---

## Execution Phases

### Phase 0 — Fix join() to merge rather than overwrite
**File**: proof_graph.ml:81-84

Current join() calls Hashtbl.replace (overwrites) and prepends new edges to all_edges,
leaving the old node's edges as orphaned duplicates in all_edges. Fix: if the node already
exists, merge its edges (deduplicating by source+target+relation triple) instead of
overwriting. Only add genuinely new edges to all_edges.

This is the safe primitive that all subsequent phases depend on (symmetry pass, tantra
registration). The existing register_tantra_in_graph already does this merge pattern
manually — fix() makes it the default behavior of join.

Run regression after this change alone (all 49 tests must pass).

### Phase 1 — New .om files (data layer)

#### Phase 1a — brahman/kosha/yantra/visheshanam/ (10 files)

One file per visheshanam. Each: `kosha visheshanam-<name>` with a descriptive sloka
connecting to the Sanskrit concept, and `shabda` carrying all property flags.

shabda key format:
  symmetric:yes|no   antisymmetric:yes|no   transitive:yes|no   reflexive:yes|no
  involutive:yes|no  congruence:yes|no       composable:yes|no
  dual:<name>        ring-op:add|mul         satya-weight:<float>

Only non-default (non-false, non-absent) keys need to be written.

Sloka connects each visheshanam node to its Sanskrit source concept and to its algebraic
class (e.g. visheshanam-abheda has "equivalence-relation-abheda domain-yantra-sthita").

#### Phase 1b — brahman/kosha/math/ (4 files)

monoid.om:
  group-sthita, associativity-yukta, identity-yukta
  op-class-monoid-abheda             ← bridges to the arity system
  addition-drishthanta, multiplication-drishthanta
  domain-math-sthita

ring.om:
  group-sthita
  addition-kriya, multiplication-kriya
  distributivity-siddha
  monoid-yukta
  integer-drishthanta, polynomial-drishthanta
  domain-math-sthita

field.om:
  ring-sthita
  pratipaksha-yukta
  rational-drishthanta, real-drishthanta
  division-siddha
  domain-math-sthita

distributivity.om:
  ring-siddha
  multiplication-kriya, addition-kriya
  domain-math-sthita

Run regression after .om files written (build only, no OCaml change yet).

### Phase 2 — Add vish_props type and global table (proof_graph.ml)

Add to proof_graph.ml:

```ocaml
type vish_props = {
  vp_symmetric     : bool;
  vp_antisymmetric : bool;
  vp_transitive    : bool;
  vp_reflexive     : bool;
  vp_involutive    : bool;
  vp_congruence    : bool;
  vp_composable    : bool;
  vp_dual          : visheshanam option;
  vp_ring_op       : [`Add | `Mul | `None];
  vp_satya_weight  : float;
}

val default_vish_props : vish_props
val vish_props_of : visheshanam -> vish_props
val register_vish_props : visheshanam -> vish_props -> unit
```

The global table `_visheshanam_props : (visheshanam, vish_props) Hashtbl.t` is module-level
mutable (like _tantra_arities and _graph_arities in yantra_parser.ml).

`vish_props_of` returns `default_vish_props` (all false, weight=0.70) if the table has not
yet been populated — this is the bootstrap case before scan_visheshanam_properties runs.

### Phase 3 — Add regression tests for satya-sensitive paths

Add tests to run-regression.sh that exercise graph structure sensitive to satya scoring:
- context-score: edge connectivity scoring used by resolution
- abheda-of: Abheda-based name matching used by to_english
- domain-of + abheda on new Phase 1b nodes: verify monoid/ring/field loaded correctly

These tests create the safety net for Phase 5 (PPR replaces satya_ganana) and Phase 6
(beam search). If PPR breaks graph resolution, these tests catch it.

Tests must pass BEFORE proceeding to Phase 5.

### Phase 4 — scan_visheshanam_properties + apply_relation_axioms (yantra_index.ml)

#### scan_visheshanam_properties (k : proof_graph) : unit

Reads the 10 visheshanam-* nodes from the graph. For each:
- Parses its shabda key:value pairs.
- Maps property flags to vish_props fields.
- Maps dual:<name> string to visheshanam option via visheshanam_of_string.
- Maps ring-op:add|mul to the polymorphic variant.
- Calls Proof_graph.register_vish_props.

Called FIRST in build_index (before scan_graph_op_arities and before tantra scan).

#### apply_relation_axioms (k : proof_graph) : int * (string * int * int) list

Iterates all edges in all_edges. For each edge (source, relation, target):
- If vp_symmetric: add (target, relation, source) if not already present.
- If vp_dual = Some d: add (target, d, source) if not already present.

Uses the safe merge pattern (same as register_tantra_in_graph lines 62-75, not raw join).

Returns (total_added, [(relation_name, n_added, n_already_present); ...]) for the startup
message.

Emits startup line:
  relation-axioms: added N edges
    yukta:       A added / B already present
    abheda:      C added / D already present
    swarupa:     E added / F already present
    pratipaksha: 0 added / 12 already present   ← confirms math files are correct
    phala→janya: G added
    janya→phala: H added

No satya_ganana re-run needed — raw_satya is a pure local function, unaffected by
new edges. PPR will account for new edges at query time.

#### Updated build_index call order

  1. scan_visheshanam_properties k    ← new: load property table
  2. scan_graph_op_arities k          ← existing: op arities
  3. apply_relation_axioms k          ← new: structural completion (emits startup message)
  4. pre_scan_arities tantra_dirs     ← existing: tantra headers
  5. load_tantra_dir                  ← existing: full tantra parse

Run regression after Phase 4 (symmetry edges added, new edges in graph).

### Phase 5 — Remove satya_ganana; add structure-driven PPR engine (proof_graph.ml)

#### Core insight: no hardcoded question types

Earlier designs used a `question_type` enum (QComputation, QDefinition, etc.) with a
hardcoded affinity table. This was discarded. The right design derives everything from
the query's own graph structure — no enums, no lookup tables, no constants except alpha.

The query carries three structural signals that together determine how exploration
should be weighted:

  1. binding_density  = |known_bindings| / (|target_edges| + 1)
       many bindings, few target edges → tightly specified → prefer short paths
       few bindings, many target edges → open exploration → allow depth

  2. link_ratio = count(bindings with direct edge to target) / (|known_bindings| + 1)
       bindings that touch target directly → computational query → short path
       no direct links → conceptual query → depth OK

  3. computational_ratio = (Sthita + Phala + Kriya edges on target) / total_target_edges
       target is computable → short path
       target is conceptual (Abheda, Yukta, Drishthanta dominant) → depth OK

  depth_affinity = geometric_mean(binding_density, link_ratio, computational_ratio)
                 = (binding_density × link_ratio × computational_ratio) ^ (1/3)
  clamped to [0, 1].

  depth_affinity = 1.0 → pure BFS, PPR only breaks ties within same depth
  depth_affinity = 0.0 → pure PPR, depth has no weight, follow strongest signal

Examples:
  "kinetic-energy when mass=10, velocity=6"
    → binding_density high (2 bindings, few target edges)
    → link_ratio high (mass and velocity have Sthita edges to kinetic-energy)
    → computational_ratio high (kinetic-energy has many Sthita/Phala edges)
    → depth_affinity ≈ 0.85 → strongly prefers 2-step path

  "what is kinetic-energy" (no bindings)
    → binding_density = 0, link_ratio = 0
    → depth_affinity = 0 → pure PPR, explores freely via Abheda/Swarupa

  "what uses addition" (no bindings, conceptual target)
    → binding_density = 0, link_ratio = 0
    → depth_affinity = 0 → pure PPR, follows Janya/Phala outward

#### Conductance: also structure-derived

Instead of a hardcoded question_type_affinity table, conductance boost per relation type
is derived from the seed neighborhood's own edge profile:

  seed_edge_freq(relation) = count(relation in edges of all seed nodes) / total_seed_edges
  conductance(relation) = vp_satya_weight(relation) × (1 + seed_edge_freq(relation))

If the seed nodes have lots of Sthita edges, Sthita conductance gets boosted automatically.
If they have lots of Abheda edges, Abheda gets boosted. No table needed.

This means:
  "kinetic-energy when mass=10, velocity=6" → seeds are {kinetic-energy, mass, velocity}
    → those nodes have many Sthita edges → Sthita conductance boosted
    → PPR flows strongly along dependency paths → correct tantras rise

  "what is addition" → seed is {addition}
    → addition has many Abheda and Kriya edges → those get boosted
    → PPR flows along equivalence and composition paths → rich definitions surface

#### What changes in proof_graph.ml

Remove: satya_ganana (Jacobi iteration — subsumed by PPR)
Remove: avrti_step (intermediate function)
Keep:   raw_satya (pure local topology function — sloka/edge/diversity counts)
Add:    init_satya — sets raw_satya on all nodes once at load time
Add:    compute_seed_conductances (k, seed_nodes) → (visheshanam → float) function
Add:    compute_depth_affinity (k, target, bindings) → float
Add:    run_ppr (k, seed_nodes, target, bindings) → (string, float) Hashtbl.t

nigamana.satya field: stores raw_satya set at load time. Never updated thereafter.
PPR produces a posterior per query — not stored on nodes, not global.

#### run_ppr signature and algorithm

```ocaml
val run_ppr :
  proof_graph
  -> seed_nodes:(string * float) list   (* target=1.0, bindings=0.5 *)
  -> target:string
  -> bindings:binding list
  -> (string, float) Hashtbl.t          (* posterior score per node *)
```

Algorithm:
  1. compute_seed_conductances → cond(rel) = vp_satya_weight(rel) × (1 + freq(rel))
  2. compute_depth_affinity → da ∈ [0, 1]
  3. normalise seed to sum 1
  4. build out-conductance index from all_edges
  5. build in-edges index
  6. initialise scores: seed nodes = seed weight, others = raw_satya × 0.01
  7. iterate: p_new(v) = α × seed(v) + (1-α) × Σ_{u→v} p(u) × cond(rel) / out_cond(u)
     stop at max_delta < 0.001 or 50 iterations
  8. return scores

alpha = 0.30 (only hardcoded constant — restart probability, mathematical not domain)

#### Beam scoring in chain_resolve using depth_affinity

beam_score(state at depth d, ppr_score s) =
  s × (1 - depth_affinity) + depth_score(d) × depth_affinity

where depth_score(d) = 1 / (d + 1)   ← higher for shallow states

When depth_affinity = 1.0: beam_score = 1/(d+1) → pure BFS, deepest states always lose
When depth_affinity = 0.0: beam_score = ppr_score → pure PPR, depth irrelevant
When depth_affinity = 0.5: blend — PPR guides within BFS tiers

States expand in descending beam_score order. Beam width 8.

Run regression after Phase 5. All 53 tests must pass.

### Phase 6 — Wire PPR into chain_resolve and to_english

#### chain_resolve

At entry: call run_ppr with target and bindings → get scores and depth_affinity.
Replace FIFO Queue with scored beam (sorted list, beam_width=8).
Each state carries its beam_score. States pop in descending beam_score order.
Forward step score: beam_score(new_state) = blend(ppr(tantra), depth_affinity, new_depth)
Inverse step score: same but ppr(tantra) weighted by vp_satya_weight(Pratipaksha).
Stop at first found.

#### to_english

When called from a query context, receives the ppr scores table from run_ppr.
Candidate scoring adds ppr_score(candidate) × 500 as bonus term (same magnitude
as existing ratio/len/sloka scores).

Signature:
  val to_english : ?context:string option
                 -> ?ppr:(string, float) Hashtbl.t option
                 -> proof_graph -> string -> string

For to_english, seed = [(name, 1.0)] with empty bindings → depth_affinity = 0 →
pure PPR, exploratory → Abheda/Swarupa paths get boosted → correct English names surface.

Run regression after Phase 6. All 53 tests must pass.

### Phase 7 — Update plan and freeze

Mark all phases complete in this file. Add section "Adding a new algebraic structure" with
the pattern:
  1. Create brahman/kosha/math/<name>.om with correct Sthita to parent structure.
  2. Add Abheda edge to relevant op-class node if applicable.
  3. Run regression.

---

## Why Jacobi (satya_ganana) is removed

satya_ganana runs Jacobi iteration:
  p_new(v) = 0.7 × p(v) + 0.3 × avg(p(u) for u → v)

PPR with a uniform seed converges to the SAME fixed point — standard PageRank.
Jacobi is just PPR with a flat seed and uniform edge weights. It is a special case.

The structural prior we need at startup is raw_satya — a PURE FUNCTION of local
structure (sloka count, edge count, type diversity). No iteration needed.
Iteration only adds neighbour influence, which PPR does better (query-specifically)
at runtime.

Therefore: satya_ganana is removed. raw_satya is the prior. PPR is the posterior.
nigamana.satya stores raw_satya set at load time — never iterated again.

## Why no question_type enum

An earlier design used a question_type enum (QComputation, QDefinition, etc.) with a
hardcoded affinity table mapping (relation, question_type) → multiplier.

This was discarded because:
1. The table is arbitrary — the values (0.5, 2.0) are ungrounded design guesses.
2. The question type itself is a classification problem that requires heuristics.
3. The graph ALREADY CONTAINS this information — the query's own edge structure
   tells us exactly what kind of question it is.

Instead: depth_affinity and conductance boosts are derived entirely from the graph
structure of the query nodes (target + bindings). No enums. No lookup tables.
The only hardcoded constant is alpha=0.30 (mathematical, not domain knowledge).

---

## Affected Files

| File                                        | Change                                           | Risk   |
|---------------------------------------------|--------------------------------------------------|--------|
| brahman/kosha/yantra/visheshanam/*.om        | New: 10 property nodes                           | Low    |
| brahman/kosha/math/monoid.om                 | New: algebraic structure node                    | Low    |
| brahman/kosha/math/ring.om                   | New: algebraic structure node                    | Low    |
| brahman/kosha/math/field.om                  | New: algebraic structure node                    | Low    |
| brahman/kosha/math/distributivity.om         | New: missing axiom node                          | Low    |
| proof_graph.ml                               | Fix join(); add vish_props type + table          | Medium |
| proof_graph.ml                               | Remove satya_ganana; add raw_satya at load; add PPR engine | High |
| yantra_index.ml                              | scan_visheshanam_properties, apply_relation_axioms, build_index order; remove satya_ganana call | Medium |
| setu.ml                                      | to_english accepts optional ppr scores table     | Medium |
| yantra_resolver.ml                           | chain_resolve: run PPR at entry, beam search with PPR scores | Medium |
| vyakarana/scripts/run-regression.sh          | 4 satya-sensitive tests added (Phase 3)          | Low    |

No changes to: om_parser.ml, yantra_parser.ml, yantra_ops.ml, any .tantra files.

---

## Key Invariants to Preserve

1. All 53 regression tests must pass after every phase.
2. PPR must converge in ≤50 iterations (contraction rate (1-α)=0.70, Banach guarantee).
3. join() merge must be idempotent (joining a node twice = joining once).
4. apply_relation_axioms must be idempotent (running twice = running once — dedup ensures).
5. chain_resolve beam search must find the SAME result as FIFO BFS on all existing
   regression test cases. This is guaranteed by depth_affinity: for computation queries
   (bindings present, direct links to target), depth_affinity is high → BFS ordering
   dominates → same result as old FIFO.
6. No hardcoded question type enums or affinity tables. Everything derived from graph
   structure of the query. Only hardcoded constant is alpha=0.30 (mathematical, not domain).
7. vp_satya_weight in .om files are edge conductances — the only domain constants.
8. PPR is stateless on the graph — reads edges and raw_satya, writes nothing back.
   nigamana.satya field is read-only after load time.

---

## Open Questions (deferred)

- Transitive closure of Sthita: 331 implied edges, but 6 Sthita 2-cycles must be resolved
  first. Deferred until cycle handling policy is decided.
- Union-Find on domain-level Abheda: the giant 350-member philosophical Abheda component
  must be stratified (domain-level vs metaphysical) before Union-Find is safe. Deferred.
- Kriya composition index: precomputing Kriya-reachability for chain_resolve pre-filtering.
  Deferred until beam search baseline is stable.
- Commutativity and distributivity as computational properties in the inverter. Deferred.
- Layer-based traversal filtering (sangati vs kosha vs yantra node layers). Deferred.
- depth_affinity could be further refined: currently geometric mean of three signals.
  Could weight signals differently or add more (e.g. target layer: kosha vs sangati).
  Deferred until baseline is stable and we have query feedback to calibrate against.

---

## Status

- [x] Phase 0: Fix join() merge
- [x] Phase 1a: 10 visheshanam property .om files
- [x] Phase 1b: 4 math structure .om files (monoid, ring, field, distributivity)
- [x] Phase 2: vish_props type + global table in proof_graph.ml
- [x] Phase 3: Add satya-sensitive regression tests (53 total now)
- [x] Phase 4: scan_visheshanam_properties + apply_relation_axioms + build_index order
- [x] Phase 5: Remove satya_ganana; add structure-driven PPR engine to proof_graph.ml
         Includes: join() fix, vish_props type, raw_satya, init_satya,
                   compute_seed_conductances, compute_depth_affinity, run_ppr
- [x] Phase 6: Structure-driven PPR-guided beam search in chain_resolve; PPR in to_english
         chain_resolve: query_depth_affinity + blend_score replace hardcoded 0.7^depth;
                        beam-pop simplified to pure highest-score.
         to_english: optional ?ppr parameter adds ppr_score×500 bonus term.
- [x] Phase 7: Update plan and freeze

---

## Adding a new algebraic structure

1. Create `brahman/kosha/math/<name>.om` with a `Sthita` edge to the parent structure
   (e.g. `ring-sthita` for a field, `monoid-sthita` for a ring).
2. Add an `Abheda` edge to the relevant `op-class-*` node if the structure corresponds
   to an existing op-class (e.g. `op-class-monoid-abheda`).
3. Run `./scripts/run-regression.sh` — all 53 checks must pass.
