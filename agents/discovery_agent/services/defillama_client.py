# services/defillama_client.py
import asyncio
import aiohttp
import logging
import time
from typing import List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Cache the raw pool list for 10 minutes — this is ~5-10MB of JSON and the
# single most expensive operation in the pipeline. All concurrent runs share it.
_pools_cache: Optional[Tuple[List, float]] = None
_POOLS_CACHE_TTL = 600  # 10 minutes
_pools_lock = asyncio.Lock()


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
        """Fetch pools from DeFiLlama yield API with a 10-minute in-process cache.
        All concurrent pipeline runs share one download — critical for launch traffic."""
        global _pools_cache

        # Fast path: cache hit (no lock needed for read)
        if _pools_cache is not None and (time.time() - _pools_cache[1]) < _POOLS_CACHE_TTL:
            logger.info("DeFiLlama pool cache hit — skipping fetch")
            return _pools_cache[0]

        # Slow path: one coroutine fetches, others wait on the lock
        async with _pools_lock:
            # Re-check after acquiring lock (another coroutine may have just fetched)
            if _pools_cache is not None and (time.time() - _pools_cache[1]) < _POOLS_CACHE_TTL:
                return _pools_cache[0]

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
                _pools_cache = (pools, time.time())
                logger.info(f"DeFiLlama pool cache refreshed — {len(pools)} pools")
                return pools

            except Exception as e:
                logger.error(f"❌ Error fetching DeFiLlama yield pools: {e}")
                # Return stale cache if available rather than empty
                if _pools_cache is not None:
                    logger.warning("Returning stale DeFiLlama cache after fetch failure")
                    return _pools_cache[0]
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
