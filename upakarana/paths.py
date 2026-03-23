"""paths.py — Shared path constants."""
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
BRAHMAN = ROOT / "brahman"
YANTRA = BRAHMAN / "yantra"
V2_DIR = ROOT / "tools" / "v2"
VENV_PYTEST = ROOT / ".venv" / "bin" / "pytest"
