#!/usr/bin/env python3
"""
read_brahman.py — thin shim for tools.brahman CLI.

Usage:
  python3 tools/read_brahman.py tantra summary
  python3 tools/read_brahman.py om domain kosha/math
  python3 tools/read_brahman.py serve
  python3 tools/read_brahman.py json '{"command":"ping"}'

See tools/brahman/cli.py for full documentation.
"""

import sys
import os

# ensure tools/ is on the path for package import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.brahman.cli import main

main()
