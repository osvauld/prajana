"""
paths.py — shared path constants for the brahman package.
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
BRAHMAN = os.path.join(ROOT, "brahman")
YANTRA = os.path.join(BRAHMAN, "yantra")
