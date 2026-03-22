"""om5_verify.py — verify Python decomposition matches live OCaml engine.

Usage: python3 -m tools.om5_verify [N]
  N = number of random nodes to sample (default 30)
"""

import random
import sys

from . import om5
from .vy import Client


def vy_subject_edges(client, name):
    """Get outgoing edges from a node via the live engine."""
    triples = client.triples_of(name)
    edges = set()
    for t in triples:
        # t = [subject, relation, object]
        if t[0] == name:
            edges.add((t[2], t[1]))
    return edges


def verify_sample(n=30, seed=42):
    """Compare Python decomposition vs OCaml engine for n random nodes."""
    results = om5.convert_all()
    random.seed(seed)
    sample = random.sample(results, min(n, len(results)))

    client = Client()

    match = 0
    mismatch = 0
    errors = 0

    for r in sample:
        parsed = om5.parse_om(r["path"])
        py_edges = set(parsed["edges"])

        try:
            ocaml_edges = vy_subject_edges(client, r["name"])
        except Exception as e:
            print(f'  ERR {r["name"]}: {e}')
            errors += 1
            continue

        # Only compare outgoing edges: filter ocaml to edges where source=name
        # (triples_of returns both directions)
        if py_edges == ocaml_edges:
            match += 1
            print(f'  OK  {r["name"]} [{r["layer"]}] -- {len(py_edges)} edges')
        else:
            py_only = py_edges - ocaml_edges
            ml_only = ocaml_edges - py_edges
            if not py_only and ml_only:
                # OCaml has extra outgoing edges (from graph joins/inheritance)
                match += 1
                print(f'  OK  {r["name"]} [{r["layer"]}] -- {len(py_edges)} py, +{len(ml_only)} inherited')
            else:
                mismatch += 1
                print(f'  !!  {r["name"]} [{r["layer"]}] -- py:{len(py_edges)} ocaml:{len(ocaml_edges)}')
                if py_only:
                    for m in sorted(py_only)[:5]:
                        print(f'      py+  {m[1]}: {m[0]}')
                if ml_only:
                    for e in sorted(ml_only)[:5]:
                        print(f'      ml+  {e[1]}: {e[0]}')

    print(f"\n  Match: {match}  Mismatch: {mismatch}  Error: {errors}  Total: {match+mismatch+errors}")
    return match, mismatch, errors


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    verify_sample(n)
