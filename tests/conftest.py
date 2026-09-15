"""Pytest configuration: make the ``scripts`` directory importable as a
plain module path, since the project doesn't install itself as a package.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
