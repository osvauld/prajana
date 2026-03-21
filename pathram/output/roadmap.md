# Roadmap — Priority Stack

## Identify abstract tantra patterns ✓



Seven patterns identified: filter-collect, scan-accumulate, shabda-read, walk, fixpoint, apply-op, om-read. Three kinds: pure math, math-with-constraints, procedures.

## Create kosha nodes for each pattern ✓



Created 5 new kosha nodes: selection, algebraic-projection, scan-accumulate, operation-dispatch, lexicon-morphism, graph-contract. Total now 1639 nodes.

## Enrich op-class nodes with algebra connections ✓



Connected all 7 op-classes to algebra: higher-order→endomorphism, relation→partial-order, binary→group, projection→morphism, pipeline→monotone-map.

## Enrich op-reduce, op-fixpoint, op-map, op-filter ✓



Enriched op-reduce (monoid-sthita, fold-abheda, closure-siddha), op-fixpoint (endomorphism-janya, monotone-map-sthita, convergence-phala), op-map (morphism-abheda), op-filter (selection-abheda, lattice-sthita).

## Replace hardcoded values in tantras with kosha reads ✓



Three tantra changes, all tests pass (78/39/0):
1. grade-sparsha: dvandva string → shabda graded-ring intra-grade-boundary
2. count-chain: seed 0 → to-number (shabda graded-ring fold-identity)  
3. execute-mantra: walk kriya → om-kriya (first om-kriya usage!)

## Activate om-kriya and om-contract in tantras ✓



Migrated 6 tantras to om-contract (derive-step, derive-chain, forward-match, inverse-match, mantra-select, mantra-coverage). om-kriya activated in execute-mantra. Tests: 78/39/0, 1.4s faster (18.25s vs 19.65s).

## Refine pathram math to paper quality

## Dissolve vartamana into pathram

## Dissolve pratibimba into pathram
