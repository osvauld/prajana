"""paths.py — shared path constants for the tools package."""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BRAHMAN = os.path.join(ROOT, "brahman")
YANTRA = os.path.join(BRAHMAN, "yantra")
VENV_PYTEST = os.path.join(ROOT, ".venv", "bin", "pytest")
V2_DIR = os.path.join(HERE, "v2")
