"""
Simple append-only audit log for MVP. Logs each recommendation run.
No hash chain or on-chain anchoring in MVP (Phase 2).
"""

import copy
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

logger = logging.getLogger(__name__)


def _audit_dir() -> Path:
    base = Path(os.environ.get("RDA_AUDIT_DIR", "."))
    return base / "audit"


def _safe_serialize(obj: Any) -> str:
    """JSON-serialize with protection against circular references."""
    seen: set = set()

    def _default(o: Any) -> Any:
        oid = id(o)
        if oid in seen:
            return "<circular ref>"
        if isinstance(o, (dict, list)):
            seen.add(oid)
        return str(o)

    try:
        return json.dumps(obj, default=_default)
    except (ValueError, TypeError):
        return json.dumps({"_serialization_error": True, "run_id": obj.get("run_id", "?")})


def log_recommendation(
    run_id: str,
    mandate_id: str,
    policy_snapshot: Dict[str, Any],
    recommendation_output: Dict[str, Any],
) -> None:
    """
    Append one recommendation log entry. Fields: run_id, mandate_id, policy_snapshot,
    recommendation_output, timestamp.
    """
    d = _audit_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / "recommendations.ndjson"
    entry = {
        "run_id": run_id,
        "mandate_id": mandate_id,
        "policy_snapshot": policy_snapshot,
        "recommendation_output": recommendation_output,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    with open(path, "a") as f:
        f.write(_safe_serialize(entry) + "\n")


def create_run_id() -> str:
    """Generate a new run_id for a treasury run."""
    return str(uuid4())
