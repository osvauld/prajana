# restructure plan

## goal

compress proof_graph.ml and prayoga.ml simultaneously:
- extract knowledge tables from .ml into .om shabda fields
- split the two large files into four clean-layered modules
- result: the graph knows, the code only walks and composes

## current state

proof_graph.ml  1995 lines
prayoga.ml       621 lines
total           2616 lines

## target state

proof_graph.ml   ~190 lines   graph core only
setu.ml          ~200 lines   graph walk + shabda reader
anuvada.ml       ~700 lines   sentence understanding + emit-from-graph
prayoga.ml       ~450 lines   PRAYOGA command execution
total           ~1540 lines   (~1000 lines removed — knowledge moved to .om)

## dependency chain

proof_graph.ml  <- setu.ml  <- anuvada.ml
                            <- prayoga.ml

## what goes where

### proof_graph.ml (keep — graph core only)
- types: visheshanam, typed_edge, nigamana, proof_graph
- visheshanam_of_string, string_of_visheshanam
- empty, join, find
- in_degree, out_degree, neighbors, edges_of
- raw_satya, avrti_step, satya_ganana

### setu.ml (new — graph walk + shabda reader)
moved from prayoga.ml:
  parse_shabda, read_shabda, shabda_get
moved from proof_graph.ml:
  kriya_of, swarupa_of, yukta_of, janya_of
  has_domain_sthita, is_setu
  infer_inputs, infer_outputs
  to_english, resolve
  sanitize_ocaml_ident, capitalize_first
  grammar_of_english, token_role type, classify_token
moved from prayoga.ml:
  find_setu_form, walk_chain
  detect_domain, domain_of_edge_target
  tokenise, bigrams

### anuvada.ml (new — sentence understanding + emit-from-graph)
moved from proof_graph.ml:
  anuvada_triple type, TripleKey, TripleSet
  next_thread_question
  walk_one_pass, avrti_anuvada
  sahaja_gloss, sahaja_render (reads node.shabda — no table)
  english_of_visheshanam (reads visheshanam-english.om shabda)
  thaalam_cycle (reads thaalam node shabda)
  render_spiral
  math_op_kind type, classify_math_op, yukta_operators
  filename_from_graph, write_program
  ocaml_of_composition, ocaml_read_of, ocaml_print_of
  emit_bridge_program, emit_math_programs, emit_ocaml_from_graph
  voice_role type, strudel_voice type
  note_of_node, gain_of_satya, voices_of_node
  emit_strudel_from_graph
  anuvada (entry function)
  print, pravaha, json_escape

### prayoga.ml (trim — PRAYOGA command only)
keep:
  prayoga_context type
  swara_to_pitch (reads graph)
  compose_music, compose_computation, compose_biology
  run
remove (call Setu. instead):
  parse_shabda, read_shabda, shabda_get
  tokenise, bigrams
  detect_domain, domain_of_edge_target
  find_setu_form, resolve_ocaml_forms, walk_chain

## knowledge tables to delete from .ml

| table | lines | replacement |
|-------|-------|-------------|
| sahaja_table | ~120 | shabda in each node's .om file |
| sahaja_of_table | ~5 | read node.shabda directly |
| grammar_of_english | ~15 | english-grammar.om shabda |
| english_of_visheshanam | ~10 | visheshanam-english.om shabda |
| thaalam_cycle | ~8 | thaalam node shabda |
| ocaml_symbol_of_operator | ~8 | extend ocaml-setu.om shabda |
| ocaml_type_of_concept | ~15 | extend ocaml-setu.om shabda |
| ocaml_prim | ~10 | extend ocaml-setu.om shabda |
| role_of_relation | ~12 | extend strudel.om shabda |
| note_names array | ~2 | already in swara-to-strudel.om |

## new .om files

brahman/kosha/language/english-grammar.om
  shabda is:swarupa are:swarupa am:swarupa was:swarupa were:swarupa being:swarupa means:swarupa
         of:sthita in:sthita on:sthita upon:sthita within:sthita rests:sthita stands:sthita
         from:janya born:janya originates:janya comes:janya arises:janya
         by:siddha through:siddha via:siddha proven:siddha established:siddha
         and:yukta with:yukta to:yukta connected:yukta joined:yukta links:yukta
         as:kriya does:kriya acts:kriya functions:kriya runs:kriya holds:kriya gives:kriya receives:kriya
         equals:abheda same:abheda identical:abheda equivalent:abheda maps:abheda
         shows:drishthanta proves:drishthanta demonstrates:drishthanta evidence:drishthanta seen:drishthanta
         produces:phala results:phala causes:phala yields:phala becomes:phala increases:phala decreases:phala grows:phala generates:phala

brahman/kosha/language/visheshanam-english.om
  shabda swarupa:is abheda:is-the-same-as drishthanta:demonstrated-by sthita:rests-on
         yukta:connects-to siddha:proven-through kriya:acts-as phala:produces janya:born-from

## modified .om files

### ~80 sangati nodes — add shabda gloss
each node in sahaja_table gets its gloss added as shabda line.
examples:
  brahma.om:      shabda the-creator/fullness-as-source
  spanda.om:      shabda self-pulsing/vibrating-from-within
  iccha.om:       shabda will/directed-reaching
  gamaka.om:      shabda the-ornament/note-in-motion
  avrti.om:       shabda the-deepening-return/spiral-not-circle
  sandhi.om:      shabda the-joining-that-produces-meaning
  (etc. for all 80 entries)

### thaalam.om — add beat counts
  shabda adi:8 rupaka:6 misra:7 khanda:5

### ocaml-setu.om — extend shabda
add to existing shabda:
  plus:+ minus:- times:* division:/ vector:float-list matrix:float-array-array scalar:float number:int
  addition-float:(+.) multiplication-float:(*.) subtraction-float:(-.) division-float:(/.)
  addition-int:(+) multiplication-int:(*) subtraction-int:(-) division-int:(/)

### strudel.om — extend shabda
add relation→voice-role mappings:
  swarupa:piano:4:0.8 abheda:piano:4:0.7 sthita:sawtooth:3:0.5 janya:triangle:3:0.5
  yukta:square:4:0.4 phala:sine:5:0.6 kriya:metal:4:0.3 siddha:sawtooth:4:0.4 drishthanta:sine:5:0.3

## execution order

step 1  create setu.ml — move graph walk utilities + shabda reader
step 2  create anuvada.ml — move anuvada engine + emit-from-graph + print/pravaha
step 3  slim proof_graph.ml to graph core only
step 4  update prayoga.ml to use Setu. calls
step 5  update dune (lib) — add setu anuvada modules
step 6  update verify.ml — Proof_graph.anuvada -> Anuvada.anuvada etc.
step 7  update vyakarana.ml — Proof_graph.print -> Anuvada.print etc.
step 8  build — verify everything compiles
step 9  add shabda to ~80 .om node files (sahaja glosses)
step 10 create english-grammar.om, visheshanam-english.om
step 11 extend ocaml-setu.om, strudel.om, thaalam.om shabda fields
step 12 replace hardcoded tables with shabda reads in setu.ml and anuvada.ml
step 13 build and test all commands:
          anuvada sentence
          PRAYOGA music / computation / biology
          sthiti (print)
          pravaha

## callers to update after restructure

verify.ml:
  Proof_graph.anuvada        -> Anuvada.anuvada
  Proof_graph.sahaja_gloss   -> Anuvada.sahaja_gloss
  Proof_graph.sahaja_render  -> Anuvada.sahaja_render
  Proof_graph.edges_of       -> stays Proof_graph.edges_of
  Proof_graph.find           -> stays Proof_graph.find
  Proof_graph.string_of_visheshanam -> stays Proof_graph.string_of_visheshanam
  Proof_graph.in_degree      -> stays Proof_graph.in_degree

vyakarana.ml:
  Proof_graph.print          -> Anuvada.print
  Proof_graph.pravaha        -> Anuvada.pravaha
  Proof_graph.empty          -> stays Proof_graph.empty

## notes

- steps 1-8 are structural: move code, no behavior change
- steps 9-12 are knowledge extraction: move data from .ml to .om
- step 13 verifies nothing broke
- sahaja_table is not a migration — it is shabda values being written
  where they belong, then read back by sahaja_gloss via node.shabda
- grammar_of_english and english_of_visheshanam become shabda reads
  once the .om files exist; the match tables are deleted
- the graph grows richer; the code shrinks; the principle holds
