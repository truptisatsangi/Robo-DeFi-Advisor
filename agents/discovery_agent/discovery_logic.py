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

# Ensure discovery agent dir on path for its local services package
_agent_dir = Path(__file__).resolve().parent
if str(_agent_dir) not in sys.path:
    sys.path.insert(0, str(_agent_dir))

from core.protocol_registry import PROTOCOL_REGISTRY, get_protocol, validate_protocols
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
        """Filter pools according to provided policy criteria using protocol registry metadata."""
        # Protocol allowlist: from registry if policy specifies allowed_protocols, else default trusted registry entries
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
                key for key, entry in PROTOCOL_REGISTRY.items() if key == entry.name
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
            proto_valid, _ = validate_protocols([protocol_lower])
            if not proto_valid:
                continue
            canonical_protocol = proto_valid[0]
            if canonical_protocol not in allowed_protocol_set:
                continue

            chain_normalized = (p.chain or "").strip().lower()
            if allowed_chains and chain_normalized not in allowed_chains:
                continue

            protocol_entry = get_protocol(canonical_protocol)
            supported_chains = {c.strip().lower() for c in protocol_entry.supported_chains}
            if chain_normalized not in supported_chains:
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
        """Rank pools based on criteria.

        Preference strategies:
          safest        — composite safety score weighted toward TVL + protocol tier + low APY
          highest_yield — pure APY descending; risk is handled post-discovery by risk policy filters
          balanced      — composite of APY (50%) + TVL (35%) + protocol tier (15%); balances
                          yield against liquidity depth and protocol trustworthiness
        """
        preference = (criteria.get("preference") or "balanced").lower()

        if preference == "safest":
            def calculate_safety_score(pool: Pool) -> float:
                score = 0
                if pool.tvl > 100_000_000: score += 40
                elif pool.tvl > 50_000_000: score += 30
                elif pool.tvl > 10_000_000: score += 20
                elif pool.tvl > 1_000_000: score += 10
                else: score += 5

                safe_protocols = ["uniswap", "aave", "compound", "makerdao", "lido", "curve", "balancer", "yearn", "convex", "frax"]
                protocol_lower = pool.protocol.lower()
                if any(safe in protocol_lower for safe in safe_protocols):
                    score += 30
                elif "v3" in protocol_lower or "v2" in protocol_lower:
                    score += 20
                else:
                    score += 10

                if pool.apy < 5: score += 30
                elif pool.apy < 10: score += 20
                elif pool.apy < 20: score += 10
                else: score += 5

                return score

            return sorted(pools, key=calculate_safety_score, reverse=True)[:top_n]

        elif preference == "highest_yield":
            # Pure APY descending; risk constraints filter out unsafe pools in the risk stage.
            return sorted(pools, key=lambda p: p.apy, reverse=True)[:top_n]

        else:
            # balanced (default): composite of APY, TVL depth, and protocol tier.
            # This produces a different candidate set than highest_yield — a pool with
            # slightly lower APY but 10× the TVL can outscore a higher-APY shallow pool.
            if not pools:
                return pools
            apys = [p.apy for p in pools]
            tvls = [p.tvl for p in pools]
            apy_lo, apy_hi = min(apys), max(apys)
            tvl_lo, tvl_hi = min(tvls), max(tvls)
            _tier1 = {"uniswap", "aave", "compound", "curve"}
            _tier2 = {"balancer", "pendle", "yearn", "lido"}

            def _balanced_score(p: Pool) -> float:
                n_apy = (p.apy - apy_lo) / (apy_hi - apy_lo) if apy_hi > apy_lo else 0.5
                n_tvl = (p.tvl - tvl_lo) / (tvl_hi - tvl_lo) if tvl_hi > tvl_lo else 0.5
                proto = p.protocol.lower()
                if any(t in proto for t in _tier1):
                    n_proto = 1.0
                elif any(t in proto for t in _tier2):
                    n_proto = 0.7
                else:
                    n_proto = 0.3
                return 0.50 * n_apy + 0.35 * n_tvl + 0.15 * n_proto

            return sorted(pools, key=_balanced_score, reverse=True)[:top_n]

    # ------------------------------
    # Orchestration
    # ------------------------------
   
    async def _discover_pools_with_stats(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Main discovery pipeline that returns pools and stage counts."""
        logger.info("🚀 Running discovery with criteria %s", criteria)
        stats: Dict[str, int] = {
            "total_fetched": 0,
            "after_policy_filters": 0,
            "after_rank_top_n": 0,
            "after_apy_crosscheck": 0,
        }

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
        stats["total_fetched"] = len(all_pools)
        
        if not all_pools:
            logger.warning("⚠️ No pools found from any source")
            return {"pools": [], "stats": stats}

        logger.info(f"✅ Found {len(all_pools)} total pools")

        # Filter + rank FIRST (fast, local) to reduce the set before expensive API calls
        filtered = self.filter_pools_by_criteria(all_pools, criteria)
        stats["after_policy_filters"] = len(filtered)
        if not filtered:
            logger.warning("⚠️ No pools match the specified criteria")
            return {"pools": [], "stats": stats}

        ranked = self.rank_pools(filtered, criteria, top_n=criteria.get("top_n", 10))
        stats["after_rank_top_n"] = len(ranked)
        logger.info(f"📊 {len(ranked)} pools after filter + rank (from {len(all_pools)} total)")

        # Cross-check APY across sources. Single-source APY is a trust assumption
        # that is inappropriate for a treasury product. See:
        # https://defillama.com/docs/api for primary source.
        # Protocol subgraphs (e.g. Aave, Compound) are the secondary source.
        # Runs only on the small ranked set (not all 19k pools).
        # All cross-checks run concurrently to avoid sequential latency.
        async def _check_pool_apy(pool: Pool) -> Optional[Pool]:
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
                    return None
            return pool

        crosscheck_results = await asyncio.gather(*[_check_pool_apy(p) for p in ranked])
        verified: List[Pool] = [p for p in crosscheck_results if p is not None]

        if not verified:
            logger.warning("⚠️ All ranked pools failed APY cross-check")
            return {"pools": [], "stats": stats}

        stats["after_apy_crosscheck"] = len(verified)
        logger.info("#### Discovery output #### %s", [p.__dict__ for p in verified])
        return {"pools": [p.__dict__ for p in verified], "stats": stats}

    async def discover_pools_async(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Backwards-compatible pool discovery API returning only pools."""
        result = await self._discover_pools_with_stats(criteria)
        return result["pools"]

    async def discover_pools_with_stats(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Discovery API returning pools plus stage telemetry."""
        return await self._discover_pools_with_stats(criteria)
