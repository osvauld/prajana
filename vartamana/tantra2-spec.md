# tantra2 — Language Specification

A tantra2 file defines a named computation over knowledge graphs. The runtime
evaluates it as a curried function: each `takes` line is one parameter, applied
left-to-right. The body is a sequence of named bindings evaluated in order;
the final `return` names the result.

---

## File structure

```
tantra2 <name>

-- comments with --

takes <param>        -- one line per parameter
takes <param>

<binding> = <expr>   -- body: named expressions, in order
...

return <binding>

done
```

Everything between `takes` and `return` is the body. Bindings are evaluated
sequentially; each binding is in scope for all subsequent bindings.

---

## Expressions

### Literals
```
42          -- number
3.14        -- float
"hello"     -- string (double-quoted)
true false  -- booleans
[]          -- empty list
[a, b, c]   -- list literal
```

### Variables
Any name that is not a keyword or known op is a variable. Looked up in the
current environment. If not found, falls back to a graph node lookup (returns
the node name string if the node exists, otherwise the name itself).

### Function calls
```
<name> <arg1> <arg2>   -- fixed arity, from arity table
(and a b c d)          -- variadic op: always wrap in parens
```

The arity table governs how many tokens each name consumes as arguments.
**A name with arity N will consume exactly N tokens as arguments wherever it
appears — including inside other expressions.** This is the single most
important rule: check arity before using any name as a local variable or
parameter (see Safety Rules below).

### Lambda
```
(fn x -> expr)
(fn x y -> expr)
```

Parameters are collected until `->`. Body is a single expression. Use parens
around the whole lambda when passing as an argument.

### Let binding (inside lambdas / reduce bodies)
```
let x = expr
let y = expr
body-expr
```

No `in` keyword needed. Each `let x = expr` is implicitly `LetIn(x, expr, rest)`.
The body is the expression that follows the last `let`.

**Rule**: if a variadic op appears in a `let` RHS and the next thing is NOT a
boundary keyword (`let`, `return`, `done`, `)`, `]`, `}`, `|`, `->`), wrap
the call in parens:
```
-- Wrong: append greedily consumes (cond ...) as its third arg
let with-word = append g triples
(cond ...)

-- Right:
let with-word = (append g triples)
(cond ...)
```

### Cond
```
(cond pred consequence otherwise alternative)
(cond pred1 c1 otherwise (cond pred2 c2 otherwise default))
```

Always wrap `cond` in outer parens when used as an expression value. The
predicate must close at the same depth as the opening paren. Consequence and
alternative follow on the same line or in the same paren group.

### Pipe (graph query)
```
graph | where [s, e, o] | and (eq e "satya") | collect o
graph | where [s, e, o] | and (eq e "satya") | collect [s, o]
graph | where [s, e, _] | and (eq e "sankhya") | collect _it
```

`| where [s, e, o]` — destructures each triple; all names are bound as
variables regardless of any arity they might have elsewhere. The `_` is a
wildcard (discards). `_it` refers to the whole item.

`| and (pred)` — filters items. `pred` is any boolean expression.

`| collect expr` — maps surviving items through `expr`. Returns a list.

Pipes can be chained: `... | collect x | collect (to-string _it)` etc.
The pipe `|` is a hard boundary for variadic ops.

### Scan (stateful graph traversal)
```
result = scan graph [state1: type = init1, state2: type = init2]:

  [word, edge, obj]
    when (guard-expr)
    ->
      state1 = new-value
      emit [new-word, new-edge, new-obj]

  [_, some-edge, _] -> emit

  _ -> emit
```

Scan is a **top-level binding only**. It cannot be nested inside `cond` or
used as a sub-expression. If you need conditional scan, compute a boolean
flag, pass it as scan state, and guard branches with `when`.

State declarations `[name: type = init]` initialise the mutable scan state.
Types: `str`, `bool`, `list`, `num`. State is updated with `name = value`
inside a branch (no `let`).

Emit forms:
- `emit` — emit the current triple unchanged
- `emit [s, e, o]` — emit a specific triple
- `emit expr` — emit the value of expr as a triple  
- (no emit) — consume the triple silently (drop it)

Branch patterns `[word, edge, obj]` bind the three triple fields. These
pattern names are safe from arity contamination — they are resolved by the
pattern compiler, not the expression parser.

`when` guards are optional boolean filters on a branch. Multiple `when`
clauses are ANDed.

The `_` pattern in `_ -> emit` is the catch-all.

---

## Parameters and multiple inputs

```
takes first-param
takes second-param
takes third-param
```

One `takes` line per parameter. Parameters are curried left-to-right. Calling
`my-tantra a b` applies `a` to the first param, `b` to the second.

**Parameter names must not appear in the global arity table** (see Safety
Rules). Use short abbreviations if the natural name is an op.

---

## Return

```
return <name>
```

The return value is the named binding. Must be a simple identifier, not an
expression. Bind to a variable first if needed.

---

## Shared tantras (calling one tantra from another)

```
result = other-tantra arg1 arg2
```

If `other-tantra` has arity N, it consumes exactly N tokens as arguments.
Pass through the lambda wrapper `(fn g -> other-tantra g)` when using as a
value (e.g. argument to `fixpoint`, `map`, `reduce`) — because the arity
table would otherwise cause it to consume the next token as its own argument
rather than being passed as a function value.

---

## Safety rules

These rules prevent the two most common silent failures:

### Rule A — Check arity before naming any variable or parameter

The arity table has two sources: tantra pre-scan and graph op nodes. Some
ordinary-looking words have arity > 0:

| Name | Arity | Safe alternative |
|------|-------|-----------------|
| `node` | 1 | `nd` |
| `role` | 1 | `rl` |
| `layer` | 1 | `ly` |
| `value` | 1 | `val` |
| `pair` | -1 | `pr`, `kv` |
| `executor` | varies | `exe` |

**Test**: `c.eval('name "x"')` — if it returns `None` or `<fn>` (not the
string `'name'`), the name has arity > 0 and is unsafe as a local variable.

### Rule B — Wrap variadic ops at `let` boundaries

Variadic ops (`append`, `concat`, `add`, `and`, `or`, `map`, `reduce`) collect
tokens until a boundary. Inside a `let` chain, the NEXT expression is consumed
as an argument unless the call is in parens:

```
-- Wrong: append consumes (cond ...) as third arg
let with-word = append g triples
(cond ...)

-- Right:
let with-word = (append g triples)
(cond ...)
```

### Rule C — Scan is top-level only

A scan block must be its own named binding. It cannot be the `otherwise`
branch of a `cond`. Put the `cond` AFTER the scan, selecting between the
scan result and a passthrough:

```
-- Wrong:
result = (cond need-scan (scan graph [...]: ...) otherwise graph)

-- Right:
scan-result = scan graph [...]: ...
result      = (cond need-scan scan-result otherwise graph)
```

### Rule D — Tantra-as-value needs a lambda wrapper

```
-- Wrong: avrti-refine has arity 1, consumes next token as its arg
refined = fixpoint raw-graph avrti-refine

-- Right:
refined = fixpoint raw-graph (fn g -> avrti-refine g)
```

---

## Parse-error visibility

When a binding fails to parse, the runtime injects a sentinel string:
`[PARSE_ERROR in 'name': reason]`. The binding is NOT silently dropped —
it evaluates to this string, making the failure visible at runtime rather
than producing mysterious `VNone` downstream.

Load-time parse errors also print to stderr:
```
[tantra2 PARSE_ERROR] binding 'name': reason  raw: [raw text...]
```

---

## Naming conventions (from migration experience)

| Pattern | Use |
|---------|-----|
| `nd`, `rl`, `ly`, `nv`, `un` | node, role, layer, num-val, unit-node |
| `ac`, `pn` | active-concept, pending-num |
| `mm`, `sf`, `final-m` | match result, solve-for, final match |
| `sc` | satya-concepts list |
| `bv`, `bcs`, `vps` | bound-vals result, bound-concepts, val-pairs |
| `pr`, `kv` | pair/key-value (instead of `pair`) |
| `exe`, `ea` | executor string, exec-args list |
| `tri` | triple `[s, e, o]` (safe, arity 0) |
| `acc`, `g`, `st` | accumulator, graph, state |

---

## Complete example

```tantra2
tantra2 emit-triples

-- word → triples dispatch. info = [nd, rl, ly, nv, un], ctx = [ac, pn].

takes word
takes info
takes context

nd   = nth info 0
rl   = nth info 1
ly   = nth info 2
nv   = nth info 3
un   = nth info 4

ac   = nth context 0
pn   = nth context 1

has-num  = gt (string-length nv) 0
has-unit = gt (string-length (to-string un)) 0
has-act  = gt (string-length (to-string ac)) 0
has-pend = neq pn ""

is-concept = (and (exists nd)
  (neq rl "grammar")
  (neq rl "intent")
  (neq rl "boundary")
  (neq rl "possession")
  (neq rl "rashi-bandha")
  (neq ly "mantra"))

is-rashi-label = (and has-act (not has-pend) is-concept (neq word (to-string nd)))

triples = (cond (eq rl "intent") [[word, "vidhi-kaala", "solve-for"]]
  otherwise (cond (eq rl "grammar") []
  otherwise (cond (and has-num has-unit has-act)
    [[(to-string ac), "sankhya", nv], [(to-string ac), "matra", (to-string un)]]
  otherwise (cond has-num [[word, "asprista-sankhya", nv]]
  otherwise (cond is-rashi-label [[word, "mithya", word]]
  otherwise (cond is-concept [[(to-string nd), "satya", (to-string nd)]]
  otherwise [[word, "mithya", word]]))))))

return triples

done
```
