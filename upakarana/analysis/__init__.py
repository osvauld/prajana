"""analysis/ — Static + live graph analysis.

Submodules:
  ghosts     — nodes referenced but never defined
  edges      — incoming/outgoing edge analysis, reverse lookups
  layers     — cross-layer edge flow, relation fingerprints
  chains     — swarupa walks, connected components
  ring       — visheshanam ring axiom verification (pratipaksha symmetry, abheda)
  signals    — signal flow tracing, emitted-not-consumed audit
  tantras    — pattern classification, concept-tantra grounding
  static     — lint, dead code, complexity (original)
  graph      — live graph analysis (original)
  ocaml      — OCaml codebase analysis (original)
  health     — combined health report (original)
"""
