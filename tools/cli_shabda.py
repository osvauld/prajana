"""cli_shabda.py — CLI commands for shabda analysis.

Handles: shabda summary|search|node|eval|gaps|words|verbs
"""

from . import shabda
from .shabda2 import get_field, get_words


def _sep(title, width=80):
    return f"\n{'=' * width}\n  {title}\n{'=' * width}\n"


def cmd_shabda(args):
    sub = args.subcmd or "summary"

    if sub == "summary":
        s = shabda.summary()
        print(_sep("SHABDA SUMMARY"))
        print(f"  Nodes:  {s['total_nodes']}")
        print(f"  Words:  {s['total_words']} unique")
        print(f"  Files:  {s['total_files']}")

        print(f"\n  Files:")
        print(f"  {'Name':<35} {'Nodes':>6}")
        print(f"  {'─' * 45}")
        for name, count in sorted(s["files"].items(), key=lambda x: -x[1]):
            print(f"  {name:<35} {count:>6}")

        print(f"\n  Keys (top 20):")
        print(f"  {'Key':<25} {'Count':>6}")
        print(f"  {'─' * 35}")
        for k, v in sorted(s["key_distribution"].items(), key=lambda x: -x[1])[:20]:
            print(f"  {k:<25} {v:>6}")

        if s["collisions"]:
            print(f"\n  Word collisions ({len(s['collisions'])}):")
            for w, nodes in sorted(s["collisions"].items()):
                print(f"    {w:<20} → {', '.join(nodes)}")

        print()

    elif sub == "search":
        pattern = args.name
        if not pattern:
            print("Usage: shabda search PATTERN")
            return
        results = shabda.search(pattern=pattern)
        if results:
            print(f"\n  {len(results)} matches for '{pattern}':\n")
            for r in results:
                print(f"  {r['name']} [{r['file']}]")
                for m in r["matches"]:
                    print(f"    {m}")
        else:
            print(f"  No matches for '{pattern}'")
        print()

    elif sub == "node":
        name = args.name
        if not name:
            print("Usage: shabda node NODE_NAME")
            return
        n = shabda.node_info(name=name)
        if not n:
            print(f"  Node '{name}' not found in shabda files.")
            # suggest
            all_nodes = shabda.load_all()
            matches = [k for k in all_nodes if name in k][:10]
            if matches:
                print(f"  Did you mean: {', '.join(matches)}?")
            return
        print(f"\n  {n['name']}  [{n.get('file_name', '')}] {n.get('domain', '')}")
        if n.get("path"):
            print(f"  {n['path']}")
        print()
        for k, v in n.get("fields", {}).items():
            if isinstance(v, list):
                print(f"  {k}: {', '.join(str(x) for x in v)}")
            else:
                print(f"  {k}: {v}")
        if n.get("comments"):
            print()
            for c in n["comments"]:
                print(f"  -- {c}")
        print()

    elif sub == "eval":
        s = shabda.summary()
        nodes = s["eval_nodes"]
        print(_sep(f"FIREABLE OPERATIONS ({len(nodes)} nodes with eval:)"))
        print(f"  {'Node':<30} {'eval':<10} {'word':<15} {'arity':<6}")
        print(f"  {'─' * 65}")
        for e in sorted(nodes, key=lambda x: x["domain"]):
            word = e["word"]
            if isinstance(word, list):
                word = ",".join(word)
            print(f"  {e['node']:<30} {e['eval']:<10} {word or '-':<15} {e['arity'] or '-':<6}")
        print()

    elif sub == "gaps":
        missing = shabda.gaps()
        print(_sep(f"NODES MISSING WORD MAPPINGS ({len(missing)})"))
        by_reason = {}
        for m in missing:
            key = ", ".join(m["reason"])
            by_reason.setdefault(key, []).append(m)
        for reason, nodes in sorted(by_reason.items()):
            print(f"\n  [{reason}] ({len(nodes)} nodes)")
            for m in sorted(nodes, key=lambda x: x["name"]):
                print(f"    {m['name']:<35} {m['domain']}")
        print()

    elif sub == "words":
        name = args.name
        if name:
            wbn = shabda.words_by_node()
            if name in wbn:
                print(f"\n  Words for '{name}': {', '.join(sorted(wbn[name]))}")
            else:
                # try word lookup
                wi = shabda.build_word_index()
                if name in wi:
                    nodes = [e["node"] for e in wi[name]]
                    print(f"\n  '{name}' maps to: {', '.join(nodes)}")
                else:
                    print(f"  '{name}' not found as node or word.")
        else:
            wi = shabda.build_word_index()
            print(_sep(f"WORD INDEX ({len(wi)} words)"))
            for word in sorted(wi.keys()):
                nodes = [e["node"] for e in wi[word]]
                print(f"  {word:<25} → {', '.join(nodes)}")
        print()

    elif sub == "verbs":
        v = shabda.verbs()
        print(_sep(f"VERB COVERAGE ({v['total']} entries)"))
        print(f"  Kshaya (departure/loss): {len(v['kshaya'])}")
        for w in v["kshaya"]:
            print(f"    {w}")
        print(f"\n  Vriddhi (arrival/gain): {len(v['vriddhi'])}")
        for w in v["vriddhi"]:
            print(f"    {w}")
        print()

    elif sub == "files":
        name = args.name
        all_nodes = shabda.load_all()
        if name:
            file_nodes = [n for n in all_nodes.values() if n.get("file_name") == name]
            if not file_nodes:
                print(f"  File '{name}' not found.")
                return
            print(f"\n  {name}.shabda ({len(file_nodes)} nodes)\n")
            for n in file_nodes:
                words = get_words(n)
                ev = get_field(n, "eval")
                suffix = []
                if words:
                    suffix.append(f"word:{','.join(words)}")
                if ev:
                    suffix.append(f"eval:{ev}")
                meta = "  ".join(suffix)
                print(f"  {n['name']:<35} {meta}")
        else:
            files = {}
            for n in all_nodes.values():
                fn = n.get("file_name", "unknown")
                files.setdefault(fn, []).append(n)
            print(_sep(f"SHABDA FILES ({len(files)})"))
            for fn, nodes in sorted(files.items()):
                domain = nodes[0].get("domain", "")
                print(f"  {fn:<35} {len(nodes):>4} nodes  {domain}")
        print()

    elif sub == "lookup":
        word = args.name
        if not word:
            print("Usage: shabda lookup WORD")
            return
        wi = shabda.build_word_index()
        entries = wi.get(word.lower(), [])
        if entries:
            print(f"\n  '{word}' maps to:\n")
            for e in entries:
                print(f"    {e['node']:<30} [{e['file_name']}] {e['domain']}")
        else:
            print(f"  '{word}' not found.")
        print()

    else:
        print(f"Unknown shabda command: {sub}")
        print("Available: summary, search, node, eval, gaps, words, verbs, files, lookup")
