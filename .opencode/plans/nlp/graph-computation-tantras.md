# Graph-Native Computation Tantras

**Status**: Design complete. No implementation yet.
**Depends on**: graded-morphisms.md (degree: + pratipaksha on operation nodes)
**Part of**: engine-tantra-migration.md step 7

---

## Goal

Replace dense hardcoded tantra dispatch tables with thin graph-walking tantras.
The `.om` nodes carry the routing information. These tantras just walk and apply.

---

## compute-from-node.tantra

Generic dispatch: given a node name and input values, walk the node's `kriya`
edge to find the operation, apply it to values, return the result.

```
tantra compute-from-node
  -- generic graph-native computation dispatcher.
  -- the node declares what operation to use via its kriya edge.
  -- no hardcoded operation names — the graph routes everything.
  inputs
    node    string
    values  list
  let
    kriya-nodes = walk node "kriya"
    op          = first kriya-nodes
    result      = apply-op op values
  return
    result  any
done
```

`apply-op` is a primitive that takes a node name (the kriya target) and dispatches
to the corresponding OCaml primitive or sub-tantra. This is the one place where
the name→implementation mapping lives — not scattered across all tantras.

---

## execute-chain.tantra

Fold composition over a sequence of operation nodes. Used for kinematic chains,
signal processing pipelines, any sequence of transforms.

```
tantra execute-chain
  -- apply a sequence of operations to an initial value by folding composition.
  -- each op-node's kriya edge names the primitive to apply.
  -- grades multiply: if product = 1, chain composes to identity.
  inputs
    op-nodes  list    -- [revolute-joint, revolute-joint, ...]
    values    list    -- [θ₁, θ₂, ...] one per op-node
  let
    paired  = map (range 0 (length op-nodes)) (fn i ->
                pair (nth op-nodes i) (nth values i))
    result  = reduce paired (fn acc p ->
                let op  = first (walk (name p) "kriya")
                let val = value p
                mat-mul acc (apply-op op [val]))
  return
    result  any
done
```

---

## scene-walk.tantra

Backward walk from a known output value through `pratipaksha` edges to infer
inputs. This is the scene understanding / inverse computation path.

```
tantra scene-walk
  -- given a node that produced a known output, walk pratipaksha to find
  -- the inverse operation and apply it to recover the inputs.
  -- this is scene understanding: phala → pratipaksha → janya.
  inputs
    output-node  string
    output-val   any
  let
    inverse-nodes = walk output-node "pratipaksha"
    inverse-op    = first inverse-nodes
    input-nodes   = walk output-node "janya"
    result        = cond (exists inverse-op)
                      (apply-op inverse-op [output-val])
                    otherwise _none
  return
    result  any
done
```

---

## compose-degrees.tantra

Given two operation nodes, multiply their degrees. If product = 1, they compose
to identity (inverses of each other in the ring).

```
tantra compose-degrees
  inputs
    node-a  string
    node-b  string
  let
    deg-a  = to-number (shabda node-a "degree")
    deg-b  = to-number (shabda node-b "degree")
    result = mul deg-a deg-b
  return
    result  float
done
```

---

## is-identity-composition.tantra

```
tantra is-identity-composition
  inputs
    node-a  string
    node-b  string
  let
    composed = compose-degrees node-a node-b
    result   = and (gt composed 0.99) (lt composed 1.01)
  return
    result  bool
done
```

---

## infer-inputs-from-output.tantra

```
tantra infer-inputs-from-output
  -- scene understanding: given a known output, recover the inputs
  -- by walking pratipaksha and applying the inverse operation.
  inputs
    output-node  string
    output-val   any
  let
    inverse = scene-walk output-node output-val
    inputs  = walk output-node "janya"
  return
    inverse  any
done
```

---

## apply-op primitive (OCaml)

`apply-op` needs to be added to `yantra_eval_primitives.ml`. It takes a node
name and a list of values, looks up the corresponding primitive by name, and
calls it. This is the one dispatch table in OCaml — everything else is in the
graph.

```ocaml
| "apply-op" ->
  let op_name = as_string (e_eval k e (List.nth args 0)) in
  let vals    = as_list (e_eval k e (List.nth args 1)) in
  (* try: 1. named tantra, 2. registered primitive, 3. VNone *)
  (match Hashtbl.find_opt ctx.ctx_index.by_name op_name with
   | Some t -> Some (!_eval_tantra_ref k t (List.mapi (fun i v ->
       (List.nth t.t_inputs i).tp_name, v) vals))
   | None   -> (* fall through to primitive dispatch *)
     Some (eval_call k e op_name (List.map (fun v -> Lit (as_float v)) vals)))
```

---

## How these tantras replace current dense tantras

### Before (anuvada-ganana style — dense dispatch)

```
let is-add  = eq node "add"
let is-mul  = eq node "mul"
let is-sub  = eq node "sub"
cond is-add (add (nth values 0) (nth values 1))
     is-mul (mul (nth values 0) (nth values 1))
     is-sub (sub (nth values 0) (nth values 1))
     otherwise _none
```

### After (graph-native)

```
let result = compute-from-node node values
```

The graph does the routing. `add.om` has `addition-kriya`. Walking that edge
gives `addition`. `apply-op` dispatches to the `add` primitive. No cond chains.

---

## Key files

```
brahman/yantra/compute-from-node.tantra        new
brahman/yantra/execute-chain.tantra            new
brahman/yantra/scene-walk.tantra               new
brahman/yantra/compose-degrees.tantra          new
brahman/yantra/is-identity-composition.tantra  new
brahman/yantra/infer-inputs-from-output.tantra new
vyakarana/lib/yantra_eval_primitives.ml        add apply-op primitive
```
