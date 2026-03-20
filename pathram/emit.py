"""emit.py — Render pathram state to markdown, glance, reports.

All output is generated from structured state — never from .md files.
LaTeX is passed through verbatim.
"""

from pathram import query


TAG_NOTICES = {
    "superseded": "**[SUPERSEDED]** → {pointer}",
    "wrong": "**[WRONG]** → corrected in {pointer}",
    "deprecated": "**[DEPRECATED]** — no longer the approach",
    "historical": "*[historical]*",
    "provisional": "*[provisional — not yet validated]*",
    "deferred": "*[deferred]*",
}


def _entry_heading(entry):
    """Render an entry as a markdown heading + body."""
    level = entry.get("level", 2)
    hashes = "#" * level
    title = entry.get("title", "")
    tag = entry.get("tag", "active")

    # Status badge for steps
    meta = entry.get("meta", {})
    status = meta.get("status")
    badge = ""
    if entry.get("type") == "step" and status:
        badges = {"done": " ✓", "next": " ←", "pending": "", "blocked": " ✗"}
        badge = badges.get(status, "")

    lines = [f"{hashes} {title}{badge}"]

    # Tag notice
    if tag in TAG_NOTICES and tag != "active":
        pointer = entry.get("tag_pointer", "")
        lines.append("")
        lines.append(TAG_NOTICES[tag].format(pointer=pointer or "?"))

    # Body
    body = entry.get("body", "")
    if body:
        lines.append("")
        lines.append(body)

    return "\n".join(lines)


def emit_md(state, doc_id):
    """Render a full markdown document from entries."""
    doc = state.doc_by_id.get(doc_id)
    if not doc:
        return f"Document not found: {doc_id}"

    lines = [f"# {doc['title']}", ""]

    # Doc-level tag notice
    tag = doc.get("tag", "active")
    if tag in TAG_NOTICES:
        lines.append(TAG_NOTICES[tag].format(pointer=""))
        lines.append("")

    entries = query.by_doc(state, doc_id)
    for entry in entries:
        lines.append(_entry_heading(entry))
        lines.append("")

    return "\n".join(lines)


def emit_all(state, out_dir):
    """Write all documents as .md files to out_dir."""
    from pathlib import Path
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    written = []
    for doc in state.docs:
        md = emit_md(state, doc["id"])
        p = d / f"{doc['id']}.md"
        p.write_text(md)
        written.append(str(p))
    return written


def emit_glance(state, bridge=None):
    """Compact 20-line LLM context summary."""
    g = query.glance(state, bridge)
    lines = ["## pathram glance", ""]

    # Baseline
    bl = g.get("baseline")
    if bl:
        lines.append(f"**Baseline**: {bl['passed']} passed / "
                      f"{bl['xfailed']} xfailed / {bl['failed']} failed")

    # Live stats
    live = g.get("live", {})
    if live:
        parts = []
        if "om_count" in live:
            parts.append(f"{live['om_count']} om nodes")
        if "tantra_count" in live:
            parts.append(f"{live['tantra_count']} tantras")
        if parts:
            lines.append(f"**Live**: {', '.join(parts)}")

    # Next step
    ns = g.get("next_step")
    if ns:
        lines.append(f"**Next**: {ns['title']}")
    lines.append("")

    # Recent discoveries
    disc = g.get("recent_discoveries", [])
    if disc:
        lines.append("**Recent discoveries**:")
        for d in disc[:5]:
            lines.append(f"  - {d['title']}")
        lines.append("")

    # Status rollup
    tc = g.get("tag_counts", {})
    if tc:
        parts = [f"{count} {tag}" for tag, count in sorted(tc.items())]
        lines.append(f"**Status**: {', '.join(parts)}")

    lines.append(f"**Total**: {g['doc_count']} docs, {g['entry_count']} entries")
    return "\n".join(lines)


def emit_index(state, bridge=None):
    """Auto-generated index/TOC."""
    lines = ["# pathram index", ""]

    # Group docs by tag: active first, then rest
    active_docs = [d for d in state.docs if d.get("tag") == "active"]
    other_docs = [d for d in state.docs if d.get("tag") != "active"]

    for group_name, docs in [("Active", active_docs), ("Other", other_docs)]:
        if not docs:
            continue
        lines.append(f"## {group_name}")
        lines.append("")
        for doc in sorted(docs, key=lambda d: d.get("position", 0)):
            entries = state.by_doc.get(doc["id"], [])
            tag = doc.get("tag", "active")
            updated = doc.get("updated_at", "")[:10]
            lines.append(f"- **{doc['title']}** ({doc['id']}) "
                         f"[{tag}] — {len(entries)} entries, updated {updated}")

            # Show active steps inline
            if tag == "active":
                doc_steps = [e for e in entries if e.get("type") == "step"]
                for s in doc_steps[:10]:
                    status = s.get("meta", {}).get("status", "pending")
                    marker = {"done": "✓", "next": "←", "pending": "·",
                              "blocked": "✗"}.get(status, "·")
                    lines.append(f"  {marker} {s['title']}")

        lines.append("")

    # Live stats
    if bridge:
        live = bridge.live_stats()
        if live:
            lines.append("## Live Stats")
            for k, v in live.items():
                lines.append(f"- {k}: {v}")
            lines.append("")

    # Broken refs
    broken = query.broken_refs(state)
    if broken:
        lines.append(f"## Broken References ({len(broken)})")
        for ref in broken:
            lines.append(f"- {ref['from_id']} → {ref['to_id']} ({ref['ref_type']})")
        lines.append("")

    return "\n".join(lines)


def emit_report(state, bridge=None):
    """Full analysis report."""
    lines = ["# pathram report", ""]

    # Overview
    lines.append(f"**Documents**: {len(state.docs)}")
    lines.append(f"**Entries**: {len(state.entries)}")
    lines.append(f"**Sessions**: {len(state.sessions)}")
    lines.append(f"**References**: {len(state.refs)}")
    lines.append(f"**Operations**: {len(state.ops)}")
    lines.append("")

    # Tag distribution
    lines.append("## Tag Distribution")
    for tag, entries in sorted(state.by_tag.items()):
        if entries:
            lines.append(f"- {tag}: {len(entries)}")
    lines.append("")

    # Type distribution
    lines.append("## Content Types")
    for etype, entries in sorted(state.by_type.items()):
        if entries:
            lines.append(f"- {etype}: {len(entries)}")
    lines.append("")

    # Staleness
    stale_7 = query.stale(state, 7)
    stale_30 = query.stale(state, 30)
    lines.append("## Staleness")
    lines.append(f"- Not updated in 7 days: {len(stale_7)}")
    lines.append(f"- Not updated in 30 days: {len(stale_30)}")
    lines.append("")

    # Baseline history
    if state.baselines:
        lines.append("## Baseline History")
        for bl in state.baselines[-5:]:
            lines.append(f"- {bl['at']}: {bl['passed']}p / "
                         f"{bl['xfailed']}x / {bl['failed']}f")
        lines.append("")

    # Broken refs
    broken = query.broken_refs(state)
    if broken:
        lines.append(f"## Broken References ({len(broken)})")
        for ref in broken:
            lines.append(f"- {ref['from_id']} → {ref['to_id']}")
        lines.append("")

    return "\n".join(lines)


def emit_timeline(state, session_start=None, session_end=None):
    """Chronological event stream."""
    events = query.timeline(state, session_start, session_end)
    lines = ["# Timeline", ""]

    current_session = None
    for e in events:
        sid = e.get("session_id")
        if sid != current_session:
            current_session = sid
            lines.append(f"## Session {sid or '?'}")
            lines.append("")

        dt = e.get("created_at", "")[:19]
        etype = e.get("type", "?")
        tag = e.get("tag", "")
        tag_str = f" [{tag}]" if tag and tag != "active" else ""
        lines.append(f"- `{dt}` **{etype}**: {e.get('title', '')}{tag_str}")

    return "\n".join(lines)
