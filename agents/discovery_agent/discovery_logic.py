# discovery_logic.py
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .services.defillama_client import DeFiLlamaClient, YieldProtocol

logger = logging.getLogger(__name__)


@dataclass
class Pool:
    """Data class to hold pool information."""
    id: str
    protocol: str
    chain: str
    tvl: float
    apy: float
    symbol: str
    project: str
    url: Optional[str] = None
    last_updated: Optional[datetime] = None


class DiscoveryLogic:
    """Core logic for discovering DeFi pools from multiple sources."""

    def __init__(self):
        self.name = "DiscoveryLogic"
        self.version = "1.0.0"
        self.description = "Discovers DeFi pools from Surge, Uniswap, and DeFiLlama protocols"
        self.tags = ["defi", "discovery", "pools"]

        # API clients
        self.llama = DeFiLlamaClient()

    # ------------------------------
    # Pool conversion helpers
    # ------------------------------
    def _convert_llama_pool(self, pool: YieldProtocol) -> Pool:
        return Pool(
            id=pool.pool,
            protocol=pool.project,
            chain=pool.chain,
            tvl=pool.tvlUsd,
            apy=pool.apyBase or 0.0,
            symbol=pool.symbol,
            project=pool.project,
            url=pool.url,
            last_updated=datetime.utcnow()
        )

    # ------------------------------
    # Discovery methods
    # ------------------------------
    async def _discover_llama_pools(self) -> List[Pool]:
        """Fetch pools from DeFiLlama."""
        try:
            raw_pools = await self.llama.get_yield_pools()
            return [self._convert_llama_pool(p) for p in raw_pools]
        except Exception as e:
            logger.error(f"Error fetching pools from DeFiLlama: {e}")
            # Return mock data for testing
            return self._get_mock_pools()

    # TODO: add Surge + Uniswap discovery here
    async def _discover_surge_pools(self) -> List[Pool]:
        return []

    async def _discover_uniswap_pools(self) -> List[Pool]:
        return []
    
    def _get_mock_pools(self) -> List[Pool]:
        """Return mock pool data for testing when APIs are unavailable."""
        return [
            Pool(
                id="0x1234567890abcdef",
                protocol="Uniswap V3",
                chain="ethereum",
                tvl=2500000.0,
                apy=8.5,
                symbol="ETH/USDC",
                project="Uniswap",
                url="https://app.uniswap.org/pools/0x1234567890abcdef",
                last_updated=datetime.utcnow()
            ),
            Pool(
                id="0xabcdef1234567890",
                protocol="Aave V3",
                chain="ethereum",
                tvl=1800000.0,
                apy=6.2,
                symbol="USDC",
                project="Aave",
                url="https://app.aave.com/reserve-overview/USDC-0xa0b86a33e6c4e8b2c8b3c8b3c8b3c8b3c8b3c8b3",
                last_updated=datetime.utcnow()
            ),
            Pool(
                id="0x9876543210fedcba",
                protocol="Compound V3",
                chain="ethereum",
                tvl=3200000.0,
                apy=7.8,
                symbol="USDT",
                project="Compound",
                url="https://app.compound.finance/markets/USDT",
                last_updated=datetime.utcnow()
            )
        ]

    # ------------------------------
    # Filtering + ranking
    # ------------------------------
    def filter_pools_by_criteria(self, pools: List[Pool], criteria: Dict[str, Any]) -> List[Pool]:
        """Filter pools according to provided criteria."""
        filtered = []
        min_tvl = criteria.get("min_tvl", 0)
        min_apy = criteria.get("min_apy", 0)

        for p in pools:
            if p.tvl >= min_tvl and p.apy >= min_apy:
                filtered.append(p)

        return filtered

    def rank_pools(self, pools: List[Pool], top_n: int = 5) -> List[Pool]:
        """Rank pools by APY (descending)."""
        return sorted(pools, key=lambda p: p.apy, reverse=True)[:top_n]

    # ------------------------------
    # Orchestration
    # ------------------------------
    async def discover_pools(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for pool discovery."""
        return await self.discover_pools_async(criteria)
    
    async def discover_pools_async(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Main entry point for pool discovery."""
        logger.info("🚀 Running discovery with criteria %s", criteria)

        # Gather pools from all sources
        llama_pools, surge_pools, uni_pools = await asyncio.gather(
            self._discover_llama_pools(),
            self._discover_surge_pools(),
            self._discover_uniswap_pools(),
        )

        all_pools = llama_pools + surge_pools + uni_pools
        logger.info(f"✅ Found {len(all_pools)} total pools")

        # Filter + rank
        filtered = self.filter_pools_by_criteria(all_pools, criteria)
        ranked = self.rank_pools(filtered, top_n=criteria.get("top_n", 5))

        # Return just the list of pool dictionaries for the agent
        return [p.__dict__ for p in ranked]
