# Tantra-Native Testing Plan

**Status**: Design complete. Not yet implemented.
**Goal**: Tests ARE tantras — same language, same graph access, no separate harness.

---

## Core Idea

Each test is a `.tantra` file that returns `bool`. The regression runner executes
it and checks the result is `true`. Tests live in `brahman/yantra/tests/`.

```
tantra test-compose-degrees-identity
  let
    result   = compose-degrees "square" "square-root"
    ok       = lt (abs (sub result expected)) 0.001
  return
    ok  bool
done
```

The regression script calls: `vyakarana EVAL test-compose-degrees-identity brahman/`
and checks output is `true`.

Tests are self-describing — the tantra name IS the test name. No test framework needed.

---

## Test Categories

### 1. Primitive / unit tests

Test individual OCaml primitives and single tantras in isolation.
Fast. No graph required (or minimal graph).

```
brahman/yantra/tests/primitives/
  test-add.tantra             -- add 2 3 = 5.0
  test-mul.tantra             -- mul 4 0.5 = 2.0
  test-sqrt.tantra            -- abs (sub (sqrt 9) 3) < 0.001
  test-concat.tantra          -- concat "hello" " " "world" = "hello world"
  test-split.tantra           -- length (split "a b c" " ") = 3
  test-nth.tantra             -- nth ["x" "y" "z"] 1 = "y"
  test-map.tantra             -- map [1 2 3] (fn x -> mul x 2) = [2 4 6]
  test-filter.tantra          -- filter [1 2 3 4] (fn x -> gt x 2) = [3 4]
  test-reduce.tantra          -- reduce [1 2 3 4] 0 (fn a x -> add a x) = 10
  test-range.tantra           -- length (range 0 5 1) = 5
  test-flatten.tantra         -- flatten [[1 2] [3 4]] = [1 2 3 4]
  test-first-match.tantra     -- first-match [1 2 3] (fn x -> cond (gt x 1) x otherwise _none) = 2
```

### 2. Math operation tests

Test that math operation nodes have correct shabda fields and compute correctly
when invoked via apply-op or execute-chain.

```
brahman/yantra/tests/math/
  test-op-word-keys.tantra        -- all core ops have word: in shabda
  test-compose-degrees-identity.tantra  -- square∘sqrt = 1.0
  test-compose-degrees-power.tantra     -- square∘square = 4.0 (not identity)
  test-is-identity-square-sqrt.tantra   -- is-identity-composition square square-root = true
  test-is-identity-deriv-antideriv.tantra -- derivative∘antiderivative = true
  test-degree-addition.tantra           -- shabda addition "degree" = "1"
  test-degree-square.tantra             -- to-number (shabda square "degree") = 2.0
  test-pratipaksha-square.tantra        -- walk "square" "pratipaksha" contains "square-root"
  test-pratipaksha-derivative.tantra    -- walk "derivative" "pratipaksha" contains "antiderivative"
```

### 3. Grammar composition tests

Test that grammar nodes have correct copula:, word: keys and that compose-response
builds correct sentence structure.

```
brahman/yantra/tests/grammar/
  test-vartamana-copula.tantra    -- shabda "vartamana-kaala" "copula" = "is"
  test-bhuta-copula.tantra        -- shabda "bhuta-kaala" "copula" = "was"
  test-article-the-word.tantra    -- shabda "article-the" "word" = "the"
  test-conj-and-word.tantra       -- shabda "conj-and" "word" = "and"
  test-prep-of-word.tantra        -- shabda "prep-of" "word" = "of"
  test-copula-equals-word.tantra  -- shabda "copula-equals" "word" = "equals"
```

### 4. Graph walk tests

Test that graph primitives return correct results on known nodes.

```
brahman/yantra/tests/graph/
  test-walk-pratipaksha.tantra    -- walk "addition" "pratipaksha" = ["subtraction"]
  test-walk-krama.tantra          -- length (walk "kinetic-energy-mantra" "krama") = 3
  test-ancestors-of.tantra        -- member "number-varga" (ancestors-of "square")
  test-has-domain-math.tantra     -- has-domain "square" "domain-math" = true
  test-domain-of-square.tantra    -- domain-of "square" starts with "domain-math" or "math"
  test-shabda-name.tantra         -- shabda "kinetic-energy-mantra" "name" = "kinetic-energy"
  test-shabda-krama-lhs.tantra    -- shabda "kinetic-energy-mantra" "krama-lhs" = "energy"
  test-shabda-krama-rhs.tantra    -- split (shabda "kinetic-energy-mantra" "krama-rhs") "," = ["mass" "velocity"]
```

### 5. Mantra execute-chain tests

Test that execute-chain on known mantra nodes produces correct numeric results.
These are the physics formula computation tests.

```
brahman/yantra/tests/mantra/
  test-chain-kinetic-energy.tantra    -- ½mv²: m=10, v=3 → 45.0 J
  test-chain-velocity.tantra          -- v=u+at: u=0, a=5, t=4 → 20.0 m/s
  test-chain-momentum.tantra          -- p=mv: m=2, v=5 → 10.0 kg·m/s
  test-chain-friction.tantra          -- f=μN: μ=0.3, N=100 → 30.0 N
  test-chain-potential-energy.tantra  -- PE=mgh: m=5, g=9.8, h=10 → 490.0 J
  test-chain-work.tantra              -- W=Fd·cosθ: F=100, d=5, θ=0 → 500.0 J
  test-chain-ohm.tantra               -- V=IR: I=2, R=5 → 10.0 V
```

### 6. Composition pipeline tests (P8 — after tantras written)

Test the full decompose→match→execute→compose pipeline end to end.

```
brahman/yantra/tests/pipeline/
  test-decompose-what-question.tantra   -- "what" token → intent = "solve-for"
  test-decompose-value-unit.tantra      -- "5kg" → {quantity: mass, value: 5, unit: kg}
  test-match-formula-direct.tantra      -- target=energy, bindings=[mass,velocity] → kinetic-energy-mantra
  test-match-formula-inverse.tantra     -- target=mass, bindings=[energy,velocity] → pratipaksha path
  test-compose-response-present.tantra  -- formula+result+vartamana → "kinetic energy is 45 J"
  test-pipeline-kinetic-energy.tantra   -- full: "what is KE of 10kg at 3m/s?" → "kinetic energy is 45 J"
  test-pipeline-velocity.tantra         -- full: "find velocity given u=0, a=5, t=4" → "velocity is 20 m/s"
```

### 7. Multi-step inference tests (P8 chain-implication)

Test that the logic layer chains formulas correctly.

```
brahman/yantra/tests/inference/
  test-chain-f-m-to-a.tantra          -- F=10N, m=2kg → a=5 m/s² (via newton 2nd law inverse)
  test-chain-f-m-t-to-v.tantra        -- F=10, m=2, t=5, u=0 → v=25 m/s (2-step chain)
  test-inverse-ke-mass.tantra         -- KE=100J, v=5m/s → m=8 kg (pratipaksha direction)
  test-janya-kinetic-energy.tantra    -- janya of kinetic-energy-mantra = [mass, velocity]
```

### 8. Logic / math proof tests

Test that math/logic kosha nodes (theorem, proof, implication) have correct
structure and are walkable.

```
brahman/yantra/tests/logic/
  test-implication-node-exists.tantra   -- lookup "implication" returns a node
  test-theorem-node-exists.tantra       -- lookup "theorem" returns a node
  test-proof-node-exists.tantra         -- lookup "proof" returns a node
  test-logic-varga-ancestors.tantra     -- member "logic-varga" (ancestors-of "implication")
```

### 9. Bhasha / language tests

Test that bhasha nodes load correctly and have proper surface forms.

```
brahman/yantra/tests/bhasha/
  test-bhasha-matra-loads.tantra       -- lookup "matra" returns node (bhasha layer)
  test-bhasha-vartamana-loads.tantra   -- lookup "vartamana-kaala" returns node
  test-bhasha-layer-weight.tantra      -- node-satya "vartamana-kaala" < 1.0 (bhasha = 0.5 weight)
```

---

## Test Runner Integration

### New script: `vyakarana/scripts/run-tantra-tests.sh`

```bash
#!/bin/bash
PASS=0; FAIL=0
for f in brahman/yantra/tests/**/*.tantra; do
  name=$(basename "$f" .tantra)
  result=$(./vyakarana EVAL "$name" brahman/)
  if [ "$result" = "true" ]; then
    echo "[PASS] $name"; ((PASS++))
  else
    echo "[FAIL] $name (got: $result)"; ((FAIL++))
  fi
done
echo "Results: $PASS passed, $FAIL failed"
```

### Integration with existing regression

The existing `run-regression.sh` runs `.test` files (shell expected-output tests).
Tantra tests complement this — they test the semantic/graph layer, not just output format.

Both suites run together. Combined target: all tantra tests pass + 49/52 shell tests.

---

## Implementation order

```
Phase 1 (now):   primitives/ + math/ + grammar/ + graph/ tests — all use existing primitives
Phase 2 (P8):    mantra/ tests — need execute-chain working (already exists per memory)
Phase 3 (P8):    pipeline/ tests — need decompose-question + match-formula + compose-response
Phase 4 (P8):    inference/ tests — need chain-implication tantra
Phase 5 (P8):    logic/ + bhasha/ tests — straightforward graph lookups
```

---

## Key design rules

1. Every test tantra returns exactly `bool` — true = pass, false = fail
2. Test name IS the description — `test-compose-degrees-identity` explains itself
3. Tests use graph access freely — they ARE graph queries
4. No mocking — tests run against the real loaded graph (brahman/)
5. A failing test must have a clear fix path — no "expected failure" tests
6. Regression gate: adding tests must not break 49/52 shell tests
