#!/usr/bin/env python3
"""restructure_sangati.py — Copy sangati/ → sangati2/ with new sub-bucket structure.

Only moves top-level .om files into sub-buckets.
Files already in subdirectories (chetan/, grammar/, etc.) stay where they are.
Sthalam meta-nodes stay at top level.

Usage:
  python3 scripts/restructure_sangati.py          # dry-run: show plan
  python3 scripts/restructure_sangati.py --apply   # actually copy
"""

import os
import shutil
import sys

BRAHMAN = os.path.join(os.path.dirname(os.path.dirname(__file__)), "brahman")
SRC = os.path.join(BRAHMAN, "sangati")
DST = os.path.join(BRAHMAN, "sangati2")

# ── Mapping: node-name → sub-bucket ──────────────────────────────────────────
# Nodes not listed here stay at top level (sthalam nodes, meta nodes, etc.)

MAPPING = {
    # ── sambandha/ — relation types, multiplicity, connection ─────────────
    "sambandha":            "sambandha",
    "aneka":                "sambandha",
    "aneka-aneka":          "sambandha",
    "aneka-eka":            "sambandha",
    "eka-aneka":            "sambandha",
    "eka-eka":              "sambandha",
    "dvaya":                "sambandha",
    "sama-kalana":          "sambandha",
    "samsarga":             "sambandha",
    "sangati":              "sambandha",      # the concept of relation itself
    "sankshepa":            "sambandha",
    "parishishtha":         "sambandha",
    "parishishtha-sankshepa": "sambandha",

    # ── viraam/ — punctuation, pause, cessation ───────────────────────────
    "viraam":               "viraam",
    "purna-viraam":         "viraam",
    "prashna-viraam":       "viraam",
    "ardha-viraam":         "viraam",
    "traya-bindu":          "viraam",
    "vismaya-viraam":       "viraam",

    # ── pramana/ — measure, proof, evidence ───────────────────────────────
    "pramana":              "pramana",
    "jnana-siddha-pramana": "pramana",
    "sarva-pramana":        "pramana",
    "ghana-pramana":        "pramana",
    "shuddhi-pramana":      "pramana",
    "pratyaksha":           "pramana",
    "dipaka":               "pramana",        # illumination → means of knowing

    # ── vidya/ — knowledge, learning ──────────────────────────────────────
    "vidya":                "vidya",
    "antarvidya":           "vidya",
    "utpatti-anveshana":    "vidya",
    "vidya-sadhana":        "vidya",
    "tarka-dvaara":         "vidya",          # gate of logic
    "nyaya":                "vidya",          # logic/inference

    # ── svabhava/ — intrinsic nature, quality ─────────────────────────────
    "sama":                 "svabhava",
    "sama-nila":            "svabhava",
    "sama-vishama":         "svabhava",
    "dharmaadharma":        "svabhava",
    "bhasha-swarupa":       "svabhava",
    "svairabhava":          "svabhava",
    "manavata":             "svabhava",
    "nirdosha":             "svabhava",

    # ── shuddhi/ — purification, refinement ───────────────────────────────
    "shuddhi":              "shuddhi",
    "prajna-vriddhi":       "shuddhi",
    "pramana-vriddhi":      "shuddhi",
    "mithya-satya":         "shuddhi",
    "kavaca":               "shuddhi",

    # ── spanda/ — already has a directory, move top-level spanda nodes ────
    "anu":                  "spanda",
    "anunada":              "spanda",
    "anusvara":             "spanda",
    "anusvara-pratibodha":  "spanda",
    "dvividha-marga":       "spanda",
    "kaalayoga":            "spanda",
    "kriya":                "spanda",
    "prasarana":            "spanda",
    "prayojana":            "spanda",
    "sahavadana":           "spanda",
    "tat-kshana":           "spanda",
    "vikrita":              "spanda",
    "vrnda":                "spanda",
    "ahara":                "spanda",
    "samsarga":             "spanda",         # also sambandha — keep in spanda (vibration/contact)
    "sparsha":              "spanda",

    # ── chetan/ — consciousness, awareness ────────────────────────────────
    "anveshana":            "chetan",
    "avahana":              "chetan",
    "dipaka":               "chetan",         # override: illumination is more chetan than pramana
    "sakshi-anubhava":      "chetan",         # if it exists at top level
    "vismaya-viraam":       "chetan",         # override: wonder-pause is chetan

    # ── jiva/ — living beings, self ───────────────────────────────────────
    "swa":                  "jiva",
    "swatantra":            "jiva",
    "seva":                 "jiva",
    "satta-yantra":         "jiva",
    "vrnda-ganita":         "jiva",

    # ── geometry/ — dimensions, frames ────────────────────────────────────
    "aayaama-dvaya":        "geometry",
    "aayaama-eka":          "geometry",
    "chala-apeksha":        "geometry",
    "sthira-apeksha":       "geometry",

    # ── parampara/ — lineage, sequence, opposition ────────────────────────
    "asparsha":             "parampara",
    "artha-viveka":         "parampara",
    "sparsha-rekha":        "parampara",
    "visarjana":            "parampara",
    "durgadha":             "parampara",

    # ── vak/ — speech, language roots ─────────────────────────────────────
    "anuvada":              "vak",
    "pratijnaa":            "vak",
    "vakya":                "vak",
    "pratishedha":          "vak",
    "vrnda-sakshi":         "vak",
    "asprishta-drishthanta": "vak",          # untouchable example → narrative

    # ── padartha/ — categories of reality ─────────────────────────────────
    "lekhana":              "padartha",
    "rashi":                "padartha",

    # ── mula/ — true roots (irreducible) ──────────────────────────────────
    "sthiti":               "mula",
    "phala":                "mula",
    "sankhya":              "mula",
    "purna-neti":           "mula",
    "abhaya":               "mula",
    "rachana":              "mula",
    "aayaama-vistara":      "mula",
    "antaraayaama":         "mula",
    "prashna-amsha":        "mula",

    # ── remaining ────────────────────────────────────────────────────────
    "asprista":             "parampara",      # abheda with asparsha
    "sphoTa":               "vak",            # sphota — meaning unit (file=sphoTa.om)
    "kaala":                "mula",           # time — fundamental root
    "matra":                "pramana",        # measure/mother → pramana family
}

# Remove duplicate assignments — last one wins, but let's be explicit about conflicts
# samsarga: listed in both sambandha and spanda — spanda wins (vibration/contact)
# dipaka: listed in both pramana and chetan — let's keep in pramana (illumination as means of knowing)
# vismaya-viraam: listed in both viraam and chetan — keep in viraam (it's a punctuation type)
MAPPING["samsarga"] = "spanda"
MAPPING["dipaka"] = "pramana"
MAPPING["vismaya-viraam"] = "viraam"


def plan():
    """Show what would be moved."""
    top_level_oms = []
    for f in sorted(os.listdir(SRC)):
        if f.endswith(".om") and os.path.isfile(os.path.join(SRC, f)):
            top_level_oms.append(f)

    moved = []
    stayed = []
    for f in top_level_oms:
        name = f[:-3]  # strip .om
        dest = MAPPING.get(name)
        if dest:
            moved.append((f, dest))
        else:
            stayed.append(f)

    print(f"\n  RESTRUCTURE PLAN: {len(top_level_oms)} top-level .om files\n")

    # Group by destination
    by_dest = {}
    for f, dest in moved:
        by_dest.setdefault(dest, []).append(f)

    print(f"  MOVING ({len(moved)} files):\n")
    for dest in sorted(by_dest.keys()):
        files = by_dest[dest]
        print(f"    → {dest}/ ({len(files)} files)")
        for f in sorted(files):
            print(f"      {f}")
    print()

    print(f"  STAYING AT TOP LEVEL ({len(stayed)} files):\n")
    for f in sorted(stayed):
        print(f"    {f}")
    print()

    # Check for unmapped non-sthalam files
    unmapped_non_sthalam = [
        f for f in stayed
        if not f.replace(".om", "").endswith("-sthalam")
        and f.replace(".om", "") not in ("visheshanam", "kaala", "matra", "spho")
    ]
    if unmapped_non_sthalam:
        print(f"  ⚠ UNMAPPED (not sthalam, not in mapping):")
        for f in unmapped_non_sthalam:
            print(f"    {f}")
        print()


def apply():
    """Copy sangati/ → sangati2/ with restructured layout."""
    if os.path.exists(DST):
        print(f"  Removing existing {DST}...")
        shutil.rmtree(DST)

    print(f"  Creating {DST}...")

    # Step 1: Copy entire directory tree
    shutil.copytree(SRC, DST)

    # Step 2: Move top-level files into sub-buckets
    moved_count = 0
    for f in sorted(os.listdir(DST)):
        if not f.endswith(".om") or not os.path.isfile(os.path.join(DST, f)):
            continue
        name = f[:-3]
        dest = MAPPING.get(name)
        if not dest:
            continue

        dest_dir = os.path.join(DST, dest)
        os.makedirs(dest_dir, exist_ok=True)

        src_file = os.path.join(DST, f)
        dst_file = os.path.join(DST, dest, f)

        if os.path.exists(dst_file):
            # File already exists in subdirectory (was already there from copytree)
            print(f"  SKIP {f} → {dest}/ (already exists)")
            os.remove(src_file)  # remove the top-level copy
        else:
            os.rename(src_file, dst_file)
            moved_count += 1

    print(f"\n  Moved {moved_count} files into sub-buckets.")

    # Step 3: Count final structure
    print(f"\n  FINAL STRUCTURE:")
    for d in sorted(os.listdir(DST)):
        full = os.path.join(DST, d)
        if os.path.isdir(full):
            count = len([f for f in os.listdir(full) if f.endswith(".om")])
            print(f"    {d:<25} {count:>3} files")
    top_count = len([f for f in os.listdir(DST) if f.endswith(".om") and os.path.isfile(os.path.join(DST, f))])
    print(f"    {'(top-level)':<25} {top_count:>3} files")
    print()


if __name__ == "__main__":
    if "--apply" in sys.argv:
        apply()
    else:
        plan()
