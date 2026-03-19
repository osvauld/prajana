"""
cache.py — read, query, and act on the pytest result cache.

The cache lives at:
  vyakarana/tests/.pytest_cache/vyakarana/
    summary.json         — aggregate summary written by conftest.pytest_sessionfinish
    <test_nodeid>.json   — per-test entry written by conftest._write_cache

Each per-test entry:
  {
    "test":     "v2/test_answers.py::test_ke_basic",
    "outcome":  "passed" | "failed" | "error" | "xfailed" | "xpassed" | "skipped",
    "calls":    [{"method": "eval|ask|walk", "input": "...", "output": ...,
                  "elapsed_ms": N, "error": null|"..."}],
    "failure":  {"expected": "...", "got": "...", "message": "...", "last_call": ...},
    "duration": N.NN,
    "xfail":    {"reason": "...", "gate": "...", "strict": bool, "file": "...", "line": N}
  }

This module replaces analyze_test_results.py and is called by the brahman
socket server so all cache queries go through the same interface.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .paths import ROOT

# ── cache location ─────────────────────────────────────────────────────────────

DEFAULT_CACHE = Path(__file__).parent / ".pytest_cache" / "vyakarana"


# ── load ───────────────────────────────────────────────────────────────────────


def load(cache_dir: Path | None = None) -> tuple[dict, list[dict]]:
    """Load summary.json and all per-test entries from cache_dir.

    Returns (summary_dict, [entry_dicts]).
    """
    d = cache_dir or DEFAULT_CACHE
    d = Path(d)

    summary_path = d / "summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    entries = []
    for f in sorted(d.glob("*.json")):
        if f.name == "summary.json":
            continue
        try:
            entries.append(json.loads(f.read_text()))
        except Exception:
            pass
    return summary, entries


# ── group / filter ─────────────────────────────────────────────────────────────


def by_outcome(entries: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        groups[e.get("outcome", "unknown")].append(e)
    return dict(groups)


def failed(entries: list[dict]) -> list[dict]:
    return [e for e in entries if e.get("outcome") in ("failed", "error")]


def xfailed(entries: list[dict]) -> list[dict]:
    return [e for e in entries if e.get("outcome") in ("xfailed", "skipped")]


def xpassed(entries: list[dict]) -> list[dict]:
    return [e for e in entries if e.get("outcome") == "xpassed"]


def passed(entries: list[dict]) -> list[dict]:
    return [e for e in entries if e.get("outcome") == "passed"]


def by_gate(entries: list[dict]) -> dict[str, list[dict]]:
    """Group xfailed entries by their gate string."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for e in xfailed(entries):
        gate = (e.get("xfail") or {}).get("gate", "other")
        if not gate:
            gate = f"other:{e['test'].split('/')[-1].split('.')[0]}"
        groups[gate].append(e)
    return dict(groups)


def entries_for_gate(entries: list[dict], gate: str) -> list[dict]:
    """Return xfailed entries whose gate contains the given string."""
    return [
        e
        for e in xfailed(entries)
        if gate.lower() in ((e.get("xfail") or {}).get("gate", "")).lower()
    ]


def node_ids(entries: list[dict]) -> list[str]:
    return [e["test"] for e in entries]


# ── extract ────────────────────────────────────────────────────────────────────


def sentences(calls: list[dict]) -> list[str]:
    """Extract natural-language sentences sent to anuvada-ganana or vy.ask."""
    result = []
    for c in calls:
        inp = c.get("input", "")
        if c.get("method") == "ask":
            result.append(inp)
        elif c.get("method") == "eval" and inp.startswith('anuvada-ganana "'):
            m = re.match(r'anuvada-ganana "(.+)"$', inp)
            if m:
                result.append(m.group(1))
    return result


def call_chain(calls: list[dict]) -> list[dict]:
    """Summarize eval chain for display."""
    chain = []
    for c in calls:
        out = c.get("output")
        if isinstance(out, str):
            out_s = out[:80]
        elif isinstance(out, list):
            out_s = f"[{len(out)} triples]"
        elif out is not None:
            out_s = str(out)[:60]
        else:
            out_s = ""
        chain.append(
            {
                "method": c.get("method", "?"),
                "input": c.get("input", "")[:100],
                "output": out_s,
                "elapsed_ms": c.get("elapsed_ms", 0),
                "error": c.get("error"),
            }
        )
    return chain


def slowest_calls(entries: list[dict], top_n: int = 20) -> list[dict]:
    """Find the slowest individual eval calls across all entries."""
    all_calls = []
    for e in entries:
        for c in e.get("calls", []):
            ms = c.get("elapsed_ms", 0)
            if ms and ms > 50:
                all_calls.append(
                    {
                        "test": e["test"],
                        "method": c.get("method", "?"),
                        "input": c.get("input", "")[:80],
                        "ms": ms,
                    }
                )
    return sorted(all_calls, key=lambda x: x["ms"], reverse=True)[:top_n]


# ── failure diagnosis ──────────────────────────────────────────────────────────


def diagnose(entry: dict) -> dict:
    """Categorize a failed test entry by likely root cause."""
    calls = entry.get("calls", [])
    failure = entry.get("failure") or {}
    s_list = sentences(calls)
    answers = []
    for c in calls:
        inp = c.get("input", "")
        out = c.get("output", "")
        if c.get("method") == "ask":
            answers.append((inp, str(out)))
        elif c.get("method") == "eval" and inp.startswith('anuvada-ganana "'):
            m = re.match(r'anuvada-ganana "(.+)"$', inp)
            if m:
                answers.append((m.group(1), str(out)))

    categories = []
    for sentence, answer in answers:
        ans_lower = answer.lower()
        if (
            "no match" in failure.get("expected", "").lower()
            and answer
            and "no match" not in ans_lower
        ):
            categories.append("has-intent-guard-missing")
        if "ball-a" in sentence.lower() or "ball-b" in sentence.lower():
            if answer and "no match" not in ans_lower:
                categories.append("scope-entity")
        if "relative-velocity" in answer:
            categories.append("relative-velocity-spurious")
        if (
            "we know: relative-velocity-mantra" in answer
            and "relative-velocity" not in sentence.lower()
        ):
            categories.append("derive-chain-contamination")
        msg = failure.get("message", "")
        if "sthita-viveka" in msg or "shashthi-vibhakti" in msg:
            categories.append("scope-shashthi-lookup")
        if "viraam" in msg:
            categories.append("viraam-scope")
        if "has-intent" in msg or "vidhi-kaala" in msg:
            categories.append("has-intent")

    return {
        "categories": list(set(categories)) or ["unknown"],
        "sentences": s_list,
        "answers": [a for _, a in answers],
        "call_count": len(calls),
        "total_ms": sum(c.get("elapsed_ms", 0) for c in calls),
    }


# ── summary ────────────────────────────────────────────────────────────────────


def summarize(entries: list[dict]) -> dict:
    """Aggregate counts and lists from entries."""
    by_o = by_outcome(entries)
    fail_entries = failed(entries)
    xf_entries = xfailed(entries)
    xp_entries = xpassed(entries)
    pass_entries = passed(entries)

    failed_list = []
    for e in fail_entries:
        diag = diagnose(e)
        f = e.get("failure") or {}
        failed_list.append(
            {
                "test": e["test"],
                "expected": f.get("expected", ""),
                "got": f.get("got", ""),
                "sentences": diag["sentences"],
                "categories": diag["categories"],
                "calls": diag["call_count"],
                "duration": e.get("duration", 0),
            }
        )

    xfail_list = []
    for e in xf_entries:
        xf = e.get("xfail") or {}
        xfail_list.append(
            {
                "test": e["test"],
                "gate": xf.get("gate", ""),
                "reason": xf.get("reason", "")[:100],
                "strict": xf.get("strict", False),
                "duration": e.get("duration", 0),
            }
        )

    xpass_list = []
    for e in xp_entries:
        xf = e.get("xfail") or {}
        xpass_list.append(
            {
                "test": e["test"],
                "file": xf.get("file", ""),
                "line": xf.get("line", 0),
                "reason": xf.get("reason", "")[:80],
            }
        )

    slow = sorted(
        [
            {
                "test": e["test"],
                "duration": e.get("duration", 0),
                "calls": len(e.get("calls", [])),
            }
            for e in entries
            if e.get("duration", 0) > 0.5
        ],
        key=lambda x: x["duration"],
        reverse=True,
    )[:20]

    gates = {}
    for gate, g_entries in by_gate(entries).items():
        gates[gate] = [e["test"] for e in g_entries]

    return {
        "total": len(entries),
        "passed": len(pass_entries),
        "failed": len(fail_entries),
        "xfailed": len(xf_entries),
        "xpassed": len(xp_entries),
        "failed_tests": failed_list,
        "xfail_tests": xfail_list,
        "xpass_tests": xpass_list,
        "slow_tests": slow,
        "gates": gates,
        "slow_calls": slowest_calls(entries, top_n=10),
    }


# ── diff ────────────────────────────────────────────────────────────────────────


def diff(current_entries: list[dict], previous_path: str) -> dict:
    """Compare current entries against a previous summary.json."""
    try:
        prev = json.loads(Path(previous_path).read_text())
    except Exception as e:
        return {"error": str(e)}

    curr_failed = {e["test"] for e in failed(current_entries)}
    prev_failed = {t["test"] for t in prev.get("failed_tests", [])}
    curr_xf = {e["test"] for e in xfailed(current_entries)}
    prev_xf = {t["test"] for t in prev.get("xfail_tests", [])}
    curr_xp = {e["test"] for e in xpassed(current_entries)}

    curr_pass = len(passed(current_entries))
    prev_pass = prev.get("passed", 0)

    return {
        "newly_failing": sorted(curr_failed - prev_failed),
        "newly_passing": sorted(prev_failed - curr_failed),
        "still_failing": sorted(curr_failed & prev_failed),
        "newly_xfailing": sorted(curr_xf - prev_xf),
        "newly_xpassing": sorted(curr_xp),
        "count_delta": {
            "failed": len(curr_failed) - len(prev_failed),
            "passed": curr_pass - prev_pass,
            "xfailed": len(curr_xf) - len(prev_xf),
        },
    }


# ── fix-xpass ──────────────────────────────────────────────────────────────────


def fix_xpass(entries: list[dict], dry_run: bool = False) -> list[dict]:
    """Remove @pytest.mark.xfail decorators from xpassed tests.

    Returns list of {file, line, test, removed_lines, status} dicts.
    """
    results = []
    for e in xpassed(entries):
        xf = e.get("xfail") or {}
        fpath = xf.get("file", "")
        def_line = xf.get("line", 0)

        if not fpath or not def_line:
            results.append({"test": e["test"], "status": "no-location"})
            continue

        try:
            lines = open(fpath).readlines()
        except Exception as ex:
            results.append({"test": e["test"], "status": f"read-error: {ex}"})
            continue

        # find @pytest.mark.xfail or @xfail near def_line
        start = None
        center = def_line - 1  # 0-based
        for delta in range(0, 12):
            for candidate in [center - delta, center + delta]:
                if 0 <= candidate < len(lines):
                    s = lines[candidate].strip()
                    if s.startswith("@pytest.mark.xfail") or s.startswith("@xfail"):
                        start = candidate
                        break
            if start is not None:
                break

        if start is None:
            results.append(
                {
                    "test": e["test"],
                    "status": "not-found",
                    "file": fpath,
                    "line": def_line,
                }
            )
            continue

        # find the def line
        def_idx = None
        for j in range(start, min(start + 20, len(lines))):
            if lines[j].strip().startswith("def "):
                def_idx = j
                break
        if def_idx is None:
            results.append(
                {
                    "test": e["test"],
                    "status": "no-def",
                    "file": fpath,
                    "line": start + 1,
                }
            )
            continue

        # find end of decorator block (may span multiple lines)
        end = start
        depth = 0
        in_dec = False
        for j in range(start, def_idx):
            s = lines[j].strip()
            if s.startswith("@pytest.mark.xfail") or s.startswith("@xfail"):
                in_dec = True
            if in_dec:
                depth += lines[j].count("(") - lines[j].count(")")
                end = j
                if depth <= 0 and j > start:
                    break

        removed = [l.rstrip() for l in lines[start : end + 1]]

        if not dry_run:
            new_lines = lines[:start] + lines[end + 1 :]
            open(fpath, "w").writelines(new_lines)

        results.append(
            {
                "test": e["test"],
                "file": fpath,
                "line": start + 1,
                "removed_lines": removed,
                "status": "dry-run" if dry_run else "fixed",
            }
        )

    return results
