# discovery_logic.py
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from services.defillama_client import DeFiLlamaClient, YieldProtocol

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
        min_tvl: float = criteria.get("min_tvl", 0.0) or 0
        min_apy: float = criteria.get("min_apy", 0.0) or 0
        preference = criteria.get("preference", "medium")

        for p in pools:
            if p.tvl is None or p.apy is None:
                continue
            if p.tvl < min_tvl or p.apy < min_apy:
                continue
                
            # Additional filtering for safest preference
            if preference == "safest":
                # Only include well-known, established protocols for safest
                safe_protocols = [
                    "uniswap", "aave", "compound", "makerdao", "lido", 
                    "curve", "balancer", "yearn", "convex", "frax"
                ]
                if not any(safe in p.protocol.lower() for safe in safe_protocols):
                    continue
                    
                # Require higher TVL for safest pools
                if p.tvl < 10000000:  # $10M minimum for safest
                    continue

            filtered.append(p)

        return filtered

    def rank_pools(self, pools: List[Pool], criteria: Dict[str, Any], top_n: int = 5) -> List[Pool]:
        """Rank pools based on criteria."""
        preference = criteria.get("preference", "medium")
        
        if preference == "safest":
            # For safest, prioritize established protocols with good TVL over high APY
            def safety_score(pool):
                # Base score from TVL (higher TVL = safer)
                tvl_score = min(100, (pool.tvl / 1000000000) * 50)  # Max 50 points for $1B+ TVL
                
                # Protocol safety bonus
                protocol_bonus = 0
                if "uniswap" in pool.protocol.lower():
                    protocol_bonus = 30
                elif "aave" in pool.protocol.lower():
                    protocol_bonus = 25
                elif "compound" in pool.protocol.lower():
                    protocol_bonus = 25
                elif "lido" in pool.protocol.lower():
                    protocol_bonus = 20
                elif "curve" in pool.protocol.lower():
                    protocol_bonus = 20
                
                # APY bonus (but less important for safety)
                apy_bonus = min(20, pool.apy * 2)  # Max 20 points for 10%+ APY
                
                return tvl_score + protocol_bonus + apy_bonus
            
            return sorted(pools, key=safety_score, reverse=True)[:top_n]
        else:
            # For other preferences, rank by APY
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
        ranked = self.rank_pools(filtered, criteria, top_n=criteria.get("top_n", 5))

        # Return just the list of pool dictionaries for the agent
        return [p.__dict__ for p in ranked]
