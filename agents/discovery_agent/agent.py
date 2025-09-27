import logging
import asyncio
from typing import Dict, Any

from uagents import Agent, Context, Protocol, Model
from .discovery_logic import DiscoveryLogic

from agents.risk_agent.agent import RiskRequest, RiskResponse, Pool 

logger = logging.getLogger(__name__)


class DiscoveryRequest(Model):
    criteria: Dict[str, Any]


class DiscoveryResponse(Model):
    status: str
    data: Dict[str, Any] | None = None
    error: str | None = None


class DiscoveryUAgent:
    def __init__(self, seed: str = "discovery_seed", name: str = "discovery_agent"):
        self.agent = Agent(name=name, seed=seed)
        self.logic = DiscoveryLogic()
        self.protocol = Protocol(name="discovery_protocol")

        self._register_handlers()
        self.agent.include(self.protocol)

    def _register_handlers(self):
        @self.protocol.on_message(model=DiscoveryRequest, replies=DiscoveryResponse)
        async def handle_discovery(ctx: Context, sender: str, msg: DiscoveryRequest):
            try:
                ctx.logger.info(f"🔍 Discovery request: {msg.criteria}")

                pools = await self.logic.discover_pools_async(msg.criteria)

                # Relay to RiskAgent
                pool_objs = [Pool(id=p["id"], metrics=p.get("metrics")) for p in pools]
                risk_req = RiskRequest(pools=pool_objs)

                ctx.logger.info(f"📤 Forwarding {len(pool_objs)} pools to RiskAgent...")
                await ctx.send("risk_agent_address_here", risk_req)  # replace with real address

                return DiscoveryResponse(status="success", data={"pools": pools})

            except Exception as e:
                ctx.logger.error(f"❌ Error in discovery: {e}")
                return DiscoveryResponse(status="error", error=str(e))

        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            ctx.logger.info(f"🚀 Discovery Agent started at {ctx.address}")

    async def act(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = await self.logic.discover_pools_async(criteria)
            return {"status": "success", "pools": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run(self):
        self.agent.run()
