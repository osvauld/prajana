"""Entry point for python3 -m pathram."""

import sys
from pathram.cli import main

sys.exit(main() or 0)
