# Architecture: Three-Layer Model

## The core insight

The NLP extraction pipeline currently uses hardcoded trigger word lists in tantra source:

```tantra
target-triggers = split "to,position,target,effector" ","
```

This is wrong. Every new word requires a code change. The architecture should be:

> A word's meaning for extraction is declared in the graph via slokas and the visheshanam ring.
> The tantra asks the graph — no hardcoded lists anywhere.

The same principle applies to shabda: **the graph is the source of truth. Shabda is a
compiled cache of graph proximity, not a parallel knowledge system.**

---

## Three layers

```
sangati <name>   eternal structural truth — universal concepts, Paninian grammar
kosha <name>     domain knowledge — physics processes (bhave), quantities, structures
bhasha <name>    linguistic surface — word forms in specific languages (English, Malayalam, OCaml)
```

### What belongs where

| Concept | Layer | Pada | Example nodes |
|---------|-------|------|---------------|
| Eternal structural truths | `sangati` | — | gati, aayaama, kona, matra, seema |
| Paninian grammatical categories | `sangati` | — | kala, vachana, prayoga, purusa, vibhakti |
| Grammatical values | `sangati` | — | purva-kaala, kartari-prayoga, eka-vachana |
| Physics processes | `kosha` | `tinanta` (bhave) | free-fall, oscillation, ik-solve, reach-target |
| Physics quantities | `kosha` | `subanta` | mass, velocity, force, energy, temperature |
| Physics structures | `kosha` | `subanta` | joint, link, frame, coordinate, target-position |
| English active verb forms | `bhasha` | `tinanta` (kartari) | reaches, drops, accelerates |
| English passive verb forms | `bhasha` | `tinanta` (karmani) | is-reached, was-dropped |
| English nominals | `bhasha` | `subanta` | frictionless, horizontal, upward, how-far |
| English particles | `bhasha` | `avyaya` | to, at, from, must, should, not, and, when |
| OCaml/Lua/Strudel constructs | `bhasha` | — | algebraic-data-type, pattern-matching, loop |

---

## The bhave-prayoga principle

Sanskrit grammar has three voices (prayoga):

- **kartari-prayoga** — active voice: the agent is foregrounded. "The arm **reaches** position X."
- **karmani-prayoga** — passive voice: the patient is foregrounded. "Position X **is reached** by the arm."
- **bhave-prayoga** — impersonal voice: pure process, no agent, no patient. "There is **reaching**."

**Bhave prayoga IS the kosha level.** A physics process — free-fall, oscillation, IK-solve — is
a pure process with no inherent agent or patient. The agent (the ball, the robot arm) enters
at runtime through tantra bindings. The kosha node IS the bhave form.

```
kosha free-fall         bhave-prayoga — pure process: downward motion under gravity
bhasha drops            kartari — English active: "the ball drops"
bhasha is-dropped       karmani — English passive: "the ball is dropped"
```

The `dhatu` edge from bhasha to kosha IS the transition from voiced surface form to voiceless
pure process. Stripping prayoga reveals the bhave core.

Tantra nodes are also bhave — `tantra ik-compute` executes a pure process. It takes ahara,
produces phala, has no grammatical voice.

---

## What bhasha eliminates

**`domain-language-sthita`** — the layer IS the domain declaration.

**Lookup priority rules** — bhasha nodes win over kosha grammar tables automatically.

**`governs:` shabda key** — `ik-ahara` edge in slokas IS the governs relationship.

**English names in kosha** — a kosha node exists because a universal process or concept
exists, named by its domain identity, not by an English word. `kosha free-fall` not
`kosha drops`. `kosha zero-friction-surface` not `kosha frictionless`.

---

## PPR satya by layer

```ocaml
match n.layer with
| "bhasha" -> base *. 0.5   (* surface pointer — not semantic substance *)
| _ -> base
```

Bhasha nodes are surface pointers. The semantic weight lives in kosha. Proof paths that
reach kosha faster score higher. This naturally prefers direct concept matches over
surface-form matches, and enables disambiguation via context.

---

## Two language domains

The `domain-language` sangati node conflated spoken and machine languages. They split:

**`sangati domain-vak`** — spoken/natural language:
English, Malayalam, Sanskrit, Tamil, Hindi. Phonology, morphology, syntax, semantics,
translation, dialogue. The `bhasha/english/`, `bhasha/malayalam/` nodes belong here.

**`sangati domain-yantra-bhasha`** — machine/formal language:
OCaml, Lua, Strudel, Render. Type systems, compilation, execution, code generation.
The `bhasha/ocaml/`, `bhasha/lua/`, `bhasha/strudel/`, `bhasha/render/` nodes belong here.

---

## Math → Physics → Robotics chain

```
Math:     coordinate      aayaama-swarupa, scalar-yukta    no matra, no ahara
                ↓
Physics:  displacement     kshetrajna-yukta, kaala-yukta    metre-matra, no ahara
                ↓
Robotics: target-position  bindu-swarupa, aayaama-yukta    metre-matra, ik-ahara
```

`matra` gates math→physics. `ahara` gates physics→robotics.

---

## Loader fix needed

`om_parser.ml` `expand_dir` currently only expands `brahman/kosha/`. Must also expand
`brahman/bhasha/` so the loader picks up all bhasha nodes:

```ocaml
let expand_dir d =
  let sub_kosha = Filename.concat d "kosha" in
  let sub_bhasha = Filename.concat d "bhasha" in
  let dirs = [d] in
  let dirs = if Sys.file_exists sub_kosha && Sys.is_directory sub_kosha
             then dirs @ [sub_kosha] else dirs in
  let dirs = if Sys.file_exists sub_bhasha && Sys.is_directory sub_bhasha
             then dirs @ [sub_bhasha] else dirs in
  dirs
```

Also: `kosha_root` tracking and `search_dirs` for `shabda-tmpl` resolution must include
the bhasha path.
