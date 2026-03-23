"""gates.py — Xfail gate classification.

Single source of truth for mapping xfail reasons to gate names.
"""

# keyword → (gate_name, description)
GATE_KEYWORDS = {
    "dvandva": ("dvandva", "dvandva: per-entity instance-map"),
    "inverse-math": ("inverse_math", "inverse-math: bound-vals / invert-math path"),
    "invert-math": ("inverse_math", "inverse-math: bound-vals / invert-math path"),
    "bound-vals": ("inverse_math", "inverse-math: bound-vals / invert-math path"),
    "sthita-viveka": ("sthita_viveka", "sthita-viveka: multi-slot entity assignment"),
    "gravitational": ("sthita_viveka", "sthita-viveka: multi-slot entity assignment"),
    "coulomb": ("sthita_viveka", "sthita-viveka: multi-slot entity assignment"),
    "motion verb": ("motion_verb", "kosha: missing concept node"),
    "moves at": ("motion_verb", "kosha: missing concept node"),
    "moving at": ("motion_verb", "kosha: missing concept node"),
    "trigram": ("compound_trigram", "sandhi-kosha only handles bigrams"),
    "three-word": ("compound_trigram", "sandhi-kosha only handles bigrams"),
    "from rest": ("from_rest", "parsing: natural phrasing not handled"),
    "total kinetic": ("total_compound", "'total' resolves to count via shabda alias"),
    "total' still": ("total_compound", "'total' resolves to count via shabda alias"),
    "colour": ("colour_classifier", "colour classifiers not treated as entity discriminators"),
    "classifier": ("colour_classifier", "colour classifiers not treated as entity discriminators"),
    "article": ("article", "parsing: article before entity name"),
    "'the'": ("article", "parsing: article before entity name"),
    "relative-velocity": ("relative_velocity", "relative-velocity: kosha concept missing"),
    "compute-then-compare": ("compute_compare", "viveka: compute-then-compare not built"),
    "compute then compare": ("compute_compare", "viveka: compute-then-compare not built"),
    "transitiv": ("transitive", "logic_nyaya: P8d anumana not built"),
    "syllogism": ("syllogism", "logic_nyaya: P8d anumana not built"),
    "modus-ponens": ("syllogism", "logic_nyaya: P8d anumana not built"),
    "count addition": ("arithmetic", "arithmetic: plain count not in pipeline"),
    "count subtraction": ("arithmetic", "arithmetic: plain count not in pipeline"),
    "plain count": ("arithmetic", "arithmetic: plain count not in pipeline"),
    "distance = speed": ("arithmetic", "arithmetic: plain count not in pipeline"),
    "area =": ("arithmetic", "arithmetic: plain count not in pipeline"),
    "proportional": ("proportional", "viveka: proportional reasoning"),
    "sentence_scope": ("sentence_scope", "sentence_scope: grade-sparsha sentence-local binding"),
    "dvandva_count": ("dvandva_count", "dvandva_count: multiple numbers in one sentence summed"),
    "entity_scope": ("entity_scope", "entity_scope: per-entity scoped count"),
    "multi_question": ("multi_question", "multi_question: multiple questions in one paragraph"),
    "multiplication": ("multiplication", "multiplication: 'each' triggers multiply"),
    "count_compare": ("count_compare", "count_compare: count then viveka comparison"),
    "long_chain": ("long_chain", "long_chain: 4+ grade count chains"),
}


def gate_from_reason(reason):
    lower = reason.lower()
    for keyword, (gate, _) in GATE_KEYWORDS.items():
        if keyword.lower() in lower:
            return gate
    return "other"


def description_from_reason(reason):
    lower = reason.lower()
    for keyword, (_, desc) in GATE_KEYWORDS.items():
        if keyword.lower() in lower:
            return desc
    return ""
