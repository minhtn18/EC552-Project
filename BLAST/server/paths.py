"""
Single source of truth for the BLAST root path and sys.path setup.
Import BLAST_ROOT from here instead of recomputing it in every route module.
"""
from __future__ import annotations

import sys
from pathlib import Path

BLAST_ROOT = Path(__file__).parent.parent

if str(BLAST_ROOT) not in sys.path:
    sys.path.insert(0, str(BLAST_ROOT))
