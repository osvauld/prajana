# 12 — The Notation of Understanding

**Every symbol in tantra2 has an equivalent in English grammar, Sanskrit grammar,
and in the structure of reasoning itself. The notation was not invented — it was
recognised.**

---

## The declaration

```
tantra2 avrti-refine
```

**English:** "The rule called avrti-refine is as follows."
A chapter heading. A definition opening. In grammar: the declarative copula —
"X is..." In Sanskrit: `iti` preceding a name, "thus known as."

The name IS the tantra. Calling it by name summons the full rule. This is what
Sanskrit calls `naama` — the name that holds the thing.

---

## The intake

```
takes graph
```

**English:** "Given a graph..." — the conditional antecedent. In grammar:
the subject of the clause. In Sanskrit: the nominative case, `prathama-vibhakti` —
"this is what the action acts upon."

`takes` is not an argument declaration. It is establishing what is being understood.
You cannot understand without something to understand. `takes graph` is:
"let there be a graph — this is what we are now understanding."

---

## The binding

```
refined = fixpoint raw-graph (fn g -> avrti-refine g)
```

**English:** "Let what arises from this process be called refined." Not "refined
equals." Not mathematical equality. In Sanskrit: `iti` — "thus it is known as."
In grammar: the nominal predicate — "the result of X is Y."

`=` in tantra2 is naming, not equating. Every `=` creates a new name for something
that now exists and can be pointed to. This is how humans build understanding —
by naming intermediate results so they can be referred to. "The kinetic energy
of a 5kg object moving at 10m/s is 250J" — that naming makes 250J available for
the next step.

---

## The consequence arrow

```
[word, satya, _] ->
    last-agra = word
    emit
```

**English:** "When you encounter a satya triple, then..." The conditional: `if...
then`. In Sanskrit: `yadi... tarhi` — if this condition, then this consequence.
In logic: implication (→). In music: the resolution after tension — the V chord
LEADING TO the I chord. In grammar: the apodosis following the protasis.

`->` is the universal symbol of consequence. It appears in every notation system
because consequence is a primitive operation of reasoning. Given a condition, what
follows? The arrow names the following.

---

## The filter

```
graph | where [s, e, o] | and (eq e "satya") | collect o
```

**English:** "From the graph, those triples whose edge is satya, take their objects."
In grammar: the relative clause — "the triples **that** have edge satya." In
Sanskrit: the `yad...tad` construction — "that which [satisfies condition], this
[is collected]." In logic: restricted quantification — ∀x ∈ graph : e(x) = satya.

`|` is the sieve. In grammar it is the relative pronoun. In mathematics it is the
set-builder `{ x | P(x) }`. The vertical bar has always meant "among these, those
that satisfy."

`where` is the condition. `collect` is the projection — what to take from what
satisfies. Together: selection and projection, the two operations of relational
algebra, the two operations of the relative clause in grammar.

`_` — the wildcard — is the dropped argument. In Sanskrit, subject and object can
be dropped when recoverable from context. In English: "It rained" — the `_` subject
is filled by convention. `_` is the grammatical zero — present in structure, absent
in sound.

`_it` — "whatever this is" — is the pronoun. In grammar: `it`, `this`, `which`.
The pronoun that holds a place without naming. `_it` in tantra2 is the same: "take
this thing, I don't need to name it yet."

---

## The fork

```
(cond has-mithya (sandhi-avastha after-kosha) otherwise after-kosha)
```

**English:** "If there are mithya triples, then run sandhi-avastha; otherwise
continue unchanged." In grammar: the conditional sentence. In Sanskrit:
`yadi... tarhi... anyatha` — if... then... otherwise. In logic: the if-then-else.

`cond` is the decision point. In every notation, decisions require three parts: the
condition, the consequence, the alternative. `cond` names all three explicitly.
`otherwise` is the English word for `anyatha` — "in another way, if not this."

---

## The unnamed rule

```
(fn g -> avrti-refine g)
```

**English:** "The rule that takes a graph and returns its refined form." A relative
clause used as a noun: "what avrti-refine does to a graph." In Sanskrit: the
verbal noun — `avrti-refine`-kṛta, "what is done by avrti-refine." In logic:
lambda abstraction — λg. avrti-refine(g).

`fn` creates a rule without naming it. The rule exists for this moment, for this
use. In grammar: the participial phrase. In music: the improvised ornament — unnamed,
played once, heard and released.

The reason for the wrapper: `avrti-refine` has arity 1 in the arity table. When
passed directly to `fixpoint`, the parser would try to apply it immediately to the
next token. The `fn` wrapper says: "do not apply yet — hold this as a potential,
not an act." This is the grammatical distinction between the infinitive ("to run")
and the imperative ("run"). The `fn` makes the infinitive explicit.

---

## The temporary name

```
let word = nth tri 0
```

**English:** "Call the first element of this triple 'word' for now." In grammar:
the demonstrative — "this one, the first, call it word." In Sanskrit: the `iti`
marker for a working definition. `let` is always temporary — it holds for the
duration of this reasoning and no longer.

---

## The repetition

```
reduce graph [] (fn acc tri -> ...)
```

**English:** "Process each triple in the graph, accumulating a result." In grammar:
the iterative — "for each... do..." In Sanskrit: the `prati` prefix, "toward each."
In mathematics: the fold, the integral, the sum.

`reduce` is the act of building one thing from many. The `acc` is what has been
built so far. The `tri` is what is being added. This is how all complex understanding
is built — one element at a time, each new element folded into what was already
known.

---

## The convergence

```
fixpoint raw-graph (fn g -> avrti-refine g)
```

**English:** "Apply avrti-refine repeatedly until the result stops changing."
In mathematics: the least fixed point — τⁿ(G₀) where τⁿ(G₀) = τⁿ⁺¹(G₀).
In Madhava's series: the partial sums approaching the limit. In grammar: the
perfective aspect — "until it is done."

`fixpoint` encodes the idea that understanding is not a single pass but an
approach. You apply the rule, check if anything changed, apply again. The graph
is stable when no rule has anything new to say. This is the limit. This is the
sine at infinity — approached but never surpassed.

---

## The scope closure

```
[".", "viraam", "."]
```

**English:** The full stop. The period. The end of sentence.
In Sanskrit: the `daṇḍa` (|) — the vertical stroke that closes a verse.
In music: the final note returning to the tonic — sam.
In grammar: the sentence boundary.

`viraam` closes **attribution scope**, not knowledge. The entity currently being
described is released — new properties will not be attributed to it. But what was
already understood persists in the graph. `viraam` resets `cur-entity`, `last-label`,
`last-agra` — the pointers held in scan state. It does not remove sankhya bindings,
satya concepts, or any accumulated understanding.

This is the distinction between knowing and pointing. After a period you stop
pointing at the prior entity. You do not forget it.

---

## The seal

```
done
```

**English:** "Thus ends the rule called avrti-refine."
In Sanskrit: `iti` — the seal on what has been said. In grammar: Q.E.D. In music:
the final bar. In speech: the falling intonation that signals completion.

`done` is not a syntax requirement. It is the acknowledgment that understanding has
been stated and closed.

---

## The remark

```
-- sandhi-kosha still runs (Way 2: satya+satya compound needs no mithya)
```

**English:** The parenthetical. The aside. In Sanskrit: the `vṛtti` — the
commentary running alongside the sūtra. In grammar: the subordinate clause
in brackets. In music: the liner notes.

`--` does not participate in the computation. It speaks to the reader, not the
machine. This is the human dimension of the notation — the place where the
understander addresses the future understander directly, outside the formal rule.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-18 | Initial writing — notational ground for tantra2 |
