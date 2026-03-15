"""
Simple append-only audit log for MVP. Logs each recommendation run.
No hash chain or on-chain anchoring in MVP (Phase 2).
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4


def _audit_dir() -> Path:
    base = Path(os.environ.get("RDA_AUDIT_DIR", "."))
    return base / "audit"


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
        f.write(json.dumps(entry, default=str) + "\n")


def create_run_id() -> str:
    """Generate a new run_id for a treasury run."""
    return str(uuid4())
