"""live.py — Live graph analysis using the running engine.

Static analysis reads files. Live analysis walks the actual graph.
The diff between them is where bugs hide.
"""

from collections import defaultdict


def connect():
    """Get a live engine client."""
    from upakarana.engine.client import Client
    return Client()


def graph_stats(client):
    """Basic graph counts from the live engine."""
    try:
        result = client.eval('graph-stats')
        if isinstance(result, dict):
            return result
    except Exception:
        pass

    # Fallback: count via inspection
    tantras = client.list_tantras()
    return {
        "tantras_loaded": len(tantras),
    }


def live_node_count(client):
    """Count nodes by sampling — engine doesn't expose total directly."""
    try:
        result = client.eval('node-count')
        return {"total": result}
    except Exception:
        pass
    return {"total": "unknown (no node-count op)"}


def live_walk(client, node, relation):
    """Walk an edge from a node in the live graph."""
    try:
        return client.walk(node, relation)
    except Exception as e:
        return {"error": str(e)}


def live_inspect(client, name):
    """Full node inspection from live graph."""
    try:
        return client.inspect(name)
    except Exception as e:
        return {"error": str(e)}


def pratipaksha_walk(client):
    """Walk pratipaksha edges on all ops and verify involution in live graph.

    For each op with eval: key, walk pratipaksha, then walk pratipaksha
    on the result. If it doesn't return to the original, the involution
    is broken in the live graph.
    """
    from upakarana.parsers import shabda
    shabda_nodes = shabda.load_all()

    ops = []
    for name, node in shabda_nodes.items():
        if "eval" in node.get("fields", {}):
            ops.append(name)

    results = []
    for op in sorted(ops):
        try:
            pp = client.walk(op, "pratipaksha")
            if not pp:
                results.append({"op": op, "pratipaksha": None, "round_trip": None})
                continue
            inv = pp[0] if isinstance(pp, list) else str(pp)
            # Walk back
            pp2 = client.walk(str(inv), "pratipaksha")
            back = pp2[0] if isinstance(pp2, list) and pp2 else None
            results.append({
                "op": op,
                "pratipaksha": str(inv),
                "round_trip": str(back) if back else None,
                "ok": str(back) == op if back else False,
            })
        except Exception as e:
            results.append({"op": op, "error": str(e)})

    return {
        "ops": results,
        "symmetric": [r for r in results if r.get("ok")],
        "broken": [r for r in results if not r.get("ok") and r.get("pratipaksha")],
        "no_pratipaksha": [r for r in results if r.get("pratipaksha") is None],
    }


def panchaavayava_walk(client):
    """Walk the five-limbed proof structure in the live graph.

    Checks: does panchaavayava exist? Do its yukta edges resolve?
    Does the phala chain connect?
    """
    result = {}

    # Check panchaavayava node
    try:
        node = client.inspect("panchaavayava")
        result["exists"] = True
        result["edges"] = node
    except Exception:
        result["exists"] = False
        return result

    # Walk yukta (the five limbs)
    try:
        limbs = client.walk("panchaavayava", "yukta")
        result["limbs"] = limbs
    except Exception as e:
        result["limbs_error"] = str(e)

    # Walk the phala chain: hetu → udaharana → upanaya → nigamana
    chain = []
    current = "hetu"
    for _ in range(5):
        try:
            phala = client.walk(current, "phala")
            if phala:
                nxt = phala[0] if isinstance(phala, list) else str(phala)
                chain.append(f"{current} →phala→ {nxt}")
                current = str(nxt)
            else:
                chain.append(f"{current} →phala→ (none)")
                break
        except Exception:
            chain.append(f"{current} →phala→ (error)")
            break
    result["phala_chain"] = chain

    return result


def ghost_walk(client, ghost_names):
    """Try to inspect ghost names in the live graph.

    Some static ghosts resolve in the live graph (the engine handles
    disambiguation that the static parser can't).
    """
    resolved = []
    truly_missing = []
    for name in ghost_names:
        try:
            node = client.inspect(name)
            if node and not node.get("error"):
                resolved.append({"name": name, "layer": node.get("layer", "?")})
            else:
                truly_missing.append(name)
        except Exception:
            truly_missing.append(name)
    return {
        "resolved": resolved,
        "truly_missing": truly_missing,
    }


def signal_trace(client, sentence):
    """Trace signal flow through an actual question.

    Runs the full pipeline via eval and extracts _signal triples.
    Also shows the pipeline stages and key derived triples.
    """
    result = {"sentence": sentence}

    # Get pipeline trace (refine stages)
    try:
        trace = client.pipeline_trace(sentence)
        result["stages"] = [t["stage"] for t in trace]
        last_refine = trace[-1] if trace else {}
        result["refine_triples"] = len(last_refine.get("triples", []))

        # Key edges in final refine stage
        triples = last_refine.get("triples", [])
        result["satya"] = [t[0] for t in triples if t[1] == "satya"]
        result["sankhya"] = [[t[0], t[2]] for t in triples if t[1] == "sankhya"]
        result["ownership"] = [[t[0], t[2]] for t in triples if t[1] == "shashthi-vibhakti"]
        result["kaala"] = [[t[0], t[2]] for t in triples if t[1] == "kaala"]
        result["vachana"] = [[t[0], t[2]] for t in triples if t[1] == "vachana"]
    except Exception as e:
        result["trace_error"] = str(e)

    # Get the full answer
    try:
        answer = client.ask(sentence)
        result["answer"] = answer
    except Exception as e:
        result["answer_error"] = str(e)

    return result


def static_vs_live(client):
    """Compare static parser view vs live engine view.

    Shows where they disagree — the meaningful diff.
    """
    from upakarana.parsers import om5, tantra4, shabda

    # Static counts
    om_nodes = om5.load_all()
    tantras = tantra4.load_all()
    shabda_nodes = shabda.load_all()

    static = {
        "om5_nodes": len(om_nodes),
        "tantras_on_disk": len(tantras),
        "shabda_nodes": len(shabda_nodes),
    }

    # Live counts
    live_tantras = client.list_tantras()
    live = {
        "tantras_loaded": len(live_tantras),
    }

    # Tantras on disk but not loaded
    disk_names = set(tantras.keys())
    live_names = set(live_tantras)
    only_disk = sorted(disk_names - live_names)
    only_live = sorted(live_names - disk_names)

    # Ghost resolution: check top structural ghosts against live graph
    from upakarana.analysis.ghosts import structural_ghosts
    top_ghosts = [g["name"] for g in structural_ghosts()[:20]]
    ghost_check = ghost_walk(client, top_ghosts)

    return {
        "static": static,
        "live": live,
        "tantras_only_on_disk": only_disk,
        "tantras_only_in_engine": only_live,
        "ghost_resolution": ghost_check,
    }
