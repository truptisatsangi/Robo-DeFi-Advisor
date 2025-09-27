"""
Decision Agent using uAgents
- Selects optimal pool with transparent reasoning
- Wraps DecisionAgent logic inside uAgents framework
"""

from uagents import Agent, Context, Model
from typing import Dict, Any, List, Optional
from datetime import datetime

from .decision_logic import DecisionAgent


class DecisionRequest(Model):
    pools: List[Dict[str, Any]]
    risk_analysis: List[Dict[str, Any]]
    criteria: Dict[str, Any]


class DecisionResponse(Model):
    success: bool
    optimalPool: Optional[Dict[str, Any]]
    reasoningTrace: Optional[List[Dict[str, Any]]]
    allCandidates: Optional[List[Dict[str, Any]]]
    error: Optional[str]
    timestamp: str


class DecisionUAgent:
    """uAgent wrapper for Decision Agent."""

    def __init__(self):
        self.agent = Agent(
            name="decision_agent",
            seed="decision_secret_seed",
            port=8000,
            endpoint=["http://localhost:8000/submit"]
        )
        self.decision_logic = DecisionAgent()
        self.address = "agent1qtrv3q6048scartdhlm26xfmrdtrs763x099pem38p3xdxy04klxq7puxyq"

        # Attach event handlers
        self._register_handlers()

    def run(self):
        """Start the uAgent event loop."""
        self.agent.run()

    def _register_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            ctx.logger.info(f"🚀 Decision Agent started at {self.agent.address}")

        @self.agent.on_message(model=DecisionRequest, replies=DecisionResponse)
        async def handle_decision_request(ctx: Context, sender: str, msg: DecisionRequest):
            ctx.logger.info(f"📩 Received decision request from {sender}")

            try:
                result = await self.decision_logic.select_optimal_pool(
                    user_criteria=msg.criteria,
                    pools=msg.pools,
                    risk_analysis=msg.risk_analysis
                )

                response = DecisionResponse(
                    success=result["success"],
                    optimalPool=result.get("optimalPool"),
                    reasoningTrace=result.get("reasoningTrace"),
                    allCandidates=result.get("allCandidates"),
                    error=result.get("error"),
                    timestamp=result["timestamp"]
                )
                await ctx.send(sender, response)

            except Exception as e:
                ctx.logger.error(f"❌ Error in decision making: {e}")
                response = DecisionResponse(
                    success=False,
                    optimalPool=None,
                    reasoningTrace=[],
                    allCandidates=[],
                    error=str(e),
                    timestamp=datetime.now().isoformat()
                )
                await ctx.send(sender, response)

    # ---------- NEW: Direct call without message passing ----------
    async def act(self, criteria: Dict[str, Any], pools: List[Dict[str, Any]], risk_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Direct method to make decision without message passing.
        Returns the final selected pool and reasoning.
        """
        try:
            result = await self.decision_logic.select_optimal_pool(
                user_criteria=criteria,
                pools=pools,
                risk_analysis=risk_analysis
            )
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
