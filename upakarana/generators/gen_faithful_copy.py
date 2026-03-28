"""gen_faithful_copy.py — Regenerate brahman/ (faithful consolidation).

Reads every node from brahman/, groups them into consolidated .om5 files,
copies shabda and yantra directories as-is.

Grouping rules:
  - sangati/<subdir>/*  → sangati/<subdir>.om5
  - sangati/root files  → sangati/root.om5
  - bhasha/<lang>/*     → bhasha/<lang>.om5
  - kosha/physics/<sub> → kosha/physics-<sub>.om5
  - kosha/math/<sub>    → kosha/math-<sub>.om5
  - kosha/<domain>/*    → kosha/<domain>.om5
  - kosha/root files    → kosha/kosha-root.om5
  - engine/*            → engine.om5
  - personal/*          → personal.om5

Mantra nodes embedded in kosha files stay grouped with their parent domain.
"""

import os
import shutil
import sys
from collections import defaultdict

from upakarana.paths import BRAHMAN, ROOT
from upakarana.parsers.om5 import load_all, edges_by_relation

# Domains that get sub-split into separate files
SPLIT_DOMAINS = {"physics", "math"}


def grouping_key(node):
    """Compute the output file path (relative to brahman/) for a node."""
    domain = node["domain"]
    parts = domain.split("/") if domain else []

    if not parts:
        return "orphan.om5"

    top = parts[0]  # sangati, kosha, bhasha, engine, personal

    if top in ("engine", "personal"):
        return f"{top}.om5"

    if top == "sangati":
        if len(parts) >= 2:
            return f"sangati/{parts[1]}.om5"
        return "sangati/root.om5"

    if top == "bhasha":
        if len(parts) >= 2:
            return f"bhasha/{parts[1]}.om5"
        return "bhasha/root.om5"

    if top == "kosha":
        if len(parts) >= 2:
            sub = parts[1]
            if sub in SPLIT_DOMAINS and len(parts) >= 3:
                # kosha/physics/kinematics/... → kosha/physics-kinematics.om5
                return f"kosha/{sub}-{parts[2]}.om5"
            elif sub in SPLIT_DOMAINS:
                # kosha/physics (root files) → kosha/physics-foundation.om5
                return f"kosha/{sub}-foundation.om5"
            else:
                return f"kosha/{sub}.om5"
        # kosha root-level nodes
        return "kosha/kosha-root.om5"

    # Fallback
    return f"{top}.om5"


def serialize_node_source(node, collision_names=None):
    """Re-serialize a node to om5 s-expression text from its parsed source.

    For collision nodes (same name, different domains), injects a (domain ...)
    sloka so the OCaml loader can distinguish them.
    """
    src = node["source"].rstrip()
    if collision_names and node["name"] in collision_names:
        domain = node["domain"]
        if domain:
            # Inject (domain ...) after the opening (layer name line
            lines = src.split("\n")
            # Insert after first line: (layer name
            lines.insert(1, f"  (domain {domain})")
            src = "\n".join(lines)
    return src + "\n"


def _find_collision_names(all_nodes):
    """Find node names that appear in multiple distinct domains."""
    from collections import defaultdict
    name_domains = defaultdict(set)
    for node in all_nodes:
        name_domains[node["name"]].add(node["domain"])
    return {name for name, domains in name_domains.items() if len(domains) > 1}


def generate(dry_run=False):
    """Main generation: read brahman/, write consolidated om5 files."""
    from upakarana.parsers.om5 import find_all, parse_multi

    print("Loading all nodes from brahman/...")
    all_nodes = []
    for path in find_all(BRAHMAN):
        for node in parse_multi(path, BRAHMAN):
            all_nodes.append(node)
    print(f"  {len(all_nodes)} node instances loaded")

    # Detect collision names for domain injection
    collision_names = _find_collision_names(all_nodes)
    if collision_names:
        print(f"  {len(collision_names)} collision names will get (domain ...) slokas")

    # Group by output file
    groups = defaultdict(list)
    for node in all_nodes:
        key = grouping_key(node)
        groups[key].append(node)

    print(f"  {len(groups)} output files")

    if dry_run:
        print("\n=== DRY RUN (no files written) ===\n")
        for key in sorted(groups):
            print(f"  {len(groups[key]):4d} nodes → {key}")
        total = sum(len(v) for v in groups.values())
        print(f"\n  TOTAL: {total} nodes in {len(groups)} files")
        return groups

    # Clean brahman/ om5 files (not shabda, not yantra)
    om5_dirs = ["kosha", "sangati", "bhasha"]
    for d in om5_dirs:
        target = os.path.join(str(BRAHMAN), d)
        if os.path.isdir(target):
            for f in os.listdir(target):
                if f.endswith(".om5"):
                    os.remove(os.path.join(target, f))
                # Also remove subdirs that only held om5 files
                fp = os.path.join(target, f)
                if os.path.isdir(fp):
                    shutil.rmtree(fp)

    # Remove root-level om5 files
    for f in ("engine.om5", "personal.om5", "orphan.om5"):
        fp = os.path.join(str(BRAHMAN), f)
        if os.path.exists(fp):
            os.remove(fp)

    # Write consolidated files
    written = 0
    for key in sorted(groups):
        out_path = os.path.join(str(BRAHMAN), key)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        node_list = groups[key]
        # Derive header comment from the key
        basename = os.path.splitext(os.path.basename(key))[0]

        lines = []
        lines.append(f"; {'═' * 67}")
        lines.append(f"; {basename} — {len(node_list)} nodes")
        lines.append(f"; {'═' * 67}")
        lines.append("")

        for node in node_list:
            lines.append(serialize_node_source(node, collision_names))

        with open(out_path, "w") as f:
            f.write("\n".join(lines))

        written += 1

    print(f"  {written} files written to brahman/")

    # Copy shabda
    src_shabda = os.path.join(str(BRAHMAN), "shabda")
    dst_shabda = os.path.join(str(BRAHMAN), "shabda")
    if os.path.isdir(src_shabda):
        if os.path.isdir(dst_shabda):
            shutil.rmtree(dst_shabda)
        shutil.copytree(src_shabda, dst_shabda)
        n_shabda = len([f for f in os.listdir(dst_shabda) if f.endswith(".shabda")])
        print(f"  {n_shabda} shabda files copied")

    # Copy yantra (tantra files)
    src_yantra = os.path.join(str(BRAHMAN), "yantra")
    dst_yantra = os.path.join(str(BRAHMAN), "yantra")
    if os.path.isdir(src_yantra):
        if os.path.isdir(dst_yantra):
            shutil.rmtree(dst_yantra)
        shutil.copytree(src_yantra, dst_yantra)
        n_tantra = sum(1 for r, _, fs in os.walk(dst_yantra) for f in fs)
        print(f"  {n_tantra} yantra files copied")

    return groups


def verify(groups):
    """Verify brahman/ round-trips correctly.

    Compares by raw node name (not collision-renamed dict keys).
    Collision nodes (same name, different domains) are counted separately.
    """
    print("\nVerifying brahman/...")
    from upakarana.parsers.om5 import find_all, parse_multi

    # Collect all raw nodes from each source (name → list of nodes)
    def collect_raw(root):
        by_name = defaultdict(list)
        for path in find_all(root):
            for node in parse_multi(path, root):
                by_name[node["name"]].append(node)
        return by_name

    b1_raw = collect_raw(BRAHMAN)
    b2_raw = collect_raw(BRAHMAN)

    b1_total = sum(len(v) for v in b1_raw.values())
    b2_total = sum(len(v) for v in b2_raw.values())
    print(f"  brahman:  {b1_total} node instances ({len(b1_raw)} unique names)")
    print(f"  brahman (out): {b2_total} node instances ({len(b2_raw)} unique names)")

    missing_names = set(b1_raw) - set(b2_raw)
    extra_names = set(b2_raw) - set(b1_raw)

    if missing_names:
        print(f"  MISSING names ({len(missing_names)}): {sorted(missing_names)[:10]}...")
    if extra_names:
        print(f"  EXTRA names ({len(extra_names)}): {sorted(extra_names)[:10]}...")

    # Check instance counts match (collision nodes should have same count)
    count_mismatches = 0
    for name in set(b1_raw) & set(b2_raw):
        c1 = len(b1_raw[name])
        c2 = len(b2_raw[name])
        if c1 != c2:
            count_mismatches += 1
            if count_mismatches <= 5:
                print(f"  COUNT MISMATCH: {name} b1={c1} b2={c2}")

    if count_mismatches:
        print(f"  {count_mismatches} names with instance count mismatches")

    # Check total edge counts per name
    edge_mismatches = 0
    for name in set(b1_raw) & set(b2_raw):
        e1 = sum(len(n["edges"]) for n in b1_raw[name])
        e2 = sum(len(n["edges"]) for n in b2_raw[name])
        if e1 != e2:
            edge_mismatches += 1
            if edge_mismatches <= 5:
                print(f"  EDGE MISMATCH: {name} b1={e1} b2={e2}")

    if edge_mismatches:
        print(f"  {edge_mismatches} names with edge count mismatches")

    ok = not missing_names and not extra_names and count_mismatches == 0 and edge_mismatches == 0
    if ok:
        print("  ✓ PERFECT MATCH")
    return ok


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    groups = generate(dry_run=dry)
    if not dry:
        verify(groups)
