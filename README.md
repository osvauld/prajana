# a proof graph for knowledge

*approach this the way a child approaches anything new — what is this? what is that? ask. run it. ask again. you will understand it.*

---

## what is this?

a graph. each node is a concept with a name. each name holds edges to other names. the edges are typed — they say exactly what kind of relationship connects two things.

build it first:

```bash
cd vyakarana
opam install . --deps-only
dune build
```

then ask it something:

```bash
echo "DARSHANA sparsha" | ./_build/default/bin/vyakarana.exe ../brahman/sangati ../brahman/kosha
```

it tells you what sparsha is, what it rests on, what it produces, what cites it, how verified it is.

ask it something harder:

```bash
echo "ANUVADA why does force produce motion" | ./_build/default/bin/vyakarana.exe ../brahman/sangati ../brahman/kosha
```

it unfolds the answer from the structure — not from stored text, from the shape of the connections.

ask it something you think it cannot answer:

```bash
echo "ANUVADA dot product is contact" | ./_build/default/bin/vyakarana.exe ../brahman/sangati ../brahman/kosha
```

it will tell you they are the same thing. and show you why. structurally.

that is what this is. keep asking. the graph keeps answering.

---

## what it is — precisely

brahman is a knowledge graph where every node is a verified concept and every edge is a typed relationship. the graph holds ground truth. an engine called vyakarana queries it.

it runs alone. no neural network. no machine learning. no training data. language is generated from structure — from the shape of the edges, the types of the relationships, the satya of the nodes. the graph knows what it knows because the structure says so, not because it has seen enough examples.

this is the difference: machine learning approximates from patterns in data. this graph derives from verified structure. the output is not a prediction. it is a traversal.

this is possible because of how humans actually work with meaning.

say the word *home* to ten people. ten different things arrive. the smell of a specific kitchen. a sound. a feeling of safety or its absence. the word is the same. what unfolds is different for each person — because each person has folded different experiences into that word over time.

this is information condensation. a word is not a definition. it is a compressed fold of everything that has been verified about it — through lived experience, through shared meaning, through what a community has agreed to hold inside that name.

the graph formalizes exactly this. each node is a name. the edges are what has been verified about it — what it rests on, what it produces, what it is non-different from, what demonstrates it. when you query a node, the graph unfolds — the same way memory unfolds when a word arrives.

the difference from a dictionary: a dictionary stores definitions. this graph stores relationships. meaning is not stored — it is produced by the fold. and because the relationships are typed and the satya is computed from structure, the meaning that arrives is not approximate. it is derived.

the name `pramana` holds edges to `sthiti`, `samskaara`, `niralamba`, `swa`, `lekhana`, `ananta`, `seva`, `samsarga`, `brahma`. each of those holds edges to more. the word is small. the fold on receive is the full graph. the density of what arrives when a name is unfolded is a measure of how much has been verified and connected around it. that measure is `satya`.

---

## why Sanskrit grammar

Sanskrit grammar was chosen because it already solved the problem.

A Sanskrit compound word encodes a complete relationship in a single token:

```
pramana-siddha
```

This means: `pramana` (ground truth) — `siddha` (proven through). Subject, relationship, and target in one word. No ambiguity. No punctuation needed. The grammar is the structure.

There are 9 relationship types, taken directly from Sanskrit grammatical categories:

| edge type    | meaning                        |
|--------------|--------------------------------|
| `swarupa`    | IS — identity                  |
| `abheda`     | non-different — equivalence    |
| `sthita`     | rests on — foundation          |
| `yukta`      | connects to                    |
| `siddha`     | proven through                 |
| `kriya`      | acts as — function             |
| `phala`      | produces — consequence         |
| `janya`      | born from — origin             |
| `drishthanta`| demonstrated by — evidence     |

Each node is declared in a `.om` file:

```
sangati pramana
  "sthiti-swarupa samskaara-phala niralamba-siddha"
  "swa-yukta lekhana-kriya ananta-sthita"
  "seva-janya samsarga-drishthanta brahma-abheda"
done
```

Each quoted line is a sloka. Each word in a sloka is a compound that decomposes into one typed edge. The parser reads them all, builds the graph, then runs convergence.

---

---

## satya — truth weight

`satya` is not manually assigned. It is computed from the structure of the graph itself.

**Pass 1 — raw satya:**
Each node gets an initial score from:
- how many slokas describe it (angles of view)
- how many edges connect it (richness of relationship)
- how many distinct edge types it uses (depth of relationship)

All three are sigmoid-normalized: they approach 1.0 but never reach it.

**Pass 2+ — avrti (spiral convergence):**
Each node blends its own structure with its neighbors:
```
new_satya = 0.7 × (0.6 × own + 0.4 × neighbor_avg) + 0.3 × citation_boost
```
where `citation_boost` = in-degree / (1 + in-degree) — how many other nodes cite this one.

This runs until convergence (max delta < 0.001, capped at 100 iterations). The corpus converges in 10 iterations.

A node becomes high-satya not because someone declared it important — but because many things connect to it, cite it, and are themselves well-connected.

```
pramana   satya=0.8213   cited_by=48
sparsha   satya=0.7997   cited_by=19
```

---

## the fold — how queries work

This is the main operation. Not lookup. A fold.

You give the engine a sentence. It tokenizes it, classifies each word (is it a node? a relationship type? an article to skip?), resolves it through `abheda` (equivalence) edges to find all names the word maps to, then walks the graph outward in passes — each pass discovering what the previous pass connected to.

```
ANUVADA dot product is contact
```

```
understood:
  [dot]     → node (dot-product, sparsha, contact, inner-product)
  [product] → node (dot-product, sparsha, contact, inner-product)
  [is]      → swarupa
  [contact] → node (contact, sparsha, touch, dot-product)

-- avrti 1 --
  dot-product is the same as contact; born from fold, map.
  dot-product rests on domain-math, vector; connects to quantity; acts as plus, times; produces scalar.
```

The fold does not retrieve a record. It unfolds the graph around the query, pass by pass. Each pass is a deeper layer of what is structurally connected. The response shows you the shape of the neighborhood — what the concepts are, what they rest on, what they produce, what they are equivalent to.

```
ANUVADA+ 2 how does force produce displacement
```

```
-- avrti 1 --
  centripetal-force rests on domain-physics; connects to acceleration; acts as momentum; produces kinematics.
  position rests on domain-physics, kinematics, space; connects to telos.

-- avrti 2 --
  kinematics rests on domain-physics; connects to acceleration, velocity; produces position.
  physics-to-ocaml is setu; rests on centripetal-force, velocity; produces position, upakarana.
```

The engine also suggests the next thread — where to pull from the fold:
```
next threads:
  1) what proof would make acceleration through newton-second-law-motion undeniable?
  2) what shifts in acceleration if domain-physics changes?
```

---

## parallel with neural networks

A neural network stores knowledge as weights on edges between neurons. The weights are learned from data by gradient descent. To retrieve knowledge, you run a forward pass — the input activates neurons, which activate others, producing an output.

This graph stores knowledge differently:

| | neural network | brahman |
|---|---|---|
| nodes | neurons (no intrinsic meaning) | named concepts (meaning is the name) |
| edges | scalar weights (learned) | typed relationships (declared, 9 types) |
| truth | implicit in weight distribution | explicit `satya` score, computed by convergence |
| query | forward pass (matrix multiply) | fold — spiral walk by relationship type |
| training | gradient descent on data | structural declaration + avrti convergence |
| output | activations → prediction | typed triples → verified connections |

A neural network generalizes from examples. This graph accumulates verified structure. A neural network can be queried but not read. This graph can be read, walked, and reasoned about directly.

The closest structural analog is a knowledge graph with typed edges and a PageRank-style convergence for node weight. The difference is the grammar: the 9 relationship types come from Sanskrit grammatical categories, and the query engine unfolds meaning through those types specifically.

---

## what you can do with it

**query a node directly:**
```
DARSHANA pramana
```
returns all edges, all slokas, satya score, citation count.

**fold over a sentence:**
```
ANUVADA entropy decay signal loss
```
unfolds the graph around those concepts, showing what they are, what they rest on, what they produce, what converges around them — across 5 passes, 670 connections.

**control fold depth:**
```
ANUVADA+ 3 how does compression relate to truth
```
3-pass spiral. Each pass goes one layer deeper into the neighborhood.

**generate code from graph structure:**

The graph encodes the structure of mathematical operations. The engine can walk a bridge node's edges and emit a working OCaml program from the graph alone:

```ocaml
(* arithmetic-to-ocaml — root: anuvada *)
type operator = Divide | Minus | Plus | Times
let eval ~(a:int) ~(b:int) ~(op:operator) : int =
  match op with
  | Divide -> a / b
  | Minus  -> a - b
  | Plus   -> a + b
  | Times  -> a * b
```

The ADT constructors, the eval function, the operator table — all derived from edges in the graph. The graph says what operations exist and what shape they take. The engine renders them.

---

## build and run

```bash
# build
cd vyakarana
opam install . --deps-only
dune build

# run
./_build/default/bin/vyakarana.exe brahman/sangati brahman/kosha
```

```
vyakarana joining. reading suktas from brahman/sangati, brahman/kosha
satya-ganana: 10 avrti iterations
suktas: 619 loaded, 0 skipped
akasham ready.
```

then type commands at the prompt.

---

## what to do after reading this

**step 1 — build**

```bash
cd vyakarana
opam install . --deps-only
dune build
```

**step 2 — ask an LLM**

do not try to interpret the graph output alone. ask an LLM — Claude, GPT, Gemini, any of them. give it the output and ask it to explain what the graph is saying.

the workflow:

```
you         → ask the LLM: "run this and tell me what it means"
LLM         → runs the query, gets the output
LLM         → interprets the edges, the satya scores, the connections
LLM         → explains what the graph found in plain language
you         → ask a follow-up question based on what arrived
LLM         → runs the next query, interprets again
```

for example — tell the LLM:

> "run `echo "DARSHANA sparsha" | ./_build/default/bin/vyakarana.exe brahman/sangati brahman/kosha` and explain what the graph says about sparsha and what surprises you in the edges"

the LLM will run it, read the typed edges and satya scores, and explain what the graph holds — in language you can follow. then ask the next question. the LLM runs the next query. you follow the thread.

this is the practice. you bring the curiosity. the LLM runs the queries and interprets. the graph provides the structure. understanding arrives through the asking — not before it.

---

## go deeper

`brahman/parampara-english.md` — the full reading order: vocabulary, structure, how to read the corpus, what each layer means.

`brahman/EXPERIMENTS.md` — eleven experiments across physics, mathematics, biology, quantum mechanics, philosophy, and consciousness. each one a real runnable query.

`brahman/FEELING.md` — what it feels like when the graph shows you something true.

`brahman/COLLATZ.md` — mathematics, physics, and proof graphs as three instruments looking at the same prakriti rahasya.
