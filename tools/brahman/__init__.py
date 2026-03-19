"""
brahman — read, query, and serve the brahman knowledge base.

Tantras (72 .tantra3 files) + Om nodes (1786 .om files).
"""

from . import tantras, om, server, tests, runner, cache
from .paths import BRAHMAN, YANTRA
