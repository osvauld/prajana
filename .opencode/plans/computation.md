# Computation Upgrade Plan

## Motivation

The proof graph has a gap: generic CS concepts like `type`, `loop`, `variable`,
`callable`, `int`, `float`, `array`, `map` either don't exist or are locked to a
specific language (`domain-ocaml-sthita`). This means:

- Lua and OCaml can't share a common understanding of what these things are
- Any future language (Python, JS, etc.) has nothing to stand on
- `prayoga_lua.ml` hardcodes knowledge that should emerge from the graph
- The graph-viz application nodes live in the wrong place (generic kosha vs session)

The fix is a new `kosha/computation/concepts/` layer — language-independent CS
primitives — with Lua, OCaml, and all future languages standing on it.
Each language then carries the **syntax** for how it realises each concept in its
own setu shabda file.

---

## Directory Structure (target state)

```
brahman/kosha/computation/
  concepts/                        ← NEW — language-independent CS primitives
    domain-cs.om
    # types
    type.om  +  type.shabda
    primitive-type.om
    composite-type.om
    int.om
    float.om
    bool.om
    cs-string.om                   ← CS string (distinct from kosha/language/string.om which is linguistic)
    nil.om                         ← absence of value: nil / null / unit / None
    array.om
    cs-list.om                     ← generic list (distinct from ocaml/list.om which is OCaml-specific)
    cs-map.om                      ← generic map (distinct from ocaml/map.om)
    record.om
    tuple.om
    # names & scope
    identifier.om
    scope.om
    binding.om
    mutation.om
    variable.om
    assignment.om
    naming-convention.om  +  naming-convention.shabda
    # computation structure
    expression.om
    statement.om
    callable.om
    parameter.om
    argument.om
    return-value.om                ← replaces kosha/language/lua/return-value.om
    loop.om                        ← generic (OCaml/Lua loop nodes stand on this)
    conditional.om
  # existing hardware/theory nodes stay:
  classical-computer.om
  domain-computation.om
  llm.om
  quantum-computer.om
  quantum-gate.om
  quantum-vyakarana.om

brahman/kosha/language/
  lua/
    lua.om                         ← update: add concepts/* sthita edges
    lua-scope.om                   ← update: add scope-sthita
    lua-setu.shabda                ← EXPAND: full Lua syntax for every concept
    domain-lua.om                  ← update: add concepts/* yukta edges
    return-value.om                ← DELETE — replaced by concepts/return-value.om
    graph-viz-lua.om               ← MOVE to sessions/graph-viz-dev/
    graph-viz-setu.om              ← MOVE to sessions/graph-viz-dev/
    graph-viz-lua.shabda           ← STAY (template, referenced via shabda-tmpl:)
    graph-viz-setu.shabda          ← STAY (template, referenced via shabda-tmpl:)
  ocaml/
    ocaml.om                       ← update: add concepts/* sthita edges
    ocaml-setu.shabda              ← EXPAND: full OCaml syntax for every concept
    ocaml-list.om                  ← RENAME from list.om + add cs-list-sthita
    ocaml-map.om                   ← RENAME from map.om  + add cs-map-sthita
    loop.om                        ← update: add concepts/loop-sthita
    recursion.om                   ← update: add concepts/loop-sthita
    type-system.om                 ← update: add concepts/type-sthita
    state-update.om                ← update: add concepts/mutation-sthita assignment-sthita
    runtime.om                     ← update: add concepts/statement-sthita
    fold.om                        ← update: add concepts/cs-list-sthita
    algebraic-data-type.om         ← update: add concepts/composite-type-sthita

brahman/kosha/
  function.om                      ← update: add callable-sthita parameter-yukta return-value-yukta
  process.om                       ← update: add statement-sthita callable-yukta
  language/string.om               ← update: add cs-string-sthita
```

---

## Phase 1 — Create `kosha/computation/concepts/`

### 1a — Domain marker

| File | Edges |
|---|---|
| `domain-cs.om` | `domain-computation-sthita domain-language-sthita` |

### 1b — Types

| File | What it is | Key edges |
|---|---|---|
| `type.om` | A set of values + operations defined on them | `domain-cs-sthita` + `type.shabda` |
| `primitive-type.om` | Atomic — no substructure | `type-swarupa int-yukta float-yukta bool-yukta cs-string-yukta nil-yukta` |
| `composite-type.om` | Built from other types | `type-swarupa primitive-type-yukta array-yukta cs-list-yukta cs-map-yukta record-yukta tuple-yukta` |
| `int.om` | Whole numbers, exact, bounded, no rounding error | `primitive-type-swarupa domain-cs-sthita` |
| `float.om` | Approximate reals, IEEE 754, has rounding error, NaN/Inf | `primitive-type-swarupa domain-cs-sthita` |
| `bool.om` | True or false — the type of conditions | `primitive-type-swarupa conditional-yukta domain-cs-sthita` |
| `cs-string.om` | Sequence of characters, immutable in most languages | `primitive-type-swarupa sequence-yukta domain-cs-sthita` |
| `nil.om` | Absence of a value — nil/null/unit/None per language | `primitive-type-swarupa domain-cs-sthita` |
| `array.om` | Ordered, same-type, O(1) integer index, fixed size | `composite-type-swarupa domain-cs-sthita` |
| `cs-list.om` | Ordered, same-type, sequential access, O(n) by index | `composite-type-swarupa domain-cs-sthita` |
| `cs-map.om` | Key-value pairs, unique keys, O(1) lookup by key | `composite-type-swarupa domain-cs-sthita` |
| `record.om` | Named fields, each field may be a different type | `composite-type-swarupa domain-cs-sthita` |
| `tuple.om` | Fixed positional collection, each position may differ | `composite-type-swarupa domain-cs-sthita` |

**`type.shabda`** — per-language type names:
```
# primitives
int-lua:      number          # Lua has no separate int; all numbers are float64
float-lua:    number          # same type as int in Lua 5.1/5.2
bool-lua:     boolean
string-lua:   string
nil-lua:      nil

int-ocaml:    int             # 63-bit on 64-bit systems
float-ocaml:  float           # 64-bit IEEE 754
bool-ocaml:   bool
string-ocaml: string
unit-ocaml:   unit            # OCaml's nil equivalent — the absence of a value

# composites
array-lua:    table           # Lua uses table for everything
list-lua:     table
map-lua:      table
record-lua:   table
tuple-lua:    table

array-ocaml:  array           # mutable, fixed size
list-ocaml:   list            # immutable linked list
map-ocaml:    Hashtbl         # mutable; Map module for immutable
record-ocaml: record
tuple-ocaml:  tuple
```

### 1c — Names and scope

| File | What it is | Key edges |
|---|---|---|
| `identifier.om` | A name token that refers to a binding in a scope | `token-sthita binding-yukta scope-yukta domain-cs-sthita` |
| `scope.om` | The region of code where a binding is visible | `binding-yukta identifier-yukta domain-cs-sthita` |
| `binding.om` | First association of a name to a value — may be immutable | `identifier-yukta scope-yukta domain-cs-sthita` |
| `mutation.om` | Changing what an existing binding refers to | `binding-yukta variable-sthita domain-cs-sthita` |
| `variable.om` | A name that can be rebound or mutated | `binding-swarupa identifier-yukta type-yukta domain-cs-sthita` |
| `assignment.om` | The syntax that performs binding or mutation | `variable-yukta binding-kriya domain-cs-sthita` |
| `naming-convention.om` | Rules for how identifiers are written | `identifier-yukta domain-cs-sthita` + `naming-convention.shabda` |

**`naming-convention.shabda`**:
```
# convention forms
camel-case:   firstWordLowerRestTitle      e.g. myVariable
pascal-case:  EachWordTitleCase            e.g. MyType
snake-case:   words_joined_by_underscores  e.g. my_variable
kebab-case:   words-joined-by-hyphens      e.g. my-variable
upper-snake:  WORDS_JOINED_BY_UNDERSCORES  e.g. MY_CONSTANT

# per-language rules
lua-local:      snake-case
lua-constant:   upper-snake
lua-function:   snake-case
ocaml-let:      snake-case
ocaml-module:   pascal-case
ocaml-type:     snake-case
ocaml-variant:  pascal-case
```

### 1d — Computation structure

| File | What it is | Key edges |
|---|---|---|
| `expression.om` | Anything that evaluates to a value | `type-phala domain-cs-sthita` |
| `statement.om` | Executed for side effects, produces no value | `expression-abheda domain-cs-sthita` |
| `callable.om` | Has parameters, body, return value, lives in a scope | `parameter-sthita return-value-yukta scope-yukta domain-cs-sthita` |
| `parameter.om` | Named input slot of a callable, may have a type | `identifier-yukta type-yukta callable-sthita domain-cs-sthita` |
| `argument.om` | Value bound to a parameter at a call site | `parameter-yukta binding-kriya domain-cs-sthita` |
| `return-value.om` | Output produced by a callable when called | `callable-phala type-yukta domain-cs-sthita` |
| `loop.om` | Finite iteration over a range or collection | `scope-yukta variable-yukta callable-yukta domain-cs-sthita` |
| `conditional.om` | Branching on a boolean condition | `bool-sthita expression-yukta scope-yukta domain-cs-sthita` |

---

## Phase 2 — Expand language setu shabdas

This is the core of what you asked: each language must say, in its setu shabda,
exactly **how** each CS concept looks in that language — the actual syntax.
The shabda is the bridge between the concept node and the generated code.

### `lua-setu.shabda` — full Lua syntax for every concept

Sections to add to the existing file:

```
# ── types ──────────────────────────────────────────────────────────────────────
# Lua has one number type for both int and float (5.1/5.2)
# Lua 5.3+ has integer subtype but we target 5.1/5.2 runtime
int:          0
float:        0.0
bool:         true
string:       ""
nil:          nil
array:        {}                     -- table with integer keys 1..n
list:         {}                     -- same as array in Lua
map:          {}                     -- table with string/any keys
record:       {}                     -- table with named string fields
tuple:        {}                     -- table with positional integer keys

# ── variable declaration ────────────────────────────────────────────────────────
# local = binding (first use in scope). No type annotation. No immutability.
# Reassignment is mutation — same syntax as binding.
variable-declare:   local x = value
variable-int:       local x = 0
variable-float:     local x = 0.0
variable-bool:      local x = true
variable-string:    local x = ""
variable-nil:       local x = nil
variable-table:     local x = {}
variable-update:    x = new_value    -- mutation: no 'local', just name = value

# ── collection literals ─────────────────────────────────────────────────────────
array-literal:      {v1, v2, v3}
array-access:       t[i]             -- 1-based index
array-length:       #t
array-append:       table.insert(t, v)
array-iterate:      for i, v in ipairs(t) do ... end

map-literal:        {k1=v1, k2=v2}
map-access:         t.key  or  t["key"]
map-set:            t.key = value
map-has:            t.key ~= nil
map-iterate:        for k, v in pairs(t) do ... end

# ── callable ────────────────────────────────────────────────────────────────────
# Functions are first-class values. No type annotations on parameters.
# Multiple return values are native.
callable-declare:   local function name(p1, p2) ... end
callable-anon:      function(p1, p2) ... end
callable-call:      name(a1, a2)
callable-method:    obj:method(a1)   -- syntactic sugar: passes obj as first arg
return-value:       return value
return-multi:       return v1, v2    -- multiple returns, no tuple needed
parameter:          p                -- just a name, no type
argument:           value

# ── scope ───────────────────────────────────────────────────────────────────────
# Lua has lexical scope. 'local' creates a new binding in current block.
# Without 'local', assignment goes to the nearest enclosing scope or global.
# No hoisting — local function f() must appear before calls to f().
scope-open:         do
scope-close:        end
scope-rule:         declaration-before-use
hoisting:           none
local-keyword:      local
global-assign:      x = value        -- no 'local' = global or outer scope

# ── loop ────────────────────────────────────────────────────────────────────────
loop-numeric:       for i = start, stop, step do ... end
loop-generic:       for k, v in pairs(t) do ... end
loop-ipairs:        for i, v in ipairs(t) do ... end
loop-while:         while condition do ... end
loop-repeat:        repeat ... until condition
loop-break:         break

# ── conditional ─────────────────────────────────────────────────────────────────
# if is a statement in Lua, not an expression. No ternary operator.
# Only nil and false are falsy — 0 and "" are truthy.
conditional:        if cond then ... end
conditional-else:   if cond then ... else ... end
conditional-elseif: if c1 then ... elseif c2 then ... else ... end
falsy-values:       nil false
truthy-zero:        true             -- 0 is truthy in Lua (unlike C)

# ── string operations ───────────────────────────────────────────────────────────
string-concat:      s1 .. s2
string-length:      #s
string-sub:         string.sub(s, i, j)
string-format:      string.format("%d %s", n, s)
string-find:        string.find(s, pattern)

# ── naming convention ────────────────────────────────────────────────────────────
# setu keys become Lua constants by kebab-to-upper-snake rule (lua-scope.om)
const-naming:       kebab-to-upper-snake
local-naming:       snake-case
function-naming:    snake-case
```

### `ocaml-setu.shabda` — full OCaml syntax for every concept

Sections to add/replace in the existing file:

```
# ── types ──────────────────────────────────────────────────────────────────────
# OCaml has a static type system with inference — types rarely need annotation
# but they exist and are checked at compile time.
int:          0
float:        0.0
bool:         true
string:       ""
unit:         ()                     -- the absence of a value
list:         []                     -- immutable linked list
array:        [||]                   -- mutable fixed-size array
tuple:        (v1, v2)
record:       { field = value }
option:       None  or  Some v       -- OCaml's way of expressing nil/null

# ── variable declaration (let binding) ─────────────────────────────────────────
# 'let' creates an immutable binding. For mutation, use 'ref'.
# OCaml infers types — annotation is optional but possible.
variable-declare:   let x = value
variable-int:       let x = 0
variable-float:     let x = 0.0
variable-bool:      let x = true
variable-string:    let x = ""
variable-typed:     let x : int = 0  -- explicit type annotation
variable-mutable:   let x = ref 0   -- ref cell for mutation
variable-update:    x := new_value  -- mutation through ref
variable-deref:     !x              -- read a ref value

# ── collection literals ─────────────────────────────────────────────────────────
list-literal:       [v1; v2; v3]
list-cons:          v :: rest
list-access:        List.nth lst i   -- O(n)
list-length:        List.length lst
list-map:           List.map f lst
list-filter:        List.filter f lst
list-fold:          List.fold_left f init lst
list-iterate:       List.iter f lst

array-literal:      [| v1; v2; v3 |]
array-access:       a.(i)           -- 0-based index
array-length:       Array.length a
array-set:          a.(i) <- value
array-map:          Array.map f a
array-iterate:      Array.iter f a

map-module:         Hashtbl          -- mutable; Map for immutable
map-create:         Hashtbl.create 16
map-set:            Hashtbl.replace tbl key value
map-get:            Hashtbl.find tbl key
map-has:            Hashtbl.mem tbl key
map-iterate:        Hashtbl.iter (fun k v -> ...) tbl

tuple-literal:      (v1, v2, v3)
tuple-access:       fst t  or  snd t  or  let (a, b, c) = t

record-define:      type t = { field1: int; field2: string }
record-literal:     { field1 = 0; field2 = "" }
record-access:      r.field
record-update:      { r with field = new_value }

# ── callable (function) ─────────────────────────────────────────────────────────
# Functions are values. 'let' binds them. 'fun' creates anonymous functions.
# All functions are curried — multiple params = nested single-param functions.
# The last expression in a function body IS the return value — no 'return'.
callable-declare:   let name p1 p2 = body
callable-typed:     let name (p1: t1) (p2: t2) : ret = body
callable-anon:      fun p1 p2 -> body
callable-call:      name a1 a2
callable-recursive: let rec name p = body  -- must use 'rec' for recursion
return-value:       last-expression        -- no return keyword needed
parameter:          p                      -- just a name
parameter-typed:    (p : type)             -- optional annotation
argument:           value

# ── scope ───────────────────────────────────────────────────────────────────────
# OCaml has lexical scope. Let bindings shadow earlier bindings.
# No mutation by default — use ref for mutable state.
# Modules create named scopes.
scope-open:         let ... in            -- let binding opens a scope
scope-module:       module Name = struct ... end
scope-rule:         declaration-before-use
hoisting:           none
let-keyword:        let
let-in:             let x = v in body

# ── loop ────────────────────────────────────────────────────────────────────────
# OCaml has imperative loops but idiomatic OCaml uses recursion or List functions.
loop-for:           for i = start to stop do ... done
loop-for-down:      for i = start downto stop do ... done
loop-while:         while condition do ... done
loop-recursive:     let rec loop i = if i > n then () else (body; loop (i+1))
loop-list:          List.iter f lst
loop-fold:          List.fold_left f init lst

# ── conditional ─────────────────────────────────────────────────────────────────
# if/then/else is an EXPRESSION in OCaml — it produces a value.
# Both branches must have the same type. 'else ()' if unit.
conditional:        if cond then expr1 else expr2
conditional-unit:   if cond then side_effect ()
pattern-match:      match x with | P1 -> e1 | P2 -> e2
falsy-values:       false            -- only 'false' is false; no nil/null
option-none:        None
option-some:        Some value
option-match:       match opt with | None -> default | Some v -> use v

# ── string operations ───────────────────────────────────────────────────────────
string-concat:      s1 ^ s2
string-length:      String.length s
string-sub:         String.sub s pos len
string-format:      Printf.sprintf "%d %s" n s
string-contains:    String.length (Str.search_forward (Str.regexp p) s 0) > 0

# ── naming convention ────────────────────────────────────────────────────────────
let-naming:         snake-case
module-naming:      pascal-case
type-naming:        snake-case
variant-naming:     pascal-case
const-naming:       upper-snake       -- though OCaml rarely uses all-caps constants
```

---

## Phase 3 — Update existing nodes

### Root kosha nodes

| File | Current state | Change |
|---|---|---|
| `kosha/function.om` | `swa-abheda process-abheda` | add `callable-sthita parameter-yukta return-value-yukta domain-cs-sthita` |
| `kosha/process.om` | `function-call-abheda running-function-abheda` | add `statement-sthita callable-yukta domain-cs-sthita` |
| `kosha/language/string.om` | `matra-sthita varna-abheda domain-language-sthita` | add `cs-string-sthita` — it is both linguistic and CS |

### Lua nodes

| File | Change |
|---|---|
| `lua/lua.om` | add `callable-sthita scope-sthita loop-sthita type-sthita domain-cs-sthita` |
| `lua/lua-scope.om` | add `scope-sthita` — grounds in concepts/scope |
| `lua/return-value.om` | **DELETE** — replaced by `concepts/return-value.om` |

### OCaml nodes

| File | Change |
|---|---|
| `ocaml/loop.om` | add `concepts/loop-sthita` |
| `ocaml/recursion.om` | add `concepts/loop-sthita` — recursion is a loop strategy |
| `ocaml/type-system.om` | add `concepts/type-sthita` |
| `ocaml/state-update.om` | add `concepts/mutation-sthita concepts/assignment-sthita` |
| `ocaml/runtime.om` | add `concepts/statement-sthita` |
| `ocaml/fold.om` | add `concepts/cs-list-sthita` |
| `ocaml/algebraic-data-type.om` | add `concepts/composite-type-sthita` |
| `ocaml/list.om` | **RENAME** to `ocaml-list.om` + add `cs-list-sthita` |
| `ocaml/map.om` | **RENAME** to `ocaml-map.om` + add `cs-map-sthita` |

---

## Phase 4 — Move graph-viz nodes to session

`graph-viz-lua.om` and `graph-viz-setu.om` are application-specific.
They belong in the session alongside all other graph-viz nodes.

| Operation | From | To |
|---|---|---|
| MOVE | `kosha/language/lua/graph-viz-lua.om` | `sessions/graph-viz-dev/graph-viz-lua.om` |
| MOVE | `kosha/language/lua/graph-viz-setu.om` | `sessions/graph-viz-dev/graph-viz-setu.om` |
| STAY | `kosha/language/lua/graph-viz-lua.shabda` | template — path stays valid via kosha_root |
| STAY | `kosha/language/lua/graph-viz-setu.shabda` | template — same |

---

## Phase 5 — What we observe and add after

These cannot be modelled until the concepts/ layer exists and we see what it produces.

**Lua-specific additions on top of concepts/:**
- `lua-table.om` — Lua's single unified type: array + list + map + record in one.
  No direct concepts/ equivalent. Unique to Lua.
- `lua-closure.om` — callable that captures surrounding scope. Lua uses this heavily.
- `lua-nil.om` — first-class value that also means "key absent from table". Distinct from
  concepts/nil which is just "absence of value".
- `lua-metatable.om` — operator overloading / prototype inheritance mechanism.
- `lua-coroutine.om` — cooperative multitasking via yield/resume. No concepts/ equivalent yet.

**OCaml-specific additions on top of concepts/:**
- `ocaml-type-system.om` — static + inferred. Distinct from Lua's dynamic typing.
  After concepts/type.om exists, OCaml's realization needs its own node.
- `ocaml-variant.om` — sum types / tagged unions. These are composite-type but with
  a specific OCaml shape that Lua has no equivalent for.
- `ocaml-ref.om` — OCaml's explicit mutation cell. This is how OCaml realizes
  concepts/mutation while keeping everything else immutable.
- `ocaml-module.om` — first-class namespaced scopes with signatures. No Lua equivalent.

**Cross-language concepts that will become visible:**
- `expression.om` vs `statement.om` diverge sharply: in OCaml everything is an expression
  (if/then/else produces a value, function body IS return value). In Lua, if is a statement,
  return is a keyword. This difference needs to be expressed in each language node once
  concepts/expression and concepts/statement exist.
- `type-inference.om` is currently OCaml-locked. After concepts/type-system exists,
  type inference is generic — Haskell, Rust, TypeScript all have it.
- `closure.om` in concepts/ — a callable that captures its surrounding scope.
  Both Lua and OCaml have closures but so does every modern language.
  Should be in concepts/ once we see the pattern clearly.

---

## Summary of file operations

| Operation | Count | Details |
|---|---|---|
| CREATE `.om` | 23 | all `concepts/*.om` nodes |
| CREATE `.shabda` | 2 | `type.shabda`, `naming-convention.shabda` |
| EXPAND `.shabda` | 2 | `lua-setu.shabda`, `ocaml-setu.shabda` — add full syntax sections |
| UPDATE `.om` | 10 | `function.om`, `process.om`, `language/string.om`, `lua/lua.om`, `lua/lua-scope.om`, `ocaml/loop.om`, `ocaml/recursion.om`, `ocaml/type-system.om`, `ocaml/state-update.om`, `ocaml/runtime.om`, `ocaml/fold.om`, `ocaml/algebraic-data-type.om` |
| RENAME `.om` | 2 | `ocaml/list.om` → `ocaml/ocaml-list.om`, `ocaml/map.om` → `ocaml/ocaml-map.om` |
| MOVE `.om` | 2 | `lua/graph-viz-lua.om` → session, `lua/graph-viz-setu.om` → session |
| DELETE `.om` | 1 | `lua/return-value.om` |
