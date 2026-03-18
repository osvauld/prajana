"""
nodes/static.py — StaticNode.

Physics constants, particle data, mathematical constants.
The reference table at the back of the textbook.
Always available, zero latency, high confidence.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from triples import BusResponse, Triple
from node_base import BusNode
from pada_viveka import PadaResult


# The built-in table.
# Extend at runtime with StaticNode.add(word, triples).
# Or pass extra={word: triples} to the constructor.
CONSTANTS: dict[str, list[Triple]] = {
    # ── fundamental constants ──────────────────────────────────────────────────
    "c": [
        ("c", "satya", "speed-of-light"),
        ("c", "sankhya", "299792458"),
        ("c", "matra", "m/s"),
    ],
    "speed-of-light": [
        ("speed-of-light", "sankhya", "299792458"),
        ("speed-of-light", "matra", "m/s"),
    ],
    "h": [
        ("h", "satya", "planck-constant"),
        ("h", "sankhya", "6.62607015e-34"),
        ("h", "matra", "J⋅s"),
    ],
    "planck-constant": [
        ("planck-constant", "sankhya", "6.62607015e-34"),
        ("planck-constant", "matra", "J⋅s"),
    ],
    "e": [
        ("e", "satya", "elementary-charge"),
        ("e", "sankhya", "1.602176634e-19"),
        ("e", "matra", "C"),
    ],
    "elementary-charge": [
        ("elementary-charge", "sankhya", "1.602176634e-19"),
        ("elementary-charge", "matra", "C"),
    ],
    "k": [
        ("k", "satya", "boltzmann-constant"),
        ("k", "sankhya", "1.380649e-23"),
        ("k", "matra", "J/K"),
    ],
    "boltzmann-constant": [
        ("boltzmann-constant", "sankhya", "1.380649e-23"),
        ("boltzmann-constant", "matra", "J/K"),
    ],
    "g": [
        ("g", "satya", "gravitational-acceleration"),
        ("g", "sankhya", "9.80665"),
        ("g", "matra", "m/s²"),
    ],
    "gravitational-acceleration": [
        ("gravitational-acceleration", "sankhya", "9.80665"),
        ("gravitational-acceleration", "matra", "m/s²"),
    ],
    "G": [
        ("G", "satya", "gravitational-constant"),
        ("G", "sankhya", "6.674e-11"),
        ("G", "matra", "N⋅m²/kg²"),
    ],
    "na": [
        ("na", "satya", "avogadro-constant"),
        ("na", "sankhya", "6.02214076e23"),
        ("na", "matra", "mol⁻¹"),
    ],
    "avogadro-constant": [
        ("avogadro-constant", "sankhya", "6.02214076e23"),
        ("avogadro-constant", "matra", "mol⁻¹"),
    ],
    "r": [
        ("r", "satya", "gas-constant"),
        ("r", "sankhya", "8.314462618"),
        ("r", "matra", "J/mol⋅K"),
    ],
    # ── particles (rest mass energies in MeV/c²) ──────────────────────────────
    "electron": [
        ("electron", "satya", "particle"),
        ("electron", "rest-mass-energy", "0.511"),
        ("electron", "matra", "MeV"),
        ("electron", "charge", "-1"),
        ("electron", "spin", "0.5"),
    ],
    "proton": [
        ("proton", "satya", "particle"),
        ("proton", "rest-mass-energy", "938.272"),
        ("proton", "matra", "MeV"),
        ("proton", "charge", "+1"),
        ("proton", "spin", "0.5"),
    ],
    "neutron": [
        ("neutron", "satya", "particle"),
        ("neutron", "rest-mass-energy", "939.565"),
        ("neutron", "matra", "MeV"),
        ("neutron", "charge", "0"),
        ("neutron", "spin", "0.5"),
    ],
    "photon": [
        ("photon", "satya", "particle"),
        ("photon", "rest-mass", "0"),
        ("photon", "spin", "1"),
        ("photon", "charge", "0"),
    ],
    "muon": [
        ("muon", "satya", "particle"),
        ("muon", "rest-mass-energy", "105.658"),
        ("muon", "matra", "MeV"),
        ("muon", "charge", "-1"),
    ],
    "positron": [
        ("positron", "satya", "particle"),
        ("positron", "rest-mass-energy", "0.511"),
        ("positron", "matra", "MeV"),
        ("positron", "charge", "+1"),
    ],
    # ── mathematical constants ─────────────────────────────────────────────────
    "pi": [
        ("pi", "satya", "mathematical-constant"),
        ("pi", "sankhya", "3.14159265358979"),
    ],
    "e-constant": [
        ("e-constant", "satya", "mathematical-constant"),
        ("e-constant", "sankhya", "2.71828182845905"),
    ],
    "phi": [
        ("phi", "satya", "mathematical-constant"),
        ("phi", "sankhya", "1.61803398874989"),
        ("phi", "sloka", "golden-ratio"),
    ],
    "sqrt2": [
        ("sqrt2", "satya", "mathematical-constant"),
        ("sqrt2", "sankhya", "1.41421356237310"),
    ],
}


class StaticNode(BusNode):
    """
    Static table of physics constants, particle data, math constants.
    Zero latency. Always available. High confidence.
    """

    name = "static"
    priority = 15

    def __init__(self, extra: dict[str, list[Triple]] | None = None):
        self._data: dict[str, list[Triple]] = dict(CONSTANTS)
        if extra:
            self._data.update(extra)

    def add(self, word: str, triples: list[Triple]) -> None:
        """Add custom triples for a word at runtime."""
        self._data[word.lower()] = triples

    def query(self, word: str, pada: PadaResult, context: dict) -> BusResponse:
        wl = word.lower()
        triples = self._data.get(wl) or self._data.get(word) or []
        conf = 1.0 if triples else 0.0
        note = "physics/math constants table" if triples else ""
        return BusResponse("static", word, pada.pada, list(triples), conf, note)
