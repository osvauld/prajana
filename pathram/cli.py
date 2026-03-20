"""cli.py — CLI dispatch for pathram.

Usage: python3 -m pathram <command> [args...]
"""

import argparse
import sys

from pathram import data, store, query, emit
from pathram.bridge import Bridge


def _sep(title, width=80):
    pad = width - len(title) - 4
    left = pad // 2
    right = pad - left
    return f"{'═' * left} {title} {'═' * right}"


def _print_entries(entries, brief=False):
    """Print a list of entries."""
    if not entries:
        print("  (none)")
        return
    for e in entries:
        tag = e.get("tag", "")
        tag_str = f" [{tag}]" if tag and tag != "active" else ""
        meta = e.get("meta", {})
        status = meta.get("status", "")
        status_str = f" ({status})" if status else ""
        dt = e.get("updated_at", "")[:10]
        print(f"  {e['id']}: {e.get('title', '')}{tag_str}{status_str}  [{dt}]")
        if not brief and e.get("body"):
            body_preview = e["body"][:120].replace("\n", " ")
            print(f"    {body_preview}")


def _print_refs(refs_dict):
    out = refs_dict.get("outgoing", [])
    inc = refs_dict.get("incoming", [])
    if out:
        print("  Outgoing:")
        for r in out:
            print(f"    → {r['to_id']} ({r['ref_type']})")
    if inc:
        print("  Incoming:")
        for r in inc:
            print(f"    ← {r['from_id']} ({r['ref_type']})")
    if not out and not inc:
        print("  (no references)")


def build_parser():
    p = argparse.ArgumentParser(prog="pathram", description="Living documentation system")
    sub = p.add_subparsers(dest="command")

    # --- Mutations ---

    sp = sub.add_parser("discover", help="Record a discovery")
    sp.add_argument("text", help="Discovery text")
    sp.add_argument("--doc", default="discoveries", help="Target document")
    sp.add_argument("--session", type=int, default=None)

    sp = sub.add_parser("step-done", help="Mark a step complete")
    sp.add_argument("step_id", help="Step entry ID")
    sp.add_argument("note", nargs="?", default="", help="Completion note")

    sp = sub.add_parser("step-add", help="Add a plan step")
    sp.add_argument("title", help="Step title")
    sp.add_argument("--doc", default="plan", help="Target plan document")
    sp.add_argument("--after", type=float, default=None, help="Position after")
    sp.add_argument("--session", type=int, default=None)
    sp.add_argument("--status", default="pending")

    sp = sub.add_parser("step-update", help="Update step status")
    sp.add_argument("step_id", help="Step entry ID")
    sp.add_argument("--status", required=True)

    sp = sub.add_parser("wrong", help="Mark entry as wrong")
    sp.add_argument("entry_id")
    sp.add_argument("--correction", default=None, help="Pointer to correction")

    sp = sub.add_parser("supersede", help="Mark entry as superseded")
    sp.add_argument("entry_id")
    sp.add_argument("--by", dest="by_id", required=True, help="Replacement entry")

    sp = sub.add_parser("baseline", help="Update test baseline")
    sp.add_argument("passed", type=int)
    sp.add_argument("xfailed", type=int)
    sp.add_argument("failed", type=int)
    sp.add_argument("--session", type=int, default=None)

    sp = sub.add_parser("add-section", help="Add a section to a doc")
    sp.add_argument("doc_id")
    sp.add_argument("title")
    sp.add_argument("--body", default="")
    sp.add_argument("--after", type=float, default=None)
    sp.add_argument("--session", type=int, default=None)
    sp.add_argument("--type", dest="entry_type", default="section")

    sp = sub.add_parser("tag", help="Set lifecycle tag on entry")
    sp.add_argument("entry_id")
    sp.add_argument("new_tag")
    sp.add_argument("--pointer", default=None)

    sp = sub.add_parser("note", help="Record a quirk or note")
    sp.add_argument("text")
    sp.add_argument("--type", dest="note_type", default="quirk")
    sp.add_argument("--doc", default="notes")
    sp.add_argument("--session", type=int, default=None)

    sp = sub.add_parser("ref", help="Add a cross-reference")
    sp.add_argument("from_id")
    sp.add_argument("to_id")
    sp.add_argument("--type", dest="ref_type", default="link")

    sp = sub.add_parser("session-start", help="Start a new session")
    sp.add_argument("title")
    sp.add_argument("--id", type=int, default=None, dest="session_id")

    sp = sub.add_parser("session-end", help="End a session")
    sp.add_argument("session_id", type=int)

    sp = sub.add_parser("create-doc", help="Create a new document")
    sp.add_argument("doc_id")
    sp.add_argument("title")
    sp.add_argument("--position", type=float, default=None)
    sp.add_argument("--tag", default="active")

    # --- Queries ---

    sp = sub.add_parser("glance", help="Compact LLM summary")

    sp = sub.add_parser("index", help="Full TOC with status")

    sp = sub.add_parser("search", help="Full-text search")
    sp.add_argument("pattern")

    sp = sub.add_parser("show", help="Show one document")
    sp.add_argument("doc_id")

    sp = sub.add_parser("tagged", help="Entries with given tag")
    sp.add_argument("tag_name")

    sp = sub.add_parser("session", help="Session timeline")
    sp.add_argument("session_id", type=int)

    sp = sub.add_parser("topic", help="Cross-source search")
    sp.add_argument("name")

    sp = sub.add_parser("steps", help="Plan steps")
    sp.add_argument("--status", default=None)

    sp = sub.add_parser("timeline", help="Chronological events")
    sp.add_argument("--session", default=None, help="Session range (e.g. 17..19)")

    sp = sub.add_parser("gaps", help="Known data gaps")

    sp = sub.add_parser("quirks", help="Recorded quirks")

    sp = sub.add_parser("stale", help="Stale entries")
    sp.add_argument("days", type=int)

    sp = sub.add_parser("refs", help="References for an entry")
    sp.add_argument("entry_id", nargs="?", default=None)
    sp.add_argument("--broken", action="store_true")

    sp = sub.add_parser("report", help="Full analysis report")

    # --- Emission ---

    sp = sub.add_parser("emit", help="Emit markdown files")
    sp.add_argument("format", choices=["md"], default="md", nargs="?")
    sp.add_argument("--out", default="pathram/output")

    sub.add_parser("math", help="Emit mathematical description from live graph")

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    # Load state
    data.ensure_data_dir()
    state = data.load()

    # Bridge for live data (lazy)
    bridge = Bridge()

    cmd = args.command

    # --- Mutations ---

    if cmd == "discover":
        # Auto-create discoveries doc if needed
        if "discoveries" not in state.doc_by_id and args.doc == "discoveries":
            store.create_doc(state, "discoveries", "Discoveries")
        entry = store.create_entry(state, args.doc, "discovery", args.text,
                                   session_id=args.session)
        print(f"Recorded: {entry['id']}")

    elif cmd == "step-done":
        entry = store.update_entry(state, args.step_id,
                                   meta={"status": "done"})
        if args.note:
            entry = store.update_entry(state, args.step_id,
                                       body=entry.get("body", "") + f"\n\n{args.note}")
        print(f"Done: {entry['title']}")

    elif cmd == "step-add":
        if args.doc not in state.doc_by_id:
            store.create_doc(state, args.doc, "Plan")
        position = args.after + 0.5 if args.after else None
        entry = store.create_entry(state, args.doc, "step", args.title,
                                   position=position, session_id=args.session,
                                   meta={"status": args.status})
        print(f"Added: {entry['id']} at position {entry['position']}")

    elif cmd == "step-update":
        entry = store.update_entry(state, args.step_id,
                                   meta={"status": args.status})
        print(f"Updated: {entry['title']} → {args.status}")

    elif cmd == "wrong":
        entry = store.update_tag(state, args.entry_id, "wrong",
                                 pointer=args.correction)
        print(f"Marked wrong: {entry['id']}")

    elif cmd == "supersede":
        entry = store.update_tag(state, args.entry_id, "superseded",
                                 pointer=args.by_id)
        print(f"Superseded: {entry['id']} → {args.by_id}")

    elif cmd == "baseline":
        bl = store.update_baseline(state, args.passed, args.xfailed,
                                   args.failed, session_id=args.session)
        print(f"Baseline: {bl['passed']}p / {bl['xfailed']}x / {bl['failed']}f")

    elif cmd == "add-section":
        position = args.after + 0.5 if args.after else None
        entry = store.create_entry(state, args.doc_id, args.entry_type,
                                   args.title, body=args.body,
                                   position=position, session_id=args.session)
        print(f"Added: {entry['id']}")

    elif cmd == "tag":
        entry = store.update_tag(state, args.entry_id, args.new_tag,
                                 pointer=args.pointer)
        print(f"Tagged: {entry['id']} → {args.new_tag}")

    elif cmd == "note":
        if args.doc not in state.doc_by_id:
            store.create_doc(state, args.doc, "Notes")
        entry = store.create_entry(state, args.doc, args.note_type, args.text,
                                   session_id=args.session)
        print(f"Noted: {entry['id']}")

    elif cmd == "ref":
        ref = store.add_ref(state, args.from_id, args.to_id,
                            ref_type=args.ref_type)
        print(f"Ref: {args.from_id} → {args.to_id}")

    elif cmd == "session-start":
        session = store.create_session(state, args.title,
                                       session_id=args.session_id)
        print(f"Session {session['id']}: {args.title}")

    elif cmd == "session-end":
        session = store.close_session(state, args.session_id)
        print(f"Closed session {args.session_id}")

    elif cmd == "create-doc":
        doc = store.create_doc(state, args.doc_id, args.title,
                               position=args.position, tag=args.tag)
        print(f"Created doc: {doc['id']}")

    # --- Queries ---

    elif cmd == "glance":
        print(emit.emit_glance(state, bridge))

    elif cmd == "index":
        print(emit.emit_index(state, bridge))

    elif cmd == "search":
        results = query.search(state, args.pattern)
        print(_sep(f"search: {args.pattern}"))
        _print_entries(results)

    elif cmd == "show":
        print(emit.emit_md(state, args.doc_id))

    elif cmd == "tagged":
        results = query.by_tag(state, args.tag_name)
        print(_sep(f"tagged: {args.tag_name}"))
        _print_entries(results)

    elif cmd == "session":
        results = query.by_session(state, args.session_id)
        print(_sep(f"session {args.session_id}"))
        _print_entries(results)

    elif cmd == "topic":
        results = query.topic(state, args.name, bridge)
        print(_sep(f"topic: {args.name}"))
        print(f"\n  pathram entries ({len(results['entries'])}):")
        _print_entries(results["entries"], brief=True)
        om_nodes = results.get("om_nodes", [])
        if om_nodes:
            print(f"\n  om nodes ({len(om_nodes)}):")
            for n in om_nodes[:10]:
                print(f"    {n['name']} ({n.get('domain', '')})")
        tantras = results.get("tantras", [])
        if tantras:
            print(f"\n  tantras ({len(tantras)}):")
            for t in tantras[:10]:
                print(f"    {t['name']} ({t.get('group', '')})")
        shabda = results.get("shabda", [])
        if shabda:
            print(f"\n  shabda ({len(shabda)}):")
            for s in shabda[:10]:
                print(f"    {s.get('word', s)}")

    elif cmd == "steps":
        results = query.steps(state, status=args.status)
        print(_sep("steps"))
        _print_entries(results)

    elif cmd == "timeline":
        s_start, s_end = None, None
        if args.session:
            parts = args.session.split("..")
            s_start = int(parts[0])
            s_end = int(parts[1]) if len(parts) > 1 else s_start
        print(emit.emit_timeline(state, s_start, s_end))

    elif cmd == "gaps":
        results = query.gaps(state)
        print(_sep("data gaps"))
        _print_entries(results)

    elif cmd == "quirks":
        results = query.quirks(state)
        print(_sep("quirks"))
        _print_entries(results)

    elif cmd == "stale":
        results = query.stale(state, args.days)
        print(_sep(f"stale > {args.days} days"))
        _print_entries(results)

    elif cmd == "refs":
        if args.broken:
            broken = query.broken_refs(state)
            print(_sep("broken refs"))
            for r in broken:
                print(f"  {r['from_id']} → {r['to_id']} ({r['ref_type']})")
            if not broken:
                print("  (none)")
        elif args.entry_id:
            refs = query.refs_for(state, args.entry_id)
            print(_sep(f"refs: {args.entry_id}"))
            _print_refs(refs)
        else:
            print("Usage: pathram refs <entry_id> or pathram refs --broken")

    elif cmd == "report":
        print(emit.emit_report(state, bridge))

    # --- Emission ---

    elif cmd == "emit":
        written = emit.emit_all(state, args.out)
        print(f"Emitted {len(written)} files to {args.out}/")
        for w in written:
            print(f"  {w}")

    elif cmd == "math":
        print(bridge.emit_math())

    else:
        parser.print_help()
        return 1

    return 0
