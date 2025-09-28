"""
Decision Agent using uAgents
- Selects optimal pool with transparent reasoning
- Wraps DecisionAgent logic inside uAgents framework
"""

from uagents import Agent, Context, Model, Protocol
from typing import Dict, Any, List, Optional
from datetime import datetime

from .decision_logic import DecisionAgent

agent = Agent(
    name="decision_agent",
    seed="decision_secret_seed",
    port=8005,
    endpoint=["http://localhost:8005/submit"]
)

class RiskResponse(Model):
    type: str
    status: str
    analysis: List[Dict[str, Any]]
    timestamp: str
    error: str | None
    user_intent: Dict[str, Any]

class DecisionResponse(Model):
    success: bool
    optimalPool: Optional[Dict[str, Any]]
    reasoningTrace: Optional[List[Dict[str, Any]]]
    allCandidates: Optional[List[Dict[str, Any]]]
    error: Optional[str]
    timestamp: str
    user_intent: Optional[Dict[str, Any]] = {}

decision_logic = DecisionAgent()

@agent.on_message(model=RiskResponse)
async def handle_decision_request(ctx: Context, sender: str, msg: RiskResponse):
    ctx.logger.info(f"Received risk analysis from {sender}")
    
    try:
        # Check if we received a successful risk analysis
        if msg.status != "success":
            ctx.logger.error(f"Risk analysis failed: {msg.error}")
            response = DecisionResponse(
                success=False,
                optimalPool=None,
                reasoningTrace=[],
                allCandidates=[],
                error=f"Risk analysis failed: {msg.error}",
                timestamp=datetime.now().isoformat(),
                user_intent=msg.user_intent
            )
            ctx.logger.info(f"Decision failed: {response}")
            return

        # Extract pool data from risk analysis
        pools_with_risk = []
        for analysis in msg.analysis:
            # Get original pool data
            original_data = analysis.get("originalPoolData", {})
            pool_data = {
                "id": analysis.get("poolId"),
                "protocol": original_data.get("protocol", "Unknown"),
                "chain": original_data.get("chain", "Unknown"),
                "tvl": original_data.get("tvl", 0),
                "apy": original_data.get("apy", 0),
                "symbol": original_data.get("symbol", "Unknown"),
                "project": original_data.get("project", "Unknown"),
                "url": original_data.get("url"),
                "riskScore": analysis.get("riskScore"),
                "riskLevel": analysis.get("riskLevel"),
                "factors": analysis.get("factors", {}),
                "confidence": analysis.get("confidence", 0),
                "recommendations": analysis.get("recommendations", [])
            }
            pools_with_risk.append(pool_data)

        # Call decision logic
        result = await decision_logic.select_optimal_pool(
            user_criteria=msg.user_intent,
            pools=pools_with_risk,
            risk_analysis=msg.analysis
        )

        response = DecisionResponse(
            success=result["success"],
            optimalPool=result.get("optimalPool"),
            reasoningTrace=result.get("reasoningTrace"),
            allCandidates=result.get("allCandidates"),
            error=result.get("error"),
            timestamp=result["timestamp"],
            user_intent=msg.user_intent
        )
        
        ctx.logger.info(f"✅ Decision completed successfully")
        ctx.logger.info(f"Optimal pool: {response.optimalPool}")
        
        # You might want to send this response back to the original requester
        await ctx.send(sender, response)

    except Exception as e:
        ctx.logger.error(f"❌ Error in decision making: {e}")
        response = DecisionResponse(
            success=False,
            optimalPool=None,
            reasoningTrace=[],
            allCandidates=[],
            error=str(e),
            timestamp=datetime.now().isoformat(),
            user_intent=getattr(msg, 'user_intent', {})
        )
        ctx.logger.info(f"Decision failed: {response}")

if __name__ == "__main__": 
    agent.run()