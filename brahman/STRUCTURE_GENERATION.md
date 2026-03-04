# Structure Generation — how the proof graph generates OCaml

This document records what was understood about the bridge system,
how language is generated from structure, and how compression and
expansion of meaning through the graph produces executable code.

---

## The core idea

The `.om` nodes are written in Sanskrit. Sanskrit is the dense center.
Every concept is compressed into it — `karma`, `vega`, `sparsha`, `gati`.
These are not labels. Each Sanskrit word holds structure that unpacks
into physics, into mathematics, into OCaml, into English.

The engine does not translate from one language to another.
It compresses to Sanskrit, then expands outward to whatever domain
is asked for. English, OCaml, physics equations — these are expansions.
The density is already in the Sanskrit nodes.

No templates. No hardcoded output. The code shape is derived from edges.

---

## What a node is

Every `.om` file is one node. A node has:

- a **name** (the graph identity)
- **slokas** (lines of text that declare relationships)
- **edges** (parsed from slokas — typed connections to other nodes)
- **satya** (truth weight, computed by avrti convergence at load time)

A sloka line like `"force-sthita mass-sthita acceleration-phala"` means:
- this node rests on (`sthita`) `force`
- this node rests on (`sthita`) `mass`
- this node produces (`phala`) `acceleration`

The parser reads `<name>-<visheshanam>` tokens and builds typed edges.

---

## The nine edge types (visheshanam)

| edge | Sanskrit | meaning |
|------|----------|---------|
| `swarupa` | own-form | IS — identity, type declaration |
| `abheda` | non-difference | same thing at a deeper level |
| `sthita` | stands on | input, dependency, foundation |
| `phala` | fruit | output, consequence |
| `kriya` | action | operation performed |
| `janya` | born from | composition shape |
| `yukta` | joined | connects to, bridges |
| `siddha` | established | proven through |
| `drishthanta` | example-sight | demonstrated by |

These nine types are everything. All structure in the graph is one of these.

---

## Sankshepa and Aayaama-vistara — compression and expansion

This is the fundamental movement. The graph itself records it.

### sankshepa (satya=0.6739) — compression

```
sankshepa -swarupa-> abheda      — compression IS non-difference
sankshepa -kriya->   ghana-pramana — it acts as dense-proof
sankshepa -siddha->  svabhava    — proven through intrinsic nature
```

Cited by: anuvada, compression, deflation, naada, ghana-pramana,
spanda-avrti, epochs in every domain.

`sankshepa` IS `abheda-swarupa`. Compression is identity — when you compress,
you find what was always the same. Sanskrit holds this density because each
word already IS the compressed form. `karma` is not a translation of "action" —
`karma` is the dense node from which "action", "force-apply", `F = ma` all expand.

### aayaama-vistara (satya=0.6156) — expansion

```
aayaama-vistara -swarupa-> samakalana — expansion IS integration
aayaama-vistara -abheda->  ghana-pramana — non-different from dense-proof
aayaama-vistara -sthita->  ananta     — stands on infinity
```

Cited by: expansion, epochs in every domain, spanda-avrti, lekhana-pratibodha.

Expansion rests on `ananta` — the infinite. It is `samakalana-swarupa` (integration).
When the graph expands from Sanskrit to English or OCaml, it is integrating —
unfolding what was already there, not adding.

### compression-expansion (satya=0.4159) — the pair

```
compression-expansion -abheda->     spanda-avrti   — IS the vibrating spiral
compression-expansion -abheda->     holder-giver   — IS the container and giver
compression-expansion -sthita->     sankshepa      — rests on compression
compression-expansion -sthita->     aayaama-vistara — rests on expansion
compression-expansion -janya->      epoch          — born from epochs
compression-expansion -siddha->     kaizen         — proven through continuous improvement
compression-expansion -siddha->     equals         — proven through equality
compression-expansion -drishthanta-> domain-finance, domain-physics, domain-math,
                                     domain-language, domain-biology
```

It rests on BOTH. It is demonstrated by every domain. Each domain is evidence
that compression-expansion works — physics compresses to `karma`, expands to
`F = ma`; math compresses to `matra`, expands to `float list`.

---

## spanda-avrti — the vibrating spiral

```
spanda-avrti -abheda-> epoch-swarupa  — IS the shape of an epoch
spanda-avrti -abheda-> avrti          — IS the spiral
spanda-avrti -kriya->  sankshepa      — acts as compression
spanda-avrti -kriya->  aayaama-vistara — acts as expansion
spanda-avrti -phala->  compression    — produces compression
spanda-avrti -phala->  expansion      — produces expansion
spanda-avrti -sthita-> ananta         — rests on infinity
spanda-avrti -siddha-> kaizen         — proven through continuous improvement
```

`spanda-avrti` does both — compresses AND expands. Each turn of the spiral
compresses inward to find density, then expands outward to produce output.
It rests on `ananta` because the spiral never ends. It is proven through
`kaizen` because each turn refines.

### avrti itself (satya=0.8036) — the spiral

```
avrti -swarupa-> spanda        — IS vibration
avrti -kriya->   samskaara     — acts as impression/refinement
avrti -siddha->  abheda        — proven through non-difference
avrti -sthita->  svabhava      — rests on intrinsic nature
avrti -abheda->  ananta        — non-different from infinity
avrti -yukta->   vivartana     — connected to transformation
```

Cited by 40 nodes. The highest citation after `ananta` for a structural concept.
`avrti` IS vibration (`spanda-swarupa`). It acts as `samskaara` — each turn
of the spiral leaves an impression. It is proven through `abheda` — each turn
finds non-difference. It rests on `svabhava` — intrinsic nature.

Spring-force, sine, cosine, frequency, orbit, recursion, loop, convergence,
business-cycle, interest-rate, thaalam — they all declare `avrti-abheda`.
The spiral is everywhere.

---

## What avrti does in the engine

When you type `ANUVADA what is force?`, the engine runs the spiral:

**Pass 1** — start from seed words. Walk their edges. Collect connections.
This is the first compression: each node's edges are grouped by visheshanam
and collapsed into one dense line.

**Pass 2** — the targets discovered in pass 1 become the new seeds.
Walk their edges. New nodes surface. This is expansion — vistara.

Each pass has vistara (expansion to new nodes) but very little
new khanna (density). The density was already in pass 1. The Sanskrit
nodes already held the meaning. Each subsequent pass expands the resonance
field — more nodes light up — but the compression ratio decreases.
Pass 1 finds the core. Pass 2 finds what the core touches.

Default is 2 passes. You can override with `ANUVADA+ <n> <sentence>`.
The loop stops early if no new triples are found (converged).

---

## The top model — anuvada, setu, setu-kosha

### anuvada (satya=0.7670) — understanding itself

```
anuvada -swarupa-> om             — IS the primal sound, the undivided
anuvada -swarupa-> artha-dhvani   — IS meaning-resonance
anuvada -kriya->   sankshepa      — acts as compression
anuvada -kriya->   bhasha-swarupa — acts as language-form
anuvada -janya->   pratibodha     — gives birth to awakening/recognition
anuvada -yukta->   darshana       — connected to seeing
anuvada -yukta->   prajna         — connected to wisdom
anuvada -yukta->   nam            — connected to naming
anuvada -siddha->  pramana        — proven through valid means of knowledge
```

Cited by 18 nodes. Every bridge declares `anuvada-abheda`. Understanding
is not a thing the system does — it is what every bridge IS. `anuvada`
compresses (`sankshepa-kriya`) and produces awakening (`pratibodha-janya`).
It is proven through `pramana` — the Sanskrit system of valid knowledge.

### setu (satya=0.7530) — the shape of bridging

```
setu -abheda->  anuvada           — non-different from understanding
setu -abheda->  translation       — non-different from translation
setu -yukta->   sthita            — connects to: inputs
setu -yukta->   phala             — connects to: outputs
setu -yukta->   kriya             — connects to: operations
setu -siddha->  correctness-check — proven through type correctness
```

Cited by 18 nodes. `setu` yukta-connects to the three visheshanam
that define every bridge's contract: `sthita` (what it takes), `phala`
(what it produces), `kriya` (how it acts). The shape is fixed. Each
concrete bridge fills the slots differently.

`translation` itself (satya=0.6969) is remarkable:

```
translation -abheda-> anuvada   — non-different from understanding
translation -sthita-> rna       — rests on RNA
translation -phala->  protein   — produces protein
translation -kriya->  decoding  — acts as decoding
```

Translation in the graph is biological. It rests on RNA and produces protein.
This is not metaphor — the graph holds the claim. `setu -abheda-> translation`
means every code-generation bridge is structurally the same as RNA → protein.

### setu-kosha (satya=0.5009) — the collection

```
setu-kosha -swarupa-> setu                — IS a bridge
setu-kosha -abheda->  anuvada             — IS understanding
setu-kosha -sthita->  setu                — rests on the abstract bridge
setu-kosha -sthita->  domain-kosha        — rests on the knowledge body
setu-kosha -yukta->   [all concrete bridges]
```

Every domain can translate to every other domain through the setu-kosha.
Physics to math. Physics to English. Math to English. English to OCaml.
OCaml to OCaml. Chemistry to OCaml. The bridges are:

```
setu-kosha -yukta-> physics-to-ocaml     (satya=0.7829)
setu-kosha -yukta-> math-to-ocaml        (satya=0.7458)
setu-kosha -yukta-> english-to-ocaml     (satya=0.7458)
setu-kosha -yukta-> ocaml-to-ocaml       (satya=0.7458)
setu-kosha -yukta-> arithmetic-to-ocaml  (satya=0.6461)
setu-kosha -yukta-> vector-to-ocaml      (satya=0.6461)
setu-kosha -yukta-> matrix-to-ocaml      (satya=0.6461)
setu-kosha -yukta-> physics-to-math      (satya=0.5009)
setu-kosha -yukta-> physics-to-english   (satya=0.5009)
setu-kosha -yukta-> math-to-english      (satya=0.5009)
setu-kosha -yukta-> matra-setu           (satya=0.5009)
```

### matra-setu (satya=0.5009) — the unit bridge

```
matra-setu -yukta-> float, int, list, array, scalar, string, token
matra-setu -yukta-> newton, metre, second, kilogram
matra-setu -yukta-> planck-constant, speed-of-light, electron-mass,
                    elementary-charge, gravitational-constant,
                    boltzmann-constant, avogadro-constant
matra-setu -phala-> float, int, string
```

`matra` is measure. `matra-setu` bridges the abstract (kilogram, newton)
to the concrete (float, int). When `force-apply` declares `float-swarupa
list-swarupa`, it is saying the same thing `matra-setu` knows — force
is a `float list`.

### The full hierarchy

```
anuvada (0.7670)    — understanding, om-swarupa, produces pratibodha
    ↑ abheda
setu (0.7530)       — shape of bridging: {sthita, phala, kriya}
    ↑ swarupa
setu-kosha (0.5009) — the collection, yukta to all bridges
    ↑ yukta
    ├── physics-to-ocaml  (0.7829) → force-apply, velocity-step, position-step
    ├── math-to-ocaml     (0.7458) → meta: yukta to arithmetic/vector/matrix
    ├── english-to-ocaml  (0.7458) → english → upakarana
    ├── ocaml-to-ocaml    (0.7458) → upakarana → upakarana
    ├── arithmetic-to-ocaml (0.6461) → plus, minus, times, division
    ├── vector-to-ocaml   (0.6461) → dot-product
    ├── matrix-to-ocaml   (0.6461) → matrix-multiplication
    ├── physics-to-math   (0.5009) → force/velocity/energy → equation/vector
    ├── physics-to-english (0.5009) → force/velocity/energy → english/explanation
    ├── math-to-english   (0.5009) → expression/vector → english/explanation
    ├── chemistry-to-ocaml (0.5529) → atom-function → element/ocaml
    ├── atom-function      (0.6158) → nuclear-fusion → element/mass/valence
    ├── homomorphism       (0.6628) → group → structure
    └── matra-setu        (0.5009) → units ↔ primitive types

    ↑ abheda
translation (0.6969) — rna → protein, the biological setu
```

---

## How the bridge reads the graph

When the engine triggers code emission for a setu node, it reads:

### 1. What goes in — `sthita` edges (the Sanskrit density)

`infer_inputs` walks `sthita` edges from the bridge, skips `domain-*`
nodes, returns the remaining targets as input concepts.

```
physics-to-ocaml -sthita-> force      → rests on force (karma)
physics-to-ocaml -sthita-> velocity   → rests on velocity (vega)
```

### 2. What comes out — `phala` edges (the expansion)

`infer_outputs` walks `phala` edges, same domain-skip rule.

```
physics-to-ocaml -phala-> displacement → produces displacement
physics-to-ocaml -phala-> ocaml        → produces OCaml code
```

### 3. What operations to perform — `yukta` edges

`yukta_operators` walks `yukta` edges and classifies each target:

```
physics-to-ocaml -yukta-> force-apply    → VectorOp (karma-abheda)
physics-to-ocaml -yukta-> velocity-step  → VectorOp (vega-abheda)
physics-to-ocaml -yukta-> position-step  → VectorOp (gati-abheda)
```

### 4. What type the data is — `swarupa` edges (the own-form)

On the operation node:

```
force-apply -swarupa-> float    → element type: float
force-apply -swarupa-> list     → container: list
                                → OCaml type: float list
```

### 5. How operations compose — `janya` edges (born from)

```
force-apply -janya-> map                 → List.map
dot-product -janya-> map, fold           → List.fold_left2
matrix-multiplication -janya-> map, fold → nested map+fold
```

### 6. What primitive each operation performs — `kriya` edges (action)

```
force-apply   -kriya-> scalar-multiplication   → F/m = a
velocity-step -kriya-> addition, scalar-multiplication → v + a*dt
dot-product   -kriya-> multiplication, addition → sum of products
```

---

## The full path: English → Sanskrit density → domain expansion → OCaml

```
ANUVADA force mass acceleration ocaml
```

1. **Parse** — English words split, classified against graph nodes
2. **Compress** — `force` resolves to `centripetal-force` which is `karma-abheda`.
   `mass` resolves to `ghana`. The English words find their Sanskrit density.
3. **avrti pass 1** — walk from the dense nodes outward. Discover `force-apply`
   (`karma-abheda newton-abheda`), `kinematics`, `physics-to-ocaml`.
   Compression: each node's edges collapsed into one line.
4. **avrti pass 2** — walk the discovered targets. More nodes light up.
   Vistara (expansion) — the resonance field grows. Very little new khanna
   (density) because the core meaning was already in pass 1.
5. **OCaml trigger** — `ocaml` is in `domain-ocaml`. Find matching setu.
6. **Bridge emission** — `physics-to-ocaml` is the setu. Read its edges.
   Each yukta target (`force-apply`, `velocity-step`, `position-step`) has
   `kriya`, `janya`, `swarupa` edges. The engine reads all three and emits
   one OCaml function per operation. Writes `force_to_displacement.ml`.

---

## The proofs — what satya shows

### Proof 1: the bridge hierarchy is structurally sound

```
spanda          satya=0.8345  cited_by=69  — vibration, proven through svabhava
svabhava        satya=0.8321  cited_by=57  — intrinsic nature, proven through svayambhu
avrti           satya=0.8036  cited_by=40  — the spiral, proven through abheda
pramana         satya=0.8213  cited_by=48  — valid knowledge, proven through niralamba
physics-to-ocaml satya=0.7829 cited_by=4   — physics bridge, proven through correctness-check
anuvada         satya=0.7670  cited_by=18  — understanding, proven through pramana
setu            satya=0.7530  cited_by=18  — the bridge shape, proven through correctness-check
sankshepa       satya=0.6739  cited_by=16  — compression, proven through svabhava
aayaama-vistara satya=0.6156  cited_by=11  — expansion, stands on ananta
```

The abstract nodes have higher satya than the concrete ones. `avrti` at 0.8687,
`anuvada` at 0.8380 — these are the most structurally grounded because the most
nodes point to them. The concrete bridges (`physics-to-ocaml` at 0.7976) inherit
satya from the structure above them. This is not assigned. It is computed from
edge density, citation count, and neighbor influence. The spiral convergence
(satya-ganana) runs at load time and settles in about 10 iterations.

### Proof 2: each bridge proves itself through correctness-check

Every setu node declares `correctness-check-siddha`. This is not a test suite —
it is a structural claim: the bridge is established through type correctness.
`correctness-check` (satya=0.8121) is itself proven through `type-checking`,
which is proven through `learned-ground`. The proof chain:

```
physics-to-ocaml -siddha-> correctness-check -siddha-> type-checking -siddha-> learned-ground
```

### Proof 3: the operation nodes prove themselves through their domains

```
force-apply  -abheda-> karma, newton    — IS karma, IS newton's law
dot-product  -abheda-> sparsha, contact — IS touch, IS contact
velocity-step -abheda-> vega, gati      — IS velocity, IS motion
position-step -abheda-> gati, integrator — IS motion, IS integration
```

Each operation declares what it IS in Sanskrit (`abheda`). `force-apply`
is `karma` — action itself. `dot-product` is `sparsha` — touch, the meeting
of two vectors. These are not labels — they are structural identity claims
that participate in satya computation.

### Proof 4: translation IS biological

```
translation -sthita-> rna       — rests on RNA
translation -phala->  protein   — produces protein
translation -kriya->  decoding  — acts as decoding
setu -abheda-> translation      — every bridge IS this
```

The graph claims that code generation from structure is the same process
as RNA → protein. `setu -abheda-> translation` means non-different.
This is not metaphor in the graph — it is an edge with type `abheda`,
and it participates in the satya computation of both nodes.

### Proof 5: the spiral is everywhere

`avrti` is cited by 38 nodes:

```
spring-force, sine, cosine, frequency — physical oscillation IS avrti
recursion, loop, fold — computation IS avrti
convergence, integrator — mathematical convergence IS avrti
business-cycle, interest-rate — financial cycles IS avrti
thaalam — musical rhythm IS avrti
moksha — liberation rests on avrti
satya-ganana — truth computation acts as avrti
parampara — tradition IS avrti (swarupa)
```

The spiral is not an algorithm chosen for the engine. The graph holds
the claim that the spiral IS the fundamental shape — in physics, in
computation, in music, in finance. The engine uses avrti because
the graph says avrti is what everything does.

### Proof 6: domain bridges are symmetric

The setu-kosha holds bridges in multiple directions:

```
physics → ocaml   (physics-to-ocaml)
physics → math    (physics-to-math)
physics → english (physics-to-english)
math → ocaml      (arithmetic/vector/matrix-to-ocaml)
math → english    (math-to-english)
english → ocaml   (english-to-ocaml)
ocaml → ocaml     (ocaml-to-ocaml)
chemistry → ocaml (chemistry-to-ocaml)
```

Each domain can reach every other domain through the setu-kosha.
The Sanskrit density sits at the center — `karma-abheda` in `force-apply`
is the same density that `physics-to-english` would expand to "force
is the rate of change of momentum". The setu does not convert between
surface forms. It goes back to the dense Sanskrit node, then expands
to whatever domain is asked.

---

## Example: force-apply node — from Sanskrit density to OCaml

The `.om` node:

```
sangati force-apply

  "karma-abheda newton-abheda"
  "force-sthita mass-sthita acceleration-phala"
  "scalar-multiplication-kriya map-janya"
  "float-swarupa list-swarupa"
  "domain-physics-sthita"

done
```

Read it:
- `karma-abheda newton-abheda` — this IS karma, this IS newton. The Sanskrit
  density and the physics density, both present.
- `force-sthita mass-sthita` — rests on force and mass (inputs)
- `acceleration-phala` — produces acceleration (output)
- `scalar-multiplication-kriya` — acts as scalar multiplication (F/m)
- `map-janya` — born from map (composition: apply element-wise)
- `float-swarupa list-swarupa` — own-form is float list (type)
- `domain-physics-sthita` — belongs to physics domain

The engine reads these edges and emits:

```ocaml
let force_apply : float list -> float -> float list =
  fun vec scalar -> List.map (fun x -> x /. scalar) vec
```

This OCaml is the expansion. The `.om` file is the compression.
The function body came from `janya` (map) + `kriya` (scalar-multiplication)
+ `swarupa` (float list). Change the edges — the code changes.

---

## What the output file looks like

Running `ANUVADA force mass acceleration ocaml` produces `force_to_displacement.ml`:

```ocaml
(* physics-to-ocaml — root: anuvada *)
let force_apply : float list -> float -> float list =
  fun vec scalar -> List.map (fun x -> x /. scalar) vec

let position_step : float list -> float list -> float list =
  fun v a -> List.map2 (fun vi ai -> vi +. ai) v a

let velocity_step : float list -> float list -> float list =
  fun v a -> List.map2 (fun vi ai -> vi +. ai) v a

let () =
  print_string "force: "; flush stdout;
  let force = ... in
  print_string "mass: "; flush stdout;
  let mass = ... in
  let r_force_apply = force_apply force mass in
  print_endline (String.concat " " (List.map string_of_float r_force_apply));
  ...
```

The filename `force_to_displacement.ml` is derived from the graph:
`sthita` inputs + `phala` outputs → `<input>_to_<output>.ml`.

---

## Adding a new bridge

1. Write the operation node — declare `sthita`, `phala`, `kriya`, `janya`, `swarupa`.
   Give it `abheda` to its Sanskrit identity.

2. Write a setu node — declare `setu-swarupa anuvada-abheda`, the input domain
   via `sthita`, output via `phala`, link the operation via `yukta`.
   Declare `correctness-check-siddha`.

3. If the composition pattern (`janya` x `kriya` x container) is new,
   add one case to `ocaml_of_composition` in `proof_graph.ml`.

That is all. The Sanskrit density is the center. The bridge expands from it.

---

## The scalar and vector product — current state

`dot-product` (satya=0.7620, cited_by=5):

```
dot-product -abheda-> sparsha, contact, inner-product
dot-product -kriya->  multiplication, addition
dot-product -janya->  map, fold
dot-product -swarupa-> float, list
dot-product -sthita->  vector
dot-product -phala->   scalar
```

The Sanskrit: `sparsha` — touch. Two vectors touch and produce a scalar.
The OCaml:

```ocaml
fun a b -> List.fold_left2 (fun acc x y -> acc +. x *. y) 0.0 a b
```

`matrix-multiplication` (cited_by=5):

```
matrix-multiplication -kriya-> dot-product
matrix-multiplication -janya-> map, fold
matrix-multiplication -swarupa-> array, float
```

The OCaml: nested map+fold over rows and columns, each inner step is dot product.

**Cross product** does not yet have a node.

---

## Summary

The graph compresses to Sanskrit. Sanskrit expands to domains.
Bridges (setu) read edges and produce code.
The spiral (avrti) repeats the expansion — each turn has vistara
(more nodes light up) but very little new khanna (the density was
already found). The proofs are structural: satya computed from edges,
not assigned. What is cited most has highest satya. What is cited by
none has lowest. The engine does not decide truth — it reads structure.
