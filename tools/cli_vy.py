"""cli_vy.py — CLI commands for the live vyakarana server.

Handles: vy (status/start/stop/restart/reload/run/eval/trace/walk/inspect)
         ask (single question or REPL mode)
"""

import json
import os
import sys
import time

from . import vyakarana


# ── helpers ───────────────────────────────────────────────────────────────────


def _print_answer(question, answer_text):
    """Display a question-answer exchange with reasoning strands."""
    from .vy import Client

    print(f"\n  Q: {question}")
    print(f"  A: {answer_text}")
    strands = Client.strands(answer_text)
    if strands:
        print()
        for name, content in strands.items():
            content = content.strip()
            if content:
                print(f"    [{name}] {content[:200]}")
    print()


def ensure_vy():
    """Auto-start vyakarana server if not running. Returns socket path."""
    vy_socket = os.environ.get("VYAKARANA_SOCKET", "/tmp/vy.sock")
    if not vyakarana.health(vy_socket):
        print("  [vyakarana] server not running, starting...", file=sys.stderr)
        try:
            vyakarana.ensure(vy_socket)
        except RuntimeError as e:
            print(f"  [vyakarana] {e}", file=sys.stderr)
            sys.exit(1)
    return vy_socket


# ── vy ────────────────────────────────────────────────────────────────────────


def cmd_vy(args):
    """Manage the vyakarana OCaml server."""
    sub = args.subcmd or "status"

    if sub == "status":
        s = vyakarana.status()
        state = "running" if s["running"] else "stopped"
        print(f"\n  vyakarana: {state}")
        print(f"  socket:    {s['socket']}")
        if s["pid"]:
            print(f"  pid:       {s['pid']}")
        if s.get("tantras"):
            print(f"  tantras:   {s['tantras']}")
        print(f"  binary:    {s['binary'] or 'not found'}")
        print()

    elif sub == "start":
        socket_path = args.name or vyakarana.DEFAULT_SOCKET
        if vyakarana.health(socket_path):
            print(f"  Already running on {socket_path}")
            return
        proc = vyakarana.start(socket_path=socket_path, background=True, quiet=False)
        if proc:
            print(f"  Started (pid {proc.pid})")
        else:
            print("  Failed to start")

    elif sub == "stop":
        if vyakarana.stop():
            print("  Stopped")
        else:
            print("  Not running (or could not stop)")

    elif sub == "restart":
        vyakarana.stop()
        time.sleep(0.5)
        proc = vyakarana.start(background=True, quiet=False)
        if proc:
            print(f"  Restarted (pid {proc.pid})")

    elif sub == "reload":
        resp = vyakarana.reload()
        if resp:
            print(f"  Reloaded: {resp.get('tantras_loaded', '?')} tantras")
        else:
            print("  Server not running")

    elif sub == "run":
        vyakarana.start(background=False, quiet=False)

    elif sub == "eval":
        _vy_eval(args)

    elif sub == "trace":
        _vy_trace(args)

    elif sub == "walk":
        _vy_walk(args)

    elif sub == "inspect":
        _vy_inspect(args)

    elif sub == "mantras":
        _vy_mantras(args)

    elif sub == "triples":
        _vy_triples(args)

    elif sub == "parse":
        _vy_parse(args)

    elif sub == "help":
        _vy_help()

    else:
        print(f"Unknown vy command: {sub}")
        print(
            "Available: status, start, stop, restart, reload, run, eval, trace, walk, inspect, mantras, triples, parse, help"
        )


# ── vy subcommands ────────────────────────────────────────────────────────────


def _vy_eval(args):
    from .vy import Client, VyakaranaError

    expr = args.name
    if not expr:
        print("Usage: vy eval '<tantra expression>'")
        return
    vy_socket = ensure_vy()
    try:
        vy = Client(vy_socket)
        result = vy.eval(expr)
        if isinstance(result, list) and result and isinstance(result[0], list):
            for t in result:
                print(f"  {t}")
        elif isinstance(result, list):
            for item in result:
                print(f"  {item}")
        elif isinstance(result, dict):
            print(json.dumps(result, indent=2))
        else:
            print(f"  {result}")
        vy.close()
    except VyakaranaError as e:
        print(f"  Error: {e}")


def _vy_trace(args):
    from .vy import Client, VyakaranaError

    sentence = args.name
    if not sentence:
        print("Usage: vy trace '<sentence>'")
        return
    vy_socket = ensure_vy()
    try:
        vy = Client(vy_socket)
        trace = vy.pipeline_trace(sentence)
        prev_triples = []
        for step in trace:
            triples = step.get("triples", [])
            n = len(triples)
            added = [t for t in triples if t not in prev_triples]
            removed = [t for t in prev_triples if t not in triples]
            delta = ""
            if added:
                delta = f"  +{len(added)}"
            if removed:
                delta += f"  -{len(removed)}"
            print(f"\n  {step['stage']:<30} {n} triples{delta}")
            if added:
                for t in added:
                    print(f"    + {t}")
            if removed:
                for t in removed:
                    print(f"    - {t}")
            prev_triples = triples
        print()
        answer = vy.answer(sentence)
        print(f"  answer: {answer}")
        vy.close()
    except VyakaranaError as e:
        print(f"  Error: {e}")


def _vy_walk(args):
    from .vy import Client, VyakaranaError

    if not args.name:
        print("Usage: vy walk '<node> <relation> [depth]'")
        print("       vy walk 'viveka-max abheda'")
        print("       vy walk 'mass matra'")
        return
    parts = args.name.split()
    if len(parts) < 2:
        print("Usage: vy walk '<node> <relation>'")
        return
    node, rel = parts[0], parts[1]
    depth = int(parts[2]) if len(parts) > 2 else 3
    vy_socket = ensure_vy()
    try:
        vy = Client(vy_socket)
        visited = []
        frontier = [node]
        for d in range(depth):
            next_frontier = []
            for name in frontier:
                targets = vy.walk(name, rel)
                for t in targets:
                    if t not in [v[0] for v in visited] and t not in frontier:
                        next_frontier.append(t)
                        eval_key = vy.eval(f'shabda "{t}" "eval"')
                        word_key = vy.eval(f'shabda "{t}" "word"')
                        keys = []
                        if eval_key:
                            keys.append(f"eval={eval_key}")
                        if word_key:
                            keys.append(f"word={word_key}")
                        keys_str = f"  ({', '.join(keys)})" if keys else ""
                        visited.append((t, d + 1, name, keys_str))
            frontier = next_frontier
            if not frontier:
                break

        if not visited:
            print(f"  {node} --[{rel}]--> (none)")
        else:
            print(f"\n  {node} --[{rel}]--> chain (depth {depth}):\n")
            for target, d, via, keys_str in visited:
                indent = "  " * d
                print(f"  {indent}{via} --[{rel}]--> {target}{keys_str}")
        vy.close()
    except VyakaranaError as e:
        print(f"  Error: {e}")


def _vy_inspect(args):
    from .vy import Client, VyakaranaError

    name = args.name
    if not name:
        print("Usage: vy inspect <node>")
        return
    vy_socket = ensure_vy()
    try:
        vy = Client(vy_socket)
        resp = vy.inspect(name)
        print(f"\n  {name}  (satya={resp.get('satya', '?')})")

        shabda_keys = {}
        for key in [
            "eval",
            "word",
            "math-op",
            "arity",
            "name",
            "constants-key",
            "role",
            "suffix",
            "stem-suffix",
            "fold",
            "degree",
            "invertible",
            "inverse",
            "speech-strand-separator",
        ]:
            val = vy.eval(f'shabda "{name}" "{key}"')
            if val:
                shabda_keys[key] = val
        if shabda_keys:
            print(f"\n  shabda:")
            for k, v in shabda_keys.items():
                print(f"    {k}: {v}")

        layer = vy.eval(f'node-layer "{name}"')
        if layer:
            print(f"\n  layer: {layer}")

        out_edges = resp.get("out_edges", [])
        if out_edges:
            print(f"\n  outgoing ({len(out_edges)}):")
            for e in out_edges:
                print(f"    --[{e['relation']}]--> {e['target']}")

        in_edges = resp.get("in_edges", [])
        if in_edges:
            print(f"\n  incoming ({len(in_edges)}):")
            for e in in_edges:
                print(f"    {e['source']} --[{e['relation']}]-->")
        print()
        vy.close()
    except VyakaranaError as e:
        print(f"  Error: {e}")


def _vy_mantras(args):
    from .vy import Client, VyakaranaError

    sentence = args.name
    if not sentence:
        print("Usage: vy mantras '<sentence>'")
        print("  Shows which mantras fire for a sentence and why.")
        return
    vy_socket = ensure_vy()
    try:
        vy = Client(vy_socket)
        status = vy.mantra_status(sentence)

        bc = status.get("bound_concepts", [])
        print(f"\n  Sentence: {sentence}")
        print(f"\n  Bound concepts ({len(bc)}):")
        for pair in bc:
            if isinstance(pair, list) and len(pair) >= 2:
                print(f"    {pair[0]} = {pair[1]}")

        mantras = status.get("mantras", [])
        fires = [m for m in mantras if isinstance(m, list) and len(m) >= 2 and m[1]]
        misses = [
            m for m in mantras if isinstance(m, list) and len(m) >= 2 and not m[1]
        ]

        if fires:
            print(f"\n  Fires ({len(fires)}):")
            for m in fires:
                name = m[0] if m else "?"
                covered = m[2] if len(m) > 2 else []
                print(f"    + {name}  covered={covered}")

        if misses:
            print(f"\n  No match ({len(misses)}):")
            for m in misses[:10]:
                name = m[0] if m else "?"
                missing = m[3] if len(m) > 3 else []
                if missing:
                    print(f"    - {name}  missing={missing}")
        print()
        vy.close()
    except VyakaranaError as e:
        print(f"  Error: {e}")


def _vy_triples(args):
    from .vy import Client, VyakaranaError

    name = args.name
    if not name:
        print("Usage: vy triples <node>")
        print("  Shows all triples touching a node in the live graph.")
        return
    vy_socket = ensure_vy()
    try:
        vy = Client(vy_socket)
        tris = vy.triples_of(name)
        as_subj = [
            t for t in tris if isinstance(t, list) and len(t) >= 3 and str(t[0]) == name
        ]
        as_obj = [
            t for t in tris if isinstance(t, list) and len(t) >= 3 and str(t[2]) == name
        ]
        other = [t for t in tris if t not in as_subj and t not in as_obj]

        print(f"\n  {name}: {len(tris)} triples")
        if as_subj:
            print(f"\n  As subject ({len(as_subj)}):")
            for t in as_subj:
                print(f"    {name} --[{t[1]}]--> {t[2]}")
        if as_obj:
            print(f"\n  As object ({len(as_obj)}):")
            for t in as_obj:
                print(f"    {t[0]} --[{t[1]}]--> {name}")
        if other:
            print(f"\n  Other ({len(other)}):")
            for t in other:
                print(f"    {t}")
        print()
        vy.close()
    except VyakaranaError as e:
        print(f"  Error: {e}")


def _vy_parse(args):
    """Per-word subgraph analysis: what emit-triples sees for each word."""
    from .vy import Client, VyakaranaError

    sentence = args.name
    if not sentence:
        print("Usage: vy parse '<sentence>'")
        print("  Shows per-word analysis: resolution, role, subgraph state, decision.")
        return
    vy_socket = ensure_vy()
    try:
        vy = Client(vy_socket)

        # get raw BQG output (before sandhi-viveka)
        raw_graph = vy.eval(f'build-question-graph "{sentence}"')
        # get refined graph (after sandhi-viveka)
        # refined = vy.bqg(sentence)

        # per-word analysis
        words = sentence.replace(".", " .").replace("?", " ?").replace("!", " !").replace(",", " ,").split()
        punct = {".", "?", "!", ","}

        print(f"\n  Sentence: {sentence}")
        print(f"  Raw BQG: {len(raw_graph) if isinstance(raw_graph, list) else 0} triples\n")

        # track subgraph state as we walk through
        current_grade = []
        entities = []
        bindings = []
        grammar_signals = []

        if isinstance(raw_graph, list):
            for t in raw_graph:
                if not isinstance(t, list) or len(t) < 3:
                    continue
                subj, edge, obj = str(t[0]), str(t[1]), str(t[2])

                # classify the triple
                kind = edge
                word_display = subj

                # update subgraph state
                if edge in ("viraam", "dvandva"):
                    # boundary — show grade summary then reset
                    if current_grade:
                        print(f"  --- {edge} boundary ---")
                        if entities:
                            print(f"      entities: {entities}")
                        if bindings:
                            print(f"      bindings: {bindings}")
                    current_grade = []
                    entities = []
                    bindings = []
                    grammar_signals = []
                    continue

                # classify the decision
                decision = ""
                if edge == "satya":
                    # check if this is a known node or dravya promotion
                    node = vy.eval(f'shabda-anveshana "{subj}"')
                    if node and str(node) != "_none":
                        role = vy.eval(f'shabda "{node}" "role"')
                        layer = vy.eval(f'node-layer "{node}"')
                        decision = f"known ({layer})"
                        if role:
                            decision += f" role={role}"
                    else:
                        decision = "DRAVYA promoted"
                    entities.append(subj)
                elif edge == "mithya":
                    node = vy.eval(f'shabda-anveshana "{subj}"')
                    if node and str(node) != "_none":
                        decision = f"known but mithya (label/modifier)"
                    else:
                        # check why not promoted
                        guards = []
                        ev = vy.eval(f'shabda "common-sense-events" "{subj}"')
                        if ev:
                            guards.append(f"verb({ev})")
                        if subj.endswith("ed"):
                            guards.append("kta-pratyaya(-ed)")
                        if subj.endswith("ing"):
                            guards.append("shatr-pratyaya(-ing)")
                        if grammar_signals:
                            last_sig = grammar_signals[-1]
                            if last_sig == "adhikarana":
                                guards.append("after-locative")
                        if guards:
                            decision = f"blocked: {', '.join(guards)}"
                        else:
                            decision = "unknown word"
                elif edge == "asprista-sankhya":
                    decision = f"number={obj}"
                elif edge == "sankhya":
                    decision = f"{subj} has value {obj}"
                    bindings.append(f"{subj}={obj}")
                elif edge == "matra":
                    decision = f"{subj} unit={obj}"
                    bindings.append(f"{subj}[{obj}]")
                elif edge == "shashthi-vibhakti":
                    decision = "possession"
                    grammar_signals.append("possession")
                elif edge == "adhikarana":
                    decision = "locative (on/in/at)"
                    grammar_signals.append("adhikarana")
                elif edge == "vidhi-kaala":
                    decision = f"intent: {obj}"

                current_grade.append(t)
                print(f"  {word_display:<20} [{edge:<22}] {decision}")

            # final grade summary
            if entities or bindings:
                print(f"\n  --- final grade ---")
                if entities:
                    print(f"      entities: {entities}")
                if bindings:
                    print(f"      bindings: {bindings}")

        # also show the answer
        answer = vy.answer(sentence)
        print(f"\n  Answer: {answer}")
        print()
        vy.close()
    except VyakaranaError as e:
        print(f"  Error: {e}")


def _vy_help():
    print("""
  vy — query the live vyakarana graph server

  Server lifecycle:
    vy status                          check if server is running
    vy start                           start in background
    vy stop                            stop server
    vy restart                         stop + start
    vy reload                          re-read tantra files from disk
    vy run                             start in foreground (blocks)

  Graph queries (talks to the live server):
    vy eval '<expr>'                   evaluate any tantra expression
    vy inspect <node>                  full node: satya, shabda, edges
    vy walk '<node> <relation> [depth]'  transitive chain walk
    vy triples <node>                  all triples touching a node
    vy mantras '<sentence>'            which mantras fire and why

  Pipeline debugging:
    vy parse '<sentence>'              per-word subgraph analysis (resolution, guards, decisions)
    vy trace '<sentence>'              pipeline stages with +/- diff
    vy eval 'build-question-graph "<sentence>"'   raw BQG
    vy eval 'anuvada-ganana "<sentence>"'          full answer

  Useful eval expressions:
    vy eval 'walk "mass" "yukta"'              outgoing yukta edges
    vy eval 'walk-in "mass" "yukta"'           incoming yukta edges
    vy eval 'shabda "addition" "eval"'         shabda key lookup → "add"
    vy eval 'word-node "kg"'                   alias resolution → "kilogram"
    vy eval 'shabda-anveshana "heavier"'       full word lookup → "viveka-max"
    vy eval 'node-layer "mass"'                which layer: kosha/sangati/etc
    vy eval 'om-janya "momentum-mantra"'       mantra inputs → ["mass","velocity"]
    vy eval 'om-phala "momentum-mantra"'       mantra output → ["momentum"]
    vy eval 'mantra-select "kinetic-energy"'   find mantras for a concept
    vy eval 'apply-op "add" [3, 4]'            fire a math operation → 7
    vy eval 'match-mantra <graph>'             find best mantra for a graph
    vy eval 'bound-state <graph>'              what concepts have values
    vy eval 'extract-solve-for <graph>'        what the question asks for
    vy eval 'sankhya-sparsha <graph>'          [concept, value] pairs
""")


# ── ask ───────────────────────────────────────────────────────────────────────


def cmd_ask(args):
    """Ask a question or enter interactive repl mode."""
    from .vy import Client, VyakaranaError

    vy_socket = ensure_vy()

    question = args.subcmd
    if args.name:
        question = f"{question} {args.name}" if question else args.name

    if question:
        try:
            vy = Client(vy_socket)
            answer = vy.answer(question)
            _print_answer(question, answer)
            vy.close()
        except (VyakaranaError, ConnectionRefusedError, FileNotFoundError) as e:
            print(f"  Error: {e}")
            print(f"  Is the vyakarana server running on {vy_socket}?")
        return

    # repl mode
    print(f"\n  vyakarana repl (server: {vy_socket})")
    print("  Type a question, or:")
    print("    :eval EXPR     evaluate a tantra expression")
    print("    :bqg SENTENCE  show refined question graph")
    print("    :trace SENTENCE show pipeline trace")
    print("    :reload        reload all tantras")
    print("    :quit          exit\n")

    try:
        vy = Client(vy_socket)
    except (ConnectionRefusedError, FileNotFoundError) as e:
        print(f"  Cannot connect to {vy_socket}: {e}")
        print("  Start the server first.")
        return

    session_id = "repl"
    while True:
        try:
            line = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue
        if line in (":quit", ":q", ":exit"):
            break

        try:
            if line.startswith(":eval "):
                expr = line[6:].strip()
                result = vy.eval(expr)
                if isinstance(result, list) and result and isinstance(result[0], list):
                    for t in result:
                        print(f"    {t}")
                else:
                    print(f"    {result}")

            elif line.startswith(":bqg "):
                sentence = line[5:].strip()
                g = vy.bqg(sentence)
                print(f"\n  Refined graph ({len(g)} triples):")
                for t in g:
                    print(f"    {t}")
                print()

            elif line.startswith(":trace "):
                sentence = line[7:].strip()
                trace = vy.pipeline_trace(sentence)
                for step in trace:
                    n = len(step.get("triples", []))
                    print(f"    {step['stage']:<30} {n} triples")

            elif line.startswith(":reload"):
                resp = vy.reload_all()
                print(f"    reloaded: {resp.get('tantras_loaded', '?')} tantras")

            elif line.startswith(":"):
                print(f"    Unknown command: {line.split()[0]}")

            else:
                answer = vy.ask(line, session_id=session_id)
                _print_answer(line, answer)

        except VyakaranaError as e:
            print(f"    Error: {e}")
        except (BrokenPipeError, ConnectionResetError, EOFError):
            print("    Connection lost, reconnecting...")
            try:
                vy = Client(vy_socket)
            except Exception as e:
                print(f"    Cannot reconnect: {e}")
                break

    vy.close()
    print("  bye")
