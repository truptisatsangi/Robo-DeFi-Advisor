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

    # Generate detailed risk reasoning
    risk_reasoning = generate_risk_reasoning(risk_score_val, {
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
        "riskReasoning": risk_reasoning,  # Detailed explanation
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
            "holderConcentration": conc.get("result"),
            "poolMetrics": metrics
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
    """Calculate risk score based on available data (0-100, higher is safer)."""
    score = 0.0
    pool_metrics = factors.get("poolMetrics", {})
    
    # Get pool data
    tvl = pool_metrics.get("tvl", 0)
    apy = pool_metrics.get("apy", 0)
    protocol = pool_metrics.get("protocol", "").lower()
    
    # 1. TVL Score (0-30 points) - Most important for actual safety
    if tvl > 100_000_000:  # > $100M
        score += 30.0
    elif tvl > 50_000_000:  # > $50M
        score += 25.0
    elif tvl > 10_000_000:  # > $10M
        score += 20.0
    elif tvl > 5_000_000:   # > $5M
        score += 15.0
    elif tvl > 1_000_000:   # > $1M
        score += 10.0
    elif tvl > 100_000:     # > $100K
        score += 5.0
    # else: 0 points for very low TVL

    # 2. Protocol Reputation Score (0-35 points)
    trusted_tier1 = ["uniswap", "aave", "compound", "curve"]  # Most trusted
    trusted_tier2 = ["balancer", "pendle", "venus", "pancakeswap"]  # Established
    
    if any(t1 in protocol for t1 in trusted_tier1):
        score += 35.0  # Maximum trust
    elif any(t2 in protocol for t2 in trusted_tier2):
        score += 25.0  # Good trust
    else:
        score += 10.0  # Unknown/new protocol

    # 3. APY Sustainability Score (0-20 points) - Lower APY often means lower risk
    if apy < 5:
        score += 20.0  # Very conservative yield
    elif apy < 10:
        score += 15.0  # Moderate yield
    elif apy < 20:
        score += 10.0  # Above-average yield
    elif apy < 50:
        score += 5.0   # High yield - some risk
    # else: 0 points for extremely high APY

    # 4. Exploit History (0-15 points)
    if factors.get("exploitHistory") is None:
        score += 15.0  # No known exploits
    else:
        score += 0.0   # Has exploit history

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

def generate_risk_reasoning(risk_score: float, factors: Dict[str, Any]) -> str:
    """Generate detailed explanation for the risk score."""
    pool_metrics = factors.get("poolMetrics", {})
    tvl = pool_metrics.get("tvl", 0)
    apy = pool_metrics.get("apy", 0)
    protocol = pool_metrics.get("protocol", "").lower()
    
    reasoning_parts = []
    
    # Overall assessment
    if risk_score >= 80:
        reasoning_parts.append("This pool has a VERY LOW risk profile.")
    elif risk_score >= 60:
        reasoning_parts.append("This pool has a LOW risk profile.")
    elif risk_score >= 40:
        reasoning_parts.append("This pool has a MEDIUM risk profile.")
    elif risk_score >= 20:
        reasoning_parts.append("This pool has a HIGH risk profile.")
    else:
        reasoning_parts.append("This pool has a VERY HIGH risk profile.")
    
    # TVL contribution to score
    if tvl > 100_000_000:
        reasoning_parts.append(f"✓ Excellent liquidity with ${tvl:,.0f} TVL provides strong stability and low slippage risk.")
    elif tvl > 10_000_000:
        reasoning_parts.append(f"✓ Good liquidity with ${tvl:,.0f} TVL provides reasonable stability.")
    elif tvl > 1_000_000:
        reasoning_parts.append(f"⚠ Moderate liquidity at ${tvl:,.0f} TVL - some slippage risk on large trades.")
    else:
        reasoning_parts.append(f"⚠ Low liquidity at ${tvl:,.0f} TVL increases risk of high slippage and price impact.")
    
    # Protocol reputation contribution
    established_protocols = ["uniswap", "aave", "compound", "curve", "balancer", "pendle", "venus", "pancake"]
    if any(est in protocol for est in established_protocols):
        reasoning_parts.append(f"✓ {protocol.title()} is an established protocol with strong track record and audits.")
    else:
        reasoning_parts.append(f"⚠ {protocol.title()} is less established - additional due diligence recommended.")
    
    # APY assessment
    if apy > 100:
        reasoning_parts.append(f"⚠ Extremely high APY ({apy:.1f}%) suggests high risk or temporary incentives - verify sustainability.")
    elif apy > 50:
        reasoning_parts.append(f"⚠ Very high APY ({apy:.1f}%) - check for impermanent loss risks and reward token volatility.")
    elif apy > 20:
        reasoning_parts.append(f"✓ High APY ({apy:.1f}%) offers good returns with acceptable risk for diversified portfolio.")
    elif apy > 5:
        reasoning_parts.append(f"✓ Moderate APY ({apy:.1f}%) suggests stable, sustainable returns.")
    else:
        reasoning_parts.append(f"✓ Low APY ({apy:.1f}%) indicates very conservative, stable yield.")
    
    # Exploit history
    if factors.get("exploitHistory") is None:
        reasoning_parts.append("✓ No known exploit history.")
    else:
        reasoning_parts.append("⚠ Past exploit detected - extra caution advised.")
    
    return " ".join(reasoning_parts)

def generate_recommendations(risk_score: float, factors: Dict[str, Any]) -> List[str]:
    recommendations: List[str] = []
    
    # Get pool metrics
    pool_metrics = factors.get("poolMetrics", {})
    tvl = pool_metrics.get("tvl", 0)
    apy = pool_metrics.get("apy", 0)
    protocol = pool_metrics.get("protocol", "").lower()
    
    # Risk-based recommendations
    if risk_score < 30:
        recommendations.append("🚨 High risk pool - only invest what you can afford to lose")
        recommendations.append("💡 Consider diversifying across multiple pools")
    elif risk_score > 70:
        recommendations.append("✅ Low risk pool - suitable for conservative investments")
        recommendations.append("📈 Good choice for long-term holdings")
    else:
        recommendations.append("⚖️ Medium risk - suitable for balanced portfolios")
    
    # TVL-based recommendations
    if tvl < 1_000_000:
        recommendations.append("⚠️ Low liquidity - may experience slippage on large trades")
    elif tvl > 100_000_000:
        recommendations.append("💧 High liquidity - excellent for large transactions")
    
    # APY-based recommendations
    if apy > 50:
        recommendations.append("📊 Very high APY - verify sustainability and potential IL risks")
    elif apy > 20:
        recommendations.append("💰 High yields available - monitor for impermanent loss")
    
    # Protocol-based recommendations
    established = ["uniswap", "aave", "compound", "curve", "balancer", "lido"]
    if any(est in protocol for est in established):
        recommendations.append("🏦 Established protocol with strong track record")
    else:
        recommendations.append("🔍 Research protocol thoroughly before investing")
    
    return recommendations[:4]  # Limit to 4 most relevant recommendations


if __name__ == "__main__": 
    agent.run()