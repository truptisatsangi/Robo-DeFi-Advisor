# Explanation agent — per-pool "why selected" for governance transparency.
# Implementation lives in core.explanation; treasury orchestrator calls it after Decision.

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from core.explanation import explain_pool_selection, explain_pool_selection_str

__all__ = ["explain_pool_selection", "explain_pool_selection_str"]
