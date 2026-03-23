#!/usr/bin/env python
"""
Dummy conftest.py for pyload.

If you don't know what this is for, just leave it empty. Read more about
conftest.py under: https://pytest.org/latest/plugins.html
"""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
