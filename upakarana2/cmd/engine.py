"""engine.py — vy command: engine management + live analysis."""

import sys


def cmd_vy(args, store):
    from upakarana2.engine import server

    if args.action == "start":
        server.start(background=True)

    elif args.action == "stop":
        server.stop()

    elif args.action == "status":
        from upakarana2.cmd.dispatch import _print_json
        _print_json(server.status())

    elif args.action == "reload":
        result = server.reload()
        if result:
            print("Reloaded.")
        else:
            print("Server not running.", file=sys.stderr)

    elif args.action == "eval":
        from upakarana2.engine.client import Client, VyakaranaError
        c = Client()
        try:
            expr = args.expr or args.name
            if not expr:
                print("usage: upakarana vy eval '<expr>'", file=sys.stderr); return
            try:
                result = c.eval(expr)
                if isinstance(result, (list, dict)):
                    from upakarana2.cmd.dispatch import _print_json
                    _print_json(result)
                else:
                    print(result)
            except VyakaranaError as e:
                store.usage.track_miss("vy", "eval", expr, error_type=e.code)
                print(f"Error [{e.code}]: {e.message}", file=sys.stderr)
        finally:
            c.close()

    elif args.action == "ask":
        from upakarana2.engine.client import Client, VyakaranaError
        c = Client()
        try:
            question = args.question or args.name
            if not question:
                print("usage: upakarana vy ask '<question>'", file=sys.stderr); return
            try:
                answer = c.ask(question)
                if not answer:
                    store.usage.track_miss("vy", "ask", question)
                print(answer)
            except VyakaranaError as e:
                store.usage.track_miss("vy", "ask", question, error_type=e.code)
                print(f"Error [{e.code}]: {e.message}", file=sys.stderr)
        finally:
            c.close()

    elif args.action == "walk":
        from upakarana2.engine.client import Client
        c = Client()
        try:
            if args.incoming:
                result = c.walk_in(args.node, args.relation)
            else:
                result = c.walk(args.node, args.relation)
            if not result:
                store.usage.track_miss("vy", "walk", f"{args.node}:{args.relation}")
            for r in result:
                print(f"  {r}")
        finally:
            c.close()

    elif args.action == "inspect":
        from upakarana2.engine.client import Client, VyakaranaError
        from upakarana2.cmd.dispatch import _print_json
        c = Client()
        try:
            try:
                _print_json(c.inspect(args.name))
            except VyakaranaError as e:
                store.usage.track_miss("vy", "inspect", args.name, error_type=e.code)
                print(f"Error [{e.code}]: {e.message}", file=sys.stderr)
        finally:
            c.close()

    # Live analysis (merged from old `live` command)
    elif args.action == "drift":
        _live_action(args, store, "drift")

    elif args.action == "pratipaksha":
        _live_action(args, store, "pratipaksha")

    elif args.action == "signal-trace":
        _live_action(args, store, "signal-trace")

    elif args.action == "panchaavayava":
        _live_action(args, store, "panchaavayava")


def _live_action(args, store, action):
    from upakarana2.engine.client import Client
    try:
        client = Client()
    except Exception as e:
        print(f"Engine not running: {e}", file=sys.stderr)
        return

    try:
        if action == "drift":
            from upakarana2.graph.flow import live_walk
            from upakarana2.parsers import om5, tantra4, shabda
            om_nodes = om5.load_all()
            tantras = tantra4.load_all()
            shabda_nodes = shabda.load_all()
            try:
                loaded = client.eval("list-tantras") or []
            except Exception:
                loaded = []
            on_disk = set(tantras.keys())
            in_engine = set(str(t) for t in (loaded if isinstance(loaded, list) else []))
            print(f"Static: {len(om_nodes)} om5 nodes, {len(tantras)} tantras on disk, {len(shabda_nodes)} shabda nodes")
            print(f"Live:   {len(in_engine)} tantras loaded")
            only_disk = sorted(on_disk - in_engine)
            only_engine = sorted(in_engine - on_disk)
            if only_disk:
                print(f"\nOn disk but NOT loaded ({len(only_disk)}):")
                for t in only_disk[:15]:
                    print(f"  {t}")
            if only_engine:
                print(f"\nIn engine but NOT on disk ({len(only_engine)}):")
                for t in only_engine[:15]:
                    print(f"  {t}")

        elif action == "pratipaksha":
            from upakarana2.graph.flow import pratipaksha_walk
            result = pratipaksha_walk(client)
            print(f"Pratipaksha involution on {len(result['ops'])} ops:")
            print(f"  symmetric: {len(result['symmetric'])}")
            for r in result["symmetric"]:
                print(f"    {r['op']} ↔ {r['pratipaksha']}")
            if result["broken"]:
                print(f"  broken ({len(result['broken'])}):")
                for r in result["broken"]:
                    print(f"    {r['op']} → {r['pratipaksha']} → {r['round_trip'] or '(none)'}")

        elif action == "signal-trace":
            sentence = getattr(args, "sentence", None) or args.name
            if not sentence:
                print("usage: upakarana vy signal-trace -s 'question'", file=sys.stderr)
                return
            try:
                result = client.ask(sentence)
                print(f"Answer: {result}")
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)

        elif action == "panchaavayava":
            try:
                result = client.walk("panchaavayava", "yukta")
                if result:
                    print(f"panchaavayava limbs: {result}")
                else:
                    print("panchaavayava node not found in live graph")
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)

    finally:
        client.close()
