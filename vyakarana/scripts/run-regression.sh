#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

PASS=0
FAIL=0
FAILURES=()

run_case() {
  local name="$1"
  local expected="$2"
  local input="$3"

  local output
  output="$(printf "%b" "${input}\nVISARJANA\n" | dune exec ./bin/vyakarana.exe -- --quiet-startup 2>&1)" || true

  if [[ "$output" == *"$expected"* ]]; then
    echo "[PASS] $name"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $name"
    echo "  expected: $expected"
    echo "  got:"
    while IFS= read -r line; do
      printf '    %s\n' "$line"
    done <<< "$output"
    FAIL=$((FAIL + 1))
    FAILURES+=("$name")
  fi
}

cd "$ROOT_DIR"

echo "Running regression checks..."

# ---- tantra resolution ----
run_case "direct-force"             "force is 20 newton."                                             "force when mass is 10 and acceleration is 2"
run_case "inverse-mass"             "mass is 10 kilogram."                                            "mass when force is 20 and acceleration is 2"
run_case "direct-kinetic-energy"    "kinetic-energy is 180 joule."                                   "kinetic-energy when mass is 10 and velocity is 6"
run_case "chain-kinetic-energy"     "computed by final-velocity and kinetic-energy."                  "kinetic-energy when mass is 10 and initial-velocity is 0 and acceleration is 2 and time is 3"
run_case "store-then-compute"       "force is 36 newton."                                             "mass is 12\nforce when acceleration is 3"
run_case "session-recompute"        "computed by final-velocity and kinetic-energy."                  "kinetic-energy when mass is 10 and velocity is 6\nkinetic-energy when mass is 10 and initial-velocity is 0 and acceleration is 2 and time is 3"
run_case "missing-input-error"      "cannot compute tantra 'force' exists but missing inputs: acceleration." "force when mass is 10"
run_case "reasoning-fallback"       "asprista"                                                        "what is machine"

# ---- basic EVAL ----
run_case "eval-direct"              $'5\nreleased (visarjana).'                                       "EVAL add 2 3"

# ---- monoid / variadic ops ----
run_case "eval-concat-two"          "helloworld"                                                      'EVAL concat "hello" "world"'
run_case "eval-concat-three"        "abc"                                                             'EVAL concat "a" "b" "c"'
run_case "eval-and-true"            "true"                                                            "EVAL and true true"
run_case "eval-and-false"           "false"                                                           "EVAL and true false"
run_case "eval-or-true"             "true"                                                            "EVAL or false true"
run_case "eval-or-false"            "false"                                                           "EVAL or false false"

# ---- projection ops (1-arg) ----
run_case "eval-upper"               "HELLO"                                                           'EVAL upper "hello"'
run_case "eval-lower"               "hello"                                                           'EVAL lower "HELLO"'
run_case "eval-string-length"       "5"                                                               'EVAL string-length "hello"'
run_case "eval-sqrt"                "3"                                                               "EVAL sqrt 9"
run_case "eval-abs"                 "4"                                                               "EVAL abs (neg 4)"
run_case "eval-not-false"           "true"                                                            "EVAL not false"
run_case "eval-floor"               "3"                                                               "EVAL floor 3.9"
run_case "eval-ceil"                "4"                                                               "EVAL ceil 3.1"

# ---- numeric binary ops (fixed arity 2, locked before Phase-5 cutover) ----
run_case "eval-sub"                 "5"                                                               "EVAL sub 8 3"
run_case "eval-mul"                 "12"                                                              "EVAL mul 3 4"
run_case "eval-div"                 "2.5"                                                             "EVAL div 5 2"
run_case "eval-power"               "8"                                                               "EVAL power 2 3"
run_case "eval-mod"                 "1"                                                               "EVAL mod 7 3"
run_case "eval-min"                 "3"                                                               "EVAL min 3 9"
run_case "eval-max"                 "9"                                                               "EVAL max 3 9"

# ---- relation ops ----
run_case "eval-eq-true"             "true"                                                            'EVAL eq "a" "a"'
run_case "eval-eq-false"            "false"                                                           'EVAL eq "a" "b"'
run_case "eval-neq-true"            "true"                                                            'EVAL neq "a" "b"'
run_case "eval-lt-true"             "true"                                                            "EVAL lt 3 5"
run_case "eval-lt-false"            "false"                                                           "EVAL lt 5 3"
run_case "eval-gt-true"             "true"                                                            "EVAL gt 5 3"
run_case "eval-le-true"             "true"                                                            "EVAL le 3 3"
run_case "eval-ge-true"             "true"                                                            "EVAL ge 5 3"

# ---- keyed ops ----
run_case "eval-nth-0"               "hello"                                                           'EVAL nth ["hello","world"] 0'
run_case "eval-nth-1"               "world"                                                           'EVAL nth ["hello","world"] 1'
run_case "eval-char-at"             "e"                                                               'EVAL char-at "hello" 1'
run_case "eval-split-join"          "a,b,c"                                                           'EVAL join (split "a,b,c" ",") ","'

# ---- list ops ----
run_case "eval-length"              "3"                                                               'EVAL length ["a","b","c"]'
run_case "eval-append"              "3"                                                               'EVAL length (append ["a"] ["b","c"])'
run_case "eval-flatten"             "3"                                                               'EVAL length (flatten [["a"],["b","c"]])'

# ---- higher-order ops ----
run_case "eval-map-double"          "6"                                                               "EVAL nth (map [1,2,3] (fn x -> mul x 2)) 2"
run_case "eval-filter-gt2"          "2"                                                               "EVAL length (filter [1,2,3,4] (fn x -> gt x 2))"
run_case "eval-first-match"         "3"                                                               "EVAL first-match [1,2,3,4] (fn x -> cond (gt x 2) x otherwise _none)"

# ---- satya-sensitive graph structure tests (Phase 3 safety net) ----
# These verify graph structure that PPR-based scoring (Phase 5+6) must not break.

# context-score: addition shares edges with both domain-math and equation
run_case "graph-context-score"      "4"                                                               'EVAL context-score "addition" ["domain-math","equation"]'

# abheda-of: plus node has abheda to addition (and others) — addition must be in the list
run_case "graph-abheda-plus"        "addition"                                                        'EVAL abheda-of "plus"'

# domain-of: new monoid node (Phase 1b) must resolve its domain to domain-math
run_case "graph-monoid-domain"      "domain-math"                                                     'EVAL domain-of "monoid"'

# abheda bridge: monoid.om encodes op-class-monoid-abheda — arity system bridge must hold
run_case "graph-monoid-op-class"    "op-class-monoid"                                                 'EVAL abheda-of "monoid"'

echo ""
echo "Results: ${PASS} passed, ${FAIL} failed."
if [ ${FAIL} -gt 0 ]; then
  echo "Failed tests:"
  for f in "${FAILURES[@]}"; do
    echo "  - $f"
  done
  exit 1
else
  echo "All regression checks passed."
fi
