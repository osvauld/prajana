"""usage.py — Command usage tracking across sessions.

Stores counts in a simple JSON file. Every CLI invocation increments
the counter for that command+action pair. Persists across sessions.
"""

import json
import os
import time
from collections import defaultdict
from upakarana.paths import ROOT

USAGE_FILE = ROOT / "upakarana" / "data" / "usage.json"


def _load():
    """Load usage data from disk."""
    if USAGE_FILE.exists():
        try:
            return json.loads(USAGE_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            return {"commands": {}, "sessions": 0, "first_use": None}
    return {"commands": {}, "sessions": 0, "first_use": None}


def _save(data):
    """Save usage data to disk."""
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(json.dumps(data, indent=2))


def track(command, action=None):
    """Record one invocation of command [action].

    Called at CLI dispatch time. Increments the counter and
    records the last-used timestamp.
    """
    data = _load()
    if data["first_use"] is None:
        data["first_use"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    key = f"{command} {action}" if action else command
    if key not in data["commands"]:
        data["commands"][key] = {"count": 0, "first": None, "last": None}

    entry = data["commands"][key]
    entry["count"] += 1
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    if entry["first"] is None:
        entry["first"] = now
    entry["last"] = now

    _save(data)


def bump_session():
    """Increment session counter (call once per CLI invocation)."""
    data = _load()
    data["sessions"] = data.get("sessions", 0) + 1
    _save(data)


def report():
    """Return usage report: most used, never used, session count."""
    data = _load()
    commands = data.get("commands", {})

    # Sort by count descending
    by_count = sorted(commands.items(), key=lambda x: -x[1]["count"])

    return {
        "sessions": data.get("sessions", 0),
        "first_use": data.get("first_use"),
        "total_invocations": sum(v["count"] for v in commands.values()),
        "unique_commands": len(commands),
        "top": [{"command": k, "count": v["count"], "last": v["last"]}
                for k, v in by_count[:20]],
        "all": {k: v["count"] for k, v in by_count},
    }


def never_used(all_commands):
    """Given a list of all possible commands, return those never invoked."""
    data = _load()
    used = set(data.get("commands", {}).keys())
    return sorted(set(all_commands) - used)
