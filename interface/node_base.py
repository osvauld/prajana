"""
node_base.py — BusNode abstract base class.

Every knowledge source on the jnana bus is a BusNode.
Every node has one job: given a word and its pada classification,
return triples. Nothing else.

The bus does not care where knowledge comes from.
It only cares that it comes back as triples.
"""

from abc import ABC, abstractmethod
from triples import BusResponse, Triple
from pada_viveka import PadaResult


class BusNode(ABC):
    """
    A single knowledge source on the jnana bus.

    Subclass this and implement query().
    Set name and priority as class attributes.

    priority: lower number = queried earlier.
      10  — proof graph (primary, fastest)
      15  — static constants (always available)
      30  — second graph (another domain)
      50  — wikipedia/wikidata (network)
      70  — llm (slow, broad coverage)
      90  — terminal (ask the human, last resort)
    """

    name: str = "unnamed"
    priority: int = 50

    @abstractmethod
    def query(self, word: str, pada: PadaResult, context: dict) -> BusResponse:
        """
        Query this node for knowledge about `word`.

        word:    the surface word to look up
        pada:    its classification from pada_viveka
        context: {session_id, known_concepts, sentence, turn_id, ...}

        Returns BusResponse with triples (may be empty if not found).
        Must not raise — catch internally and return empty BusResponse.
        """
        pass

    def available(self) -> bool:
        """
        Is this node currently reachable?
        Default: always available.
        Override for nodes that require network or a running process.
        """
        return True

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} name={self.name!r} priority={self.priority}>"
        )
