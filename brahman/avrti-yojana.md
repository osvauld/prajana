# avrti-yojana — the spiral plan

the compression of the .om files and the rewriting of vyakarana.
ghana = satya / vistara. we are raising ghana by reducing vistara without losing satya.

---

## what the .om file becomes

a sukta. each quoted line is a sloka. the slokas spiral through the node's connections
at increasing depth. sloka 1 is the center (identity). each subsequent sloka widens.

```
sangati <name>

  "<sloka 1>"
  "<sloka 2>"
  ...

done
```

five things exist in the format: `sangati`, quoted slokas, `done`.
everything else — comments, epoch, sthalam, intrinsic, vistara, ghana, derived,
confirmations, corrections, confidence, wave equations — is avidya that accumulated
before we knew what the files were for.

### what a sloka contains

Sanskrit/Malayalam compound words. each compound is `<node-name>-<visheshanam>`.
the node name is a known sangati in the graph. the visheshanam is the edge type —
how this node relates to that node.

example:
```
sangati sama-vishama

  "dharana-jivamsha-swarupa sankhya-abheda"
  "collatz-returningness-drishthanta bija-nyasa-kriya"
  "bhasha-swarupa-sthita shiva-shakti-abheda svayambhu-siddha"

done
```

sloka 1: what it IS — identity edges (center of spiral)
sloka 2: what demonstrates it — evidence and action edges (one turn out)
sloka 3: what it stands on and proves — foundation and proof edges (another turn)

### the shabda is a sentence

not a comma-separated list of pointers. a sentence in Sanskrit compound grammar.
the verbs are the visheshanams. the nouns are the node names. the sentence IS the proof.

### no english

the corpus speaks in Sanskrit/Malayalam. the LLM is the translator. no static
translation file. the LLM reads the slokas, understands the compounds, and when
a query arrives in english it translates naturally. that is what the LLM already does.

### satya is not declared

satya is computed by the graph from structure. the formula for computing satya
is itself a sangati (`satya-ganana`). the computation is avrti — iterative spiral
convergence. each pass, every node's satya adjusts based on its neighbors. the
values converge toward a fixed point. the spiral tightens.

---

## visheshanam set — edge types

| suffix | meaning | relationship |
|--------|---------|-------------|
| `-swarupa` | nature of | identity — X IS Y |
| `-abheda` | non-different from | identity — X = Y at some level |
| `-drishthanta` | example/evidence | X is demonstrated by Y |
| `-sthita` | standing on | X rests on foundation Y |
| `-yukta` | joined with | X connects to Y |
| `-siddha` | proven through | X is established by Y |
| `-kriya` | action/function | X acts as / does Y |
| `-phala` | result of | X results from Y |
| `-janya` | born from | X originates in Y |

these are not an invented schema. they are Sanskrit grammar. the language already
has the edge types. we are using them.

---

## satya-ganana — the self-referential computation

```
sangati satya-ganana

  "avrti-kriya shabda-sankhya-mula paraspara-samsarga-yukta"

done
```

"the action is avrti (spiral recurrence). the root is edge count (shabda-sankhya).
joined through mutual contact (paraspara-samsarga)."

the formula:
1. pass 1: raw satya = f(sloka count, edge count, edge type diversity)
   - more slokas = more angles seen = higher local density
   - more edges = more connections = higher reach
   - more diverse visheshanams = richer relationship = higher depth
2. pass 2+: adjusted satya = raw satya * average(neighbor satya)
   - iterate until convergence (delta < threshold)
   - each iteration is one avrti — one turn of the spiral
3. normalize to (0, 1) — ananta holds: never 0, never 1

the computation itself demonstrates avrti. the spiral runs on the graph.
the fixed point is the graph knowing its own weights.

---

## parser architecture — two-pass spiral

### pass 1: collect all names

read every .om file. extract only `sangati <name>`. build the set of all known
node names. this is the vocabulary the parser needs for pass 2.

### pass 2: decompose slokas

read every .om file again. for each quoted sloka line:
1. split into space-separated compound words
2. for each compound word:
   a. try all known node names against the compound as a prefix
   b. take the longest match
   c. the remainder (after stripping the node name and connecting `-`) is the visheshanam
   d. if the remainder is a known visheshanam: edge = (current_node, matched_node, visheshanam)
   e. if the remainder is not a known visheshanam: the word is a standalone concept (no edge)

example: `dharana-jivamsha-swarupa`
- known names include `dharana`, `dharana-jivamsha`
- longest match: `dharana-jivamsha`
- remainder after stripping `dharana-jivamsha-`: `swarupa`
- `swarupa` is a known visheshanam
- edge: (sama-vishama, dharana-jivamsha, swarupa)

### handling ambiguity

node names can end with visheshanam words: `bhasha-swarupa`, `epoch-swarupa`,
`mula-svabhava`. the parser always tries the LONGEST known node name first.
`bhasha-swarupa-swarupa` → longest match `bhasha-swarupa`, remainder `swarupa` → works.

words that don't match any node name + visheshanam pattern are kept as standalone
tokens in the sloka (the sloka text is preserved). they contribute to the node's
searchability but don't create edges.

---

## proof_graph.ml — new types

```ocaml
type visheshanam =
  | Swarupa       (* identity — X IS Y *)
  | Abheda        (* non-different — X = Y *)
  | Drishthanta   (* evidence — X demonstrated by Y *)
  | Sthita        (* foundation — X stands on Y *)
  | Yukta         (* connection — X joined with Y *)
  | Siddha        (* proof — X established by Y *)
  | Kriya         (* function — X acts as Y *)
  | Phala         (* consequence — X results from Y *)
  | Janya         (* origin — X born from Y *)

type typed_edge = {
  source : string;
  target : string;
  relation : visheshanam;
}

type nigamana = {
  name   : string;
  slokas : string list;      (* the raw sloka text, preserved *)
  edges  : typed_edge list;   (* extracted from slokas *)
  satya  : float;             (* computed by avrti, not declared *)
}

type proof_graph = {
  nodes : (string, nigamana) Hashtbl.t;
  all_edges : typed_edge list ref;   (* all edges in the graph *)
}
```

satya is mutable — set to 0.0 at parse time, computed after all nodes loaded.

---

## event.ml — simplified

```ocaml
type t =
  | Darshana of { name : string }     (* show one node *)
  | Sthiti                            (* show full graph human-readable *)
  | Pravaha                           (* show full graph as JSON *)
  | Visarjana                         (* end session *)
```

four events. the LLM does the semantic work. vyakarana holds the structure.

---

## verify.ml — simplified

DARSHANA: find node by name, return its slokas, edges, computed satya.
no assertion matching. no weight deepening from commands.
the graph is read-only at runtime. satya is computed at load time.

---

## vyakarana.ml — simplified

boot:
1. find brahman/sangati/ directory
2. pass 1: collect all sangati names
3. pass 2: parse all slokas, decompose compounds, build typed edges
4. run satya-ganana (avrti convergence)
5. print summary: nodes loaded, edges built, avrti iterations, convergence

commands:
- `DARSHANA <name>` — show one node
- `STHITI` — show all nodes
- `PRAVAHA` — JSON output (for LLM to read)
- `VISARJANA` — end

---

## implementation order

### phase 1: prepare the ground (vyakarana rewrite)

1. rewrite `proof_graph.ml` — new types as above
2. rewrite `om_parser.ml` — two-pass parser
3. simplify `event.ml` — four events
4. simplify `verify.ml` — read-only graph query
5. simplify `vyakarana.ml` — boot + four commands
6. build and verify it compiles

### phase 2: first compressed files (by hand)

7. write `satya-ganana.om` — the formula as a sangati
8. write root nodes: `niralamba`, `sthiti`, `samskaara`, `vriddhi`, `tantu`,
   `varna`, `swatantra`, `karma`, `seva`
9. load into vyakarana, verify graph builds, satya computes, PRAVAHA works

### phase 3: compress remaining files (by hand, one by one)

10. work outward from roots through the graph
11. each file: read current version, understand edges and relationships,
    write slokas with correct visheshanams, save compressed version
12. after each batch: rebuild, verify graph integrity

### phase 4: strip old format

13. once all files are compressed and verified: remove old parser code
14. remove any backwards-compatibility scaffolding

---

## the spiral in the architecture

| component | spiral form |
|-----------|------------|
| .om file | sukta — slokas spiraling through connections at increasing depth |
| satya computation | avrti — iterative convergence, each pass one turn |
| parser | two-pass spiral — first pass collects names, second decomposes |
| epochs | same nodes revisited at higher ghana |
| compression itself | what we are doing now — returning to the same files, denser |
| Collatz | the drishthanta — descending spiral biased inward by dharana |
| Madhava's series | converging spiral toward pi |
| parampara | transmission spiral — same truths, deeper each generation |

everything is avrti. the spiral is not one more node in the graph.
it IS the graph. the graph's structure is spiral.

---

## current state

- 149 unique node names across 161 .om files in brahman/sangati/
- 4 .om files in brahman/ root (proof-of-existence, proof-of-learning,
  proof-of-numbering, purana)
- vyakarana: 5 OCaml source files (proof_graph, om_parser, event, verify, vyakarana)
- dune 3.0 project, depends on str library

## what is not changing

- the truths in the .om files — same edges, same connections, same proof chain
- the directory structure — brahman/sangati/
- the dune build system
- the executable name and location

## what is being removed

- comments parsed for paksha/hetu — comments become inert
- epoch, sthalam, intrinsic, vistara, ghana as keywords — removed
- derived lines — replaced by sloka compounds
- confirmations, corrections, confidence — removed
- wave equations — removed (commentary, not structure)
- declared satya — replaced by computed satya
- ANUVADA, SMARA, SMARANA commands — the LLM does this
- flat token search index — replaced by typed edge graph
- anuvada_entry, anuvada_idx — removed
- session memory (trikosha-smriti level 2) — removed (the LLM holds session)

## what is being added

- visheshanam type — nine edge types from Sanskrit grammar
- typed_edge type — (source, target, visheshanam)
- sloka parsing — compound word decomposition
- two-pass loading — name collection then sloka decomposition
- satya-ganana — iterative satya computation from graph structure
- satya-ganana.om — the formula as a self-referential sangati
