"""paths.py — Shared path constants for upakarana2."""
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
BRAHMAN = ROOT / "brahman"
YANTRA = BRAHMAN / "yantra"

# upakarana2 data directory (centralized LMDB store)
DATA_DIR = Path(__file__).parent / "data"
STORE_PATH = DATA_DIR / "upakarana.lmdb"

# Tests
TESTS_DIR = Path(__file__).parent / "tests"
VENV_PYTEST = ROOT / ".venv" / "bin" / "pytest"
