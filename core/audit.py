"""
Simple append-only audit log for MVP. Logs each recommendation run.
No hash chain or on-chain anchoring in MVP (Phase 2).
"""

import copy
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
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


def _format_human_timestamps(raw_timestamp: str) -> tuple[str, str]:
    """Return (utc_label, local_label) for an ISO timestamp."""
    try:
        dt = datetime.fromisoformat(str(raw_timestamp).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt_local = dt.astimezone()
        else:
            dt_local = dt.astimezone()
        dt_utc = dt_local.astimezone(timezone.utc)
        utc_label = dt_utc.strftime("%d %b %Y, %H:%M UTC")
        local_tz = dt_local.tzname() or dt_local.strftime("UTC%z")
        local_label = dt_local.strftime("%d %b %Y, %H:%M") + f" {local_tz}"
        return utc_label, local_label
    except (ValueError, TypeError):
        return str(raw_timestamp), str(raw_timestamp)


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
    readable_path = d / "recommendations_readable.log"
    generated_at = datetime.utcnow().isoformat() + "Z"
    generated_utc, generated_local = _format_human_timestamps(generated_at)
    entry = {
        "run_id": run_id,
        "mandate_id": mandate_id,
        "policy_snapshot": policy_snapshot,
        "recommendation_output": recommendation_output,
        "timestamp": generated_at,
    }
    with open(path, "a") as f:
        f.write(_safe_serialize(entry) + "\n")
    # Human-readable log with separators for easier manual inspection.
    with open(readable_path, "a") as f:
        f.write(
            "===== Treasury Recommendation Entry | "
            f"UTC: {generated_utc} | Local: {generated_local} =====\n"
        )
        f.write(f"Mandate: {mandate_id}\n")
        f.write(f"Run ID: {run_id}\n")
        f.write(f"Generated At (UTC): {generated_utc}\n")
        f.write(f"Generated At (Local): {generated_local}\n")
        f.write(json.dumps(entry, indent=2, default=str))
        f.write("\n----- End Entry -----\n\n")


def create_run_id() -> str:
    """Generate a new run_id for a treasury run."""
    return str(uuid4())


def read_recommendation_entries(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Read recommendation entries from NDJSON audit log."""
    path = _audit_dir() / "recommendations.ndjson"
    if not path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if limit is not None:
        return entries[-limit:]
    return entries


def get_recommendation_by_run_id(run_id: str) -> Optional[Dict[str, Any]]:
    """Return one recommendation entry for the given run_id, if present."""
    entries = read_recommendation_entries()
    for entry in reversed(entries):
        if entry.get("run_id") == run_id:
            return entry
    return None


def get_latest_recommendation() -> Optional[Dict[str, Any]]:
    """Return the most recent recommendation entry."""
    entries = read_recommendation_entries(limit=1)
    return entries[0] if entries else None
