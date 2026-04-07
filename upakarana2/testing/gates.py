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
    "compound word": ("compound_word", "compound_word: multi-word concept missing word: mapping"),
    "compound_word": ("compound_word", "compound_word: multi-word concept missing word: mapping"),
    "negation": ("negation", "negation: pratishedha / double-negation logic"),
    "pratishedha": ("negation", "negation: pratishedha / double-negation logic"),
    "disjunctive": ("disjunctive", "disjunctive: disjunctive syllogism"),
    "conditional chain": ("conditional_chain", "conditional_chain: chained implications"),
    "quantifier": ("quantifier", "quantifier: universal/existential with exception"),
    "tense": ("tense", "tense: past/future temporal handling"),
    "rashi": ("rashi", "rashi: symbolic variable names"),
    "graph primitive": ("graph_primitive", "graph_primitive: node-satya / register-dimension return type"),
    "node-satya": ("graph_primitive", "graph_primitive: node-satya / register-dimension return type"),
    "register-dimension": ("graph_primitive", "graph_primitive: node-satya / register-dimension return type"),
    "unit parse": ("unit_parse", "unit_parse: unit words in natural language"),
    "chain inverse": ("chain_inverse", "chain_inverse: multi-step inverse solve"),
    "sandhi grammar": ("sandhi_grammar", "sandhi_grammar: grammar word promotion in sandhi-viveka"),
    "math_L0_arithmetic": ("math_L0_arithmetic", "math_L0: natural phrasing of basic operations"),
    "math_L0_number": ("math_L0_number", "math_L0: sign, absolute value, mod, floor/ceil, negatives"),
    "math_L1_coordinate": ("math_L1_coordinate", "math_L1: coordinate pairs, distance, midpoint"),
    "math_L2_trig": ("math_L2_trig", "math_L2: sine, cosine, tangent, Pythagorean theorem"),
    "math_L3_line": ("math_L3_line", "math_L3: slope, line equations, parallel, perpendicular"),
    "math_L4_intersect": ("math_L4_intersect", "math_L4: line-line, segment, line-circle intersection"),
    "math_L5_vector": ("math_L5_vector", "math_L5: vector add, magnitude, dot/cross product"),
    "math_L6_apply": ("math_L6_apply", "math_L6: torus distance, composite spatial problems"),
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
