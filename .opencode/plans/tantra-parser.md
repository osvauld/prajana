# Tantra Parser Plan

## Goal

Build the conversion pipeline that takes natural language input, recognises computable concepts + values, finds the right tantra file, emits OCaml, executes it, and returns the result. The conversion itself is structured as a tantra (anuvada-ganana) — written first in OCaml to bootstrap, later replaceable by its own tantra definition.

---

## Architecture

```
User input (any form)
  |
  v
[1. Tokenise] ---- preserve floats, hyphens, operators
  |
  v
[2. Classify] ---- concept / number / grammar / operator / unknown
  |
  v
[3. Bigram]   ---- join multi-word concepts: "initial velocity" -> initial-velocity
  |
  v
[4. Bind]     ---- pair concepts with values using grammar context
  |                "mass is 10" -> (mass, 10.0)
  |                "f = 10"     -> (force, 10.0)  (alias resolution)
  v
[5. Resolve]  ---- find the right tantra file from operation + bindings
  |
  v
[6. Emit]     ---- generate OCaml from tantra + bindings
  |
  v
[7. Execute]  ---- compile and run the OCaml, capture output
  |
  v
[8. Return]   ---- return result to user, store in session memory
```

---

## Input Forms (all must work)

### Phase A — Single sentence computation

```
what is 3 plus 5?
what is 7 times 6?
square root of 144
sine of 1.57
factorial of 6
negate 7
absolute value of -3
```

### Phase B — Named parameter binding

```
what is the force when mass is 10 and acceleration is 9.8?
find displacement when initial velocity is 10 acceleration is 9.8 and time is 2
solve x squared minus 3x plus 2 equals zero
```

### Phase C — Variable assignment with shorthand

```
f = 10, m = 5, what is the acceleration?
v0 = 20, theta = 0.785, t = 2, find the displacement
```

### Phase D — Multi-sentence / paragraph (chaining)

```
A ball is thrown with velocity 20 at angle 45 degrees.
Find the displacement after 2 seconds.
What is the kinetic energy at that point?
```

Each sentence can reference results from previous sentences.
Session memory carries bindings across queries.

### Phase E — Code-like input (future)

```
mass = 10
velocity = 5
ke = 0.5 * mass * velocity ** 2
```

Full file of assignments and expressions, parsed and executed.

---

## Sub-tantra breakdown

### 1. Tokenise (tantra: varna-vibhajana)

**What it does:** Split input into tokens, preserving structure the current tokeniser destroys.

**Current bugs to fix:**
- `9.8` becomes `98` — the `.` is stripped by `clean` function in anuvada.ml
- `1.57` becomes `157` — same bug
- `-3` should be a negative number, not `minus` + `three`
- Parentheses `(`, `)` are stripped — need them for nested expressions

**Fix:** In the `clean` function (anuvada.ml lines 1496-1507), add `.` to the allowed character set when it appears between digits. A token is a float if it matches `[0-9]+\.[0-9]+`.

**Implementation:**
- Modify `clean` in anuvada.ml: preserve `.` between digits
- Add float detection: `float_of_string_opt` before `int_of_string_opt`
- Preserve parentheses as structural tokens (not content, not grammar)
- Handle negative numbers: `-` immediately before a digit with no space = negative number

**File:** `vyakarana/lib/setu.ml` or `vyakarana/lib/anuvada.ml` (the `clean` function and `classify_token`)

### 2. Classify (tantra: varna-parichaya)

**What it does:** Each token gets a role. Currently uses `token_role` type with `Article | Grammar | Content | Unknown`.

**Extend to:**
```ocaml
type token_role =
  | Article                          (* the, a, an — filtered *)
  | Grammar of visheshanam           (* is -> Swarupa, of -> Sthita, etc. *)
  | Concept of string                (* graph node name *)
  | Number of float                  (* 3.0, 9.8, 1.57 *)
  | Operator of string               (* +, -, *, / *)
  | Unit of string                   (* N, kg, m, s, m/s — future *)
  | Unknown of string                (* unresolved *)
```

**Key change:** Numbers become their own token type with the actual float value, not mapped to graph node names like `"three"`.

**Implementation:**
- Extend `token_role` in setu.ml
- In `classify_token`: try `float_of_string_opt` first, return `Number f`
- Keep integer-to-word mapping (`3` -> `three`) only for Anuvada reasoning, NOT for Yantra computation
- Operators `+`, `-`, `*`, `/` return `Operator` not `Content`

**File:** `vyakarana/lib/setu.ml` (token_role type and classify_token function)

### 3. Bigram (tantra: pada-sandhi)

**What it does:** Join adjacent content words into multi-word concepts.

**Already exists:** `Setu.bigrams` function (setu.ml lines 164-168) creates hyphenated pairs. Currently NOT called from anuvada_query.

**Implementation:**
- After classifying all tokens, take consecutive `Concept` tokens
- Try the bigram (hyphenated join) against the graph
- If the bigram matches a graph node, replace the two tokens with one
- Example: `[Concept "initial"; Concept "velocity"]` -> try `"initial-velocity"` -> found! -> `[Concept "initial-velocity"]`
- Also try: `[Concept "kinetic"; Concept "energy"]` -> `"kinetic-energy"` -> found!

**File:** `vyakarana/lib/anuvada.ml` (new step in anuvada_query pipeline)

### 4. Bind (tantra: nama-bandha)

**What it does:** Pair concepts with their numeric values using grammar context.

**Binding patterns to recognise:**

| Pattern | Example | Binding |
|---|---|---|
| `Concept` `Grammar(Swarupa)` `Number` | `mass is 10` | `(mass, 10.0)` |
| `Concept` `Operator(=)` `Number` | `mass = 10` | `(mass, 10.0)` |
| `Concept` `Number` | `velocity 20` | `(velocity, 20.0)` |
| `Concept` `Number` `Unit` | `force 10 N` | `(force, 10.0)` (future: with unit) |
| `Alias` `Operator(=)` `Number` | `f = 10` | resolve alias `f` -> `force`, `(force, 10.0)` |
| `Concept` `Grammar(Sthita)` `Number` | `mass of 10` | `(mass, 10.0)` |

**Alias table** (stored in graph, or as a simple lookup):

| Alias | Full concept |
|---|---|
| `f` | `force` |
| `m` | `mass` |
| `a` | `acceleration` |
| `v` | `velocity` |
| `v0` | `initial-velocity` |
| `u` | `initial-velocity` |
| `t` | `time` |
| `s` | `displacement` |
| `g` | `gravity` (9.81) |
| `ke` | `kinetic-energy` |
| `pe` | `potential-energy` |
| `p` | `momentum` |
| `w` | `work` |
| `theta` | `angle` |
| `omega` | `angular-velocity` |
| `tau` | `torque` |
| `r` | `radius` |
| `h` | `height` |
| `x` | `variable` |

**Implementation:**
- Walk the classified token list left-to-right
- When pattern `Concept/Alias` `is/=` `Number` is found, create binding
- When pattern `Concept` `Number` is found (no grammar word between), create binding
- Unbound concepts (no number follows) are candidates for the operation name
- Unbound numbers (no concept precedes) are positional arguments

**File:** `vyakarana/lib/yantra.ml` (new file)

### 5. Resolve (tantra: tantra-anveshana)

**What it does:** Given a target concept (what to solve for), a set of parameter bindings (what we know), find the right tantra and determine how to use it.

**Tantra index:** At startup, the engine loads all `.tantra` files from `brahman/yantra/` and builds an index:

```ocaml
type tantra_input = {
  name : string;     (* "mass" *)
  typ  : string;     (* "float" *)
  unit : string option; (* Some "kilogram" *)
}

type tantra = {
  name      : string;              (* "force" *)
  file      : string;              (* "brahman/yantra/bhautika/bala.tantra" *)
  inputs    : tantra_input list;   (* [{name="mass"; typ="float"; unit=Some "kilogram"}; ...] *)
  lets      : (string * string) list;  (* [("f", "mul mass acceleration"); ...] *)
  returns   : tantra_input list;   (* [{name="f"; typ="float"; unit=Some "newton"}] *)
}

(* Index built at startup *)
type tantra_index = {
  by_name    : (string, tantra) Hashtbl.t;        (* "force" -> bala.tantra *)
  by_output  : (string, tantra list) Hashtbl.t;   (* "force" -> [bala.tantra] — tantras that produce this concept *)
  by_inputs  : (string, tantra list) Hashtbl.t;   (* "mass" -> [bala.tantra, kinetic-energy.tantra, momentum.tantra, ...] *)
  constants  : (string, float) Hashtbl.t;         (* "gravity" -> 9.80665, "pi" -> 3.14159... *)
  conversions: (string * string, tantra) Hashtbl.t; (* ("kilometre-per-hour", "metre-per-second") -> kmph-to-mps.tantra *)
}
```

**The graph helps resolution.** The tantra index gives candidate tantras. The proof graph disambiguates:
- When multiple tantras could apply, the graph's domain edges narrow the search (physics query → bhautika tantras preferred)
- When a binding name doesn't exactly match a tantra input name, the graph's `abheda`/`swarupa` edges find equivalences ("velocity" ≈ "initial-velocity" via the graph)
- When a concept appears in multiple tantras, the graph's `yukta` edges between the bound concepts and the target tell us which tantra is most relevant

**Resolution strategy (in priority order):**

```
1. DIRECT    — tantra name matches target concept
               "what is the force" → tantra named "force" → bala.tantra
               Check: all inputs have bindings? → YES → use it

2. OUTPUT    — target concept is a return value of some tantra
               "what is the displacement" → sthana-antara.tantra returns "s" 
               which is displacement (tantra named "displacement")
               Check: all inputs have bindings? → YES → use it

3. INVERSE   — target concept is an INPUT of a tantra whose OUTPUT we already have
               "what is the acceleration" + we have force and mass
               → bala.tantra has acceleration as input, force as output
               → we HAVE force, so invert: acceleration = div force mass
               Algebraic inversion rules for single operations:
                 mul a b, solve for a → div result b
                 mul a b, solve for b → div result a
                 add a b, solve for a → sub result b
                 sub a b, solve for a → add result b
                 div a b, solve for a → mul result b
                 power a b, solve for a → power result (div 1.0 b)

4. CHAIN     — no single tantra suffices, but a sequence does
               "what is the kinetic energy" + we have force, mass, time
               → no direct ke tantra with those inputs
               → but: final-velocity.tantra gives us velocity from (initial-velocity, acceleration, time)
               → then: kinetic-energy.tantra gives us ke from (mass, velocity)
               → chain: velocity = v0 + a*t, then ke = 0.5*m*v^2
               Search: BFS/DFS through tantra graph — which sequence of tantras 
               transforms our known bindings into the target?

5. CONVERT   — inputs available but units don't match
               We have velocity in km/h, tantra expects m/s
               → find conversion tantra: kmph-to-mps.tantra
               → apply conversion, then proceed with step 1-4
```

**Full resolution trace:**

```
QUERY: "f = 100 N, m = 10 kg, what is the acceleration?"

Bindings after alias resolution:
  (force, 100.0, newton)
  (mass, 10.0, kilogram)
Target: acceleration

Step 1 — DIRECT: tantra named "acceleration"? NO (no such tantra)

Step 2 — OUTPUT: any tantra returns "acceleration"? NO

Step 3 — INVERSE: any tantra has "acceleration" as INPUT?
  → bala.tantra: inputs [mass, acceleration] → returns [f, newton]
  → We have: force ✓ (100.0), mass ✓ (10.0)
  → Missing input IS our target: acceleration ✓
  → Invert: f = mul mass acceleration
           → acceleration = div f mass
  → USE inverted bala.tantra

Emit:
  let force = 100.0 in
  let mass = 10.0 in
  let acceleration = (force /. mass) in
  Printf.printf "acceleration = %f m/s^2\n" acceleration
→ acceleration = 10.0 m/s^2
```

```
QUERY: "velocity is 72 km/h, acceleration is 9.8, time is 3, find displacement"

Bindings:
  (velocity, 72.0, kilometre-per-hour)
  (acceleration, 9.8, metre-per-second-squared)
  (time, 3.0, second)
Target: displacement

Step 1 — DIRECT: sthana-antara.tantra (displacement) ✓
  Inputs: initial-velocity (metre-per-second), acceleration (m/s^2), time (second)
  
Step 5 — CONVERT: velocity is in km/h, tantra expects m/s
  → conversions index: (km/h, m/s) → kmph-to-mps.tantra
  → Apply: 72.0 / 3.6 = 20.0 m/s
  
  Also: "velocity" → "initial-velocity" name mismatch
  → Graph walk: velocity and initial-velocity share abheda or swarupa?
  → Or: initial-velocity contains "velocity" as substring
  → Map: velocity → initial-velocity

All inputs now satisfied → emit + execute
→ displacement = 104.1 m
```

**File:** `vyakarana/lib/yantra.ml`

### 6. Emit (tantra: lekhana)

**What it does:** Generate OCaml source code from the tantra definition + bound values.

**Operation-to-OCaml mapping** (replaces ocaml-setu.shabda for computation):

| Tantra op | OCaml emission |
|---|---|
| `add a b` | `(a +. b)` |
| `sub a b` | `(a -. b)` |
| `mul a b` | `(a *. b)` |
| `div a b` | `(a /. b)` |
| `power a b` | `(a ** b)` |
| `sqrt a` | `(sqrt a)` |
| `sin a` | `(sin a)` |
| `cos a` | `(cos a)` |
| `tan a` | `(tan a)` |
| `log a` | `(log a)` |
| `abs a` | `(abs_float a)` |
| `neg a` | `(-. a)` |
| `floor a` | `(floor a)` |
| `ceil a` | `(ceil a)` |
| `min a b` | `(min a b)` |
| `max a b` | `(max a b)` |
| `mod a b` | `(mod_float a b)` |
| `factorial n` | `(let rec fact n = if n <= 1 then 1 else n * fact (n-1) in fact n)` |
| `horner cs x` | `(List.fold_left (fun acc c -> acc *. x +. c) 0.0 cs)` |

**Emission template:**
```ocaml
let () =
  (* inputs from bindings *)
  let initial_velocity = 10.0 in
  let acceleration = 9.8 in
  let time = 2.0 in
  (* let block from tantra *)
  let ut = (initial_velocity *. time) in
  let at2 = ((0.5 *. acceleration) *. (time ** 2.0)) in
  let s = (ut +. at2) in
  (* return *)
  Printf.printf "displacement = %f\n" s
```

**Nested expression handling:**
The `let` block in a tantra can have nested calls: `mul (mul 0.5 acceleration) (power time 2.0)`.
The emitter must recursively expand: `((0.5 *. acceleration) *. (time ** 2.0))`.

**Implementation:**
- Parse each `let` binding's RHS as a tree: `op arg1 arg2` where args can be `(op arg1 arg2)` recursively, or names, or literal numbers
- Walk the tree, emitting OCaml with proper parenthesisation
- For `factorial`, emit a local `let rec` since OCaml stdlib doesn't have it
- For `horner`, emit a local `List.fold_left`

**File:** `vyakarana/lib/yantra.ml`

### 7. Execute (tantra: prayoga-chalana)

**What it does:** Compile and run the emitted OCaml, capture stdout.

**Approach:**
1. Write emitted code to a temp file: `/tmp/yantra_<hash>.ml`
2. Run `ocaml /tmp/yantra_<hash>.ml` via `Unix.open_process_in`
3. Read stdout — this is the result
4. Parse the result back into floats
5. Clean up temp file

**Alternative (faster, no file):**
- Pipe the OCaml source directly to `ocaml` via stdin
- `echo "<code>" | ocaml -stdin`
- Avoids file I/O

**Error handling:**
- If `ocaml` returns non-zero exit code, capture stderr
- Report: "computation failed: <error message>"
- Common errors: division by zero, sqrt of negative, overflow

**File:** `vyakarana/lib/yantra.ml`

### 8. Return + Session Memory (tantra: smriti)

**What it does:** Return the result to the user and store bindings for future queries.

**Session state:**
```ocaml
type session = {
  mutable bindings : (string * float) list;    (* named values *)
  mutable last_result : (string * float) list;  (* last tantra's return values *)
  mutable history : string list;                (* previous queries *)
}
```

**Carry-forward rules:**
- After computing `displacement`, the result `s = 39.6` is stored in session
- Next query `"what is the kinetic energy?"` can use the velocity from the projectile computation
- Explicit assignment `"let v = 20"` or `"v = 20"` adds to session bindings
- `"using the previous result"` or `"at that point"` references `last_result`

**Output format:**
```
displacement = 39.6000

  tantra: sthana-antara (displacement)
  inputs: initial-velocity = 10.0, acceleration = 9.8, time = 2.0
  computation: s = u*t + 0.5*a*t^2
```

Show the tantra name, the bound inputs, and a human-readable form of the computation. The user sees what happened, not just the number.

**File:** `vyakarana/lib/yantra.ml` + `vyakarana/bin/vyakarana.ml` (session state in main loop)

---

## Implementation Order

### Step 1: Tantra file parser
- Parse `.tantra` files into the `tantra` record type
- Load all tantras from `brahman/yantra/` at engine startup
- Build the tantra index (name -> tantra, parameter-names -> tantra)
- **File:** `vyakarana/lib/yantra.ml` (new file)
- **Test:** load all 31 tantra files, print the index

### Step 2: Fix tokeniser for numbers
- Modify `clean` in anuvada.ml to preserve `.` between digits
- Add `float_of_string_opt` detection in `classify_token`
- Add `Number of float` to `token_role` type
- **File:** `vyakarana/lib/setu.ml`, `vyakarana/lib/anuvada.ml`
- **Test:** `"sine of 1.57"` should give `[Concept "sine"; Number 1.57]`

### Step 3: Activate bigrams
- After classification, try bigram joins against the graph
- Replace consecutive Concepts with joined Concept if graph has it
- **File:** `vyakarana/lib/anuvada.ml`
- **Test:** `"initial velocity"` -> `Concept "initial-velocity"` (if node exists) or two separate concepts

### Step 4: Binding extractor
- Walk classified tokens, extract `(concept, value)` pairs
- Handle patterns: `concept is number`, `concept = number`, `concept number`
- Add alias table for single-letter variables
- **File:** `vyakarana/lib/yantra.ml`
- **Test:** `"mass is 10 and acceleration is 9.8"` -> `[(mass, 10.0); (acceleration, 9.8)]`

### Step 5: Tantra resolver
- Given operation concept + bindings, find matching tantra
- Verify all required inputs are bound
- **File:** `vyakarana/lib/yantra.ml`
- **Test:** `operation = "displacement"`, bindings match `sthana-antara.tantra`

### Step 6: OCaml emitter
- Emit OCaml from tantra definition + bound values
- Handle nested expressions, the op-to-OCaml table
- **File:** `vyakarana/lib/yantra.ml`
- **Test:** emit code for displacement tantra, verify it compiles

### Step 7: Executor
- Run emitted OCaml via `Unix.open_process_in`
- Capture result, parse back to float
- **File:** `vyakarana/lib/yantra.ml`
- **Test:** full round trip: `"what is 3 plus 5?"` -> `8.0`

### Step 8: Yantra event routing
- Add `Yantra` event type to event.ml
- In vyakarana.ml main loop: after tokenise + classify, check if input has computable content
- If yes: route to Yantra pipeline instead of Anuvada
- If no: fall through to normal Anuvada reasoning
- **File:** `vyakarana/lib/event.ml`, `vyakarana/bin/vyakarana.ml`
- **Test:** `"what is 3 plus 5?"` returns `8.0`, `"what is consciousness?"` still does graph reasoning

### Step 9: Session memory
- Add session state to main loop
- Carry bindings across queries
- Handle `"using the previous result"` / `"at that point"`
- **File:** `vyakarana/bin/vyakarana.ml`, `vyakarana/lib/yantra.ml`
- **Test:** `"v = 20"` then `"find momentum when mass is 5"` uses session velocity

### Step 10: English language graph nodes
- Write `.om` nodes for English words that carry computational meaning
- Each word node connects to the physics/math concept it implies via graph edges
- The parser resolves words by walking the graph, not by hardcoded lookup tables
- **Directory:** `brahman/kosha/language/yantra-english/`
- **Categories:**
  - Verbs: accelerates, stops, weighs, travels, drops, thrown, falls, heats, cools
  - Implied values: rest, horizontal, vertical, upward, downward
  - Pronouns/references: it, its, that, this, the-previous
  - Preposition patterns: at, for, with, from (binding patterns)
  - Unit words: seconds, meters, kilograms, newtons, joules, degrees
  - Question patterns: how-far, how-long, how-fast, how-much
  - Aliases: f→force, m→mass, a→acceleration, v→velocity, t→time, s→displacement
- **Test:** engine resolves "from rest" → (initial-velocity, 0.0) via graph walk

### Step 11: Multi-sentence / paragraph
- Split input on sentence boundaries (`. ` `? ` `! ` but NOT `.` inside numbers/units)
- Process each sentence through the pipeline
- Chain results: output of sentence N feeds input of sentence N+1
- Context tracking: entity introduced in sentence 1 is available in sentence 5
- Phase transitions: "now it brakes" overrides acceleration, carries velocity forward
- **File:** `vyakarana/lib/yantra.ml`
- **Test:** 5-sentence car paragraph: setup → velocity → displacement → energy → braking time

### Step 12: Meta-tantra (anuvada-ganana)
- Write the parsing pipeline itself as a tantra file
- Uses graph operations: resolve, walk, match, bind, chain, context, recall
- Bootstrapped: OCaml implementation first, tantra definition second
- Eventually the tantra replaces the OCaml — self-hosting parser
- **File:** `brahman/yantra/anuvada-ganana.tantra`

---

## English Language Graph Design

### Principle

The proof graph IS the language understanding. English words are nodes.
Each word connects to the concept it expresses via standard edge types:
- `abheda` — this word IS that concept (rest abheda velocity, rest abheda zero)
- `ahara` — this word takes input (weighs ahara mass — weighs receives mass)
- `phala` — this word produces output (accelerates phala acceleration)
- `sthita` — this word implies context (horizontal sthita angle)
- `yukta` — this word connects to (drops yukta gravity)

### How parsing works via graph walk

```
Sentence: "A car starts from rest and accelerates at 5 m/s2 for 10 seconds"

Token "rest":
  → graph lookup: word-rest node exists
  → follow abheda edges: velocity-abheda, shunya-abheda
  → resolve: velocity = 0 (shunya = zero)
  → binding: (initial-velocity, 0.0)

Token "accelerates":
  → graph lookup: word-accelerates node exists
  → follow phala edge: acceleration-phala
  → next token is number → bind it
  → binding: (acceleration, 5.0)

Token "at":
  → graph lookup: word-at node exists
  → preposition-binding pattern: number follows → bind to preceding concept

Token "5":
  → Number 5.0
  → bound to acceleration (from "accelerates ... at 5")

Token "m/s2":
  → graph lookup: unit-mps2 node exists
  → follow abheda: metre-per-second-squared
  → unit: metre-per-second-squared

Token "for":
  → graph lookup: word-for node exists
  → preposition-binding pattern: number follows → bind to duration/time

Token "10":
  → Number 10.0
  → bound to time (from "for 10")

Token "seconds":
  → graph lookup: unit-seconds node exists
  → follow abheda: second
  → unit: second

Result: [(initial-velocity, 0.0, m/s), (acceleration, 5.0, m/s²), (time, 10.0, s)]
```

No hardcoded patterns. Every resolution is a graph walk.

### Node categories

**Verbs (kriya-pada):** Words that imply a physics concept is being set or computed.
Each has `phala` edges pointing to what it produces.

**Implied values (niyata-pada):** Words that carry a specific numeric value.
Each has `abheda` edges to the concept AND to the value (shunya, eka, etc).

**Pronouns (sarvanama):** Words that reference session context.
Each has `context-abheda` — resolved at runtime to the current entity.

**Prepositions (vibhakti):** Words that structure bindings.
Each has `ahara-swarupa` — they take the next number and bind it to the preceding concept.

**Unit words (matra-pada):** Full English names for units.
Each has `abheda` to the unit node (seconds abheda second, meters abheda metre).

**Question patterns (prashna-pada):** Multi-word phrases that imply a target concept.
Each has `phala` pointing to what they're asking for (how-far phala displacement).

**Aliases (sankshepa):** Single-letter or short abbreviations.
Each has `abheda` to the full concept (f abheda force).

---

## Files to create / modify

| File | Action | Purpose |
|---|---|---|
| `vyakarana/lib/yantra.ml` | **CREATE** | tantra parser, binder, resolver, emitter, executor |
| `vyakarana/lib/event.ml` | MODIFY | add Yantra event type |
| `vyakarana/lib/setu.ml` | MODIFY | extend token_role, fix classify_token for floats |
| `vyakarana/lib/anuvada.ml` | MODIFY | fix clean function, activate bigrams, add yantra routing |
| `vyakarana/bin/vyakarana.ml` | MODIFY | add yantra event handling, session state |
| `vyakarana/lib/dune` | MODIFY | add yantra.ml to library |
| `brahman/kosha/language/yantra-english/*.om` | **CREATE** | English word nodes for computational vocabulary |

---

## Tantra files (already written)

### ganaka/ (basic calculator — 7 files)
- sankalana.tantra (addition)
- vyavakalana.tantra (subtraction)
- gunana.tantra (multiplication)
- vibhajana.tantra (division)
- viparita.tantra (negation)
- shesha.tantra (modulo)
- matra.tantra (abs)

### vidnyana/ (scientific calculator — 13 files)
- ghana.tantra (power)
- mula-ganana.tantra (sqrt)
- jya.tantra (sine)
- kojya.tantra (cosine)
- sparshjya.tantra (tangent)
- ganita-log.tantra (logarithm)
- kramaguna.tantra (factorial)
- adho-seema.tantra (floor)
- urdha-seema.tantra (ceil)
- laghu.tantra (min)
- guru.tantra (max)
- dvighata.tantra (quadratic)
- bahupada-ganana.tantra (polynomial-eval)

### bhautika/ (physics — 11 files)
- sthana-antara.tantra (displacement)
- antya-vega.tantra (final-velocity)
- vega-varga.tantra (velocity-squared)
- kshipra.tantra (projectile)
- bala.tantra (force)
- karya.tantra (work)
- chala-urja.tantra (kinetic-energy)
- sthithi-urja.tantra (potential-energy)
- tirupu.tantra (torque)
- kona-vega.tantra (angular-velocity)
- samvega.tantra (momentum)

---

## Example end-to-end traces

### Trace 1: Basic arithmetic
```
Input:  "what is 3 plus 5?"
Tokens: [Grammar(Drishthanta) "what"] [Grammar(Swarupa) "is"] [Number 3.0] [Concept "plus"] [Number 5.0]
Bind:   operation = "addition" (plus -> addition via graph), args = [3.0, 5.0]
Tantra: sankalana.tantra (addition), inputs: a float, b float
Emit:   let () = let a = 3.0 in let b = 5.0 in let result = (a +. b) in Printf.printf "%f\n" result
Run:    ocaml -> "8.000000"
Output: 8.0
```

### Trace 2: Scientific calculator
```
Input:  "what is the sine of 1.57?"
Tokens: [Grammar "what"] [Grammar "is"] [Article "the"] [Concept "sine"] [Grammar(Sthita) "of"] [Number 1.57]
Bind:   operation = "sine", args = [(angle, 1.57)]
Tantra: jya.tantra (sine), inputs: angle float
Emit:   let () = let angle = 1.57 in let result = (sin angle) in Printf.printf "%f\n" result
Run:    ocaml -> "0.999998"
Output: 0.999998
```

### Trace 3: Physics with named parameters
```
Input:  "find displacement when initial velocity is 10 acceleration is 9.8 and time is 2"
Tokens: [Grammar "find"] [Concept "displacement"] [Grammar "when"] [Concept "initial-velocity"] [Grammar(Swarupa) "is"] [Number 10.0] [Concept "acceleration"] [Grammar(Swarupa) "is"] [Number 9.8] [Grammar(Yukta) "and"] [Concept "time"] [Grammar(Swarupa) "is"] [Number 2.0]
Bind:   operation = "displacement", bindings = [(initial-velocity, 10.0), (acceleration, 9.8), (time, 2.0)]
Tantra: sthana-antara.tantra, inputs: initial-velocity float, acceleration float, time float
Emit:   let () =
          let initial_velocity = 10.0 in
          let acceleration = 9.8 in
          let time = 2.0 in
          let ut = (initial_velocity *. time) in
          let at2 = ((0.5 *. acceleration) *. (time ** 2.0)) in
          let s = (ut +. at2) in
          Printf.printf "displacement = %f\n" s
Run:    ocaml -> "displacement = 39.600000"
Output: displacement = 39.6
```

### Trace 4: Variable shorthand with session
```
Input 1: "f = 100, m = 10"
Tokens:  [Unknown "f"] [Operator "="] [Number 100.0] [Unknown "m"] [Operator "="] [Number 10.0]
Alias:   f -> force, m -> mass
Bind:    session += [(force, 100.0), (mass, 10.0)]
Output:  force = 100.0, mass = 10.0 (stored)

Input 2: "what is the acceleration?"
Tokens:  [Grammar "what"] [Grammar "is"] [Article "the"] [Concept "acceleration"]
Bind:    operation = "acceleration", no direct tantra
         BUT: session has force + mass, and force.tantra says force = mul mass acceleration
         -> invert: acceleration = div force mass
Emit:    let () = let f = 100.0 in let m = 10.0 in let a = (f /. m) in Printf.printf "acceleration = %f\n" a
Run:     ocaml -> "acceleration = 10.000000"
Output:  acceleration = 10.0
```

### Trace 5: Multi-sentence paragraph
```
Input: "A ball is thrown with velocity 20 at angle 0.785. Find the position after 2 seconds."

Sentence 1: "A ball is thrown with velocity 20 at angle 0.785"
  Bind: session += [(velocity, 20.0), (angle, 0.785)]
  No operation requested — just bindings stored.

Sentence 2: "Find the position after 2 seconds"
  Bind: operation = "projectile", session has velocity + angle, new binding: time = 2.0
  Tantra: kshipra.tantra (projectile)
  Inputs: initial-velocity = 20.0 (from session "velocity"), angle = 0.785, time = 2.0
  Emit + Run -> x = 14.14, y = 4.33
  Output: x = 14.14, y = 4.33
```

---

## Units System (tantra: matra-parivartana)

### What the graph already has

The graph has a working unit/constant system via `matra-setu`:

| Unit node | Satya | Linked to |
|---|---|---|
| `newton` | 0.68 | `force-yukta kilogram-yukta metre-yukta second-yukta` |
| `kilogram` | 0.71 | `mass-yukta` |
| `metre` | 0.68 | `length-yukta displacement-yukta` |
| `second` | 0.69 | `kaala-yukta duration-yukta` |
| `radian` | 0.67 | `kona-swarupa pi-yukta` |
| `planck-constant` | 0.72 | `joule-yukta second-yukta` |
| `speed-of-light` | 0.65 | `photon-yukta` |
| `gravitational-constant` | 0.65 | `newton-yukta metre-yukta kilogram-yukta` |

The graph already knows the STRUCTURE of units — newton is `kilogram-yukta metre-yukta second-yukta` (kg*m/s^2). The relationships ARE the dimensional analysis.

### What's missing

| Missing | Needed for |
|---|---|
| `joule` | energy units (kg*m^2/s^2) |
| `watt` | power units (J/s) |
| `degree` | angle input in degrees (convert to radian) |
| `meter` (alias) | American spelling -> metre |
| SI prefixes | kilo, milli, micro, mega, giga |
| Unit shorthand | N, kg, m, s, J, W, rad, deg |
| Numeric constants | g=9.81, c=299792458, pi=3.14159... |

### Units in tantra files

Units belong in the tantra as a third column on inputs and returns:

```
tantra force

  inputs
    mass          float  kilogram
    acceleration  float  metre-per-second-squared

  let
    f = mul mass acceleration

  return
    f  float  newton

done
```

This way the tantra declares:
- What units the inputs expect
- What units the output is in
- The engine can verify dimensional consistency

### Unit conversion tantra

When the user says `"force is 10 N"` or `"mass is 5 kg"`, the parser:
1. Recognises `N` as shorthand for `newton`
2. Recognises `kg` as shorthand for `kilogram`
3. Verifies the unit matches what the tantra expects for that parameter
4. If units don't match, applies conversion

Conversions are themselves tantras:

```
tantra degree-to-radian

  inputs
    angle  float  degree

  let
    result = mul angle (div pi 180.0)

  return
    result  float  radian

done
```

```
tantra kilometre-to-metre

  inputs
    distance  float  kilometre

  let
    result = mul distance 1000.0

  return
    result  float  metre

done
```

### Unit shorthand table (new .om node: yantra-matra.om)

```
N:newton kg:kilogram m:metre s:second
J:joule W:watt rad:radian deg:degree
km:kilometre cm:centimetre mm:millimetre
m/s:metre-per-second m/s2:metre-per-second-squared
kg*m/s2:newton N*m:newton-metre
```

### Dimensional analysis via the graph

The graph already encodes unit composition through `yukta` edges:
- `newton` has `kilogram-yukta metre-yukta second-yukta`
- This means N = kg * m / s^2

To verify that `force = mass * acceleration` produces newtons:
- `mass` is in `kilogram`
- `acceleration` is in `metre-per-second-squared` (m/s^2)
- `kilogram * (metre / second^2)` = `kilogram * metre * second^-2` = `newton`

The graph walk can verify this. Each unit node's `yukta` edges define its dimension. Multiplication combines dimensions, division inverts them. If the result matches the declared output unit, the computation is dimensionally consistent.

### Physical constants tantra

Constants are tantras with no inputs:

```
tantra gravity

  inputs

  let
    g = 9.80665

  return
    g  float  metre-per-second-squared

done
```

```
tantra speed-of-light

  inputs

  let
    c = 299792458.0

  return
    c  float  metre-per-second

done
```

```
tantra pi-constant

  inputs

  let
    pi = 3.14159265358979323846

  return
    pi  float

done
```

When a tantra references `gravity` or `pi` in its let block, the engine resolves it by loading the constant tantra and inlining the value.

### Implementation order for units

Units come AFTER the basic pipeline works (Steps 1-8). Then:

**Step 11: Unit node creation**
- Create missing unit .om nodes: `joule`, `watt`, `degree`, `metre-per-second`, `metre-per-second-squared`, `newton-metre`
- Create `yantra-matra.om` with shorthand table
- Create SI prefix nodes

**Step 12: Unit column in tantra parser**
- Extend tantra parser to read optional third column on inputs/returns
- Store unit info in tantra record type

**Step 13: Unit recognition in tokeniser**
- After a number token, check if the next token is a unit shorthand
- `"10 N"` -> `Number 10.0` + `Unit "newton"`
- `"5 kg"` -> `Number 5.0` + `Unit "kilogram"`

**Step 14: Unit conversion**
- When bound unit doesn't match tantra's expected unit, find a conversion tantra
- Apply conversion automatically
- `"angle is 45 degrees"` -> tantra expects radian -> apply degree-to-radian -> 0.785

**Step 15: Dimensional verification**
- Walk unit nodes' yukta edges to extract dimensions
- Verify input dimensions produce output dimensions through the computation
- Warn if dimensions don't match

---

## Decision log

- **No shabda for op-to-OCaml mapping.** The tantra file itself is the mapping. The emit table is a small hardcoded lookup in yantra.ml (15-20 entries). If we ever need to change it, we change it in one place.
- **Aliases stored in graph.** Single-letter physics aliases (f, m, a, v, t, s) will be a new `.om` node: `yantra-aliases.om` with shabda `f:force m:mass a:acceleration v:velocity t:time s:displacement`.
- **Tantra files loaded at startup.** Same pattern as `.om` files. Walk `brahman/yantra/` recursively, parse each `.tantra`, build index.
- **Yantra routing happens BEFORE Anuvada.** If the input contains computable content (a known tantra operation + numbers), it goes to Yantra. If not, it falls through to Anuvada reasoning. The user doesn't need to type `PRAYOGA` or any prefix.
- **Session state lives in the main loop.** Not in a file, not serialised. Persists for the duration of the interactive session. Reset on `VISARJANA`.
- **OCaml execution via process pipe.** No file I/O for simple computations. Pipe to `ocaml -stdin`. Only write to file for complex/multi-file programs.
- **The conversion pipeline itself is structured as a tantra** (anuvada-ganana) so it can eventually be self-hosted. But first implementation is pure OCaml.
- **Units are declared in tantra files** as a third column on inputs/returns. This makes dimensional analysis explicit and verifiable.
- **Unit conversions are themselves tantras.** degree-to-radian, kilometre-to-metre, etc. The engine chains them automatically when needed.
- **Physical constants are zero-input tantras.** gravity, pi, speed-of-light, etc. Referenced by name in other tantras, resolved by inlining the value.
- **Dimensional verification uses the graph.** Unit nodes' yukta edges encode dimension composition. The engine walks these to verify consistency — no hardcoded dimension tables.
