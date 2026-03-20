"""cli_shabda.py — CLI commands for unified shabda analysis.

Handles: shabda summary|words|files|node|eval|gaps|search|lookup
"""

from . import shabda


def _sep(title, width=80):
    return f"\n{'=' * width}\n  {title}\n{'=' * width}\n"


def _header(name, meta, width=80):
    return f"\n{'─' * width}\n  {name}  ({meta})\n{'─' * width}"


def cmd_shabda(args):
    sub = args.subcmd or "summary"

    if sub == "summary":
        s = shabda.summary()
        print(_sep(f"SHABDA SUMMARY"))

        print(
            f"  Word index:  {s['total_words']} unique words -> {s['total_om_nodes_with_words']} om nodes"
        )
        print(f"  Om nodes:    {s['total_om_nodes']} total")
        print(f"  Shabda files: {s['total_shabda_files']} .shabda template files")

        # key distribution
        print(f"\n  Shabda keys across om files:")
        print(f"  {'Key':<25} {'Nodes':>6}")
        print(f"  {'─' * 35}")
        for k, v in sorted(s["key_distribution"].items(), key=lambda x: -x[1]):
            if v >= 3:  # only show keys with 3+ nodes
                print(f"  {k:<25} {v:>6}")

        # words by layer
        print(f"\n  Words by layer:")
        print(f"  {'Layer':<25} {'Words':>6}")
        print(f"  {'─' * 35}")
        for layer, count in sorted(s["layer_word_counts"].items(), key=lambda x: -x[1]):
            print(f"  {layer:<25} {count:>6}")

        # shabda files
        print(f"\n  Shabda template files ({s['total_shabda_files']}):")
        print(f"  {'Name':<35} {'Entries':>8}  Domain")
        print(f"  {'─' * 70}")
        for name, info in sorted(s["shabda_file_entries"].items()):
            print(f"  {name:<35} {info['entry_count']:>8}  {info['domain']}")

        # tmpl links
        if s["tmpl_links"]:
            print(f"\n  Om nodes linked to .shabda templates ({len(s['tmpl_links'])}):")
            for node, tmpl in sorted(s["tmpl_links"].items()):
                print(f"    {node:<30} -> {tmpl}")

        # collisions
        if s["collisions"]:
            print(
                f"\n  Word collisions ({len(s['collisions'])} words map to multiple nodes):"
            )
            for w, nodes in sorted(s["collisions"].items()):
                print(f"    {w:<20} -> {', '.join(nodes)}")

        print()

    elif sub == "words":
        # words [domain|node-name]
        name = args.name
        if name:
            # check if it's a domain path
            wd = shabda.words_by_domain()
            if name in wd:
                words = wd[name]
                print(f"\n  Words in domain '{name}' ({len(words)}):\n")
                print(f"  {'Word':<25} {'Node':<30} Source")
                print(f"  {'─' * 70}")
                for w in words:
                    print(f"  {w['word']:<25} {w['node']:<30} {w['source_type']}")
            else:
                # treat as node name
                nw = shabda.words_by_node()
                if name in nw:
                    print(
                        f"\n  Words mapping to '{name}': {', '.join(sorted(nw[name]))}"
                    )
                else:
                    print(f"  No words found for '{name}'")
                    # suggest close matches
                    matches = [n for n in nw if name in n][:10]
                    if matches:
                        print(f"  Did you mean: {', '.join(matches)}?")
        else:
            # show words by domain
            wd = shabda.words_by_domain()
            print(_sep(f"WORDS BY DOMAIN"))
            for domain, words in sorted(wd.items()):
                print(f"\n  {domain}/ ({len(words)} words)")
                for w in words[:20]:
                    print(f"    {w['word']:<25} -> {w['node']}")
                if len(words) > 20:
                    print(f"    ... +{len(words) - 20} more")
            print()

    elif sub == "files":
        # show .shabda file details
        name = args.name
        shabda_files = shabda.load_shabda_files()
        if name:
            s = shabda_files.get(name)
            if not s:
                print(f"  Shabda file '{name}' not found.")
                matches = [n for n in shabda_files if name in n]
                if matches:
                    print(f"  Available: {', '.join(matches)}")
                return
            print(_header(s["name"], f"{len(s['entries'])} entries | {s['domain']}"))
            print(f"  {s['path']}\n")
            for k, v in s["entries"]:
                print(f"  {k:<35} {v}")
        else:
            print(_sep(f"SHABDA FILES ({len(shabda_files)})"))
            for s in shabda_files.values():
                print(
                    f"  {s['name']:<35} {len(s['entries']):>4} entries  {s['domain']}"
                )
            print()

    elif sub == "node":
        name = args.name
        if not name:
            print("Usage: shabda node NODE_NAME")
            return
        info = shabda.node_shabda(node_name=name)
        if not info:
            print(f"  Node '{name}' not found.")
            return
        print(_header(info["name"], f"[{info['layer']}] {info['domain']}"))
        print(f"  {info['path']}\n")
        print(f"  raw: {info['shabda_raw']}\n")
        if info["shabda_keys"]:
            print(f"  Shabda keys:")
            for k, v in sorted(info["shabda_keys"].items()):
                print(f"    {k:<20} {v}")
        if info["shabda_words"]:
            print(f"\n  Words: {', '.join(info['shabda_words'])}")
        if info["edges"]:
            print(f"\n  Edges ({len(info['edges'])}):")
            for e in info["edges"]:
                print(f"    --[{e['relation']}]--> {e['target']}")
        print()

    elif sub == "eval":
        # show all fireable operations
        s = shabda.summary()
        print(_sep(f"FIREABLE OPERATIONS ({len(s['eval_nodes'])} nodes with eval:)"))
        print(f"  {'Node':<25} {'eval':<12} {'word':<18} {'arity':<6} {'inverse'}")
        print(f"  {'─' * 85}")
        for e in sorted(s["eval_nodes"], key=lambda x: x["domain"]):
            print(
                f"  {e['node']:<25} {e['eval']:<12} {e['word'] or '-':<18} "
                f"{e['arity'] or '-':<6} {e['inverse'] or '-'}"
            )
        print()

    elif sub == "gaps":
        missing = shabda.gaps()
        print(_sep(f"NODES MISSING WORD MAPPINGS ({len(missing)})"))
        # group by reason
        by_reason = {}
        for m in missing:
            key = ", ".join(m["reason"])
            by_reason.setdefault(key, []).append(m)
        for reason, nodes in sorted(by_reason.items()):
            print(f"\n  [{reason}] ({len(nodes)} nodes)")
            for m in sorted(nodes, key=lambda x: x["name"]):
                print(f"    {m['name']:<35} [{m['layer']}] {m['domain']}")
        print()

    elif sub == "search":
        pattern = args.name
        if not pattern:
            print("Usage: shabda search PATTERN")
            return

        # search both word index and .shabda file contents
        word_results = shabda.search_words(pattern=pattern)
        file_results = shabda.search_files(pattern=pattern)

        if word_results:
            print(f"\n  Word index matches ({len(word_results)}):\n")
            for r in word_results:
                nodes = [e["node"] for e in r["entries"]]
                sources = [e["source_type"] for e in r["entries"]]
                print(
                    f"  {r['word']:<25} -> {', '.join(nodes)}  ({', '.join(sources)})"
                )

        if file_results:
            print(f"\n  Shabda file matches ({len(file_results)}):\n")
            for r in file_results:
                print(f"  {r['name']} ({r['domain']})")
                for m in r["matches"]:
                    print(f"    {m['line']:>4}: {m['text']}")

        if not word_results and not file_results:
            print(f"  No matches for '{pattern}'")
        print()

    elif sub == "lookup":
        word = args.name
        if not word:
            print("Usage: shabda lookup WORD")
            return
        word_index = shabda.build_word_index()
        entries = word_index.get(word, [])
        if entries:
            print(f"\n  '{word}' maps to:\n")
            for e in entries:
                print(
                    f"    {e['node']:<30} [{e['layer']}] {e['domain']}  ({e['source_type']})"
                )
                if e["shabda_keys"]:
                    for k, v in sorted(e["shabda_keys"].items()):
                        if k != "word":
                            print(f"      {k}: {v}")
        else:
            # try partial match
            results = shabda.search_words(pattern=word)
            if results:
                print(f"\n  '{word}' not found. Partial matches:\n")
                for r in results[:10]:
                    nodes = [e["node"] for e in r["entries"]]
                    print(f"    {r['word']:<25} -> {', '.join(nodes)}")
            else:
                print(f"  '{word}' not found in any shabda source.")
        print()

    elif sub == "verbs":
        # show verb coverage in common-sense-events
        shabda_files = shabda.load_shabda_files()
        events = shabda_files.get("common-sense-events")
        if not events:
            print("  common-sense-events.shabda not found")
            return
        kshaya = []
        vriddhi = []
        for k, v in events["entries"]:
            if v.strip() == "kshaya":
                kshaya.append(k)
            elif v.strip() == "vriddhi":
                vriddhi.append(k)

        bigram_k = [v for v in kshaya if "-" in v]
        bigram_v = [v for v in vriddhi if "-" in v]
        single_k = [v for v in kshaya if "-" not in v]
        single_v = [v for v in vriddhi if "-" not in v]

        print(_sep(f"VERB COVERAGE — common-sense-events"))
        print(f"  Total: {len(kshaya) + len(vriddhi)} entries ({len(kshaya)} kshaya, {len(vriddhi)} vriddhi)")
        print(f"  Single words: {len(single_k)} kshaya, {len(single_v)} vriddhi")
        print(f"  Bigram phrases: {len(bigram_k)} kshaya, {len(bigram_v)} vriddhi")

        print(f"\n  Kshaya (departure/loss) — {len(kshaya)} entries:")
        for v in sorted(single_k):
            print(f"    {v}")
        if bigram_k:
            print(f"\n  Kshaya bigrams:")
            for v in sorted(bigram_k):
                print(f"    {v}")

        print(f"\n  Vriddhi (arrival/gain) — {len(vriddhi)} entries:")
        for v in sorted(single_v):
            print(f"    {v}")
        if bigram_v:
            print(f"\n  Vriddhi bigrams:")
            for v in sorted(bigram_v):
                print(f"    {v}")

        # coverage gaps: common verbs that might be missing
        common_missing = []
        common_verbs = [
            "ran", "walked", "took", "made", "put", "gave", "kept", "let",
            "said", "told", "asked", "moved", "fell", "threw", "hit", "cut",
            "won", "lost", "paid", "saved", "earned", "spent", "lent",
            "picked", "carried", "passed", "shared", "split", "donated",
            "planted", "grew", "built", "cooked", "baked", "washed",
        ]
        known = set(k for k, _ in events["entries"])
        for v in common_verbs:
            if v not in known:
                common_missing.append(v)
        if common_missing:
            print(f"\n  Possibly missing common verbs ({len(common_missing)}):")
            for v in sorted(common_missing):
                print(f"    {v}")
        print()

    elif sub == "karaka":
        # show karaka/vibhakti wiring status
        from . import om as om_mod
        oms = om_mod.load_all()

        # find karaka nodes
        karakas = {n: o for n, o in oms.items() if o["domain"].startswith("sangati/grammar/karaka") and n != "karaka"}
        vibhaktis = {n: o for n, o in oms.items() if o["domain"].startswith("sangati/grammar/vibhakti") and n != "vibhakti"}
        preps = {n: o for n, o in oms.items() if o["domain"].startswith("bhasha/english/grammar") and n.startswith("prep-")}
        copulas = {n: o for n, o in oms.items() if o["domain"].startswith("bhasha/english/grammar") and n.startswith("copula-")}

        print(_sep("KARAKA / VIBHAKTI / GRAMMAR WIRING"))

        print(f"  Karaka nodes ({len(karakas)}):")
        print(f"  {'Name':<20} {'Vibhakti':<25} {'Sangati root':<20} Edges")
        print(f"  {'─' * 80}")
        for name, o in sorted(karakas.items()):
            edges = o.get("edges", [])
            vibhakti_edges = [e for e in edges if "vibhakti" in e["relation"]]
            swarupa_edges = [e for e in edges if e["relation"] == "swarupa"]
            vib = ", ".join(e["target"] for e in vibhakti_edges) if vibhakti_edges else "-"
            root = ", ".join(e["target"] for e in swarupa_edges) if swarupa_edges else "-"
            print(f"  {name:<20} {vib:<25} {root:<20} {len(edges)}")

        print(f"\n  Vibhakti nodes ({len(vibhaktis)}):")
        for name in sorted(vibhaktis):
            print(f"    {name}")

        print(f"\n  Prepositions ({len(preps)}):")
        print(f"  {'Name':<15} {'word':<10} {'Vibhakti connection'}")
        print(f"  {'─' * 50}")
        for name, o in sorted(preps.items()):
            word = o["shabda_keys"].get("word", "-")
            edges = o.get("edges", [])
            vib_edges = [e for e in edges if "vibhakti" in e["target"]]
            vib = ", ".join(e["target"] for e in vib_edges) if vib_edges else "-"
            print(f"  {name:<15} {word:<10} {vib}")

        print(f"\n  Copulas ({len(copulas)}):")
        print(f"  {'Name':<15} {'word':<10} {'Kaala':<20} {'Vachana'}")
        print(f"  {'─' * 60}")
        for name, o in sorted(copulas.items()):
            word = o["shabda_keys"].get("word", "-")
            edges = o.get("edges", [])
            kaala_edges = [e["target"] for e in edges if "kaala" in e["target"]]
            vachana_edges = [e["target"] for e in edges if "vachana" in e["target"]]
            kaala = ", ".join(kaala_edges) if kaala_edges else "-"
            vachana = ", ".join(vachana_edges) if vachana_edges else "-"
            print(f"  {name:<15} {word:<10} {kaala:<20} {vachana}")

        # check for missing connections
        print(f"\n  Coverage check:")
        all_vib = set(vibhaktis.keys())
        karaka_vibs = set()
        for o in karakas.values():
            for e in o.get("edges", []):
                if "vibhakti" in e["target"]:
                    karaka_vibs.add(e["target"])
        prep_vibs = set()
        for o in preps.values():
            for e in o.get("edges", []):
                if "vibhakti" in e["target"]:
                    prep_vibs.add(e["target"])
        uncovered_karaka = all_vib - karaka_vibs - {"vibhakti", "sambodhana"}
        uncovered_prep = all_vib - prep_vibs - {"vibhakti", "sambodhana", "prathama-vibhakti"}
        if uncovered_karaka:
            print(f"    Vibhaktis without karaka: {', '.join(sorted(uncovered_karaka))}")
        else:
            print(f"    All vibhaktis have karaka nodes ✓")
        if uncovered_prep:
            print(f"    Vibhaktis without English preposition: {', '.join(sorted(uncovered_prep))}")
        else:
            print(f"    All vibhaktis have English prepositions ✓")
        print()

    else:
        print(f"Unknown shabda command: {sub}")
        print("Available: summary, words, files, node, eval, gaps, search, lookup, verbs, karaka")
