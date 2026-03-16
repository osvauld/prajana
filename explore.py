"""explore.py — exploratory probe of the live vyakarana graph.

Run: python3 explore.py
Server must be running at /tmp/vy.sock
"""

import json
import socket
import sys

SOCK = "/tmp/vy.sock"


class Client:
    def __init__(self, path=SOCK):
        self._path = path
        self._sock = None
        self._buf = b""
        self._connect()

    def _connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self._path)
        self._sock = s

    def _send(self, payload):
        data = json.dumps(payload) + "\n"
        self._sock.sendall(data.encode())
        while b"\n" not in self._buf:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise EOFError("server closed")
            self._buf += chunk
        line, self._buf = self._buf.split(b"\n", 1)
        return json.loads(line.decode())

    def eval(self, expr):
        resp = self._send({"command": "eval-json", "expr": expr})
        if resp.get("status") == "error":
            return f"ERROR: {resp['error']}"
        return resp["result"]

    def ask(self, question, session_id="explore"):
        resp = self._send({"question": question, "session_id": session_id})
        if resp.get("status") == "error":
            return f"ERROR: {resp['error']}"
        return resp.get("answer_text", "")


def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def show(label, val):
    print(f"  {label:45s} => {val!r}")


vy = Client()

# ── 1. ALL MANTRAS: krama-rhs, krama-lhs, janya edges ─────────────────────────
section("1. All physics mantras — krama-rhs / janya / krama-lhs")

mantras = vy.eval('walk-in "execute-chain" "kriya"')
print(f"  Total mantras with execute-chain-kriya: {len(mantras)}\n")

for m in sorted(mantras):
    rhs = vy.eval(f'shabda "{m}" "krama-rhs"')
    lhs = vy.eval(f'shabda "{m}" "krama-lhs"')
    name = vy.eval(f'shabda "{m}" "name"')
    janya = vy.eval(f'walk "{m}" "janya"')
    phala = vy.eval(f'walk "{m}" "phala"')
    krama = vy.eval(f'walk "{m}" "krama"')
    print(f"  [{m}]")
    print(f"    name:      {name!r}")
    print(f"    krama-lhs: {lhs!r}")
    print(f"    krama-rhs: {rhs!r}")
    print(f"    janya:     {janya}")
    print(f"    phala:     {phala}")
    print(f"    krama:     {krama}")

# ── 2. MASS-DENSITY BUG: why is test failing? ─────────────────────────────────
section("2. mass-density-mantra — debug why test fails")

q = "find density given mass 60 volume 2"
print(f"  Question: {q!r}")
answer = vy.ask(q)
print(f"  Answer: {answer!r}")

# check if volume and mass resolve
show("lookup-word 'volume'", vy.eval('lookup-word "volume"'))
show("lookup-word 'mass'", vy.eval('lookup-word "mass"'))
show("lookup-word 'density'", vy.eval('lookup-word "density"'))

# check the BQG output
print("\n  BQG graph for 'find density given mass 60 volume 2':")
bqg = vy.eval('build-question-graph "find density given mass 60 volume 2"')
for t in bqg:
    print(f"    {t}")

# ── 3. DERIVE-STEP: what does it do on a simple graph? ─────────────────────────
section("3. derive-step — probe on a known-good graph")

# manually construct a graph with mass + volume bound
print("  Testing derive-step with mass=60, volume=2 manually:")
expr = """derive-step [["mass","sankhya",60],["mass","satya","mass"],
                        ["volume","sankhya",2],["volume","satya","volume"],
                        ["mass-density","satya","mass-density"]]"""
result = vy.eval(expr)
print(f"  Result triples:")
for t in result:
    print(f"    {t}")

# ── 4. EXECUTE-CHAIN: test directly ───────────────────────────────────────────
section("4. execute-chain — direct tests on division mantras")

# mass-density: ρ = m/V = 60/2 = 30
# krama-rhs: volume,mass → after List.rev stack is [mass_val, volume_val]
# stack machine: pop top (mass=60) as dividend, pop next (volume=2) as divisor → 60/2=30
show(
    "execute-chain mass-density-mantra [60, 2]",
    vy.eval('execute-chain "mass-density-mantra" [60, 2]'),
)
show(
    "execute-chain mass-density-mantra [2, 60]",
    vy.eval('execute-chain "mass-density-mantra" [2, 60]'),
)

# acceleration: a=(v-u)/t, krama=[sub,div], krama-rhs: time,initial-velocity,final-velocity
# List.rev → stack [final-vel, initial-vel, time]
# sub: pop final-vel, pop initial-vel → final-vel - initial-vel
# div: pop result, pop time → result/time
# For v=20, u=0, t=4: sub(20,0)=20, div(20,4)=5 ✓
show(
    "execute-chain acceleration-mantra [4, 0, 20] (t,u,v order)",
    vy.eval('execute-chain "acceleration-mantra" [4, 0, 20]'),
)
show(
    "execute-chain acceleration-mantra [0, 4, 20]",
    vy.eval('execute-chain "acceleration-mantra" [0, 4, 20]'),
)
show(
    "execute-chain acceleration-mantra [20, 0, 4]",
    vy.eval('execute-chain "acceleration-mantra" [20, 0, 4]'),
)

# ── 5. MATCH-MANTRA: solve-for detection ──────────────────────────────────────
section("5. match-mantra — solve-for detection on density graph")

# build full pipeline graph
full_graph = vy.eval(
    'fixpoint (build-question-graph "find density given mass 60 volume 2") avrti-refine'
)
print("  After avrti-refine:")
for t in full_graph:
    print(f"    {t}")

match = vy.eval(
    'match-mantra (fixpoint (build-question-graph "find density given mass 60 volume 2") avrti-refine)'
)
print(f"\n  match-mantra result: {match!r}")

# ── 6. JANYA EDGES: do any mantras have them? ─────────────────────────────────
section("6. janya edges — which mantras have them?")

for m in sorted(mantras):
    janya = vy.eval(f'walk "{m}" "janya"')
    if janya:
        print(f"  {m}: janya={janya}")
    else:
        print(f"  {m}: NO janya edges")

# ── 7. PHALA EDGES: do any mantras have them? ─────────────────────────────────
section("7. phala edges — which mantras have them?")

for m in sorted(mantras):
    phala = vy.eval(f'walk "{m}" "phala"')
    if phala:
        print(f"  {m}: phala={phala}")
    else:
        print(f"  {m}: NO phala edges")

# ── 8. KNOWN NODE: does brahman/sangati/known.om exist? ───────────────────────
section("8. sangati/known node — exists?")
show("lookup-word 'known'", vy.eval('lookup-word "known"'))
show("node-satya 'known'", vy.eval('node-satya "known"'))
show("walk 'acceleration' 'known'", vy.eval('walk "acceleration" "known"'))

# ── 9. CHAIN TESTS: current full pipeline behaviour ───────────────────────────
section("9. Full pipeline — current behaviour on key questions")

questions = [
    "find density given mass 60 volume 2",
    "find pressure given force 100 area 5",
    "find acceleration given initial velocity 0 final velocity 20 time 4",
    "find kinetic energy given initial velocity 0 acceleration 4 time 10 mass 1200",
    "find force given initial velocity 0 final velocity 20 time 4 mass 5",
]
for q in questions:
    ans = vy.ask(q, session_id=q[:20])
    print(f"  Q: {q!r}")
    print(f"  A: {ans!r}\n")

# ── 10. DERIVE-STEP: does it fire mass-density? ───────────────────────────────
section("10. derive-step on density — step by step")

# start from a clean graph with mass+volume bound
g0 = vy.eval("""[["mass","satya","mass"],["mass","sankhya",60],
                  ["volume","satya","volume"],["volume","sankhya",2],
                  ["mass-density","satya","mass-density"]]""")
print("  Input graph:")
for t in g0:
    print(f"    {t}")

g1 = vy.eval("""derive-step [["mass","satya","mass"],["mass","sankhya",60],
                               ["volume","satya","volume"],["volume","sankhya",2],
                               ["mass-density","satya","mass-density"]]""")
print("  After derive-step:")
for t in g1:
    print(f"    {t}")

print("\nDone.")
