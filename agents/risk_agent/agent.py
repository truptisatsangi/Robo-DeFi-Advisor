# risk_agent.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uagents import Agent, Context, Model
from pydantic import Field
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from decision_agent.agent import handle_decision_request 


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- CONFIG ---
METTA_ENDPOINT = "https://beta-lipia-api.singularitynet.io/metta-api" 
starting_agent_address = "agent1q26a60535xkty6hfq6xkwp573gd9d2lradhexvps2d9w5p552qf85qnrzjk"
decision_agent_address="agent1qtrv3q6048scartdhlm26xfmrdtrs763x099pem38p3xdxy04klxq7puxyq"

agent = Agent(name="risk-agent-seed", seed="risk_agent_seed", port=8002, endpoint="http://localhost:8002/submit")

class PoolListMessage(Model):
    pool_id: str
    metrics: Optional[Dict[str, Any]] = None

class DiscoveryResponse(Model):
    pools: List[PoolListMessage]
    user_intent: Dict[str, Any] = {}

class RiskResponse(Model):
    type: str = "RiskResponse"
    status: str
    analysis: List[Dict[str, Any]] = []
    timestamp: str 
    error: Optional[str] = None
    user_intent: Dict[str, Any]

@agent.on_message(model=DiscoveryResponse)
async def risk_analysis(
    ctx: Context,
    sender: str,
    msg: DiscoveryResponse
):
    """
    Programmatic API:
        - pools: list of pool dicts (each must have "id" and optional "metrics")
        - forward_to_decision_url: if provided, will POST the RiskResponse to that URL (e.g. Decision agent's /submit endpoint)
    Returns a dict with keys: status, analysis (list), timestamp, optionally forward_result
    """
    ctx.logger.info(f"Received {len(msg.pools)} pools from DiscoveryAgent for risk analysis")
    try:
        # normalize pools into minimal dicts - fix data access
        normalized = [{"pool_id": p.pool_id, "metrics": p.metrics or {}} for p in msg.pools]

        # analyze in parallel
        analyses = await asyncio.gather(*[analyze_pool(p) for p in normalized])

        response = RiskResponse(
            type= "RiskResponse",
            status="success",
            analysis=analyses,
            timestamp = datetime.now().isoformat(),
            error = None,
            user_intent=msg.user_intent
        )

        # FUTURE SCOPE: Send to decision agent
        await handle_decision_request(ctx, starting_agent_address, response)

    except Exception as e:
        logger.exception("Error in risk_analysis")
        error_response = RiskResponse(
            type= "RiskResponse",
            status="error",
            error=str(e),
            analysis=[],
            user_intent=msg.user_intent,
            timestamp = datetime.now().isoformat(),
        )
        await handle_decision_request(ctx, starting_agent_address, error_response)
# ------------------------------
# Internal: analyze one pool
# ------------------------------

async def analyze_pool(pool: Dict[str, Any]) -> Dict[str, Any]:
    pool_id = pool.get("pool_id")
    metrics = pool.get("metrics", {}) or {}

    # Build MeTTa facts to query
    queries = [
        f"contract_verified({pool_id}, Status)",
        f"audit_link({pool_id}, Link)",
        f"holder_concentration({pool_id}, Conc)",
        f"liquidity_score({pool_id}, Score)",
        f"last_exploit({pool_id}, Timestamp)",
        f"risk_score({pool_id}, Score)"
    ]

    # execute queries in parallel (each returns dict with result/confidence or fallback)
    results = await asyncio.gather(*[query_metta(q) for q in queries])

    # unpack results safely
    cv = results[0] or {}
    audit = results[1] or {}
    conc = results[2] or {}
    liq = results[3] or {}
    exploit = results[4] or {}
    existing_risk = results[5] or {}

    # compute risk score
    risk_score_val = calculate_risk_score({
        "contractVerification": cv.get("result"),
        "auditStatus": audit.get("result"),
        "holderConcentration": conc.get("result"),
        "liquidityScore": liq.get("result"),
        "exploitHistory": exploit.get("result"),
        "poolMetrics": metrics
    })

    analysis = {
        "poolId": pool_id,
        "riskScore": risk_score_val,
        "riskLevel": get_risk_level(risk_score_val),
        "factors": {
            "contractVerified": cv.get("result"),
            "auditLink": audit.get("result"),
            "holderConcentration": conc.get("result"),
            "liquidityScore": liq.get("result"),
            "exploitHistory": exploit.get("result"),
            "existingRisk": existing_risk.get("result")
        },
        "confidence": calculate_confidence([
            cv.get("confidence", 0),
            audit.get("confidence", 0),
            conc.get("confidence", 0),
            liq.get("confidence", 0),
            exploit.get("confidence", 0)
        ]),
        "recommendations": generate_recommendations(risk_score_val, {
            "contractVerification": cv.get("result"),
            "auditStatus": audit.get("result"),
            "holderConcentration": conc.get("result")
        }),
        # Include original pool data
        "originalPoolData": metrics
    }

    # Optionally persist back to MeTTa (non-blocking)
    try:
        # store new risk score and timestamp (fire-and-forget)
        asyncio.create_task(assert_metta(f"risk_score({pool_id}, {risk_score_val})"))
        asyncio.create_task(assert_metta(f"risk_analysis_timestamp({pool_id}, {int(datetime.now().timestamp())})"))
    except Exception:
        logger.debug("Failed to assert risk into MeTTa (continuing)")

    return analysis

# ------------------------------
# MeTTa helpers (query/assert)
# ------------------------------
async def query_metta(fact: str) -> Dict[str, Any]:
    """Query MeTTa knowledge graph, with fallback to empty result on error."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{METTA_ENDPOINT}/query", json={"fact": fact}, headers={"Content-Type": "application/json"}) as resp:
                if resp.status == 200:
                    logger.info(f"Metta response {resp}")
                    return await resp.json()
                else:
                    logger.debug(f"MeTTa returned {resp.status} for {fact}")
                    return {"result": None, "confidence": 0}
    except Exception as e:
        logger.debug(f"MeTTa unreachable for {fact}: {e}")
        return {"result": None, "confidence": 0}

async def assert_metta(fact: str) -> Dict[str, Any]:
    """Assert a fact into MeTTa; returns response or fallback."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{METTA_ENDPOINT}/assert", json={"fact": fact}, headers={"Content-Type": "application/json"}) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.debug(f"MeTTa assert failed {resp.status} for {fact}")
                    return {"success": False}
    except Exception as e:
        logger.debug(f"MeTTa assert failed locally for {fact}: {e}")
        return {"success": False}

# ------------------------------
# Scoring & recommendations
# ------------------------------
def calculate_risk_score(factors: Dict[str, Any]) -> float:
    score = 0.0

    if factors.get("contractVerification"):
        score += 25.0

    if factors.get("auditStatus"):
        score += 20.0

    if factors.get("holderConcentration") is not None:
        concentration = factors["holderConcentration"]
        concentration_score = max(0, 20.0 - (concentration * 20.0))
        score += concentration_score

    if factors.get("liquidityScore") is not None:
        score += factors["liquidityScore"] * 15.0

    if factors.get("exploitHistory") is None:
        score += 10.0

    if factors.get("poolMetrics", {}).get("tvlUSD"):
        tvl = factors["poolMetrics"]["tvlUSD"]
        tvl_score = min(10.0, (tvl ** 0.1) / 10.0)
        score += tvl_score

    return round(score, 2)

def get_risk_level(score: float) -> str:
    if score >= 80:
        return "very_low"
    if score >= 60:
        return "low"
    if score >= 40:
        return "medium"
    if score >= 20:
        return "high"
    return "very_high"

def calculate_confidence(confidences: List[float]) -> float:
    return sum(confidences) / len(confidences) if confidences else 0.0

def generate_recommendations(risk_score: float, factors: Dict[str, Any]) -> List[str]:
    recommendations: List[str] = []
    if not factors.get("contractVerification"):
        recommendations.append("⚠️ Contract not verified - high risk")
    if not factors.get("auditStatus"):
        recommendations.append("🔍 No audit found - consider alternative pools")
    if factors.get("holderConcentration") and factors["holderConcentration"] > 0.3:
        recommendations.append("📊 High holder concentration - potential manipulation risk")
    if risk_score < 30:
        recommendations.append("🚨 High risk pool - consider safer alternatives")
    elif risk_score > 70:
        recommendations.append("✅ Low risk pool - suitable for conservative investments")
    return recommendations


if __name__ == "__main__": 
    agent.run()