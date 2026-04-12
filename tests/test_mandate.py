import json
from pathlib import Path

import pytest

from core.mandate import MandateExpiredError, MandateNotFoundError, get_mandate


def _write_mandate(base: Path, dao_id: str, mandate_id: str, valid_until: str) -> None:
    mandate_dir = base / "mandates" / dao_id
    mandate_dir.mkdir(parents=True, exist_ok=True)
    mandate_path = mandate_dir / f"{mandate_id}.json"
    mandate_path.write_text(
        json.dumps(
            {
                "mandate_id": mandate_id,
                "mandate_version": 1,
                "dao_id": dao_id,
                "dao_name": "Test DAO",
                "policy": {"min_apy": 2.0, "allowed_protocols": ["aave"]},
                "approval_ref": "Snapshot proposal #TEST",
                "valid_from": "2025-01-01",
                "valid_until": valid_until,
            }
        )
    )


def test_get_mandate_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _write_mandate(tmp_path, "dao-a", "m-1", "2099-12-31")
    monkeypatch.setenv("RDA_MANDATES_DIR", str(tmp_path))

    mandate = get_mandate("m-1", "dao-a")
    assert mandate["mandate_id"] == "m-1"
    assert mandate["dao_id"] == "dao-a"


def test_get_mandate_raises_when_expired(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _write_mandate(tmp_path, "dao-a", "m-expired", "2000-01-01")
    monkeypatch.setenv("RDA_MANDATES_DIR", str(tmp_path))

    with pytest.raises(MandateExpiredError):
        get_mandate("m-expired", "dao-a")


def test_get_mandate_raises_when_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("RDA_MANDATES_DIR", str(tmp_path))

    with pytest.raises(MandateNotFoundError):
        get_mandate("missing-id", "dao-a")
