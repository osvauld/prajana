#!/usr/bin/env python3
"""
pada_viveka.py — word-class discrimination for unknown words.

pada   (Sanskrit) = word, foot, step — the unit of grammatical form.
viveka (Sanskrit) = discrimination, discernment — seeing what IS from what IS NOT.

pada-viveka: given a word the graph does not know, determine what KIND of thing
it is — verb, noun, proper noun, adjective, number-like, unit-like — so the
right inference path can be taken.

This is the bhasha layer of anveshana.
Before searching externally, we ask: what does the SHAPE of this word tell us?

PADA CLASSIFICATION (aligned to Sanskrit grammar categories):

  TINANTA  — verbal form (finite verb). English: -ing, -ed, -tion, -ate, -ify, -ize
             graph role: kriya (action). seek: does a process/action node exist?
             example: "accelerating", "ionized", "transforms"

  SUBANTA  — nominal form (noun/noun phrase). English: -ness, -ity, -ment, -ance, -er
             or known physics/chemistry/biology patterns.
             graph role: kosha concept. seek: is there a concept node? add as mithya→satya candidate.
             example: "resistance", "momentum", "conductance"

  VISHESHANA — adjectival/qualifying form. English: -al, -ous, -ic, -ive, -able, -ful
             graph role: vishesa (qualifier). attach to preceding noun.
             example: "thermal", "magnetic", "relativistic"

  SANKHYA  — number or numeric-adjacent. starts with digit, or known numeric suffix.
             graph role: asprista-sankhya → will bind to preceding concept.
             example: "9.8e-31", "1.67×10⁻²⁷", "0.511"

  MATRA    — unit-like. known SI prefix + unit pattern, or ends in known unit suffix.
             graph role: matra. seek: is there a unit node?
             example: "MeV", "km/s", "kg⋅m/s²"

  NAAMA    — proper noun (named entity). capitalized, or follows known entity signals.
             graph role: prathama-vibhakti (first case — subject/entity).
             no kosha lookup needed — it IS the entity, not a concept.
             example: "electron", "ball-A", "proton", "Earth"

  AVYAYA   — indeclinable / particle. connecting words with no independent meaning.
             graph role: ignore or use as grammatical signal.
             example: "the", "of", "with", "by"

  ASPRISTA — truly unknown. none of the above patterns match.
             graph role: mithya → survives fixpoint as asprista.
             anveshana must seek externally.

CONFIDENCE SCORES:
  Each classification comes with a confidence (0.0-1.0).
  Multiple classifications are possible (e.g. "running" could be TINANTA or SUBANTA).
  The highest-confidence one is primary; others are alternatives.

CROSS-REFERENCES:
  When a word is classified, pada_viveka also suggests:
  - which bhasha node to attach it to (e.g. TINANTA → tinanta node)
  - which graph edge to emit (e.g. VISHESHANA → vishesa edge)
  - which anveshana source to try (e.g. SUBANTA → kosha lookup first)
  - what the graph should do if not found (e.g. NAAMA → create entity node)
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ── pada categories ───────────────────────────────────────────────────────────

TINANTA = "tinanta"  # verbal
SUBANTA = "subanta"  # nominal
VISHESHANA = "visheshana"  # adjectival
SANKHYA = "sankhya"  # numeric
MATRA = "matra"  # unit
NAAMA = "naama"  # proper noun / entity
AVYAYA = "avyaya"  # indeclinable / particle
ASPRISTA = "asprista"  # truly unknown


@dataclass
class PadaResult:
    """
    The result of pada-viveka: what a word is and what to do with it.
    """

    word: str
    pada: str  # primary classification
    confidence: float  # 0.0-1.0
    alternatives: list  # [(pada, confidence), ...]
    graph_edge: str  # which edge to emit: satya/mithya/vishesa/matra/sankhya
    graph_role: str  # philosophical role in the graph
    seek_source: list[str]  # which anveshana sources to try, in order
    graph_action: str  # what to do: lookup / create-entity / attach / ignore
    bhasha_node: str  # which bhasha node to reference
    reason: str  # why this classification

    def __repr__(self):
        return (
            f"<pada:{self.pada} conf={self.confidence:.2f} "
            f"edge={self.graph_edge} action={self.graph_action}>"
        )


# ── suffix tables (English morphology → pada) ─────────────────────────────────

# TINANTA suffixes — verbal forms
TINANTA_SUFFIXES = [
    # gerunds / present participles → high confidence verbal
    (r"ing$", 0.70, "present-participle or gerund"),
    # past participles / adjectives from verbs
    (r"(ated|ized|ified|ised|ified|ened|ened)$", 0.75, "verbal past form"),
    # infinitive markers (process/action words)
    (r"(ate|ify|ize|ise|fy)$", 0.65, "verbal infinitive pattern"),
    # nominalised actions (borderline tinanta/subanta)
    (r"(ation|ition|sion|tion|xion)$", 0.55, "nominalised action"),
]

# SUBANTA suffixes — nominal forms
SUBANTA_SUFFIXES = [
    (
        r"(ness|ity|ment|ance|ence|age|hood|ship|dom|ism|ist|ics|ology|ometry|onomy|physics|chemistry|biology)$",
        0.80,
        "abstract noun suffix",
    ),
    (r"(er|or|eur|ant|ent|ee|eer)$", 0.65, "agent/patient noun"),
    (
        r"(ium|ion|ine|ene|ane|yne|ide|ate|ite|ite|ase|ose|osis|itis)$",
        0.75,
        "chemical/biological noun",
    ),
    # physics/science compound nouns
    (
        r"(energy|force|mass|velocity|momentum|pressure|temperature|current|voltage|resistance|"
        r"frequency|wavelength|amplitude|density|entropy|enthalpy|flux|field|charge|spin|"
        r"potential|power|work|heat|torque|acceleration|displacement|position|speed)$",
        0.90,
        "physics concept noun",
    ),
    # math nouns
    (
        r"(matrix|vector|tensor|scalar|gradient|divergence|curl|integral|derivative|"
        r"eigenvalue|eigenvector|determinant|polynomial|function|sequence|series|limit|"
        r"permutation|combination|probability|distribution|variance|deviation)$",
        0.90,
        "mathematics concept noun",
    ),
]

# VISHESHANA suffixes — adjectival forms
VISHESHANA_SUFFIXES = [
    (r"(al|ial|ical|ional|onal|ual|ral)$", 0.70, "adjectival -al suffix"),
    (r"(ous|ious|eous|uous)$", 0.75, "adjectival -ous suffix"),
    (r"(ic|tic|ric|stic)$", 0.70, "adjectival -ic suffix"),
    (r"(ive|ative|itive|sive)$", 0.65, "adjectival -ive suffix"),
    (r"(able|ible|uble)$", 0.70, "adjectival -able suffix"),
    (r"(ful|less|like|ward|wise|most)$", 0.70, "adjectival suffix"),
    (r"(ar|lar|iar|ular|icular)$", 0.60, "adjectival -ar suffix"),
    # relativistic, quantum, classical, thermal, etc.
    (
        r"(relativistic|quantum|classical|thermal|mechanical|electrical|magnetic|"
        r"gravitational|nuclear|atomic|molecular|optical|acoustic|elastic|plastic|"
        r"kinetic|potential|angular|linear|circular|rotational|translational)$",
        0.90,
        "physics adjective",
    ),
]

# MATRA patterns — unit-like forms
MATRA_PATTERNS = [
    # SI units and common physics units
    (
        r"^(m|kg|s|A|K|mol|cd|N|J|W|Pa|Hz|V|Ω|F|C|T|H|lm|lx|Bq|Gy|Sv|kat)$",
        0.95,
        "SI base or derived unit",
    ),
    # unit with SI prefix
    (
        r"^(Y|Z|E|P|T|G|M|k|h|da|d|c|m|μ|n|p|f|a|z|y)"
        r"(m|g|s|A|K|mol|cd|N|J|W|Pa|Hz|V|Ω|F|C|T|H|eV|cal|bar|atm|L|b|B)$",
        0.90,
        "SI prefix + unit",
    ),
    # eV and multiples (particle physics)
    (r"^(k|M|G|T)?eV$", 0.95, "electron-volt unit"),
    # compound units
    (r"[/⋅·]", 0.75, "compound unit (contains / or ⋅)"),
    # ends in known unit abbreviation
    (r"(m|s|g|J|N|W|K|Hz|V|A|Pa|mol|rad|sr)$", 0.60, "ends in unit abbreviation"),
    # common non-SI
    (
        r"^(cal|kcal|BTU|hp|mph|kph|rpm|ppm|ppb|atm|bar|torr|mmHg|in|ft|yd|mi|oz|lb|gal|fl)$",
        0.85,
        "common non-SI unit",
    ),
]

# SANKHYA patterns — numeric forms
SANKHYA_PATTERNS = [
    (r"^\d", 0.95, "starts with digit"),
    (r"^[+-]?\d", 0.95, "signed number"),
    (r"^\d+[.,]\d+$", 0.98, "decimal number"),
    (r"^\d+[eE][+-]?\d+$", 0.98, "scientific notation"),
    (r"^[0-9]+$", 0.99, "integer"),
    # fractions
    (r"^\d+/\d+$", 0.95, "fraction"),
    # unicode superscripts (exponents)
    (r"[⁰¹²³⁴⁵⁶⁷⁸⁹]", 0.80, "contains superscript digit"),
    # number words
    (
        r"^(zero|one|two|three|four|five|six|seven|eight|nine|ten|"
        r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
        r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|"
        r"hundred|thousand|million|billion|trillion|"
        r"half|quarter|third|fourth|fifth)$",
        0.90,
        "number word",
    ),
]

# NAAMA patterns — proper noun / entity patterns
NAAMA_PATTERNS = [
    # starts with capital letter (after first word in sentence)
    # handled in context-aware classification
    # hyphenated labels: ball-A, particle-1, entity-X
    (r"^[a-zA-Z]+-[A-Z0-9]+$", 0.85, "entity label with suffix"),
    # Greek letter names (particle physics)
    (
        r"^(alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|"
        r"omicron|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega|"
        r"Alpha|Beta|Gamma|Delta|Epsilon|Zeta|Eta|Theta|Iota|Kappa|Lambda|Mu|Nu|Xi|"
        r"Omicron|Pi|Rho|Sigma|Tau|Upsilon|Phi|Chi|Psi|Omega)$",
        0.90,
        "Greek letter name — likely particle/entity",
    ),
    # particle names
    (
        r"^(electron|proton|neutron|photon|muon|tauon|neutrino|quark|gluon|boson|"
        r"fermion|lepton|baryon|meson|hadron|positron|antiproton|pion|kaon)$",
        0.95,
        "known particle name",
    ),
    # element names and symbols
    (
        r"^(hydrogen|helium|lithium|beryllium|boron|carbon|nitrogen|oxygen|fluorine|neon|"
        r"sodium|magnesium|aluminium|silicon|phosphorus|sulfur|chlorine|argon|potassium|"
        r"calcium|iron|copper|zinc|silver|gold|platinum|lead|mercury|uranium|plutonium)$",
        0.92,
        "chemical element name",
    ),
    # element symbols (1-2 capital letters)
    (r"^[A-Z][a-z]?$", 0.70, "possible element symbol"),
    # celestial bodies
    (
        r"^(Sun|Moon|Earth|Mars|Venus|Jupiter|Saturn|Uranus|Neptune|Mercury|Pluto|"
        r"Milky Way|Andromeda|Alpha Centauri)$",
        0.92,
        "celestial body",
    ),
]

# AVYAYA words — indeclinables (always ignore in graph construction)
AVYAYA_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "nor",
        "yet",
        "so",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "by",
        "from",
        "with",
        "as",
        "if",
        "then",
        "when",
        "where",
        "which",
        "that",
        "who",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "am",
        "has",
        "have",
        "had",
        "do",
        "does",
        "did",
        "its",
        "their",
        "his",
        "her",
        "our",
        "your",
        "my",
        "it",
        "they",
        "he",
        "she",
        "we",
        "you",
        "i",
        "not",
        "no",
        "yes",
        "also",
        "both",
        "either",
        "each",
        "between",
        "among",
        "through",
        "over",
        "under",
        "above",
        "below",
        "into",
        "onto",
        "upon",
        "about",
        "around",
        "along",
        "given",
        "such",
        "same",
        "other",
        "another",
        "some",
        "any",
        "all",
        "both",
        "many",
        "much",
        "more",
        "most",
        "less",
        "fewer",
        "what",
        "how",
        "why",
        "who",
        "whose",
        "whom",
        # vidhi-kaala / intent words — graph signals, not unknown words
        "find",
        "calculate",
        "compute",
        "determine",
        "solve",
        "evaluate",
        "show",
        "derive",
        "prove",
        "verify",
        "check",
        # common connecting / modifier words that look unknown
        "rest",
        "total",
        "net",
        "final",
        "initial",
        "average",
        "maximum",
        "minimum",
        "using",
        "let",
        "hence",
    }
)


# ── graph action and source mapping ───────────────────────────────────────────

PADA_TO_GRAPH = {
    TINANTA: {
        "edge": "satya",  # if found: satya edge to kriya node
        "role": "kriya",  # philosophical role
        "action": "lookup-kriya",  # look for a kriya/process node
        "source": ["graph", "transliteration", "user"],
        "bhasha": "tinanta",
    },
    SUBANTA: {
        "edge": "mithya",  # start as mithya, resolve to satya
        "role": "naama",  # noun role
        "action": "lookup",  # standard kosha lookup
        "source": ["graph", "transliteration", "sanskrit", "wikipedia"],
        "bhasha": "subanta",
    },
    VISHESHANA: {
        "edge": "vishesa",  # qualifier edge
        "role": "visheshana",
        "action": "attach-vishesa",  # attach to preceding noun as vishesa
        "source": ["graph", "transliteration"],
        "bhasha": "visheshana",
    },
    SANKHYA: {
        "edge": "asprista-sankhya",  # unattached number
        "role": "sankhya",
        "action": "bind-number",  # sankhya-bandha will pick it up
        "source": [],  # no external lookup needed — it IS a number
        "bhasha": "sankhya",
    },
    MATRA: {
        "edge": "matra",  # unit edge
        "role": "matra",
        "action": "lookup-unit",  # look for unit node
        "source": ["graph", "si-units"],
        "bhasha": "matra",
    },
    NAAMA: {
        "edge": "prathama-vibhakti",  # entity (first case)
        "role": "naama",  # proper noun / entity
        "action": "create-entity",  # create entity node if not found
        "source": ["graph", "wikidata", "user"],
        "bhasha": "naama",
    },
    AVYAYA: {
        "edge": "",  # no edge needed
        "role": "avyaya",
        "action": "ignore",
        "source": [],
        "bhasha": "avyaya",
    },
    ASPRISTA: {
        "edge": "mithya",  # survives as mithya → asprista
        "role": "asprista",
        "action": "anveshana",  # full external search
        "source": ["transliteration", "graph", "sanskrit", "wikipedia", "user"],
        "bhasha": "",
    },
}


# ── main classifier ───────────────────────────────────────────────────────────


def classify(
    word: str,
    position: int = 0,
    prev_word: str = "",
    is_capitalized_mid_sentence: bool = False,
) -> PadaResult:
    """
    Classify a single word by shape, position, and context.

    word:        the surface word to classify
    position:    position in sentence (0 = first word)
    prev_word:   the word immediately before (for context)
    is_capitalized_mid_sentence: True if word is capitalized and not sentence-first
    """
    w = word.strip()
    wl = w.lower()

    # ── 0. empty ──────────────────────────────────────────────────────────────
    if not w:
        return _make(w, ASPRISTA, 0.0, [], "empty word")

    # ── 1. avyaya: particles/indeclinables ────────────────────────────────────
    if wl in AVYAYA_WORDS:
        return _make(w, AVYAYA, 1.0, [], f"known particle word: {wl}")

    # ── 1b. hyphenated entity labels: ball-A, particle-1, entity-X ──────────
    # check BEFORE matra to prevent "ball-A" hitting element symbol pattern
    if re.match(r"^[a-zA-Z][a-zA-Z0-9]*-[A-Z0-9]+$", w):
        return _make(w, NAAMA, 0.88, [], "hyphenated entity label (word-SUFFIX)")

    # ── 2. sankhya: numeric ───────────────────────────────────────────────────
    scores = []
    for pattern, conf, reason in SANKHYA_PATTERNS:
        if re.search(pattern, wl, re.IGNORECASE):
            scores.append((SANKHYA, conf, reason))
    if scores:
        best = max(scores, key=lambda x: x[1])
        alts = [(p, c) for p, c, _ in scores if (p, c) != (best[0], best[1])]
        return _make(w, best[0], best[1], alts, best[2])

    # ── 3. matra: unit ────────────────────────────────────────────────────────
    # only run matra if word is SHORT (<=6 chars) or contains unit-separator chars.
    # this prevents long words like "accelerating" from matching the trailing-g pattern.
    is_unit_candidate = (
        len(w) <= 6 or re.search(r"[/⋅·^]", w) or re.match(r"^[A-Z]", w)
    )  # units often start with capital
    scores = []
    if is_unit_candidate:
        for pattern, conf, reason in MATRA_PATTERNS:
            if re.search(pattern, w):  # case-sensitive for units
                scores.append((MATRA, conf, reason))
    if scores:
        best = max(scores, key=lambda x: x[1])
        alts = [(p, c) for p, c, _ in scores if (p, c) != (best[0], best[1])]
        return _make(w, best[0], best[1], alts, best[2])

    # ── 4. naama: proper noun / entity ────────────────────────────────────────
    naama_scores = []
    for pattern, conf, reason in NAAMA_PATTERNS:
        if re.search(pattern, w, re.IGNORECASE):
            naama_scores.append((NAAMA, conf, reason))
    # capitalized mid-sentence = strong proper noun signal
    if is_capitalized_mid_sentence and w[0].isupper() and position > 0:
        naama_scores.append((NAAMA, 0.80, "capitalized mid-sentence"))
    # hyphenated entity labels: ball-A, particle-1
    if re.match(r"^[a-zA-Z]+-[A-Z0-9]+$", w):
        naama_scores.append((NAAMA, 0.88, "hyphenated entity label"))

    # ── 5. morphological analysis: tinanta / subanta / visheshana ────────────
    morph_scores = []

    for pattern, conf, reason in TINANTA_SUFFIXES:
        if re.search(pattern, wl):
            morph_scores.append((TINANTA, conf, reason))

    for pattern, conf, reason in SUBANTA_SUFFIXES:
        if re.search(pattern, wl):
            morph_scores.append((SUBANTA, conf, reason))

    for pattern, conf, reason in VISHESHANA_SUFFIXES:
        if re.search(pattern, wl):
            morph_scores.append((VISHESHANA, conf, reason))

    # ── 6. combine all scores and pick best ───────────────────────────────────
    all_scores = naama_scores + morph_scores

    if not all_scores:
        # no pattern matched — truly asprista
        return _make(w, ASPRISTA, 0.3, [], "no morphological pattern matched")

    # sort by confidence
    all_scores.sort(key=lambda x: x[1], reverse=True)
    best_pada, best_conf, best_reason = all_scores[0]

    # build alternatives (different pada with lower confidence)
    seen = {best_pada}
    alts = []
    for pada, conf, _ in all_scores[1:]:
        if pada not in seen:
            alts.append((pada, conf))
            seen.add(pada)

    return _make(w, best_pada, best_conf, alts, best_reason)


def _make(word: str, pada: str, conf: float, alts: list, reason: str) -> PadaResult:
    g = PADA_TO_GRAPH[pada]
    return PadaResult(
        word=word,
        pada=pada,
        confidence=conf,
        alternatives=alts,
        graph_edge=g["edge"],
        graph_role=g["role"],
        seek_source=g["source"],
        graph_action=g["action"],
        bhasha_node=g["bhasha"],
        reason=reason,
    )


# ── sentence-level classifier ─────────────────────────────────────────────────


def classify_sentence(words: list[str]) -> list[PadaResult]:
    """
    Classify all words in a sentence with positional context.
    First word is never classified as NAAMA based on capitalization alone.
    """
    results = []
    for i, word in enumerate(words):
        is_cap_mid = bool(i > 0 and word and word[0].isupper())
        prev = words[i - 1] if i > 0 else ""
        result = classify(
            word, position=i, prev_word=prev, is_capitalized_mid_sentence=is_cap_mid
        )
        results.append(result)
    return results


def classify_unknown_words(words: list[str], known_nodes: set) -> list[PadaResult]:
    """
    Only classify words that are NOT already known to the graph.
    known_nodes: set of node names the graph already has (from lookup).
    """
    unknown = [
        w for w in words if w.lower() not in known_nodes and w not in known_nodes
    ]
    return classify_sentence(unknown)


# ── report: what to do with each pada ─────────────────────────────────────────


def explain(result: PadaResult) -> str:
    """Human-readable explanation of what to do with a classified word."""
    lines = [
        f"word:       {result.word!r}",
        f"pada:       {result.pada}  (confidence: {result.confidence:.0%})",
        f"reason:     {result.reason}",
        f"graph edge: {result.graph_edge or '(none)'}",
        f"role:       {result.graph_role}",
        f"action:     {result.graph_action}",
        f"seek:       {result.seek_source}",
    ]
    if result.alternatives:
        alts = ", ".join(f"{p}({c:.0%})" for p, c in result.alternatives[:3])
        lines.append(f"alternatives: {alts}")

    # philosophical note
    notes = {
        TINANTA: "tinanta = finite verb. the action. seek a kriya node.",
        SUBANTA: "subanta = nominal. the thing. seek a kosha concept node.",
        VISHESHANA: "visheshana = qualifier. attaches as vishesa to the preceding noun.",
        SANKHYA: "sankhya = number. sankhya-bandha will bind it to the preceding concept.",
        MATRA: "matra = unit. the measure. seek a unit node in the kosha.",
        NAAMA: "naama = proper noun. the named entity. prathama-vibhakti in the graph.",
        AVYAYA: "avyaya = particle. grammatical glue. no graph node needed.",
        ASPRISTA: "asprista = untouched. the graph does not know this. anveshana must seek.",
    }
    lines.append(f"note:       {notes.get(result.pada, '')}")
    return "\n  ".join(lines)


# ── quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_words = [
        # verbs
        "accelerating",
        "ionized",
        "transforms",
        "oscillates",
        # nouns (physics)
        "resistance",
        "momentum",
        "conductance",
        "kinetic-energy",
        # adjectives
        "relativistic",
        "thermal",
        "magnetic",
        "quantum",
        # units
        "MeV",
        "kg",
        "km/s",
        "kJ/mol",
        # numbers
        "9.8",
        "0.511",
        "1.67e-27",
        "three",
        # proper nouns
        "electron",
        "proton",
        "ball-A",
        "Alpha",
        # particles
        "the",
        "of",
        "and",
        "given",
        # truly unknown
        "zhabotinsky",
        "kolmogorov",
        "feigenbaum",
        # Malayalam/Sanskrit words
        "spanda",
        "avrti",
        "pramana",
    ]

    print("pada-viveka: word-class discrimination")
    print("=" * 60)
    for word in test_words:
        r = classify(word)
        print(f"\n  {explain(r)}")
