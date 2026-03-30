#!/usr/bin/env python3
"""find_false_positives.py — identify weak/suspicious passing tests.

Loads cache files (actual inputs/outputs per test), then parses the
test source to extract assertion strings. For each passing test it flags:

1. WRONG_ANSWER    — assert "X" in r, but r contains a known failure signal
                     (e.g. "no match" when expecting a number, "yes" when
                      "no" is expected, "no" when "yes" is expected)
2. TRIVIAL         — assert len(r) > 0, or assert True/always-true form
3. DISJUNCTION_OR  — assert uses `or` with a very broad fallback
4. SUBSTRING_SNEAK — asserted substring appears in the response but only
                     as part of a *different* word (e.g. "no" inside "know")
5. INCIDENTAL      — numeric assertion matches but only in an intermediate
                     derivation step, not as the stated answer

Usage:
    python3 upakarana/tests/find_false_positives.py [--verbose]
"""

import ast
import re
import sys
from pathlib import Path

TEST_DIR = Path(__file__).parent

# ─────────────────────────────────────────────────────────────
# Load entries (passed tests only) from LMDB store
# ─────────────────────────────────────────────────────────────

def load_cache():
    from upakarana.testing.store import load_run_entries_with_traces
    entries = {}
    for e in load_run_entries_with_traces():
        if e.get("outcome") == "passed":
            test_id = e["test"]
            outputs = [
                c["output"]
                for c in e.get("calls", [])
                if c.get("method") in ("answer", "ask") and c.get("output")
            ]
            entries[test_id] = {"entry": e, "outputs": outputs}
    return entries


# ─────────────────────────────────────────────────────────────
# Parse test source — extract per-test assertion lines
# ─────────────────────────────────────────────────────────────

def extract_test_assertions(test_file: Path) -> dict:
    """Returns {test_name: [assertion_source_lines]}."""
    src = test_file.read_text()
    tree = ast.parse(src)
    results = {}

    # collect all top-level and class method functions
    def collect_funcs(node, prefix=""):
        funcs = []
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef) and child.name.startswith("test_"):
                funcs.append((prefix + child.name, child))
            elif isinstance(child, ast.ClassDef):
                funcs.extend(collect_funcs(child, child.name + "::"))
        return funcs

    for name, func in collect_funcs(tree):
        lines = []
        for node in ast.walk(func):
            if isinstance(node, ast.Assert):
                lines.append(ast.unparse(node.test))
        results[name] = lines
    return results


# ─────────────────────────────────────────────────────────────
# Heuristic checks
# ─────────────────────────────────────────────────────────────

# Words that indicate IS-A wrong reasoning pattern
WRONG_REASONING_SIGNALS = [
    "animal has animal",
    "animal has mammal",
    "mammal has animal",
    "sparrow has bird",
    "copper has metal",
    "ground has negation",
    "IS-A negation",
    "does not have bird",
    "does not have verb-have",
    # viveka comparing entity to itself
    r"(\w+-\w+) is (?:viveka max|more|heavier|lighter) than \1",
]

WRONG_REASONING_REGEX = [
    # viveka comparing entity to itself: "ball-B is viveka max than ball-B"
    (re.compile(r'(\w[\w-]+) is (?:viveka max|the viveka max|more|heavier|lighter) than \1', re.I),
     "viveka self-comparison: entity compared to itself"),
]

def check_wrong_reasoning(output: str) -> list[str]:
    issues = []
    ol = output.lower()
    for sig in WRONG_REASONING_SIGNALS:
        if isinstance(sig, str) and sig.lower() in ol:
            issues.append(f"wrong-reasoning: contains '{sig}'")
    for pat, label in WRONG_REASONING_REGEX:
        if pat.search(output):
            issues.append(f"wrong-reasoning: {label}")
    return issues


def _quoted(s: str) -> str:
    """Return regex that matches s as a single- or double-quoted Python string literal."""
    return r"""(?:['"]""" + re.escape(s) + r"""['"])"""


def check_no_in_know(output: str, assertion: str) -> list[str]:
    """'no' in r.lower() passes because 'know' contains 'no'."""
    issues = []
    if re.search(_quoted("no"), assertion):
        if re.search(r'\bno\b', output.lower()) is None:
            if 'no' in output.lower():
                issues.append("substring-sneak: 'no' only inside another word (e.g. 'know', 'not', 'node')")
    return issues


def check_trivial(assertion: str) -> list[str]:
    issues = []
    trivials = [
        r"len\s*\(\s*\w+\s*\)\s*>\s*0",
        r"\bTrue\b",
        r"assert\s+\w+$",          # bare variable
    ]
    for t in trivials:
        if re.search(t, assertion):
            issues.append(f"trivial: '{assertion}'")
    return issues


def check_disjunction(assertion: str) -> list[str]:
    """Flag assertions with 'or' where the fallback is very broad."""
    issues = []
    if " or " in assertion:
        # flag if any branch is like: "X" in r.lower() where X is a common word
        broad_fallback_patterns = [
            r'"we\s+\w+"',           # "we find", "we seek" etc.
            r'"force"',
            r'"no\s*match"',
            r'len\s*\(',
            r'\bTrue\b',
        ]
        for bp in broad_fallback_patterns:
            if re.search(bp, assertion):
                issues.append(f"disjunction-or: broad fallback in '{assertion}'")
                break
    return issues


def check_number_incidental(output: str, assertion: str) -> list[str]:
    """Numeric assertion passes because number is in derivation chain, not as answer."""
    issues = []
    # extract quoted numbers from assertion (single or double quoted)
    nums = re.findall(r"""['"](\d+(?:\.\d+)?)['"]""", assertion)
    if not nums:
        return issues
    # check if the output's stated answer line contains the number
    # "We find that X is N" or "we find N" is the answer line
    answer_line = ""
    for m in re.finditer(r'(?:we find|we find that)[^\n.]*', output, re.IGNORECASE):
        answer_line += " " + m.group(0)
    if not answer_line:
        return issues
    for num in nums:
        if num not in answer_line:
            # number is in output but NOT in the answer line — check if it's elsewhere
            if re.search(r'\b' + re.escape(num) + r'\b', output):
                issues.append(
                    f"incidental: '{num}' present in derivation but not in answer line '{answer_line.strip()[:80]}'"
                )
    return issues


def check_wrong_yes_no(output: str, assertion: str) -> list[str]:
    """Response says yes but assertion expects no, or vice versa."""
    issues = []
    ol = output.lower()
    expects_yes = bool(re.search(_quoted("yes"), assertion))
    expects_no  = bool(re.search(_quoted("no"),  assertion))

    # look at the final "yes/no" in the response
    # the conclusive sentence is usually the last one starting with yes/no
    final_verdict = None
    for m in re.finditer(r'\b(yes|no)\b', ol):
        final_verdict = m.group(1)

    if expects_no and final_verdict == "yes":
        issues.append(f"wrong-answer: assertion expects 'no' but response ends with 'yes — ...'")
    if expects_yes and final_verdict == "no":
        issues.append(f"wrong-answer: assertion expects 'yes' but response ends with 'no — ...'")
    return issues


def check_entity_as_loser(output: str, assertion: str) -> list[str]:
    """Entity name in assertion appears in output only as the *losing* comparison side."""
    issues = []
    # look for patterns like: assert "box-A" in r when output says "X is more than box-A"
    names = re.findall(r"""['"]([a-zA-Z][a-zA-Z0-9-]+)['"]""", assertion)
    for name in names:
        # check if name appears after "than" in the output (= loser side)
        if re.search(r'\bthan\s+' + re.escape(name) + r'\b', output, re.I):
            # and the name doesn't also appear as the winner
            if not re.search(r'\b' + re.escape(name) + r'\s+is\b', output, re.I):
                issues.append(f"entity-as-loser: '{name}' appears in output only as the loser")
    return issues


def check_rest_in_header(output: str, assertion: str) -> list[str]:
    """'rest' passes because 'at-rest' appears in a header line, not as the answer."""
    issues = []
    if re.search(_quoted("rest"), assertion):
        ol = output.lower()
        if "at-rest" in ol and re.search(r'\brest\b', ol) is None:
            issues.append("substring-sneak: 'rest' only in 'at-rest' compound")
    return issues


# ─────────────────────────────────────────────────────────────
# Main analysis
# ─────────────────────────────────────────────────────────────

def analyze(verbose=False):
    cache = load_cache()
    # map short test name → full test_id
    name_to_id = {}
    for test_id in cache:
        parts = test_id.split("::")
        short = parts[-1]
        name_to_id.setdefault(short, []).append(test_id)

    all_issues = []

    for test_file in sorted(TEST_DIR.glob("test_*.py")):
        assertions = extract_test_assertions(test_file)
        for func_name, assert_lines in assertions.items():
            # match to cache — try exact name, then by class::name
            candidates = name_to_id.get(func_name.split("::")[-1], [])
            matched = None
            for c in candidates:
                # prefer match from same file
                if test_file.stem in c:
                    matched = c
                    break
            if matched is None and candidates:
                matched = candidates[0]
            if matched is None or matched not in cache:
                continue

            entry_data = cache[matched]
            outputs = entry_data["outputs"]
            if not outputs:
                continue
            output = outputs[-1] if outputs else ""
            if not isinstance(output, str):
                output = str(output)

            issues = []
            for aline in assert_lines:
                issues += check_trivial(aline)
                issues += check_disjunction(aline)
                issues += check_no_in_know(output, aline)
                issues += check_wrong_yes_no(output, aline)
                issues += check_rest_in_header(output, aline)
                issues += check_number_incidental(output, aline)
                issues += check_entity_as_loser(output, aline)
            issues += check_wrong_reasoning(output)

            if issues:
                all_issues.append({
                    "test": matched,
                    "output_preview": output[:120].replace("\n", " "),
                    "assertions": assert_lines,
                    "issues": issues,
                })

    # print report
    print(f"\n{'='*70}")
    print(f"  FALSE POSITIVE CANDIDATES  ({len(all_issues)} tests)")
    print(f"{'='*70}\n")

    by_issue_type = {}
    for item in all_issues:
        for iss in item["issues"]:
            kind = iss.split(":")[0]
            by_issue_type.setdefault(kind, []).append(item)

    for kind, items in sorted(by_issue_type.items()):
        print(f"\n── {kind.upper()} ({len(items)}) {'─'*50}")
        seen = set()
        for item in items:
            tid = item["test"]
            if tid in seen:
                continue
            seen.add(tid)
            # find issues of this kind
            relevant = [i for i in item["issues"] if i.startswith(kind)]
            for iss in relevant:
                print(f"  {tid}")
                print(f"    issue    : {iss}")
                if verbose:
                    print(f"    assertion: {' | '.join(item['assertions'])}")
                    print(f"    output   : {item['output_preview']}")
                print()

    print(f"\nTotal suspicious tests: {len(all_issues)}")
    return all_issues


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    analyze(verbose=verbose)
