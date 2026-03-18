"""
interface — the open-book knowledge layer for nam.

The proof graph knows what is in the brahman.
The interface layer knows how to ask elsewhere when the graph doesn't know.

Modules:
  transport    — Unix socket send/receive (one function)
  triples      — Triple type, BusResponse, graph extraction helpers
  pada_viveka  — word-class discrimination (tinanta/subanta/visheshana/...)
  node_base    — BusNode abstract base
  nodes/       — concrete nodes: graph, terminal, static, llm
  bus          — JnanaBus: routes queries, injects triples
  session      — BusSession: open-book question/answer loop
  anveshana    — transliteration and Sanskrit lookup sources

Quick start:
    from interface.bus     import JnanaBus
    from interface.session import BusSession
    from interface.nodes   import TerminalNode, LLMNode

    bus = JnanaBus('/tmp/vy.sock')
    bus.add(TerminalNode())

    session = bus.open_session('my-session')
    result  = session.ask("find rest energy of electron")
    print(result['answer'])
"""

from bus import JnanaBus
from session import BusSession, PartialKnowledge

__all__ = ["JnanaBus", "BusSession", "PartialKnowledge"]
