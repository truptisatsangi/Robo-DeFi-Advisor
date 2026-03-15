"""
Mandate system — DAO-approved treasury policy. Every recommendation must be tied to a valid mandate.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from .treasury_policy import TreasuryPolicy


def _mandates_dir() -> Path:
    base = Path(os.environ.get("RDA_MANDATES_DIR", "."))
    return base / "mandates"


def _mandate_path(dao_id: str, mandate_id: str) -> Path:
    return _mandates_dir() / dao_id / f"{mandate_id}.json"


class MandateExpiredError(Exception):
    """Raised when mandate valid_until is in the past."""

    def __init__(self, mandate_id: str, valid_until: Optional[str]):
        self.mandate_id = mandate_id
        self.valid_until = valid_until
        super().__init__(
            f"Mandate {mandate_id!r} has expired (valid_until={valid_until}). "
            "Governance must renew or amend the mandate before new recommendations can be generated."
        )


class MandateNotFoundError(Exception):
    """Raised when mandate_id is not found."""

    def __init__(self, mandate_id: str):
        super().__init__(f"Mandate not found: {mandate_id!r}")


def load_mandate(mandate_id: str, dao_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Load mandate by mandate_id. If dao_id is not provided, search all DAO dirs (slow).
    Returns mandate dict with policy, approval_ref, valid_from, valid_until, etc.
    Raises MandateNotFoundError if not found, MandateExpiredError if expired.
    """
    md = _mandates_dir()
    if dao_id:
        path = _mandate_path(dao_id, mandate_id)
        if not path.is_file():
            raise MandateNotFoundError(mandate_id)
        with open(path, "r") as f:
            data = json.load(f)
    else:
        data = None
        for dao_dir in md.iterdir():
            if not dao_dir.is_dir():
                continue
            path = dao_dir / f"{mandate_id}.json"
            if path.is_file():
                with open(path, "r") as f:
                    data = json.load(f)
                break
        if data is None:
            raise MandateNotFoundError(mandate_id)

    valid_until = data.get("valid_until")
    if valid_until:
        try:
            # ISO format or YYYY-MM-DD
            if "T" in str(valid_until):
                until = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            else:
                until = datetime.strptime(str(valid_until)[:10], "%Y-%m-%d").replace(tzinfo=None)
            if until.tzinfo:
                now = datetime.now(until.tzinfo)
            else:
                now = datetime.utcnow()
            if now > until:
                raise MandateExpiredError(mandate_id, valid_until)
        except (ValueError, TypeError):
            pass  # if we can't parse, don't block
    return data


def get_mandate(mandate_id: str, dao_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Alias for load_mandate. Used by Treasury entry point.
    Returns mandate dict; policy is under key 'policy' (dict or TreasuryPolicy-compatible).
    """
    return load_mandate(mandate_id, dao_id)


def save_mandate(dao_id: str, mandate_id: str, mandate: Dict[str, Any]) -> None:
    """Persist mandate to JSON. Creates dao dir if needed."""
    path = _mandate_path(dao_id, mandate_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(mandate, f, indent=2)


def is_mandate_expired(mandate: Dict[str, Any]) -> bool:
    """Return True if valid_until is in the past."""
    valid_until = mandate.get("valid_until")
    if not valid_until:
        return False
    try:
        if "T" in str(valid_until):
            until = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
        else:
            until = datetime.strptime(str(valid_until)[:10], "%Y-%m-%d")
        if until.tzinfo:
            now = datetime.now(until.tzinfo)
        else:
            now = datetime.utcnow()
        return now > until
    except (ValueError, TypeError):
        return False
