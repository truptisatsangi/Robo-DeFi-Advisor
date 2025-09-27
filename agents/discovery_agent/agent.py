import logging
from typing import Dict, Any

from uagents import Agent, Context, Protocol, Model
from .discovery_logic import DiscoveryLogic

from agents.risk_agent.agent import RiskRequest, Pool


risk_agent_address = "agent1qtsc37wq536s6xsfrp2th206t6gevkxskpx2c2d37mt4zru8zpuushp64ml"


logger = logging.getLogger(__name__)


class DiscoveryRequest(Model):
    criteria: Dict[str, Any]


class DiscoveryResponse(Model):
    status: str
    data: Dict[str, Any] | None = None
    error: str | None = None


class DiscoveryUAgent:
    def __init__(self, seed: str = "discovery_seed", name: str = "discovery_agent"):
        self.agent = Agent(name=name, seed=seed, port=8001, endpoint=["http://localhost:8001/submit"])
        self.logic = DiscoveryLogic()
        self.protocol = Protocol(name="discovery_protocol")

        self._register_handlers()
        self.agent.include(self.protocol)
        self.address = "agent1qvk9d7hcwrv3jhazh5f7vmrzy255dvu6tpj5eg89n8ekc4f94dtm6jjxex2"

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
                await ctx.send(risk_agent_address, risk_req) 

                return DiscoveryResponse(status="success", data={"pools": pools})

            except Exception as e:
                ctx.logger.error(f"❌ Error in discovery: {e}")
                return DiscoveryResponse(status="error", error=str(e))

        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            ctx.logger.info(f"🚀 Discovery Agent {self.agent.name} started at {self.agent.address}")

    async def act(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = await self.logic.discover_pools_async(criteria)
            return {"status": "success", "pools": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run(self):
        self.agent.run()
