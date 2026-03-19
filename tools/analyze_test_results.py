#!/usr/bin/env python3
"""
analyze_test_results.py — read the pytest cache and emit a structured report.

Reads .pytest_cache/vyakarana/*.json written by conftest.py after each test run.
Cross-references failing sentences against the tantra analysis to explain WHY
each test failed at the graph/mantra level.

Usage:
    python3 tools/analyze_test_results.py
    python3 tools/analyze_test_results.py --json | jq '.failed_tests'
    python3 tools/analyze_test_results.py --cache /path/to/.pytest_cache/vyakarana
    python3 tools/analyze_test_results.py --diff previous_summary.json

Reads from:
    vyakarana/tests/.pytest_cache/vyakarana/summary.json
    vyakarana/tests/.pytest_cache/vyakarana/<test>.json

Cross-references with (if available):
    /tmp/analysis.json     (tantra analysis)
    /tmp/sa_clean.json     (shabda analysis)
"""

import json, sys, os, re, argparse, subprocess, shlex
from pathlib import Path
from collections import Counter, defaultdict

REPO_ROOT = Path(__file__).parent.parent
CACHE_DEFAULT = REPO_ROOT / "vyakarana" / ".pytest_cache" / "vyakarana"
PYTEST_ROOT = REPO_ROOT / "vyakarana"
SOCKET_PATH = "/tmp/vy.sock"


# ── load cache ────────────────────────────────────────────────────────────────


def load_cache(cache_dir: Path) -> tuple[dict, list[dict]]:
    """Returns (summary, [test_entries]).

    Each entry has:
      test      — nodeid string
      outcome   — passed|failed|error|xfailed|xpassed|skipped|unknown
      calls     — [{method, input, output, elapsed_ms, error}]
      failure   — {expected, got, message, last_call} or None
      duration  — float seconds
    """
    summary_path = cache_dir / "summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    entries = []
    for f in sorted(cache_dir.glob("*.json")):
        if f.name == "summary.json":
            continue
        try:
            entries.append(json.loads(f.read_text()))
        except Exception:
            pass
    return summary, entries


def entries_by_outcome(entries: list[dict]) -> dict[str, list[dict]]:
    """Group entries by outcome."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        groups[e.get("outcome", "unknown")].append(e)
    return dict(groups)


def extract_tantra_calls(calls: list[dict]) -> list[str]:
    """Extract all tantra names referenced in eval inputs."""
    tantras = []
    for c in calls:
        inp = c.get("input", "")
        # tantra calls appear as bare words at start of eval expr
        m = re.match(r"^([a-z][a-z0-9-]+)\s", inp)
        if m:
            tantras.append(m.group(1))
    return tantras


def extract_eval_chain(calls: list[dict]) -> list[dict]:
    """Return the full eval chain with timing and result summary."""
    chain = []
    for c in calls:
        out = c.get("output")
        out_summary = ""
        if isinstance(out, str):
            out_summary = out[:80]
        elif isinstance(out, list):
            out_summary = f"[{len(out)} triples]"
        elif out is not None:
            out_summary = str(out)[:60]
        chain.append(
            {
                "method": c.get("method", "?"),
                "input": c.get("input", "")[:100],
                "output": out_summary,
                "elapsed_ms": c.get("elapsed_ms", 0),
                "error": c.get("error"),
            }
        )
    return chain


def slowest_calls(entries: list[dict], top_n: int = 20) -> list[dict]:
    """Find the individual slowest eval calls across all tests."""
    all_calls = []
    for e in entries:
        for c in e.get("calls", []):
            ms = c.get("elapsed_ms", 0)
            if ms and ms > 50:
                all_calls.append(
                    {
                        "test": e["test"],
                        "input": c.get("input", "")[:80],
                        "ms": ms,
                        "method": c.get("method", "?"),
                    }
                )
    return sorted(all_calls, key=lambda x: x["ms"], reverse=True)[:top_n]


def xfail_reason_groups(entries: list[dict]) -> dict[str, list[str]]:
    """
    Group xfailed tests by their stored gate field (from conftest xfail marker).
    Falls back to file-based grouping for tests without a stored gate.
    """
    groups: dict[str, list[str]] = defaultdict(list)
    for e in entries:
        if e.get("outcome") not in ("skipped", "xfailed"):
            continue
        # prefer stored gate from conftest xfail capture
        gate = (e.get("xfail") or {}).get("gate", "")
        if not gate:
            # fall back to file-based group
            file_part = e["test"].split("::")[0].split("/")[-1].replace(".py", "")
            gate = f"other:{file_part}"
        groups[gate].append(e["test"])
    return dict(groups)


def xfailed_node_ids_for_gate(entries: list[dict], gate: str) -> list[str]:
    """Return pytest node IDs for xfailed tests whose gate contains the given string."""
    result = []
    for e in entries:
        if e.get("outcome") not in ("skipped", "xfailed"):
            continue
        stored_gate = (e.get("xfail") or {}).get("gate", "")
        file_part = e["test"].split("::")[0].split("/")[-1].replace(".py", "")
        match_gate = stored_gate or f"other:{file_part}"
        if gate.lower() in match_gate.lower():
            result.append(e["test"])
    return result


# ── sentence extraction ────────────────────────────────────────────────────────


def extract_sentences(calls: list[dict]) -> list[str]:
    """Pull the actual sentences sent to anuvada-ganana or vy.ask from calls."""
    sentences = []
    for c in calls:
        inp = c.get("input", "")
        method = c.get("method", "")
        if method == "ask":
            sentences.append(inp)
        elif method == "eval" and inp.startswith('anuvada-ganana "'):
            # strip anuvada-ganana "..." wrapper
            m = re.match(r'anuvada-ganana "(.+)"$', inp)
            if m:
                sentences.append(m.group(1))
    return sentences


def extract_answers(calls: list[dict]) -> list[tuple[str, str]]:
    """Returns [(sentence, answer)] pairs."""
    pairs = []
    for c in calls:
        inp = c.get("input", "")
        out = c.get("output", "")
        method = c.get("method", "")
        if method == "ask":
            pairs.append((inp, str(out) if out else ""))
        elif method == "eval" and inp.startswith('anuvada-ganana "'):
            m = re.match(r'anuvada-ganana "(.+)"$', inp)
            if m:
                pairs.append((m.group(1), str(out) if out else ""))
    return pairs


# ── cross-reference with tantra analysis ────────────────────────────────────


def load_tantra_analysis() -> dict:
    p = Path("/tmp/analysis.json")
    if p.exists():
        try:
            return json.loads(p.read_text())
        except:
            pass
    return {}


def categorize_failure(entry: dict, analysis: dict) -> dict:
    """
    Given a failed test entry, determine the likely root cause
    by cross-referencing calls with tantra patterns.
    """
    calls = entry.get("calls", [])
    failure = entry.get("failure") or {}
    answers = extract_answers(calls)
    sentences = extract_sentences(calls)

    categories = []

    for sentence, answer in answers:
        ans_lower = answer.lower()

        # no-intent: has no vidhi-kaala but got an answer
        if (
            "no match" in failure.get("expected", "").lower()
            and answer
            and "no match" not in ans_lower
        ):
            categories.append("has-intent-guard-missing")

        # scope: wrong entity values used
        if "ball-a" in sentence.lower() or "ball-b" in sentence.lower():
            if answer and "no match" not in ans_lower:
                categories.append("scope-entity")

        # relative-velocity firing incorrectly
        if "relative-velocity" in answer:
            categories.append("relative-velocity-spurious")

        # chain contamination: derive-chain intermediate values in answer
        if (
            "we know: relative-velocity-mantra" in answer
            and "relative-velocity" not in sentence.lower()
        ):
            categories.append("derive-chain-contamination")

        # xfail explanation: read the xfail reason
        xfail_reason = failure.get("message", "")
        if "sthita-viveka" in xfail_reason or "shashthi-vibhakti" in xfail_reason:
            categories.append("scope-shashthi-lookup")
        if "viraam" in xfail_reason:
            categories.append("viraam-scope")
        if "has-intent" in xfail_reason or "vidhi-kaala" in xfail_reason:
            categories.append("has-intent")

    return {
        "categories": list(set(categories)) or ["unknown"],
        "sentences": sentences,
        "answers": [a for _, a in answers],
        "call_count": len(calls),
        "total_ms": sum(c.get("elapsed_ms", 0) for c in calls),
    }


# ── diff against previous ─────────────────────────────────────────────────────


def diff_summaries(current: dict, previous_path: str) -> dict:
    """Compare current summary against a previous one."""
    try:
        prev = json.loads(Path(previous_path).read_text())
    except Exception as e:
        return {"error": str(e)}

    curr_failed = {t["test"] for t in current.get("failed_tests", [])}
    prev_failed = {t["test"] for t in prev.get("failed_tests", [])}
    curr_xfailed = {t["test"] for t in current.get("xfail_tests", [])}
    prev_xfailed = {t["test"] for t in prev.get("xfail_tests", [])}

    return {
        "newly_failing": sorted(curr_failed - prev_failed),
        "newly_passing": sorted(prev_failed - curr_failed),
        "still_failing": sorted(curr_failed & prev_failed),
        "newly_xfailing": sorted(curr_xfailed - prev_xfailed),
        "newly_passing_xfail": sorted(prev_xfailed - curr_xfailed),
        "count_delta": {
            "failed": current.get("failed", 0) - prev.get("failed", 0),
            "passed": current.get("passed", 0) - prev.get("passed", 0),
            "xfailed": current.get("xfailed", 0) - prev.get("xfailed", 0),
        },
    }


# ── test pipeline runner ──────────────────────────────────────────────────────


def failed_node_ids(entries: list[dict]) -> list[str]:
    """Return pytest node IDs for all failed tests from the cache."""
    return [e["test"] for e in entries if e.get("outcome") in ("failed", "error")]


def xpassed_node_ids(entries: list[dict]) -> list[str]:
    """Return pytest node IDs for xpassed tests (strict xfail now passing)."""
    return [e["test"] for e in entries if e.get("outcome") == "xpassed"]


def fix_xpass_markers(entries: list[dict], dry_run: bool = False) -> list[str]:
    """
    Remove @pytest.mark.xfail(...) decorators from tests that now pass (xpassed).

    For each xpassed entry, reads file + line from the stored xfail metadata,
    finds the @pytest.mark.xfail block immediately above the def, and removes it.

    Returns list of (file:line) locations that were fixed.
    """
    import re

    fixed = []
    for e in entries:
        if e.get("outcome") != "xpassed":
            continue
        xf = e.get("xfail") or {}
        fpath = xf.get("file", "")
        def_line = xf.get("line", 0)  # 1-based line of the def
        if not fpath or not def_line:
            print(f"  no file/line stored for {e['test']} — run suite first")
            continue

        try:
            src = open(fpath).read()
            lines = src.splitlines(keepends=True)
        except Exception as ex:
            print(f"  cannot read {fpath}: {ex}")
            continue

        # stored line is 1-based; may point at the @pytest.mark.xfail line OR the def line
        # search in a window around it for the @pytest.mark.xfail start
        start = None
        search_center = def_line - 1  # 0-based
        for delta in range(0, 12):
            for candidate in [search_center - delta, search_center + delta]:
                if 0 <= candidate < len(lines):
                    s = lines[candidate].strip()
                    if s.startswith("@pytest.mark.xfail") or s.startswith("@xfail"):
                        start = candidate
                        break
            if start is not None:
                break

        if start is None:
            print(f"  no @pytest.mark.xfail found near line {def_line} in {fpath}")
            continue

        # find the def line: scan forward from start until we hit 'def '
        def_idx = None
        for j in range(start, min(start + 20, len(lines))):
            if lines[j].strip().startswith("def "):
                def_idx = j
                break
        if def_idx is None:
            print(f"  cannot find def after xfail at line {start + 1} in {fpath}")
            continue

        # find end of the xfail decorator block (may span multiple lines with parens)
        end = start
        depth = 0
        in_decorator = False
        for j in range(start, def_idx):
            stripped_j = lines[j].strip()
            if stripped_j.startswith("@pytest.mark.xfail") or stripped_j.startswith(
                "@xfail"
            ):
                in_decorator = True
            if in_decorator:
                depth += lines[j].count("(") - lines[j].count(")")
                end = j
                if depth <= 0 and j > start:
                    break

        removed_lines = lines[start : end + 1]
        location = f"{fpath}:{start + 1}"
        print(f"  {'[dry-run] ' if dry_run else ''}removing xfail at {location}:")
        for ln in removed_lines:
            print(f"    - {ln.rstrip()}")

        if not dry_run:
            new_lines = lines[:start] + lines[end + 1 :]
            open(fpath, "w").writelines(new_lines)
            fixed.append(location)
        else:
            fixed.append(location)

    return fixed


def run_pytest(
    node_ids: list[str] | None, label: str, extra_args: list[str] | None = None
) -> int:
    """
    Run pytest on specific node_ids (or full suite if None).
    Streams output live. Returns exit code.
    """
    cmd = ["python3", "-m", "pytest", "--tb=short", "-q"]
    if extra_args:
        cmd.extend(extra_args)
    if node_ids:
        cmd.extend(node_ids)
    print(f"\n{'─' * 72}", flush=True)
    print(f"  {label}", flush=True)
    print(f"  cmd: {' '.join(shlex.quote(a) for a in cmd)}", flush=True)
    print(f"{'─' * 72}\n", flush=True)
    result = subprocess.run(cmd, cwd=str(PYTEST_ROOT))
    return result.returncode


def server_alive(socket_path: str = SOCKET_PATH) -> bool:
    """Check whether the vyakarana server is responding."""
    import socket as _socket

    try:
        s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(socket_path)
        s.sendall(b'{"command":"eval-json","expr":"1"}\n')
        data = s.recv(256)
        s.close()
        return b'"ok"' in data
    except Exception:
        return False


def start_server(
    brahman_dir: str | None = None, socket_path: str = SOCKET_PATH
) -> subprocess.Popen | None:
    """Start the vyakarana server in the background. Returns the process."""
    exe = PYTEST_ROOT / "_build" / "default" / "bin" / "vyakarana.exe"
    if not exe.exists():
        print(f"  server binary not found: {exe}", file=sys.stderr)
        return None
    brahman = brahman_dir or str(REPO_ROOT / "brahman")
    cmd = [str(exe), "--quiet-startup", "--socket", socket_path, brahman]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import time

    for _ in range(10):
        time.sleep(0.5)
        if server_alive(socket_path):
            return proc
    proc.kill()
    print("  server failed to start", file=sys.stderr)
    return None


def run_pipeline(
    cache_dir: Path,
    full: bool = False,
    auto_server: bool = False,
    brahman_dir: str | None = None,
    gate: str | None = None,
) -> int:
    """
    The controlled test pipeline:

    1. Read failures from cache.
    2. If failures exist → run only those tests.
       If they all pass → run full suite.
       If they still fail → report and stop.
    3. If no failures in cache → run full suite directly (or skip if --fast).
    4. Print analysis report after each run.

    Returns 0 if all tests pass (or no failures), non-zero otherwise.
    """
    SEP = "═" * 72

    # ensure server is up
    if not server_alive():
        if auto_server:
            print("  server not responding — starting...", flush=True)
            proc = start_server(brahman_dir)
            if proc is None:
                print("  cannot start server. aborting.", file=sys.stderr)
                return 2
        else:
            print("  server not responding at /tmp/vy.sock", file=sys.stderr)
            print("  start it first, or use --auto-server", file=sys.stderr)
            return 2

    # load current cache state
    summary, entries = load_cache(cache_dir)
    failures = failed_node_ids(entries)

    print(SEP)
    print("  TEST PIPELINE")
    print(SEP)
    print(f"  cache: {cache_dir}")

    # gate mode: run only tests belonging to one xfail group
    if gate:
        gate_ids = xfailed_node_ids_for_gate(entries, gate)
        print(f"  gate: {gate!r} → {len(gate_ids)} test(s)")
        for t in gate_ids:
            print(f"    ? {t.split('::')[-1]}")
        print()
        if not gate_ids:
            print(f"  no xfailed tests match gate {gate!r}")
            print("  available gates:")
            groups = xfail_reason_groups(entries)
            for g in sorted(groups):
                print(f"    {g}  ({len(groups[g])} tests)")
            return 0
        rc = run_pytest(gate_ids, f"gate run — {gate!r}")
        summary_g, entries_g = load_cache(cache_dir)
        analysis = load_tantra_analysis()
        print_report(summary_g, entries_g, analysis)
        return rc

    print(f"  failures in cache: {len(failures)}")
    if failures:
        for f in failures:
            print(f"    ✗ {f.split('::')[-1]}")
    print()

    if not failures and not full:
        print("  no failures in cache — nothing to re-run.")
        print("  use --full to run the complete suite anyway.")
        return 0

    exit_code = 0

    if failures:
        # phase 1: run only the failing tests
        rc = run_pytest(
            failures, f"phase 1 — re-running {len(failures)} failed test(s)"
        )
        summary_new, entries_new = load_cache(cache_dir)
        still_failing = failed_node_ids(entries_new)

        if still_failing:
            print(f"\n  {len(still_failing)} test(s) still failing — stopping here.")
            for f in still_failing:
                print(f"  ✗ {f.split('::')[-1]}")
            exit_code = 1
        else:
            print(f"\n  all {len(failures)} previously-failing test(s) now pass.")
            full = True  # promote to full run

    if full and exit_code == 0:
        # phase 2: full suite
        rc = run_pytest(None, "phase 2 — full suite")
        summary_full, entries_full = load_cache(cache_dir)
        final_failures = failed_node_ids(entries_full)
        if final_failures:
            print(f"\n  {len(final_failures)} test(s) failing in full suite:")
            for f in final_failures:
                print(f"  ✗ {f.split('::')[-1]}")
            exit_code = rc

    # always print the report after running
    print()
    summary_final, entries_final = load_cache(cache_dir)
    analysis = load_tantra_analysis()
    print_report(summary_final, entries_final, analysis)

    return exit_code


# ── report ────────────────────────────────────────────────────────────────────


def print_report(
    summary: dict, entries: list[dict], analysis: dict, diff: dict | None = None
):
    SEP = "═" * 72

    by_outcome = entries_by_outcome(entries)
    # xfailed entries now stored as "xfailed"; "skipped" is legacy fallback
    skipped = by_outcome.get("xfailed", []) + by_outcome.get("skipped", [])
    failed = by_outcome.get("failed", []) + by_outcome.get("error", [])
    passed = by_outcome.get("passed", [])

    print(SEP)
    print("  TEST RESULTS ANALYSIS")
    print(SEP)
    xpassed_entries = by_outcome.get("xpassed", [])
    print(f"""
  total:   {len(entries)}
  passed:  {len(passed)}
  failed:  {len(failed)}
  xfailed: {len(skipped)}
  xpassed: {len(xpassed_entries)}
""")

    # diff if available
    if diff:
        print("── DIFF FROM PREVIOUS ───────────────────────────────────────────────")
        dc = diff.get("count_delta", {})
        symbol = lambda n: f"+{n}" if n > 0 else str(n)
        print(
            f"  failed {symbol(dc.get('failed', 0))}  passed {symbol(dc.get('passed', 0))}  xfailed {symbol(dc.get('xfailed', 0))}"
        )
        if diff.get("newly_failing"):
            print(f"\n  NEWLY FAILING ({len(diff['newly_failing'])}):")
            for t in diff["newly_failing"]:
                print(f"    ✗ {t}")
        if diff.get("newly_passing"):
            print(f"\n  NEWLY PASSING ({len(diff['newly_passing'])}):")
            for t in diff["newly_passing"]:
                print(f"    ✓ {t}")
        print()

    # failed tests with full call chain diagnosis
    if failed:
        print("── FAILED TESTS ─────────────────────────────────────────────────────")
        cat_counts = Counter()

        for e in failed:
            diag = categorize_failure(e, analysis)
            cats = diag["categories"]
            cat_counts.update(cats)
            failure = e.get("failure") or {}

            print(f"\n  {e['test']}")
            print(f"  categories: {cats}")
            if failure.get("expected"):
                print(f"  expected:   {failure['expected'][:70]!r}")

            # show the triggering call (last_call from failure info, or last eval call)
            last_call = failure.get("last_call")
            if not last_call:
                # find last eval/ask call from the call chain
                for c in reversed(e.get("calls", [])):
                    if c.get("method") in ("eval", "ask"):
                        last_call = c
                        break
            if last_call:
                print(
                    f"  trigger:    {last_call.get('method', '?')}({last_call.get('input', '')[:70]!r})"
                )
                out = last_call.get("output")
                if out is not None:
                    print(f"  got:        {str(out)[:100]!r}")
                ms = last_call.get("elapsed_ms", 0)
                if ms:
                    print(f"  elapsed:    {ms}ms")

            # show full eval chain if multiple calls
            chain = extract_eval_chain(e.get("calls", []))
            if len(chain) > 1:
                print(
                    f"  call chain ({len(chain)} calls, {e.get('duration', 0) * 1000:.0f}ms total):"
                )
                for step in chain:
                    err = f" ERROR:{step['error'][:40]}" if step.get("error") else ""
                    print(
                        f"    [{step['elapsed_ms']:>4}ms] {step['method']}  {step['input'][:60]}{err}"
                    )

        print(
            f"\n── FAILURE CATEGORIES ────────────────────────────────────────────────"
        )
        for cat, count in cat_counts.most_common():
            print(f"  {cat:<35} {count}×")

    # xpassed (strict xfails that now pass — need marker update)
    xpass = xpassed_entries
    if xpass:
        print(
            f"\n── XPASSED (remove xfail marker) ─────────────────────────────────────"
        )
        for e in xpass:
            xf = e.get("xfail") or {}
            loc = (
                f"  {xf.get('file', '?')}:{xf.get('line', '?')}"
                if xf.get("file")
                else ""
            )
            print(f"  {e['test']}{loc}")

    # xfail groups — what gate is each waiting on
    if skipped:
        print(
            f"\n── XFAILED by gate ({len(skipped)} tests) ────────────────────────────────────"
        )
        groups = xfail_reason_groups(entries)
        for gate, tests in sorted(groups.items()):
            print(f"\n  [{gate}]  {len(tests)} tests")
            for t in tests[:5]:
                print(f"    {t.split('::')[-1]}")
            if len(tests) > 5:
                print(f"    ... +{len(tests) - 5} more")

    # slowest individual calls (not just slowest tests)
    slow_calls = slowest_calls(entries, top_n=10)
    if slow_calls:
        print(
            f"\n── SLOWEST INDIVIDUAL CALLS ──────────────────────────────────────────"
        )
        for sc in slow_calls:
            print(f"  {sc['ms']:>5}ms  {sc['method']}  {sc['input'][:55]}")
            print(f"           in {sc['test'].split('::')[-1]}")

    # slow tests (by total duration)
    slow = summary.get("slow_tests", [])
    if slow:
        print(
            f"\n── SLOWEST TESTS (by total duration) ────────────────────────────────"
        )
        for t in slow[:8]:
            print(
                f"  {t['duration']:>6.2f}s  {t['calls']:>3} calls  {t['test'].split('::')[-1]}"
            )

    print()


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--cache",
        default=str(CACHE_DEFAULT),
        help="path to .pytest_cache/vyakarana dir",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit JSON instead of human report"
    )
    parser.add_argument(
        "--diff", default=None, help="path to previous summary.json for comparison"
    )
    # pipeline control
    parser.add_argument(
        "--run",
        action="store_true",
        help="run only failed tests from cache; if they pass, run full suite",
    )
    parser.add_argument(
        "--full", action="store_true", help="run the full test suite unconditionally"
    )
    parser.add_argument(
        "--auto-server",
        action="store_true",
        help="start the vyakarana server if not already running",
    )
    parser.add_argument(
        "--brahman", default=None, help="brahman dir (for --auto-server)"
    )
    parser.add_argument(
        "--gate",
        default=None,
        metavar="NAME",
        help="run only xfailed tests whose gate contains NAME (e.g. 'session_gap2', 'inverse')",
    )
    parser.add_argument(
        "--fix-xpass",
        action="store_true",
        help="remove @pytest.mark.xfail decorators from tests that now pass (xpassed)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="with --fix-xpass: show what would be removed without writing files",
    )
    args = parser.parse_args()

    cache_dir = Path(args.cache)

    # fix-xpass mode: strip markers from xpassed tests
    if args.fix_xpass:
        if not cache_dir.exists():
            print(f"Cache not found: {cache_dir}", file=sys.stderr)
            sys.exit(1)
        _, entries = load_cache(cache_dir)
        xpassed = [e for e in entries if e.get("outcome") == "xpassed"]
        if not xpassed:
            print("No xpassed tests in cache. Run the suite first.")
            sys.exit(0)
        print(f"Found {len(xpassed)} xpassed test(s):")
        fixed = fix_xpass_markers(xpassed, dry_run=args.dry_run)
        if fixed and not args.dry_run:
            print(f"\nFixed {len(fixed)} marker(s). Re-run suite to confirm.")
        sys.exit(0)

    # pipeline mode: run tests then report
    if args.run or args.full or args.gate:
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
        sys.exit(
            run_pipeline(
                cache_dir,
                full=args.full,
                auto_server=args.auto_server,
                brahman_dir=args.brahman,
                gate=args.gate,
            )
        )

    # report-only mode
    if not cache_dir.exists():
        print(f"Cache directory not found: {cache_dir}", file=sys.stderr)
        print("Run:  python3 tools/analyze_test_results.py --run", file=sys.stderr)
        sys.exit(1)

    summary, entries = load_cache(cache_dir)
    analysis = load_tantra_analysis()
    diff = diff_summaries(summary, args.diff) if args.diff else None

    # augment failed_tests with diagnosis
    entry_map = {e["test"]: e for e in entries}
    for ft in summary.get("failed_tests", []):
        entry = entry_map.get(ft["test"], {})
        ft["diagnosis"] = categorize_failure(entry, analysis)

    if args.json:
        print(
            json.dumps(
                {
                    "summary": summary,
                    "diff": diff,
                },
                indent=2,
                default=str,
            )
        )
    else:
        print_report(summary, entries, analysis, diff)
