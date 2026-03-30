"""paths.py — Shared path constants."""
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
BRAHMAN = ROOT / "brahman"
YANTRA = BRAHMAN / "yantra"
TESTS_DIR = Path(__file__).parent / "tests"
VENV_PYTEST = ROOT / ".venv" / "bin" / "pytest"
TESTS_STORE_DIR = ROOT / "upakarana" / "data" / "tests.lmdb"
