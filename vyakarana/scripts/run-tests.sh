#!/usr/bin/env bash
# run-tests.sh — tantra-native test runner.
# discovers test-*.tantra under brahman/yantra/tests/ and runs each via EVAL.
# each test tantra returns bool; true = pass, false/other = fail.
#
# usage:
#   ./run-tests.sh                    run all suites
#   ./run-tests.sh avrti              run only the avrti suite
#   ./run-tests.sh lookup bqg         run lookup and bqg suites
#   ./run-tests.sh match              run the match suite
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TESTS_DIR="$ROOT_DIR/../brahman/yantra/tests"
PASS=0
FAIL=0
FAILURES=()

run_tantra_test() {
  local name="$1"
  local raw
  raw="$(printf "EVAL %s\nVISARJANA\n" "$name" \
       | dune exec ./bin/vyakarana.exe -- --quiet-startup 2>&1)"

  if echo "$raw" | grep -q "^true$"; then
    printf "[PASS] %s\n" "$name"
    PASS=$((PASS + 1))
  else
    local got
    got="$(echo "$raw" | grep -vE "^(  |csr:|relation|released|^$)" | head -1)"
    printf "[FAIL] %s\n" "$name"
    printf "       got: %s\n" "${got:-<empty>}"
    FAIL=$((FAIL + 1))
    FAILURES+=("$name")
  fi
}

# build find command based on suite args
find_tests() {
  if [ $# -eq 0 ]; then
    find "$TESTS_DIR" -name "test-*.tantra" 2>/dev/null | sort
  else
    for suite in "$@"; do
      find "$TESTS_DIR/$suite" -name "test-*.tantra" 2>/dev/null | sort
    done
  fi
}

cd "$ROOT_DIR"

echo "Building..."
dune build 2>&1

SUITES=("${@}")
if [ ${#SUITES[@]} -eq 0 ]; then
  echo ""
  echo "Running all tests..."
else
  echo ""
  echo "Running suites: ${SUITES[*]}"
fi
echo ""

while IFS= read -r f; do
  name="$(basename "$f" .tantra)"
  run_tantra_test "$name"
done < <(find_tests "${SUITES[@]}")

echo ""
echo "Results: ${PASS} passed, ${FAIL} failed."
if [ "${FAIL}" -gt 0 ]; then
  echo "Failed:"
  for f in "${FAILURES[@]-}"; do
    printf "  - %s\n" "$f"
  done
  exit 1
else
  echo "All tests passed."
fi
