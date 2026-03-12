# Composition Pipeline — Design Plan

**Status**: Design complete. Implementation not yet started.
**Depends on**: P5 (degree enrichment done), P6b (grammar connectives), P6c (implication edges),
               P8 (execute-chain exists)
**Supersedes**: yantra-plan-extraction.tantra, yantra-plan-resolution.tantra, format-response.tantra
               (those become thin shims or are removed)

---

## Core Insight

**Decomposition IS the inverse of composition.**

If we can compose "kinetic energy equals half times mass times velocity squared" from
the graph, then parsing "what is the kinetic energy of a 5kg object at 3m/s?" is the
same walk in reverse. Grammar nodes and formula nodes are shared between both directions.
The direction is determined by query intent (what is asked vs what is given).

This unifies:
- NLP parsing (question → formula + bindings)
- Computation (formula + bindings → result)
- Response generation (result + formula + grammar context → sentence)

Into one graph-native pipeline with no hardcoded dispatch tables.

---

## The Full Pipeline

```
QUESTION
  ↓ [decompose-question.tantra]
  grammar role classification (question word, nouns, values, units)
  ↓
  query intent + anchor nodes + value bindings
  ↓ [match-formula.tantra]
  implication walk from target → formula candidates
  binding coverage check → select formula chain
  ↓ [execute-chain (existing)]
  stack machine over krama edges → computed result
  ↓ [compose-response.tantra]
  krama-lhs + copula + krama-rhs + ops + result + unit
  ↓
ANSWER
```

---

## Composition Direction (answer → sentence)

Given a formula node + computed result + grammar context:

```
formula:  kinetic-energy-mantra
bindings: {mass: 5kg, velocity: 3m/s, result: 22.5J}
context:  vartamana-kaala + kartari-prayoga

→ "kinetic energy is 22.5 joules"
→ "kinetic energy equals half times mass times velocity squared"
→ "½ × 5 × 3² = 22.5 J"   (terse mode)
```

Walk:
1. `krama-lhs` shabda `name:` → subject noun ("kinetic energy")
2. grammar context node → copula form ("is" / "equals" / "was")
3. `krama-rhs` vars + bhasha forms of krama operations → formula body
4. result value + unit node → numeric conclusion

The **word order of the formula body** comes from krama-rhs declaration order
(not krama computation order — these differ). krama-rhs is already in reading
order: `mass,velocity` → "mass times velocity squared".

---

## Decomposition Direction (question → formula + bindings)

```
"what is the kinetic energy of a 5kg object moving at 3m/s?"
```

1. **Grammar layer** — classify each token:
   - `what` → prashna node → query-intent: solve-for krama-lhs
   - `is` → vartamana-kaala + kartari-prayoga → present active
   - `kinetic energy` → anchor: kinetic-energy-mantra (or kinetic-energy kosha node)
   - `5kg` → value=5.0, unit=kg → unit-resolve → mass
   - `3m/s` → value=3.0, unit=m/s → unit-resolve → velocity

2. **Logic layer** — implication walk:
   - kinetic-energy-mantra krama-rhs: [mass, velocity] — both bound ✓
   - implication edge: (mass ∧ velocity) → kinetic-energy
   - formula fully resolvable → execute

3. **Execute-chain** → 22.5 J

4. **Compose response** → "kinetic energy is 22.5 J"

---

## Logic Layer — Multi-step Inference

When no single formula covers the question, logic nodes chain formulas:

```
"if I know force 10N and mass 2kg, what velocity after 5 seconds from rest?"

Step 1: F=ma → pratipaksha → a = F/m = 5 m/s²
        implication: (F ∧ m) → a   [newton-second-law pratipaksha]

Step 2: v = u + at → a=5, t=5, u=0 → v = 25 m/s
        implication: (u ∧ a ∧ t) → v   [velocity-mantra]

chain: (F ∧ m ∧ t) → a → v
```

Logic nodes involved:
- `implication`: if these premises known, this conclusion follows
  → declared as edge on formula nodes: `(mass ∧ force)-implication-acceleration`
- `theorem`: a formula node established and usable as a premise
  → every mantra node IS a theorem node (execute-chain-kriya declares it)
- `proof`: the krama chain execution that establishes the result
  → the execute-chain output IS the proof

`match-formula.tantra` walks implication edges to find the chain.
Depth-first or breadth-first strategy declared via graph/ nodes (P6c).

---

## Inverse Questions (pratipaksha direction)

```
"what mass gives kinetic energy of 100J at velocity 5m/s?"
```

1. Target is krama-rhs member (mass), not krama-lhs (kinetic-energy)
2. Walk pratipaksha of kinetic-energy-mantra → inverse formula
3. Rearrange: mass = 2×KE / v² = 2×100 / 25 = 8 kg

The `pratipaksha` edge on mantra nodes (P5.5) enables this automatically.
`match-formula.tantra` detects that the target is in krama-rhs, not krama-lhs,
and takes the pratipaksha path.

---

## "What do I need?" Questions

```
"what do I need to know to find the period of a pendulum?"
```

1. target-node = period-mantra
2. walk `janya` edges → [length, gravity]
3. compose: "to find the period you need: length of pendulum, gravitational acceleration"

Same tantra, different query-intent: `janya-prashna` instead of `solve-for`.

---

## Relational Questions

```
"how are kinetic energy and momentum related?"
```

1. anchor nodes: kinetic-energy, momentum
2. walk graph paths between them (BFS, max depth 3)
3. find shared formula nodes or shared krama-rhs variables (velocity, mass)
4. compose: "kinetic energy and momentum both depend on mass and velocity;
            KE = p²/2m where p is momentum"

Uses graph/ operations nodes (BFS/DFS from P6c) for path finding.

---

## Tantra Specifications

### decompose-question.tantra

```
tantra decompose-question
  inputs
    sentence  string
  let
    tokens     = tokenise sentence
    classified = map tokens (fn t -> classify t)
    -- find query intent from question word
    intent     = first-match classified (fn t ->
                   cond (eq (nth t 1) "prashna") (nth t 0) otherwise _none)
    -- find anchor nodes (domain terms that exist in graph)
    anchors    = filter classified (fn t -> eq (nth t 1) "kosha-node"))
    -- extract value+unit pairs
    values     = filter classified (fn t -> eq (nth t 1) "value-unit"))
    -- resolve units to quantity nodes
    bindings   = map values (fn v -> resolve-unit-to-quantity v)
    -- determine target: what are we solving for?
    target     = derive-target intent anchors
  return
    (bind "intent"   intent
    (bind "target"   target
    (bind "anchors"  anchors
    (bind "bindings" bindings _none))))  list
done
```

### match-formula.tantra

```
tantra match-formula
  inputs
    target    string   -- node we want to compute / know about
    bindings  list     -- [(quantity-node, value, unit), ...]
    intent    string   -- "solve-for" | "explain" | "janya-prashna" | "relational"
  let
    -- direct: formula with krama-lhs = target
    direct    = filter (walk-in target "swarupa")
                  (fn n -> eq (shabda n "krama-lhs") target)
    -- inverse: target is in krama-rhs of some formula
    inverse   = filter (all-edges)
                  (fn e -> member target (split (shabda (nth e 0) "krama-rhs") ","))
    -- coverage check: which formulas have all krama-rhs satisfied by bindings?
    bound-qty = map bindings (fn b -> nth b 0)
    covered   = filter direct (fn f ->
                  let rhs = split (shabda f "krama-rhs") ","
                  let missing = filter rhs (fn v -> not (member v bound-qty))
                  eq (length missing) 0)
    -- if no direct covered: walk implication edges one level deeper
    chained   = cond (eq (length covered) 0)
                  (chain-implication target bindings 2)
                  otherwise covered
    -- select by intent
    result    = cond (eq intent "solve-for") chained
                     (eq intent "janya-prashna") (walk target "janya")
                     (eq intent "inverse") inverse
                     otherwise chained
  return
    result  list
done
```

### compose-response.tantra

```
tantra compose-response
  inputs
    formula   string   -- mantra node name
    result    any      -- computed VFloat
    bindings  list     -- [(quantity-node, value, unit), ...]
    context   string   -- grammar context node (vartamana-kaala etc.)
  let
    -- subject: the thing computed
    lhs-node  = shabda formula "krama-lhs"
    subject   = shabda lhs-node "name"
    -- copula from grammar context
    copula    = shabda context "copula"
    -- formula body: rhs vars in declaration order + their bhasha forms
    rhs-vars  = split (shabda formula "krama-rhs") ","
    rhs-names = map rhs-vars (fn v -> shabda v "name")
    ops       = walk formula "krama"
    -- compose formula string (krama ops + rhs names in reading order)
    formula-str = compose-formula-body ops rhs-names
    -- result with unit
    unit-node = shabda formula "krama-lhs-unit"
    result-str = concat [to-string result " " (shabda unit-node "symbol")]
    -- full sentence
    sentence  = concat [subject " " copula " " result-str]
  return
    sentence  string
done
```

### compose-formula-body.tantra (helper)

```
tantra compose-formula-body
  inputs
    ops       list   -- ordered krama operation nodes
    rhs-names list   -- argument names in reading order
  let
    -- pair each op with its bhasha form
    op-words  = map ops (fn op ->
                  let kriya-roots = walk op "kriya"
                  let root = first kriya-roots
                  shabda root "word")  -- from P6a bhasha layer
    -- interleave: name op name op name...
    result    = interleave rhs-names op-words
  return
    result  string
done
```

---

## Shabda Name Field Convention

All formula/mantra nodes need a clean `name:` field in shabda replacing the
long hyphenated descriptions. Convention:

```
-- before:
shabda kinetic-energy-mantra / KE-equals-half-mv-squared degree:2 ...

-- after:
shabda name:kinetic-energy degree:2 krama-lhs:energy krama-rhs:mass,velocity ...
```

The composition tantra generates the description. The shabda `name:` is just
the short English noun phrase for the quantity (used as sentence subject/object).

`krama-lhs-unit:` declares the unit of the output quantity (for response composition).

---

## Bhasha Forms Needed for Operations

The compose-formula-body tantra reads operation bhasha from sangati root bhasha nodes.
Mapping needed (kriya edge from op → sangati root → bhasha form):

| Operation node | kriya → sangati root | bhasha word |
|---|---|---|
| `half` | kshaya-kriya → kshaya | "half" |
| `double` | vriddhi-kriya → vriddhi | "double" |
| `multiplication` | taranga-kriya → taranga | "times" |
| `division` | sama-vibhaga | "divided by" |
| `addition` | sankalana | "plus" |
| `subtraction` | kshaya-kriya → kshaya | "minus" |
| `square` | vriddhi-kriya → vriddhi | "squared" |
| `square-root` | viveka-kriya → viveka | "square root of" |
| `power` | avrti-kriya → avrti | "to the power" |
| `cos` | kona → kona | "cosine of" |

These bhasha forms live in `brahman/bhasha/english/` sangati root nodes (P6a done).
Some may need a `word:` key added to their shabda.

---

## Grammar Connectives Needed (P6b)

`brahman/bhasha/english/grammar/` needs these files for compose-response.tantra:

| File | Content |
|---|---|
| `copula.om` | is, equals, was, gives (vartamana/bhuta-kaala forms) |
| `articles.om` | a, an, the (for formula body noun phrases) |
| `prepositions.om` | of, by, from, through (for formula body connectives) |
| `conjunctions.om` | and, or (for listing krama-rhs vars) |

---

## Implication Edges on Formula Nodes (P6c)

Each mantra node needs `implication` edges declaring what it can derive:

```
-- in kinetic-energy-mantra.om:
"(mass ∧ velocity)-implication-kinetic-energy"

-- in velocity-mantra.om:
"(initial-velocity ∧ acceleration ∧ time)-implication-velocity"
```

These are compound tokens that om_parser decomposes into:
- implication edge: source = conjunction of premises, target = conclusion
- The engine walks these to find applicable formulas

---

## Dependency Stack

```
NOW:     P5 two tantras (compose-degrees, is-identity-composition)
         Loader fix for brahman/bhasha/ (done in om_parser.ml)

P6b:     grammar/copula.om, articles.om, prepositions.om, conjunctions.om
         word: key added to operation-relevant sangati bhasha nodes

P6c:     implication edges on all mantra nodes (physics + math)
         name: + krama-lhs-unit: keys on all mantra node shabda

P8:      decompose-question.tantra
         match-formula.tantra
         compose-response.tantra
         compose-formula-body.tantra (helper)
         chain-implication.tantra (helper for multi-step)

P7:      replace yantra-plan-extraction with decompose-question
         replace yantra-plan-resolution with match-formula
         (keep old tantras as fallback shims until regression confirmed)

P7.5:    replace format-response with compose-response
         strip hyphenated shabda descriptions → name: fields
```

---

## What This Unlocks

| Capability | How |
|---|---|
| Any .om formula auto-queryable | krama-lhs/rhs + implication = discoverable |
| Multi-step inference | chain-implication walks theorem nodes |
| Inverse questions | pratipaksha walk on mantra node |
| "What do I need?" | walk janya edges of target |
| "How are X and Y related?" | BFS between anchor nodes |
| Units handled | matra-ganana.tantra (already exists) |
| New domain = zero tantra changes | add .om node with krama + implication edges |
| Grammar correctness | grammar context nodes drive copula + inflection |
| Response = composed sentence | not a template — a graph walk |

---

## Living Notes

- `chain-implication` depth limit: read from `shabda "yantra-policy" "chain-depth-limit"`
  (same policy node already used by yantra-plan-resolution.tantra)
- `interleave` helper may need OCaml primitive if tantra reduce can't do it cleanly
- `compose-formula-body` output style: "mass times velocity squared" (reading order)
  NOT "square velocity multiply mass halve" (computation order) — rhs-names drives order
- Regression gate throughout: 49/52
