"""
server.py — Unix socket server for querying tantras and om files.

Protocol: newline-delimited JSON over a Unix domain socket.
Same style as the vyakarana server — one JSON command per line,
one JSON response per line.

Commands:
  {"command": "tantra-summary"}
  {"command": "tantra-source", "name": "execute-mantra"}
  {"command": "tantra-group", "group": "pipeline"}
  {"command": "tantra-groups"}
  {"command": "tantra-callgraph"}
  {"command": "tantra-callers", "name": "derive-chain"}
  {"command": "tantra-callees", "name": "anuvada-ganana"}

  {"command": "om-summary"}
  {"command": "om-summary", "depth": 3}
  {"command": "om-source", "name": "velocity"}
  {"command": "om-domain", "domain": "kosha/math/number/operations"}
  {"command": "om-domains"}
  {"command": "om-domains", "depth": 2}
  {"command": "om-with-key", "key": "eval"}
  {"command": "om-with-relation", "relation": "pratipaksha"}

  {"command": "search", "pattern": "viveka"}
  {"command": "search", "pattern": "viveka", "scope": "tantras"}
  {"command": "search", "pattern": "viveka", "scope": "om"}

  {"command": "reload"}
  {"command": "ping"}

Usage:
  python3 -m tools.brahman serve --socket /tmp/brahman.sock
"""

import json
import os
import socket
import sys
import threading
from pathlib import Path

from . import tantras, om, tests as test_meta, runner, cache as cache_mod


DEFAULT_SOCKET = "/tmp/brahman.sock"


class BrahmanServer:
    """Serves tantra + om queries over a Unix socket."""

    def __init__(self, socket_path=DEFAULT_SOCKET):
        self.socket_path = socket_path
        self._tantras = None
        self._oms = None
        self._tantra_cg = None
        self._tantra_rcg = None
        self._load()

    def _load(self):
        """Load all data from disk."""
        self._tantras = tantras.load_all()
        self._oms = om.load_all()
        self._tantra_cg = tantras.call_graph(self._tantras)
        self._tantra_rcg = tantras.reverse_call_graph(self._tantra_cg)
        n_t = len(self._tantras)
        n_o = len(self._oms)
        print(f"[brahman] loaded {n_t} tantras, {n_o} om nodes", file=sys.stderr)

    def _reload(self):
        """Reload from disk."""
        self._load()
        return {"status": "ok", "tantras": len(self._tantras), "oms": len(self._oms)}

    def handle_command(self, req):
        """Dispatch a parsed JSON command dict, return response dict."""
        cmd = req.get("command", "")

        try:
            # ── tantra commands ────────────────────────────────────────────
            if cmd == "tantra-summary":
                return {"status": "ok", **tantras.to_json_summary(self._tantras)}

            elif cmd == "tantra-source":
                name = req.get("name", "")
                t = self._tantras.get(name)
                if not t:
                    return {"status": "error", "error": f"tantra '{name}' not found"}
                return {
                    "status": "ok",
                    "tantra": {
                        "name": t["name"],
                        "group": t["group"],
                        "path": t["path"],
                        "lines": t["lines"],
                        "takes": t["takes"],
                        "bindings": t["bindings"],
                        "calls": t["calls"],
                        "returns": t["returns"],
                        "source": t["source"],
                    },
                }

            elif cmd == "tantra-group":
                group = req.get("group", "")
                data = tantras.to_json_full(self._tantras, group=group)
                if not data:
                    return {
                        "status": "error",
                        "error": f"group '{group}' not found",
                        "available": list(tantras.TANTRA_GROUPS.keys()),
                    }
                return {
                    "status": "ok",
                    "group": group,
                    "count": len(data),
                    "tantras": data,
                }

            elif cmd == "tantra-groups":
                bg = tantras.by_group(self._tantras)
                groups = {}
                for gname, desc in tantras.TANTRA_GROUPS.items():
                    gt = bg.get(gname, [])
                    if gt:
                        groups[gname] = {
                            "description": desc,
                            "count": len(gt),
                            "lines": sum(t["lines"] for t in gt),
                            "tantras": sorted(t["name"] for t in gt),
                        }
                return {"status": "ok", "groups": groups}

            elif cmd == "tantra-callgraph":
                return {
                    "status": "ok",
                    "calls": self._tantra_cg,
                    "called_by": self._tantra_rcg,
                }

            elif cmd == "tantra-callers":
                name = req.get("name", "")
                callers = self._tantra_rcg.get(name, [])
                return {"status": "ok", "name": name, "callers": callers}

            elif cmd == "tantra-callees":
                name = req.get("name", "")
                if name not in self._tantras:
                    return {"status": "error", "error": f"tantra '{name}' not found"}
                callees = self._tantra_cg.get(name, [])
                return {"status": "ok", "name": name, "callees": callees}

            # ── om commands ────────────────────────────────────────────────
            elif cmd == "om-summary":
                depth = req.get("depth", 2)
                return {"status": "ok", **om.to_json_summary(self._oms)}

            elif cmd == "om-source":
                name = req.get("name", "")
                o = self._oms.get(name)
                if not o:
                    return {"status": "error", "error": f"om node '{name}' not found"}
                return {"status": "ok", "om": om.to_json_node(o)}

            elif cmd == "om-domain":
                domain = req.get("domain", "")
                info = om.domain_info(self._oms, domain)
                if info["total_count"] == 0:
                    return {
                        "status": "error",
                        "error": f"no nodes under domain '{domain}'",
                    }
                # include subdomains + direct nodes with source
                data = om.to_json_domain(self._oms, domain)
                return {
                    "status": "ok",
                    "domain": domain,
                    "total_count": info["total_count"],
                    "direct_count": info["direct_count"],
                    "total_lines": info["total_lines"],
                    "direct_nodes": info["direct_nodes"],
                    "subdomains": info["subdomains"],
                    "nodes": data,
                }

            elif cmd == "om-domains":
                depth = req.get("depth", 2)
                groups = om.by_domain(self._oms, depth=depth)
                domains = {}
                for dname, nodes in groups.items():
                    domains[dname] = {
                        "count": len(nodes),
                        "lines": sum(n["lines"] for n in nodes),
                        "nodes": sorted(n["name"] for n in nodes),
                    }
                return {"status": "ok", "depth": depth, "domains": domains}

            elif cmd == "om-with-key":
                key = req.get("key", "")
                nodes = om.with_shabda_key(self._oms, key)
                return {
                    "status": "ok",
                    "key": key,
                    "count": len(nodes),
                    "nodes": [
                        {
                            "name": n["name"],
                            "domain": n["domain"],
                            "value": n["shabda_keys"].get(key, ""),
                        }
                        for n in nodes
                    ],
                }

            elif cmd == "om-with-relation":
                rel = req.get("relation", "")
                nodes = om.with_edge_relation(self._oms, rel)
                return {
                    "status": "ok",
                    "relation": rel,
                    "count": len(nodes),
                    "nodes": [
                        {
                            "name": n["name"],
                            "domain": n["domain"],
                            "edges": [e for e in n["edges"] if e["relation"] == rel],
                        }
                        for n in nodes
                    ],
                }

            # ── cross-cutting ──────────────────────────────────────────────
            elif cmd == "search":
                pattern = req.get("pattern", "")
                scope = req.get("scope", "all")
                results = {}
                if scope in ("all", "tantras"):
                    results["tantras"] = tantras.search(self._tantras, pattern)
                if scope in ("all", "om"):
                    results["om"] = om.search(self._oms, pattern)
                total = sum(
                    sum(len(r["matches"]) for r in rs) for rs in results.values()
                )
                return {
                    "status": "ok",
                    "pattern": pattern,
                    "total_matches": total,
                    **results,
                }

            elif cmd == "reload":
                return self._reload()

            elif cmd == "ping":
                return {
                    "status": "ok",
                    "tantras": len(self._tantras),
                    "oms": len(self._oms),
                }

            # ── test commands ──────────────────────────────────────────────
            elif cmd == "test-list":
                # discover tests from v2/ files statically (no server needed)
                # optional filters: layer, gate, pattern, xfail_only, passing_only
                all_tests = test_meta.load_all()
                filtered = test_meta.filter_tests(
                    all_tests,
                    layer=req.get("layer"),
                    gate=req.get("gate"),
                    pattern=req.get("pattern"),
                    xfail_only=req.get("xfail_only", False),
                    passing_only=req.get("passing_only", False),
                )
                return {
                    "status": "ok",
                    "total": len(filtered),
                    "summary": test_meta.summary(all_tests),
                    "tests": [
                        {
                            "name": t["name"],
                            "layer": t["layer"],
                            "xfail": t["xfail"],
                            "gate": t["xfail_gate"],
                            "doc": t["doc"],
                            "lineno": t["lineno"],
                        }
                        for t in filtered
                    ],
                }

            elif cmd == "test-run":
                # run tests via pytest subprocess
                # optional: layer, gate, name, pattern, socket (default /tmp/vy.sock)
                socket_path = req.get("socket", "/tmp/vy.sock")
                result = runner.run(
                    layer=req.get("layer"),
                    gate=req.get("gate"),
                    name=req.get("name"),
                    pattern=req.get("pattern"),
                    socket_path=socket_path,
                    verbose=req.get("verbose", False),
                    timeout=req.get("timeout", 120),
                )
                return {"status": "ok", **result}

            elif cmd == "test-summary":
                all_tests = test_meta.load_all()
                return {"status": "ok", **test_meta.summary(all_tests)}

            # ── cache commands ─────────────────────────────────────────────
            elif cmd == "cache-summary":
                # read the pytest result cache and return aggregate summary
                cache_dir = req.get("cache_dir")
                cache_path = Path(cache_dir) if cache_dir else cache_mod.DEFAULT_CACHE
                if not cache_path.exists():
                    return {
                        "status": "error",
                        "error": f"cache not found: {cache_path}",
                    }
                _, entries = cache_mod.load(cache_path)
                return {"status": "ok", **cache_mod.summarize(entries)}

            elif cmd == "cache-entry":
                # return the full cached entry for one test
                test_name = req.get("test", "")
                cache_dir = req.get("cache_dir")
                cache_path = Path(cache_dir) if cache_dir else cache_mod.DEFAULT_CACHE
                _, entries = cache_mod.load(cache_path)
                # match by test name substring or full nodeid
                matches = [e for e in entries if test_name in e["test"]]
                if not matches:
                    return {
                        "status": "error",
                        "error": f"no entry matching '{test_name}'",
                    }
                return {"status": "ok", "entries": matches}

            elif cmd == "cache-failed":
                # return all failed test entries with diagnosis
                cache_dir = req.get("cache_dir")
                cache_path = Path(cache_dir) if cache_dir else cache_mod.DEFAULT_CACHE
                _, entries = cache_mod.load(cache_path)
                fail_entries = cache_mod.failed(entries)
                return {
                    "status": "ok",
                    "count": len(fail_entries),
                    "tests": [
                        {
                            **cache_mod.diagnose(e),
                            "test": e["test"],
                            "failure": e.get("failure"),
                            "duration": e.get("duration", 0),
                            "calls": cache_mod.call_chain(e.get("calls", [])),
                        }
                        for e in fail_entries
                    ],
                }

            elif cmd == "cache-gates":
                # return xfailed entries grouped by gate
                cache_dir = req.get("cache_dir")
                cache_path = Path(cache_dir) if cache_dir else cache_mod.DEFAULT_CACHE
                gate = req.get("gate")
                _, entries = cache_mod.load(cache_path)
                if gate:
                    gate_entries = cache_mod.entries_for_gate(entries, gate)
                    return {
                        "status": "ok",
                        "gate": gate,
                        "count": len(gate_entries),
                        "tests": [e["test"] for e in gate_entries],
                        "details": [
                            {
                                "test": e["test"],
                                "reason": (e.get("xfail") or {}).get("reason", "")[
                                    :120
                                ],
                            }
                            for e in gate_entries
                        ],
                    }
                else:
                    gates = cache_mod.by_gate(entries)
                    return {
                        "status": "ok",
                        "gates": {
                            g: [e["test"] for e in gl]
                            for g, gl in sorted(gates.items())
                        },
                    }

            elif cmd == "cache-diff":
                # diff current cache against a previous summary.json
                previous = req.get("previous")
                if not previous:
                    return {
                        "status": "error",
                        "error": "missing required field: previous (path to previous summary.json)",
                    }
                cache_dir = req.get("cache_dir")
                cache_path = Path(cache_dir) if cache_dir else cache_mod.DEFAULT_CACHE
                _, entries = cache_mod.load(cache_path)
                return {"status": "ok", **cache_mod.diff(entries, previous)}

            elif cmd == "cache-fix-xpass":
                # remove @xfail markers from tests that now pass
                dry_run = req.get("dry_run", True)
                cache_dir = req.get("cache_dir")
                cache_path = Path(cache_dir) if cache_dir else cache_mod.DEFAULT_CACHE
                _, entries = cache_mod.load(cache_path)
                xp = cache_mod.xpassed(entries)
                if not xp:
                    return {
                        "status": "ok",
                        "message": "no xpassed tests in cache",
                        "fixed": [],
                    }
                results = cache_mod.fix_xpass(entries, dry_run=dry_run)
                return {
                    "status": "ok",
                    "dry_run": dry_run,
                    "count": len(
                        [r for r in results if r.get("status") in ("fixed", "dry-run")]
                    ),
                    "results": results,
                }

            elif cmd == "cache-slow":
                # return slowest calls and tests
                cache_dir = req.get("cache_dir")
                cache_path = Path(cache_dir) if cache_dir else cache_mod.DEFAULT_CACHE
                top_n = req.get("top_n", 10)
                _, entries = cache_mod.load(cache_path)
                return {
                    "status": "ok",
                    "slow_calls": cache_mod.slowest_calls(entries, top_n=top_n),
                    "slow_tests": sorted(
                        [
                            {
                                "test": e["test"],
                                "duration": e.get("duration", 0),
                                "calls": len(e.get("calls", [])),
                            }
                            for e in entries
                            if e.get("duration", 0) > 0.5
                        ],
                        key=lambda x: x["duration"],
                        reverse=True,
                    )[:top_n],
                }

            else:
                return {
                    "status": "error",
                    "error": f"unknown command: {cmd}",
                    "available": [
                        "tantra-summary",
                        "tantra-source",
                        "tantra-group",
                        "tantra-groups",
                        "tantra-callgraph",
                        "tantra-callers",
                        "tantra-callees",
                        "om-summary",
                        "om-source",
                        "om-domain",
                        "test-list",
                        "test-run",
                        "test-summary",
                        "om-domains",
                        "om-with-key",
                        "om-with-relation",
                        "search",
                        "reload",
                        "ping",
                    ],
                }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _handle_client(self, conn):
        """Handle one client connection (multiple commands allowed)."""
        try:
            buf = b""
            while True:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                buf += chunk
                # process complete lines
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        req = json.loads(line.decode("utf-8"))
                    except json.JSONDecodeError as e:
                        resp = {"status": "error", "error": f"invalid JSON: {e}"}
                        conn.sendall((json.dumps(resp) + "\n").encode())
                        continue
                    resp = self.handle_command(req)
                    conn.sendall((json.dumps(resp) + "\n").encode())
                # also try to parse buf as a complete JSON (no trailing newline)
                if buf.strip():
                    try:
                        req = json.loads(buf.decode("utf-8"))
                        resp = self.handle_command(req)
                        conn.sendall((json.dumps(resp) + "\n").encode())
                        buf = b""
                    except json.JSONDecodeError:
                        pass  # incomplete, wait for more data
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            conn.close()

    def serve(self):
        """Start the socket server. Blocks forever."""
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(self.socket_path)
        sock.listen(5)
        print(f"[brahman] listening on {self.socket_path}", file=sys.stderr)
        print(
            f"[brahman] {len(self._tantras)} tantras, {len(self._oms)} om nodes ready",
            file=sys.stderr,
        )

        try:
            while True:
                conn, _ = sock.accept()
                t = threading.Thread(
                    target=self._handle_client, args=(conn,), daemon=True
                )
                t.start()
        except KeyboardInterrupt:
            print("\n[brahman] shutting down", file=sys.stderr)
        finally:
            sock.close()
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)


# ── client (for use from other Python code / CLI) ─────────────────────────────


class BrahmanClient:
    """Thin client for the brahman socket server."""

    def __init__(self, socket_path=DEFAULT_SOCKET):
        self.socket_path = socket_path

    def _call(self, req):
        """Send one command, receive one response."""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.socket_path)
        try:
            sock.sendall((json.dumps(req) + "\n").encode())
            data = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk
                try:
                    return json.loads(data.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
            return {"status": "error", "error": "no response"}
        finally:
            sock.close()

    def ping(self):
        return self._call({"command": "ping"})

    def tantra_summary(self):
        return self._call({"command": "tantra-summary"})

    def tantra_source(self, name):
        return self._call({"command": "tantra-source", "name": name})

    def tantra_group(self, group):
        return self._call({"command": "tantra-group", "group": group})

    def tantra_groups(self):
        return self._call({"command": "tantra-groups"})

    def tantra_callgraph(self):
        return self._call({"command": "tantra-callgraph"})

    def tantra_callers(self, name):
        return self._call({"command": "tantra-callers", "name": name})

    def tantra_callees(self, name):
        return self._call({"command": "tantra-callees", "name": name})

    def om_summary(self, depth=2):
        return self._call({"command": "om-summary", "depth": depth})

    def om_source(self, name):
        return self._call({"command": "om-source", "name": name})

    def om_domain(self, domain):
        return self._call({"command": "om-domain", "domain": domain})

    def om_domains(self, depth=2):
        return self._call({"command": "om-domains", "depth": depth})

    def om_with_key(self, key):
        return self._call({"command": "om-with-key", "key": key})

    def om_with_relation(self, relation):
        return self._call({"command": "om-with-relation", "relation": relation})

    def search(self, pattern, scope="all"):
        return self._call({"command": "search", "pattern": pattern, "scope": scope})

    def reload(self):
        return self._call({"command": "reload"})
