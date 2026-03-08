# Ring Algebra & N-Dimensional Graded Graph — Plan

## The Full Algebraic Picture

There are **two ring structures** in this system, and they compose:

### Ring 1 — The Visheshanam Ring (edge algebra)

The 10 relation types form a non-commutative ring R = (V, ⊕, ⊗):
- **⊕ = yukta** (addition): symmetric, identity = shunya, inverse = pratipaksha
- **⊗ = kriya** (multiplication): composable, non-commutative, identity = swarupa
- **Distributivity**: kriya distributes over yukta

This is already defined in `.om`, referenced in `.tantra`, stored in `.ml` — but never used in computation.

### Ring 2 — The Layer Grading (node algebra)

The graph has a **graded ring** structure over its layers.

The grading is NOT flat — kosha itself is a tower of increasing compositional complexity.
The `sthita` (foundation) chain from any node down to sangati defines its **sthita-depth**,
which is its sub-grade within kosha.

#### The major grades

| Grade | Layer | Keyword | What it holds | Count |
|---|---|---|---|---|
| 0 | sangati | `sangati` | Universal structural truths — domain-independent first principles | 240 nodes (in `brahman/sangati/`) |
| 1+ | kosha | `kosha` | Domain knowledge — rests on grade 0 via `sthita`, internally graded by depth | ~1,000 nodes (in `brahman/kosha/`) |
| ∞ | yantra | `tantra` | Executable computation — morphisms acting on all lower grades | 94 programs (in `brahman/yantra/`) |

#### The kosha sub-grading (sthita-depth within a domain)

Within each domain, kosha nodes form a **filtration** — a tower of increasing complexity
where each level rests on the levels below via `sthita` chains.

Example: physics domain tower

```
sthita-depth 0 (sangati):   karma, spanda, kshetra, niyama, matra
                               ↑ sthita
sthita-depth 1 (base kosha): mass, velocity, acceleration, current, voltage, resistance
                               ↑ sthita
sthita-depth 2 (composed):   force (mass + acceleration), ohms-law (current + resistance)
                               ↑ sthita
sthita-depth 3 (higher):     kinetic-energy (mass + velocity), electrical-power (voltage + current)
                               ↑ sthita
sthita-depth 4 (derived):    escape-velocity (mass + radius + G), power-from-resistance (current + resistance)
```

Example: biology domain tower

```
sthita-depth 0 (sangati):   iccha, jiva-sphurana, parampara, matrika
                               ↑ sthita
sthita-depth 1 (base kosha): nucleotide, nitrogenous-base, amino-acid
                               ↑ sthita
sthita-depth 2 (composed):   codon (nucleotide triplet), base-pairing
                               ↑ sthita
sthita-depth 3 (higher):     gene (codon sequence), protein (amino-acid chain)
                               ↑ sthita
sthita-depth 4 (derived):    genome, operon, heredity
```

**This is already in the graph.** We don't need to name it or label it — the `sthita` edges
ARE the grading. Every `sthita` chain from a derived concept down to a fundamental one is
the filtration made explicit. The structure is the math.

The runtime just needs to **compute** what's already encoded:
```
sthita_depth(v) = length of shortest sthita-chain from v to any node with no outgoing sthita
```

This is a single BFS from every node. O(|E|) total at load time.

Observations from live graph:
- `mass` → sthita → `kshetrajna`, `niyama`, `domain-physics` (depth 1 from sangati)
- `force` → sthita → `mass`, `acceleration` (depth 2 — rests on depth-1 concepts)
- `kinetic-energy` → sthita → `mass`, `velocity` (depth 2)
- `escape-velocity` → sthita → `mass`, `radius` (depth 2, but those rest on depth-1)
- `voltage` → sthita → `matra`, `domain-physics` (depth 1)
- `ohms-law` → sthita → `current`, `resistance` (depth 2)
- `electrical-power` → sthita → `voltage`, `current` (depth 2)
- `power-from-resistance` → sthita → `current`, `resistance` (depth 2)

Fundamental concepts have shallow sthita-depth. Derived concepts have deeper sthita-depth.
This is already true in the graph — it's not something we add, it's something we read.

**The grading is a filtered ring:**

$$
R_0 \subset R_1 \subset R_2 \subset \cdots \subset R_n
$$

where $R_k$ = all nodes with sthita-depth ≤ k. Each $R_k$ is closed: composing
concepts at depth k can only produce concepts at depth ≤ k+1.

The tantra is the morphism: it takes inputs at various depths and produces output
at the next level. `force.tantra` takes `mass` (depth 1) + `acceleration` (depth 1)
→ `force` (depth 2). The depth arithmetic is already encoded in the sthita edges
of the `.om` files that describe those same concepts.

**The current problem:** 586 files in `brahman/kosha/` use `sangati` as their keyword.
This means the runtime tags them as grade 0 when they are actually grade 1+.
The major grade boundary (sangati vs kosha) is unreliable. The fine-grained grading
(sthita-depth) is not computed at all — but it's fully derivable from existing edges.

### How the two rings compose

The full graph is a **graded ring with typed edges**:

$$
\mathcal{G} \in \{0,1\}^{N \times N \times R \times L}
$$

where:
- N = 1,240 nodes (the set)
- R = 10 relation types (the visheshanam ring)
- L = 3 layer grades (the grading ring)

Each edge is: `(source_node, target_node, relation_type, source_grade, target_grade)`

The grading constrains which edges are meaningful:
- Grade 0 → Grade 0: sangati edges (pure ontology, e.g. `spanda-swarupa avrti-kriya`)
- Grade 0 → Grade 1: foundation edges (kosha rests on sangati, e.g. `domain-physics-sthita`)
- Grade 1 → Grade 1: domain edges (kosha-to-kosha, e.g. `force-sthita mass`)
- Grade 1 → Grade 0: reference-back (kosha citing sangati, e.g. `iccha-sthita`)
- Grade 2 acts on Grade 0+1: yantra takes inputs from both layers, produces results

Within each domain, both grades are present:
- `force` (currently labeled sangati, should be kosha grade 1) rests on `karma` (sangati grade 0)
- `ring` (currently labeled sangati, should be kosha grade 1) rests on `group` (sangati grade 0)
- `dna` (currently labeled sangati, should be kosha grade 1) rests on `iccha`, `life` (sangati grade 0)

---

## What Already Exists

### In `.om` (defines the algebra)

**Visheshanam ring:**
- `visheshanam-yukta.om`: `ring-op:add` — yukta IS addition
- `visheshanam-kriya.om`: `ring-op:mul` — kriya IS multiplication
- `ring.om`: `group-sthita monoid-yukta addition-kriya multiplication-kriya distributivity-siddha`
- `group.om`: `set-swarupa closure-yukta identity-yukta inverse-yukta associativity-yukta`
- `field.om`: `ring-sthita pratipaksha-yukta division-siddha`
- `addition.om`: `subtraction-pratipaksha` (additive inverse)
- `multiplication.om`: `division-pratipaksha` (mult inverse)

**Grading vocabulary:**
- `shunya.om`: zero / additive identity
- `aayaama.om`: dimension
- `aayaama-vistara.om`: expansion of dimension
- `vector-space.om`: `aayaama-yukta addition-kriya multiplication-kriya`
- `basis.om`: `mula-swarupa independent-abheda aayaama-yukta vector-space-sthita`

**Layer distinction in parser:**
- `om_parser.ml:62-64`: explicitly parses `sangati` vs `kosha` keyword
- `proof_graph.ml:30`: stores `layer : string` on every node

### In `.tantra` (uses the algebra to compute)

- `visheshanam-projection.tantra` says:
  - "closure (group axiom) — edges must stay within the seed domain subgroup"
  - "projection (aneka-eka) — tier as basis; anuvritta has zero coefficient → dropped"
  - "vector-space (basis) — each relation type is an independent axis"
- `firstness-of-triple.tantra`: intent-dependent tier = scalar coefficient per relation-basis-vector
- `visheshanam-entropy-weights.tantra`: computes edge weights from Shannon entropy
- `spiral-domain.tantra`: context-score = inner product on edge neighborhoods

### In `proof_graph.ml` (stores but doesn't use)

- `vp_ring_op : [`Add | `Mul | `None]` — parsed from `.om`, stored per relation, **never read**
- `layer : string` — stored per node, **only used for JSON export** (`anuvada.ml:1377`)
- `nigamana.edges` — flat list, no per-relation or per-layer indexing
- `all_edges` — flat list ref, no structure

---

## What's Missing

### The Visheshanam Ring — Gaps

1. `vp_ring_op` is dead code — stored but never read during PPR or beam search
2. No formal identity elements linked — shunya not connected as yukta-identity, swarupa not as kriya-identity
3. No ring-aware conductance — PPR treats all relation types as same-kind flow
4. No `visheshanam-ring.om` node — the ring itself isn't named in the graph

### The Layer Grading — Gaps

1. **586 kosha files say `sangati`** — the grade field is wrong for half the graph
2. **Layer field is unused in scoring** — `raw_satya`, PPR, beam search, projection all ignore `n.layer`
3. **No grade-aware conductance** — an edge from grade 0 to grade 0 should flow differently than grade 0 to grade 1
4. **No grade-aware projection** — answers don't distinguish sangati-depth from kosha-breadth
5. **No formal grading node** — the graph doesn't describe its own grading structure
6. **Domains are not modeled as submodules** — domain-physics, domain-math, etc. are just yukta-linked to domain-kosha, not formally grade-1 submodules

### The Full Tensor — Gaps

1. No per-relation edge index — everything is a flat list
2. No per-layer edge index — can't ask "all grade-0 edges" cheaply
3. No graph-dimension metadata exposed to tantras
4. PPR collapses R=10 dimensions to R=1 before scoring (loses information)

---

## The Plan

### Phase 0: Fix the Layer Keywords (prerequisite)

**Goal:** Every node's `layer` field must match its actual grade.

- All 586 files in `brahman/kosha/` currently saying `sangati` → change to `kosha`
- Verify: no node in `brahman/sangati/` says `kosha` (they shouldn't)
- After this, `layer` field is reliable and can be used in scoring

**Rule (formalized):**
```
File in brahman/sangati/  → keyword must be "sangati"  → grade 0
File in brahman/kosha/    → keyword must be "kosha"    → grade 1
File in brahman/engine/   → keyword must be "kosha"    → grade 1 (engine self-description)
File in brahman/personal/ → keyword must be "sangati"  → grade 0 (experiential, pre-domain)
```

This is a mass rename but semantically correct — kosha nodes are domain applications, not universal truths.

**Impact:** After the rename, the runtime knows true grade for every node. This unlocks all downstream grading work.

### Phase 1: Name the ring that's already there in `.om`

**Goal:** The visheshanam ring is already defined by its parts. We just need one node
that names it as a whole, so the graph can talk about its own edge algebra.
The layer grading does NOT need a new node — it's already the sthita chains.

1. **Add `brahman/kosha/math/visheshanam-ring.om`:**
   ```
   kosha visheshanam-ring

     "ring-swarupa domain-math-sthita domain-yantra-sthita"
     "yukta-kriya-siddha"         -- yukta is the additive operation
     "kriya-kriya-siddha"         -- kriya is the multiplicative operation
     "shunya-identity-siddha"     -- shunya is additive identity
     "swarupa-identity-siddha"    -- swarupa is multiplicative identity
     "pratipaksha-inverse-siddha" -- pratipaksha is additive inverse
     "distributivity-siddha"      -- kriya distributes over yukta

   shabda visheshanam-ring / the-algebraic-ring-formed-by-the-ten-relation-types
   done
   ```

2. **Add `brahman/kosha/math/graph-aayaama.om`:**
   ```
   kosha graph-aayaama

     "aayaama-swarupa vector-space-sthita domain-math-sthita"
     "visheshanam-ring-yukta"
     "basis-siddha"

   shabda graph-dimension / the-dimensional-structure-of-the-proof-graph
   done
   ```

3. **Update identity links:**
   - `shunya.om`: add `yukta-identity-swarupa` — zero is already there, just link it
   - `ring.om`: add `visheshanam-ring-drishthanta` — the visheshanam ring is a concrete instance

4. **Do NOT add a node for the layer grading.**
   The grading is the sthita chains themselves. Adding a "graded-ring" node would be
   naming something that's already expressed by the structure. The runtime should
   compute sthita-depth from existing edges, not from a declaration.

### Phase 2: Upgrade proof_graph.ml (represent both rings)

**Goal:** The runtime should represent, know, and expose its graded ring structure.

1. **Add structured edge indexes:**
   ```ocaml
   type proof_graph = {
     nodes       : (string, nigamana) Hashtbl.t;
     all_edges   : typed_edge list ref;
     
     (* NEW: per-relation index — the R dimension *)
     edges_by_rel   : (visheshanam, typed_edge list ref) Hashtbl.t;
     
     (* NEW: per-layer index — the L dimension *)
     edges_by_grade : (int, typed_edge list ref) Hashtbl.t;
     (* grade of edge = max(grade(source), grade(target)) *)
     
     kosha_root  : string ref;
     search_dirs : string list ref;
   }
   ```

2. **Compute sthita-depth at load time (read the grading that's already in the graph):**
   ```ocaml
   (* stored on each node — computed once after axiom expansion *)
   type nigamana = {
     ...
     sthita_depth : int;   (* NEW: shortest sthita-chain to a leaf (no outgoing sthita) *)
   }
   
   (* BFS from every node following outgoing sthita edges.
      Leaf = node with no outgoing sthita edges → depth 0.
      Everything else = 1 + min(depth of sthita targets).
      O(|E_sthita|) total. *)
   let compute_sthita_depths (k : proof_graph) : unit = ...
   ```
   This doesn't invent new structure — it reads the depth that's already
   encoded in the existing sthita chains. `mass` gets depth 1, `force` gets
   depth 2, `kinetic-energy` gets depth 2 or 3, sangati roots get depth 0.

3. **Add graph dimension metadata:**
   ```ocaml
   type graph_dimensions = {
     n_nodes      : int;       (* N *)
     n_relations  : int;       (* R = 10 *)
     n_edges      : int;       (* |E| *)
     max_depth    : int;       (* deepest sthita-depth in the graph *)
     density      : float;     (* |E| / (N × N × R) *)
     depth_histogram : int array;  (* nodes per sthita-depth: [|42; 310; 580; ...|] *)
   }
   ```

4. **Depth-aware raw_satya:**
   Currently:
   ```
   σ(v) = (s · e · d)^(1/3)
   ```
   The sthita-depth already reflects fundamentality — shallow nodes are
   foundations, deep nodes are derivatives. Use it as a fourth factor:
   ```
   σ(v) = (s · e · d)^(1/3) × depth_factor(v)
   
   depth_factor(v) = 1.0 / (1.0 + 0.05 × sthita_depth(v))
   ```
   Shallow (fundamental) nodes score slightly higher than deep (derived) nodes
   with the same topology. This is a soft preference, not a hard cutoff.
   The 0.05 coefficient means depth-5 nodes lose ~20% — significant but not
   dominating. The topology factors (s, e, d) still matter most.

5. **Ring+depth-aware conductance:**
   ```
   κ(r, e) = w_r × (1 + f_r) × μ(ring_op(r)) × δ(depth_gap(e))
   
   μ(Add)  = 1.0    -- yukta: free association flow
   μ(Mul)  = c_mul  -- kriya: directional composition weight
   μ(None) = 1.0    -- default
   
   depth_gap(e) = |sthita_depth(source) - sthita_depth(target)|
   δ(gap) = 1.0 / (1.0 + 0.1 × gap)
   ```
   Edges between nodes at similar depth flow freely.
   Edges spanning many depth levels (connecting a root to a highly derived
   concept) are slightly dampened — they're long-range jumps in the filtration.

### Phase 3: Use Both Rings in Graph Walking

**Goal:** PPR and projection should be grade-aware and ring-aware.

1. **Grade-aware PPR:**
   Currently PPR initializes all non-seed nodes to `n.satya × 0.01`.
   Grade-aware initialization:
   ```
   init(v) = seed(v) if v ∈ seeds
   init(v) = σ(v) × 0.01 × grade_weight(v) otherwise
   ```
   Plus grade-aware conductance in the iteration (from Phase 2 step 5).

2. **Grade-aware projection in `visheshanam-projection.tantra`:**
   Currently domain closure filters by domain. Add layer closure:
   - If the target is grade 0 (sangati), prefer grade 0 neighbors in the answer
   - If the target is grade 1 (kosha), include both grade 0 foundations and grade 1 peers
   - This prevents kosha noise from polluting sangati-level conceptual answers

3. **Per-relation PPR (the full N×R upgrade):**
   Produce `p(v, r) ∈ ℝ^{N×R}` instead of `p(v) ∈ ℝ^N`.
   Final score:
   ```
   p(v) = Σ_r intent_weight(r) × p(v, r)
   ```
   where `intent_weight` comes from `firstness-of-triple` tier assignments.
   This is the intent-conditioned dot product in the relation vector space.

4. **Expose structure to tantras:**
   New primitives:
   - `ring-op <relation>` → "add" | "mul" | "none"
   - `grade-of <node>` → 0 | 1 | 2
   - `graph-dimension` → [N, R, L]
   - `graph-density` → float
   - `edges-in-grade <grade>` → count
   - `edges-of-rel <relation>` → count

### Phase 4: Fix Layer Keywords (the mass rename)

**Goal:** Every kosha file uses `kosha` keyword. Every sangati file uses `sangati` keyword.

This is Phase 4 (not Phase 0) because:
- Phase 1-3 add the algebraic structure that makes the grading meaningful
- The rename is mechanical (sed across 586 files)
- But it should happen AFTER the runtime can actually use the grade field
- Otherwise we rename 586 files and nothing changes in behavior

Steps:
1. Verify rule: file in `brahman/kosha/` → must say `kosha`, file in `brahman/sangati/` → must say `sangati`
2. Automated rename: `sed -i 's/^sangati /kosha /' brahman/kosha/**/*.om`
3. Verify: `grep -rl "^sangati " brahman/kosha/` returns empty
4. Rebuild + regression test

Some exceptions to review manually:
- `brahman/kosha/math/ring.om` currently says `sangati ring` — is ring truly universal (grade 0) or domain-specific (grade 1)?
- Same question for: `group.om`, `field.om`, `monoid.om`, `morphism.om`, `closure.om`, `topology.om`
- These might genuinely be grade 0 concepts that happen to live in kosha/ — consider moving them to sangati/ instead

Decision rule:
- If a node has NO `domain-X-sthita` edge → it's universal → should be sangati (either rename keyword or move file)
- If a node has `domain-X-sthita` → it's domain-specific → should be kosha

### Phase 5: Whitepaper Documentation

Document the full graded ring structure:

#### Section: The Graded Visheshanam Ring

$$
\mathcal{R} = \bigoplus_{g=0}^{2} R_g
$$

where:
- $R_0$ = sangati (ground ring) — 240 nodes, universal structural truths
- $R_1$ = kosha (module over $R_0$) — ~1,000 nodes, domain knowledge
- $R_2$ = yantra (morphisms) — 94 programs, computation

Grading rule:
$$
\text{grade}(a \otimes b) = \text{grade}(a) + \text{grade}(b)
$$

The grading relation is `sthita`:
$$
a \xrightarrow{\text{sthita}} b \implies \text{grade}(a) \geq \text{grade}(b)
$$

Kosha nodes rest on sangati nodes. Yantra acts on both.

#### Section: The Full Tensor

$$
\mathcal{G} \in \{0,1\}^{N \times N \times R \times L}
$$

| Dimension | Size | What |
|---|---|---|
| N | 1,240 | nodes |
| R | 10 | relation types (visheshanam ring) |
| L | 3 | layer grades (grading ring) |
| Total slots | 46,128,000 | N × N × R × L |
| Filled | ~13,164 | actual edges |
| Density | 0.029% | extremely sparse |

#### Section: Grade-Aware Conductance

$$
\kappa(r, g) = w_r \cdot (1 + f_r) \cdot \mu(\text{ring\_op}(r)) \cdot \gamma(g)
$$

#### Section: Per-Relation PPR

$$
p_{t+1}(v, r) = \alpha \cdot s_r(v) + (1-\alpha) \sum_{u \xrightarrow{r} v} \frac{p_t(u,r) \cdot \kappa(r, g_{uv})}{\text{out\_cond}_r(u)}
$$

Final intent-projected score:
$$
p(v) = \sum_{r \in R} \omega_I(r) \cdot p(v, r)
$$

where $\omega_I(r)$ is the intent weight from `firstness-of-triple`.

---

## Priority Order

| # | Phase | Risk | Impact | Depends on |
|---|---|---|---|---|
| 1 | Phase 1: Formalize rings in `.om` | None (additive) | High (conceptual foundation) | — |
| 2 | Phase 2.1-2: Edge indexes + dimensions | Low (additive) | Medium (enables everything) | — |
| 3 | Phase 2.3: Grade function + grade_of | Low | Medium | Phase 2.1 |
| 4 | Phase 2.4: Grade-aware raw_satya | Low | Medium | Phase 2.3 |
| 5 | Phase 2.5: Ring+grade-aware conductance | Medium | High | Phase 2.3 |
| 6 | Phase 3.1: Grade-aware PPR init | Medium | High | Phase 2.5 |
| 7 | Phase 4: Mass rename 586 files | Low (mechanical) | High (fixes grading) | Phase 2.3 |
| 8 | Phase 3.2: Grade-aware projection | Medium | High | Phase 4 |
| 9 | Phase 3.3: Per-relation PPR | High (big change) | Very high | Phase 2.5 |
| 10 | Phase 3.4: Expose primitives to tantra | Low | Medium | Phase 2 |
| 11 | Phase 5: Whitepaper | None | High | All above |

## Verification

After each phase:
```
dune build                          → must succeed
run-regression.sh                   → all existing tests pass

what is ring                        → should show visheshanam-ring connection
what is visheshanam-ring            → should describe the ring structure
DARSHANA force                      → should show layer=kosha (after Phase 4)
DARSHANA spanda                     → should show layer=sangati
EVAL grade-of force                 → should return 1
EVAL grade-of spanda                → should return 0
EVAL graph-dimension                → should return [1240, 10, 3]
EVAL ring-op yukta                  → should return "add"
EVAL ring-op kriya                  → should return "mul"
```

## Source Files

**New `.om`:**
- `brahman/kosha/math/visheshanam-ring.om`
- `brahman/kosha/math/graded-ring.om`
- `brahman/kosha/math/graph-aayaama.om`

**Update `.om`:**
- `brahman/sangati/shunya.om` — add yukta-identity link
- `brahman/kosha/math/ring.om` — add visheshanam-ring-drishthanta
- 586 files in `brahman/kosha/` — keyword `sangati` → `kosha`

**Runtime:**
- `vyakarana/lib/proof_graph.ml` — edges_by_rel, edges_by_grade, grade_of, graph_dimensions, grade-aware satya + conductance
- `vyakarana/lib/yantra_eval_primitives.ml` — ring-op, grade-of, graph-dimension primitives

**Tantras:**
- `brahman/yantra/visheshanam-projection.tantra` — grade-aware closure
- `brahman/yantra/darshana.tantra` — show layer/grade in output

**Whitepaper:**
- `prabandam/src/content/docs/whitepaper/ontology.md` — graded ring section
- `prabandam/src/content/docs/whitepaper/input-output-graph-math.md` — grade-aware equations

---

_Created: exploratory session, Sun Mar 08 2026_
