# services/defillama_client.py
import aiohttp
import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ------------------------------
# Data Models
# ------------------------------
@dataclass
class YieldProtocol:
    pool: str
    project: str
    chain: str
    tvlUsd: float
    apyBase: Optional[float]
    symbol: str
    url: Optional[str] = None
    poolMeta: Optional[str] = None
    underlyingTokens: Optional[List[str]] = None
    rewardTokens: Optional[List[str]] = None


@dataclass
class Protocol:
    name: str
    slug: str
    category: str
    tvl: float
    chains: List[str]


# ------------------------------
# API Client
# ------------------------------
class DeFiLlamaClient:
    """Async client for DeFiLlama API (yields + protocols)."""

    BASE_URL = "https://api.llama.fi"
    YIELDS_URL = "https://yields.llama.fi"

    # ---- Yield Pools ----
    async def get_yield_pools(self) -> List[YieldProtocol]:
        """Fetch pools from DeFiLlama yield API."""
        url = f"{self.YIELDS_URL}/pools"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise RuntimeError(f"DeFiLlama API error {resp.status}")
                    data = await resp.json()

            pools = []
            for p in data.get("data", []):
                pools.append(
                    YieldProtocol(
                        pool=p.get("pool"),
                        project=p.get("project"),
                        chain=p.get("chain"),
                        tvlUsd=p.get("tvlUsd", 0.0),
                        apyBase=p.get("apyBase"),
                        symbol=p.get("symbol", ""),
                        url=p.get("url"),
                        poolMeta=p.get("poolMeta"),
                        underlyingTokens=p.get("underlyingTokens", []),
                        rewardTokens=p.get("rewardTokens", [])
                    )
                )
            return pools

        except Exception as e:
            logger.error(f"❌ Error fetching DeFiLlama yield pools: {e}")
            return []

    # ---- Protocols ----
    async def get_protocols(self) -> List[Protocol]:
        """Fetch protocols list from DeFiLlama API."""
        url = f"{self.BASE_URL}/protocols"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise RuntimeError(f"DeFiLlama API error {resp.status}")
                    data = await resp.json()

            protocols = []
            for p in data:
                protocols.append(
                    Protocol(
                        name=p.get("name"),
                        slug=p.get("slug"),
                        category=p.get("category", "unknown"),
                        tvl=p.get("tvl", 0.0),
                        chains=p.get("chains", []),
                    )
                )
            return protocols

        except Exception as e:
            logger.error(f"❌ Error fetching DeFiLlama protocols: {e}")
            return []
