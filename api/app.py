"""
HTTP API for treasury recommendations and audit retrieval.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agents.treasury_agent.run import run_treasury_recommendation
from core.audit import (
    get_latest_recommendation,
    get_recommendation_by_run_id,
    read_recommendation_entries,
)
from core.mandate import MandateNotFoundError, get_mandate, list_mandates

app = FastAPI(
    title="RDA Treasury API",
    description="Minimal API for DAO treasury recommendation runs and audit visibility.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRecommendationRequest(BaseModel):
    mandate_id: str = Field(..., description="DAO-approved mandate identifier")
    dao_id: Optional[str] = Field(None, description="DAO id to narrow mandate lookup")
    amount_usd: Optional[float] = Field(None, ge=0, description="Optional amount override")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/recommendations/run")
async def run_recommendation(payload: RunRecommendationRequest) -> Dict[str, Any]:
    return await run_treasury_recommendation(
        mandate_id=payload.mandate_id,
        amount_usd=payload.amount_usd,
        dao_id=payload.dao_id,
    )


@app.get("/api/mandates")
def get_mandates(dao_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    mandates = list_mandates(dao_id=dao_id)
    return {"count": len(mandates), "mandates": mandates}


@app.get("/api/mandates/{mandate_id}")
def get_mandate_by_id(mandate_id: str, dao_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    try:
        return get_mandate(mandate_id, dao_id=dao_id)
    except MandateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/runs/latest")
def get_latest_run() -> Dict[str, Any]:
    latest = get_latest_recommendation()
    if not latest:
        raise HTTPException(status_code=404, detail="No run found in audit log")
    output = dict(latest.get("recommendation_output") or {})
    output.setdefault("run_id", latest.get("run_id"))
    output.setdefault("mandate_id", latest.get("mandate_id"))
    output["audit_timestamp"] = latest.get("timestamp")
    return output


@app.get("/api/runs/{run_id}")
def get_run_by_id(run_id: str) -> Dict[str, Any]:
    entry = get_recommendation_by_run_id(run_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    output = dict(entry.get("recommendation_output") or {})
    output.setdefault("run_id", entry.get("run_id"))
    output.setdefault("mandate_id", entry.get("mandate_id"))
    output["audit_timestamp"] = entry.get("timestamp")
    return output


@app.get("/api/audit/latest")
def get_latest_audit(format: str = Query(default="json", pattern="^(json|ndjson)$")) -> Any:
    latest = get_latest_recommendation()
    if not latest:
        raise HTTPException(status_code=404, detail="No audit entries found")
    if format == "ndjson":
        return PlainTextResponse(json.dumps(latest), media_type="application/x-ndjson")
    return latest


@app.get("/api/audit/export")
def export_audit(limit: Optional[int] = Query(default=None, ge=1), format: str = Query(default="ndjson", pattern="^(json|ndjson)$")) -> Any:
    entries = read_recommendation_entries(limit=limit)
    if format == "json":
        return {"count": len(entries), "entries": entries}
    ndjson_payload = "\n".join(json.dumps(e) for e in entries)
    return PlainTextResponse(ndjson_payload, media_type="application/x-ndjson")
