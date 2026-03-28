"""gen_grammar.py — Generate inflected word→node shabda entries.

Reads existing shabda word: entries, generates English inflections
(plurals, verb tenses, participles), writes them as additional word:
values on the same shabda node.

No hardcoded word lists — reads the graph to find base forms, then
applies regular English morphology. Irregular forms from a small table.

Output: appends to bhasha-english.shabda (reverse index entries).
"""

import os
import re
from collections import defaultdict

from upakarana.paths import BRAHMAN
from upakarana.parsers.shabda import load_all


# ── irregular tables ─────────────────────────────────────────────────────────

IRREGULAR_VERBS = {
    # base: (past, past_participle, present_participle)
    "be": ("was", "been", "being"),
    "have": ("had", "had", "having"),
    "do": ("did", "done", "doing"),
    "go": ("went", "gone", "going"),
    "drive": ("drove", "driven", "driving"),
    "fall": ("fell", "fallen", "falling"),
    "give": ("gave", "given", "giving"),
    "take": ("took", "taken", "taking"),
    "break": ("broke", "broken", "breaking"),
    "run": ("ran", "run", "running"),
    "see": ("saw", "seen", "seeing"),
    "know": ("knew", "known", "knowing"),
    "grow": ("grew", "grown", "growing"),
    "fly": ("flew", "flown", "flying"),
    "draw": ("drew", "drawn", "drawing"),
    "rise": ("rose", "risen", "rising"),
    "spin": ("spun", "spun", "spinning"),
    "slide": ("slid", "slid", "sliding"),
}

IRREGULAR_PLURALS = {
    "mouse": "mice",
    "vertex": "vertices",
    "matrix": "matrices",
    "index": "indices",
    "radius": "radii",
    "focus": "foci",
    "axis": "axes",
    "basis": "bases",
    "analysis": "analyses",
    "hypothesis": "hypotheses",
    "thesis": "theses",
    "datum": "data",
    "medium": "media",
    "spectrum": "spectra",
    "phenomenon": "phenomena",
    "criterion": "criteria",
}

# words that are already plural or uncountable — skip
SKIP_PLURAL = {
    "data", "media", "spectra", "phenomena", "criteria",
    "physics", "mathematics", "dynamics", "statistics",
    "momentum", "information", "evidence", "knowledge",
}


# ── morphology rules ─────────────────────────────────────────────────────────

def pluralize(word):
    """Regular English plural."""
    if word in IRREGULAR_PLURALS:
        return IRREGULAR_PLURALS[word]
    if word in SKIP_PLURAL:
        return None
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    if word.endswith("f"):
        return word[:-1] + "ves"
    if word.endswith("fe"):
        return word[:-2] + "ves"
    return word + "s"


def verb_inflections(base):
    """Generate verb forms: 3rd person singular, past, present participle."""
    if base in IRREGULAR_VERBS:
        past, pp, ing = IRREGULAR_VERBS[base]
        # 3rd person: base + s (even irregular)
        if base == "have":
            s3 = "has"
        elif base == "be":
            s3 = "is"
        elif base == "do":
            s3 = "does"
        elif base == "go":
            s3 = "goes"
        else:
            s3 = _third_person(base)
        return {"3sg": s3, "past": past, "pp": pp, "ing": ing}

    s3 = _third_person(base)

    # -ing form
    if base.endswith("e") and not base.endswith("ee"):
        ing = base[:-1] + "ing"
    elif (len(base) >= 3 and base[-1] not in "aeiouwxy"
          and base[-2] in "aeiou" and base[-3] not in "aeiou"):
        ing = base + base[-1] + "ing"  # run→running, stop→stopping
    else:
        ing = base + "ing"

    # past tense
    if base.endswith("e"):
        past = base + "d"
    elif base.endswith("y") and len(base) > 1 and base[-2] not in "aeiou":
        past = base[:-1] + "ied"
    elif (len(base) >= 3 and base[-1] not in "aeiouwxy"
          and base[-2] in "aeiou" and base[-3] not in "aeiou"):
        past = base + base[-1] + "ed"  # stop→stopped
    else:
        past = base + "ed"

    return {"3sg": s3, "past": past, "pp": past, "ing": ing}


def _third_person(base):
    if base.endswith(("s", "x", "z", "ch", "sh")):
        return base + "es"
    if base.endswith("y") and len(base) > 1 and base[-2] not in "aeiou":
        return base[:-1] + "ies"
    if base.endswith("o"):
        return base + "es"
    return base + "s"


# ── classification ───────────────────────────────────────────────────────────

# Words that are verbs (action words that should get tense inflections)
VERB_INDICATORS = {
    "accelerate", "move", "travel", "apply", "rotate", "oscillate",
    "collide", "compress", "expand", "conduct", "radiate", "absorb",
    "reflect", "refract", "diffract", "transfer", "transform",
    "conserve", "converge", "diverge", "belong", "contain",
    "generate", "compute", "derive", "measure", "observe",
    "flow", "decay", "emit", "scatter",
}


def is_verb_candidate(word):
    """Check if a word looks like it could be a verb stem."""
    return word in VERB_INDICATORS or word.endswith(("ate", "ize", "ify"))


# ── generator ────────────────────────────────────────────────────────────────

def generate(dry_run=False):
    """Generate inflected word entries from existing shabda."""
    all_shabda = load_all()

    # Collect base word → node_name mappings
    # Track nodes with eval: entries — never overwrite these
    eval_nodes = {name for name, entry in all_shabda.items()
                  if "eval" in entry["fields"] or "arity" in entry["fields"]}

    base_words = {}  # word → node_name
    for name, entry in all_shabda.items():
        # Skip grammar/meta nodes
        if name.startswith(("verb-", "conj-", "prep-", "qword-", "tense-",
                            "article-", "sandhi-")):
            continue
        # Skip nodes with eval/arity — these have operational shabda we must not overwrite
        if name in eval_nodes:
            continue

        word_val = entry["fields"].get("word", "")
        if isinstance(word_val, list):
            words = word_val
        else:
            words = [w.strip() for w in word_val.split(",") if w.strip()]

        # Skip nodes with too many word entries (meta/semantic nodes)
        if len(words) > 6:
            continue

        for w in words:
            w = w.strip().lower()
            # Skip short words, non-alpha, already-inflected forms
            if len(w) < 3 or not w.isalpha():
                continue
            if w.endswith(("ed", "ing")) and len(w) > 5:
                continue  # already inflected
            if w != w.rstrip("s") and w.endswith("s") and not w.endswith("ss"):
                # already plural (forces, masses) — but keep base forms like "gas"
                if len(w) > 4:
                    continue
            base_words[w] = name

    print(f"  {len(base_words)} base words from shabda")

    # Generate inflections
    new_entries = defaultdict(set)  # node_name → set of new words

    for word, node_name in sorted(base_words.items()):
        # Plural only — verb inflections (-ed/-ing) handled by suffix rules
        # in shabda-anveshana, not by word: entries (which would conflict with
        # emit-triples is-verb-form check)
        plural = pluralize(word)
        if plural and plural != word and plural not in base_words:
            new_entries[node_name].add(plural)

        # Only add 3rd person -s (not -ed/-ing) for verb candidates
        if is_verb_candidate(word):
            forms = verb_inflections(word)
            s3 = forms.get("3sg")
            if s3 and s3 != word and s3 not in base_words:
                new_entries[node_name].add(s3)

    # Phase 2: inflect plain English node names that have no word: entry
    all_nodes = load_all()  # shabda
    from upakarana.parsers.om5 import load_all as load_om5
    om_nodes = load_om5()

    for name in sorted(om_nodes):
        # Skip nodes that already have word: entries (handled in phase 1)
        if name in base_words.values():
            continue
        # Skip nodes with eval/arity — must not overwrite
        if name in eval_nodes:
            continue
        # Skip non-English names (hyphenated, short)
        if "-" in name or len(name) < 4 or not name.isalpha() or not name.islower():
            continue
        # Skip if name is already a known base word
        if name in base_words:
            continue
        # Skip Sanskrit/domain names — check if it's a real English word
        # Heuristic: if node is in sangati layer, it's likely Sanskrit
        node_info = om_nodes[name]
        if node_info.get("layer") == "sangati":
            continue

        # Noun plural from node name
        plural = pluralize(name)
        if plural and plural != name and plural not in base_words:
            new_entries[name].add(plural)

        # Back-formation: -ation → -ate verb stem + 3rd person -s only
        # -ed/-ing handled by suffix rules in shabda-anveshana
        if name.endswith("ation") and len(name) > 7:
            verb_stem = name[:-5] + "ate"  # acceleration → accelerate
            if verb_stem not in base_words:
                new_entries[name].add(verb_stem)
            s3 = _third_person(verb_stem)
            if s3 not in base_words:
                new_entries[name].add(s3)

        # Back-formation: -ment → verb stem + 3rd person only
        if name.endswith("ment") and len(name) > 6:
            verb_stem = name[:-4]  # displacement → displace
            if verb_stem not in base_words:
                new_entries[name].add(verb_stem)
            s3 = _third_person(verb_stem)
            if s3 not in base_words:
                new_entries[name].add(s3)

    # Count
    total_new = sum(len(v) for v in new_entries.values())
    print(f"  {total_new} new inflected forms across {len(new_entries)} nodes")

    if dry_run:
        for node, words in sorted(new_entries.items()):
            print(f"    {node}: +{sorted(words)}")
        return new_entries

    # Write to shabda file
    out_path = os.path.join(str(BRAHMAN), "shabda", "grammar-inflections.shabda")
    lines = [
        "# grammar-inflections.shabda — auto-generated inflected word forms",
        f"# {total_new} entries across {len(new_entries)} nodes",
        "",
    ]

    for node_name in sorted(new_entries):
        words = sorted(new_entries[node_name])
        # space-separated (no commas) — OCaml tokenizer splits on whitespace,
        # then rejoins with commas internally. Commas in source cause double-comma bug.
        word_str = " ".join(words)
        lines.append(f"shabda {node_name}")
        lines.append(f"  (word {word_str})")
        lines.append("done")
        lines.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(lines))

    print(f"  written to {out_path}")
    return new_entries


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    generate(dry_run=dry)
