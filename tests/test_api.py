import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.app import app


client = TestClient(app)


def test_run_recommendation_endpoint(monkeypatch):
    async def fake_run_treasury_recommendation(mandate_id, amount_usd=None, dao_id=None):
        return {
            "success": True,
            "run_id": "run-1",
            "mandate_id": mandate_id,
            "approval_ref": "Snapshot #1",
            "recommendation": {"recommended_pools": []},
            "proposal_draft": "draft",
            "pipeline_stats": {"discovery": {}, "risk": {}, "decision": {}, "timestamps": {}},
        }

    monkeypatch.setattr("api.app.run_treasury_recommendation", fake_run_treasury_recommendation)
    response = client.post(
        "/api/recommendations/run",
        json={"mandate_id": "m-1", "dao_id": "dao-a", "amount_usd": 1000},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["mandate_id"] == "m-1"


def test_mandates_endpoints(monkeypatch, tmp_path: Path):
    mandate_dir = tmp_path / "mandates" / "dao-a"
    mandate_dir.mkdir(parents=True, exist_ok=True)
    (mandate_dir / "m-1.json").write_text(
        json.dumps(
            {
                "mandate_id": "m-1",
                "mandate_version": 1,
                "dao_id": "dao-a",
                "policy": {"min_apy": 2.0, "allowed_protocols": ["aave"]},
                "approval_ref": "Snapshot #1",
            }
        )
    )
    monkeypatch.setenv("RDA_MANDATES_DIR", str(tmp_path))

    list_resp = client.get("/api/mandates")
    assert list_resp.status_code == 200
    assert list_resp.json()["count"] == 1

    detail_resp = client.get("/api/mandates/m-1?dao_id=dao-a")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["mandate_id"] == "m-1"


def test_latest_run_endpoint(monkeypatch):
    monkeypatch.setattr(
        "api.app.get_latest_recommendation",
        lambda: {
            "run_id": "run-latest",
            "mandate_id": "m-1",
            "timestamp": "2026-03-31T00:00:00Z",
            "recommendation_output": {
                "success": True,
                "run_id": "run-latest",
                "mandate_id": "m-1",
                "recommendation": {"recommended_pools": []},
                "proposal_draft": "draft",
                "pipeline_stats": {},
            },
        },
    )
    response = client.get("/api/runs/latest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run-latest"
    assert payload["audit_timestamp"] == "2026-03-31T00:00:00Z"
