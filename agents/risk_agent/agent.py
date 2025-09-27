# risk_agent.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uagents import Agent, Context, Model

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- CONFIG ---
METTA_ENDPOINT = "http://localhost:5000/metta"  # adjust to your MeTTa
DEFAULT_PORT = 8001
DEFAULT_ENDPOINT = [f"http://localhost:{DEFAULT_PORT}/submit"]

# ------------------------------
# Message models for uAgents
# ------------------------------
class Pool(Model):
    id: str
    metrics: Optional[Dict[str, Any]] = None


class RiskRequest(Model):
    pools: List[Pool]


class RiskResponse(Model):
    type: str = "RiskResponse"
    success: bool = True
    analysis: List[Dict[str, Any]] = []
    timestamp: str = datetime.now().isoformat()
    error: Optional[str] = None


# ------------------------------
# Risk Agent (uAgents wrapper)
# ------------------------------
class RiskUAgent:
    def __init__(
        self,
        seed: str = "risk-agent-seed",
        name: str = "risk_agent",
        port: int = DEFAULT_PORT,
        endpoint: Optional[List[str]] = None,
        metta_endpoint: str = METTA_ENDPOINT,
    ):
        self.agent = Agent(name=name, seed=seed, port=port, endpoint=endpoint or DEFAULT_ENDPOINT)
        self.metta_endpoint = metta_endpoint

        # register message handler
        self._register_handlers()

    # ------------------------------
    # Public programmatic entrypoint
    # ------------------------------
    async def act(
        self,
        pools: List[Dict[str, Any]],
        forward_to_decision_url: Optional[str] = None,
        timeout_seconds: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Programmatic API:
         - pools: list of pool dicts (each must have "id" and optional "metrics")
         - forward_to_decision_url: if provided, will POST the RiskResponse to that URL (e.g. Decision agent's /submit endpoint)
        Returns a dict with keys: status, analysis (list), timestamp, optionally forward_result
        """
        try:
            # normalize pools into minimal dicts
            normalized = [{"id": p.get("id"), "metrics": p.get("metrics", {})} for p in pools]

            # analyze in parallel
            analyses = await asyncio.gather(*[self._analyze_pool(p) for p in normalized])

            response = {
                "status": "success",
                "analysis": analyses,
                "timestamp": datetime.now().isoformat(),
            }

            # optionally relay to Decision Agent over HTTP (simple, robust)
            if forward_to_decision_url:
                forward_result = await self._relay_to_decision(forward_to_decision_url, analyses, timeout_seconds)
                response["forward_result"] = forward_result

            return response

        except Exception as e:
            logger.exception("Error in RiskUAgent.act")
            return {"status": "error", "error": str(e), "analysis": []}

    # ------------------------------
    # Internal: analyze one pool
    # ------------------------------
    async def _analyze_pool(self, pool: Dict[str, Any]) -> Dict[str, Any]:
        pool_id = pool.get("id")
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
        results = await asyncio.gather(*[self.query_metta(q) for q in queries])

        # unpack results safely
        cv = results[0] or {}
        audit = results[1] or {}
        conc = results[2] or {}
        liq = results[3] or {}
        exploit = results[4] or {}
        existing_risk = results[5] or {}

        # compute risk score
        risk_score_val = self.calculate_risk_score({
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
            "riskLevel": self.get_risk_level(risk_score_val),
            "factors": {
                "contractVerified": cv.get("result"),
                "auditLink": audit.get("result"),
                "holderConcentration": conc.get("result"),
                "liquidityScore": liq.get("result"),
                "exploitHistory": exploit.get("result"),
                "existingRisk": existing_risk.get("result")
            },
            "confidence": self.calculate_confidence([
                cv.get("confidence", 0),
                audit.get("confidence", 0),
                conc.get("confidence", 0),
                liq.get("confidence", 0),
                exploit.get("confidence", 0)
            ]),
            "recommendations": self.generate_recommendations(risk_score_val, {
                "contractVerification": cv.get("result"),
                "auditStatus": audit.get("result"),
                "holderConcentration": conc.get("result")
            })
        }

        # Optionally persist back to MeTTa (non-blocking)
        try:
            # store new risk score and timestamp (fire-and-forget)
            asyncio.create_task(self.assert_metta(f"risk_score({pool_id}, {risk_score_val})"))
            asyncio.create_task(self.assert_metta(f"risk_analysis_timestamp({pool_id}, {int(datetime.now().timestamp())})"))
        except Exception:
            logger.debug("Failed to assert risk into MeTTa (continuing)")

        return analysis

    # ------------------------------
    # Relay to decision agent via HTTP POST
    # ------------------------------
    async def _relay_to_decision(self, decision_url: str, analyses: List[Dict[str, Any]], timeout_seconds: float = 10.0) -> Dict[str, Any]:
        """
        POST the risk response to decision_url (e.g. http://localhost:8002/submit).
        Returns dict with status and HTTP response info (or error).
        """
        payload = {
            "type": "RiskResponse",
            "success": True,
            "analysis": analyses,
            "timestamp": datetime.now().isoformat()
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(decision_url, json=payload, timeout=timeout_seconds) as resp:
                    text = await resp.text()
                    return {"status": "sent", "http_status": resp.status, "response_text": text}
        except Exception as e:
            logger.exception("Failed to forward to decision agent")
            return {"status": "error", "error": str(e)}

    # ------------------------------
    # MeTTa helpers (query/assert)
    # ------------------------------
    async def query_metta(self, fact: str) -> Dict[str, Any]:
        """Query MeTTa knowledge graph, with fallback to empty result on error."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.metta_endpoint}/query", json={"fact": fact}, headers={"Content-Type": "application/json"}) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        logger.debug(f"MeTTa returned {resp.status} for {fact}")
                        return {"result": None, "confidence": 0}
        except Exception as e:
            logger.debug(f"MeTTa unreachable for {fact}: {e}")
            return {"result": None, "confidence": 0}

    async def assert_metta(self, fact: str) -> Dict[str, Any]:
        """Assert a fact into MeTTa; returns response or fallback."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.metta_endpoint}/assert", json={"fact": fact}, headers={"Content-Type": "application/json"}) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        logger.debug(f"MeTTa assert failed {resp.status} for {fact}")
                        return {"success": False}
        except Exception as e:
            logger.debug(f"MeTTa assert failed locally for {fact}: {e}")
            return {"success": False}

    # ------------------------------
    # Scoring & recommendations (same as your logic)
    # ------------------------------
    def calculate_risk_score(self, factors: Dict[str, Any]) -> float:
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

    def get_risk_level(self, score: float) -> str:
        if score >= 80:
            return "very_low"
        if score >= 60:
            return "low"
        if score >= 40:
            return "medium"
        if score >= 20:
            return "high"
        return "very_high"

    def calculate_confidence(self, confidences: List[float]) -> float:
        return sum(confidences) / len(confidences) if confidences else 0.0

    def generate_recommendations(self, risk_score: float, factors: Dict[str, Any]) -> List[str]:
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

    # ------------------------------
    # uAgents message handler wiring
    # ------------------------------
    def _register_handlers(self):
        # handle incoming RiskRequest messages (reactive)
        @self.agent.on_message(model=RiskRequest, replies=RiskResponse)
        async def handle_risk_request(ctx: Context, sender: str, msg: RiskRequest):
            try:
                # msg.pools are Pool model objects; convert to simple dicts
                pools = [{"id": p.id, "metrics": p.metrics} for p in msg.pools]
                logger.info(f"RiskAgent: received {len(pools)} pools from {sender}")

                # compute analyses
                analyses = await asyncio.gather(*[self._analyze_pool(p) for p in pools])

                # Send back to sender
                resp = RiskResponse(success=True, analysis=analyses, timestamp=datetime.now().isoformat())
                await ctx.send(sender, resp)

                # Optionally forward to decision agent if the sender requested that pattern
                # (You can configure forwarding via metadata in 'msg' or a known decision agent URL)
                # Example: if caller passed a special header or expects automatic forwarding, implement here.

            except Exception as e:
                logger.exception("Error handling risk request")
                await ctx.send(sender, RiskResponse(success=False, analysis=[], timestamp=datetime.now().isoformat(), error=str(e)))

    def run(self):
        logger.info("Starting Risk Agent...")
        self.agent.run()


# If run directly, demonstrate simple act() usage
# if __name__ == "__main__":
#     async def demo():
#         ra = RiskUAgent()
#         demo_pools = [
#             {"id": "0x1234...5678", "metrics": {"tvlUSD": 2_000_000}},
#             {"id": "0x9876...4321", "metrics": {"tvlUSD": 200_000}}
#         ]
#         result = await ra.act(demo_pools)
#         print("Demo result:", result)

#     asyncio.run(demo())
