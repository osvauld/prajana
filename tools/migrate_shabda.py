"""migrate_shabda.py — extract inline shabda from .om files into .shabda files.

Groups by domain (depth 2), creates one .shabda file per group.
Strips shabda lines from .om files afterward.

Usage:
  python3 -m tools.migrate_shabda --dry-run    # preview only
  python3 -m tools.migrate_shabda              # do the migration
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# project root
ROOT = Path(__file__).resolve().parent.parent
BRAHMAN = ROOT / "brahman"
SHABDA_DIR = BRAHMAN / "shabda"

# layers that own .om files
LAYERS = ["sangati", "kosha", "bhasha", "mantra"]


def find_om_files():
    """Find all .om files under brahman/."""
    files = []
    for root, _, names in os.walk(BRAHMAN):
        for name in names:
            if name.endswith(".om"):
                files.append(os.path.join(root, name))
    return sorted(files)


def parse_shabda_from_file(path):
    """Extract the shabda line from an .om file.

    Returns (node_name, layer, shabda_raw, domain_key) or None.
    """
    with open(path) as f:
        lines = f.readlines()

    node_name = None
    layer = None
    shabda_raw = None

    for line in lines:
        stripped = line.strip()
        # parse header
        if not node_name:
            for prefix in LAYERS:
                if stripped.startswith(prefix + " "):
                    parts = stripped.split()
                    if len(parts) >= 2:
                        layer = parts[0]
                        node_name = parts[1]
                    break
        # parse shabda line
        if stripped.startswith("shabda "):
            shabda_raw = stripped[7:].strip()

    if not node_name or not shabda_raw:
        return None

    # domain key: relative path from brahman, depth 2
    rel = os.path.relpath(os.path.dirname(path), BRAHMAN)
    parts = rel.split(os.sep)
    if len(parts) >= 2:
        domain_key = os.sep.join(parts[:2])
    else:
        domain_key = parts[0]

    return {
        "name": node_name,
        "layer": layer,
        "shabda_raw": shabda_raw,
        "domain_key": domain_key,
        "path": path,
    }


def strip_shabda_from_file(path):
    """Remove the shabda line from an .om file."""
    with open(path) as f:
        lines = f.readlines()

    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("shabda "):
            # skip this line, and skip an empty line before it if present
            if result and result[-1].strip() == "":
                result.pop()
            continue
        result.append(line)

    with open(path, "w") as f:
        f.writelines(result)


def format_shabda_entry(entry):
    """Format one entry for a .shabda file.

    Input: shabda_raw string from .om file
    Output: node_name: shabda_raw (ready to write)
    """
    return f"{entry['name']}: {entry['shabda_raw']}"


def main():
    dry_run = "--dry-run" in sys.argv

    # collect all .om files with shabda
    om_files = find_om_files()
    entries = []
    for path in om_files:
        result = parse_shabda_from_file(path)
        if result:
            entries.append(result)

    print(f"Found {len(entries)} nodes with inline shabda across {len(om_files)} .om files\n")

    # group by domain
    by_domain = defaultdict(list)
    for entry in entries:
        by_domain[entry["domain_key"]].append(entry)

    # skip shabda-tmpl references — these already point to external files
    tmpl_count = 0
    for domain, items in by_domain.items():
        for item in items[:]:
            if item["shabda_raw"].startswith("shabda-tmpl:"):
                tmpl_count += 1
                items.remove(item)

    # remove empty domains after filtering
    by_domain = {k: v for k, v in by_domain.items() if v}

    print(f"Skipping {tmpl_count} shabda-tmpl references (already external)\n")
    print(f"Will create {len(by_domain)} .shabda files:\n")

    total_written = 0
    total_stripped = 0

    for domain in sorted(by_domain.keys()):
        items = by_domain[domain]
        # shabda file path: brahman/shabda/<domain>.shabda
        shabda_filename = domain.replace(os.sep, "-") + ".shabda"
        shabda_path = SHABDA_DIR / shabda_filename

        print(f"  {str(shabda_path.relative_to(ROOT)):<55} {len(items):>4} entries")

        if not dry_run:
            # ensure directory
            shabda_path.parent.mkdir(parents=True, exist_ok=True)

            # write shabda file
            with open(shabda_path, "w") as f:
                f.write(f"# {domain} — shabda extracted from .om files\n")
                f.write(f"# {len(items)} entries\n\n")
                for item in sorted(items, key=lambda x: x["name"]):
                    f.write(format_shabda_entry(item) + "\n")

            total_written += 1

            # strip shabda from .om files
            for item in items:
                strip_shabda_from_file(item["path"])
                total_stripped += 1

    print()
    if dry_run:
        print(f"DRY RUN — no files modified. Run without --dry-run to execute.")
    else:
        print(f"Done: {total_written} .shabda files written, {total_stripped} .om files stripped")
        print(f"\nRestart the server to pick up changes:")
        print(f"  python3 -m tools vy restart")


if __name__ == "__main__":
    main()
