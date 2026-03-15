# discovery_logic.py
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Ensure project root on path for core imports (protocol registry)
_proj_root = Path(__file__).resolve().parents[2]
if str(_proj_root) not in sys.path:
    sys.path.insert(0, str(_proj_root))

from core.protocol_registry import PROTOCOL_REGISTRY, validate_protocols
from services.defillama_client import DeFiLlamaClient, YieldProtocol
from services.protocol_apy import get_secondary_apy

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
    poolMeta: Optional[str] = None
    underlyingTokens: Optional[List[str]] = None
    rewardTokens: Optional[List[str]] = None
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
            poolMeta=pool.poolMeta,
            underlyingTokens=pool.underlyingTokens,
            rewardTokens=pool.rewardTokens,
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
            # Return empty list when API fails
            return []

    # # TODO: add Surge + Uniswap discovery here
    # async def _discover_surge_pools(self) -> List[Pool]:
    #     return []

    # async def _discover_uniswap_pools(self) -> List[Pool]:
    #     return []
    

    # ------------------------------
    # Filtering + ranking
    # ------------------------------
    def filter_pools_by_criteria(self, pools: List[Pool], criteria: Dict[str, Any]) -> List[Pool]:
        """Filter pools according to provided criteria. Uses protocol registry when allowed_protocols provided."""
        # Protocol allowlist: from registry if policy specifies allowed_protocols, else default trusted
        allowed_protocols_raw: List[str] = criteria.get("allowed_protocols") or []
        if allowed_protocols_raw:
            valid_names, invalid_names = validate_protocols(allowed_protocols_raw)
            if invalid_names:
                logger.warning("Unknown protocols in policy (excluded): %s", invalid_names)
            # Set of registry keys that are allowed (canonical + aliases e.g. aave-v3 -> aave)
            allowed_protocol_set = set(valid_names) | {
                k for k, v in PROTOCOL_REGISTRY.items()
                if v.name in valid_names
            }
        else:
            allowed_protocol_set = {
                "uniswap", "uniswap-v2", "uniswap-v3",
                "compound", "compound-v2", "compound-v3",
                "aave", "aave-v2", "aave-v3",
                "venus", "curve", "curve-dex", "pendle",
                "pancakeswap", "pancake", "balancer", "balancer-v2", "yearn",
            }

        allowed_chains: List[str] = [c.strip().lower() for c in (criteria.get("allowed_chains") or []) if c]
        min_tvl: float = float(criteria.get("min_pool_tvl_usd") or criteria.get("min_tvl") or 0)
        min_apy: float = criteria.get("min_apy", 0.0) or 0
        max_apy = criteria.get("max_apy")
        preference = criteria.get("preference", "medium")

        filtered = []
        for p in pools:
            if p.tvl is None or p.apy is None:
                continue

            protocol_lower = p.protocol.lower()
            if protocol_lower not in allowed_protocol_set:
                continue
            if allowed_chains and (p.chain or "").strip().lower() not in allowed_chains:
                continue
            if p.tvl < min_tvl or p.apy < min_apy:
                continue
            if max_apy is not None and p.apy > max_apy:
                continue
            if preference == "safest" and p.tvl < 10_000_000:
                continue
            filtered.append(p)

        return filtered

    def rank_pools(self, pools: List[Pool], criteria: Dict[str, Any], top_n: int = 5) -> List[Pool]:
        """Rank pools based on criteria."""
        preference = criteria.get("preference", "medium")
        
        if preference == "safest":
            
            def calculate_safety_score(pool: Pool) -> float:
                """Calculate a composite safety score (0-100)."""
                score = 0
                
                # TVL weight (40 points)
                if pool.tvl > 100_000_000: score += 40
                elif pool.tvl > 50_000_000: score += 30
                elif pool.tvl > 10_000_000: score += 20
                elif pool.tvl > 1_000_000: score += 10
                else: score += 5
                
                # Protocol reputation weight (30 points) - using available data
                safe_protocols = ["uniswap", "aave", "compound", "makerdao", "lido", "curve", "balancer", "yearn", "convex", "frax"]
                protocol_lower = pool.protocol.lower()
                if any(safe in protocol_lower for safe in safe_protocols):
                    score += 30
                elif "v3" in protocol_lower or "v2" in protocol_lower:
                    score += 20  # Versioned protocols are generally more mature
                else:
                    score += 10  # Default for unknown protocols
                
                # APY stability weight (30 points) - using APY as proxy for stability
                if pool.apy < 5: score += 30  # Very stable, low APY
                elif pool.apy < 10: score += 20  # Moderate APY
                elif pool.apy < 20: score += 10  # Higher APY, more risk
                else: score += 5  # Very high APY, high risk
                
                return score
                            
            return sorted(pools, key=calculate_safety_score, reverse=True)[:top_n]
        else:
            # For other preferences, rank by APY
            return sorted(pools, key=lambda p: p.apy, reverse=True)[:top_n]

    # ------------------------------
    # Orchestration
    # ------------------------------
   
    async def discover_pools_async(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Main entry point for pool discovery."""
        logger.info("🚀 Running discovery with criteria %s", criteria)

        # Gather pools from all sources
        llama_pools = await asyncio.gather(
            self._discover_llama_pools(),
            # self._discover_surge_pools(),
            # self._discover_uniswap_pools(),
        )

        # Flatten the results since asyncio.gather returns a list of results
        all_pools = []
        for pool_list in llama_pools:
            if pool_list:  # Check if the list is not empty
                all_pools.extend(pool_list)
        
        if not all_pools:
            logger.warning("⚠️ No pools found from any source")
            return []

        logger.info(f"✅ Found {len(all_pools)} total pools")

        # Cross-check APY across sources. Single-source APY is a trust assumption
        # that is inappropriate for a treasury product. See:
        # https://defillama.com/docs/api for primary source.
        # Protocol subgraphs (e.g. Aave, Compound) are the secondary source.
        pools_after_apy_check: List[Pool] = []
        for pool in all_pools:
            secondary_apy = await get_secondary_apy(pool.protocol, pool.chain, pool.symbol)
            if secondary_apy is not None:
                denom = max(pool.apy, secondary_apy, 0.01)
                deviation = abs(pool.apy - secondary_apy) / denom
                if deviation > 0.20:
                    logger.warning(
                        "APY deviation >20%% between DeFiLlama and protocol source for pool %s. "
                        "Excluding from recommendations.",
                        pool.id,
                    )
                    continue
            pools_after_apy_check.append(pool)
        all_pools = pools_after_apy_check

        # Filter + rank
        filtered = self.filter_pools_by_criteria(all_pools, criteria)
        if not filtered:
            logger.warning("⚠️ No pools match the specified criteria")
            return []
            
        ranked = self.rank_pools(filtered, criteria, top_n=criteria.get("top_n", 10))
        logger.info("#### Discovery output #### %s", [p.__dict__ for p in ranked])

        # Return just the list of pool dictionaries for the agent
        return [p.__dict__ for p in ranked]
