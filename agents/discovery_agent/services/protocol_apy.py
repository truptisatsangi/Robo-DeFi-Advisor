# protocol_apy.py
# Secondary APY sources (protocol subgraphs/APIs) for cross-checking DeFiLlama.
# See discovery_logic.py: cross-check APY across sources for treasury product trust.

import logging
from typing import Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=4)

# ---------------------------------------------------------------------------
# Cache — avoids repeated API calls within one discovery run
# ---------------------------------------------------------------------------
_secondary_apy_cache: dict = {}

# ---------------------------------------------------------------------------
# Chain mappings
# ---------------------------------------------------------------------------
CHAIN_TO_ID: Dict[str, int] = {
    "ethereum": 1,
    "arbitrum": 42161,
    "polygon": 137,
    "optimism": 10,
    "base": 8453,
    "avalanche": 43114,
}

CURVE_CHAIN_NAMES: Dict[str, str] = {
    "ethereum": "ethereum",
    "arbitrum": "arbitrum",
    "polygon": "polygon",
    "optimism": "optimism",
    "base": "base",
    "avalanche": "avalanche",
    "fantom": "fantom",
}

YEARN_CHAIN_IDS: Dict[str, int] = {
    "ethereum": 1,
    "arbitrum": 42161,
    "polygon": 137,
    "optimism": 10,
    "base": 8453,
    "fantom": 250,
}


# ---------------------------------------------------------------------------
# Aave V3  (GraphQL API)
# ---------------------------------------------------------------------------
AAVE_V3_GRAPHQL = "https://api.v3.aave.com/graphql"


async def get_secondary_apy_aave_v3(chain: str, symbol: str) -> Optional[float]:
    """Fetch supply APY for a reserve from Aave V3 GraphQL API. Returns APY in percent (e.g. 5.5) or None."""
    chain_id = CHAIN_TO_ID.get(chain.lower() if chain else "")
    if not chain_id:
        return None
    symbol_upper = (symbol or "").split("-")[0].strip().upper()
    if not symbol_upper:
        return None
    cache_key = ("aave-v3", chain, symbol_upper)
    if cache_key in _secondary_apy_cache:
        return _secondary_apy_cache[cache_key]
    query = """
    query GetMarkets($chainIds: [ChainId!]!) {
      markets(chainIds: $chainIds) {
        supplyReserves {
          underlyingToken { symbol }
          supplyInfo { apy { formatted } }
        }
      }
    }
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                AAVE_V3_GRAPHQL,
                json={"query": query, "variables": {"chainIds": [chain_id]}},
                headers={"Content-Type": "application/json"},
                timeout=_REQUEST_TIMEOUT,
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
    except Exception as e:
        logger.debug("Aave V3 APY fetch failed: %s", e)
        return None
    markets = (data.get("data") or {}).get("markets") or []
    for market in markets:
        for reserve in market.get("supplyReserves") or []:
            token = (reserve.get("underlyingToken") or {}).get("symbol") or ""
            if token.upper() == symbol_upper:
                apy_val = (reserve.get("supplyInfo") or {}).get("apy") or {}
                formatted = apy_val.get("formatted")
                if formatted is not None:
                    try:
                        apy_float = float(formatted)
                        _secondary_apy_cache[cache_key] = apy_float
                        return apy_float
                    except (TypeError, ValueError):
                        pass
    return None


# ---------------------------------------------------------------------------
# Compound V3  (Compound REST API — v2 endpoint still serves v3 cTokens)
# ---------------------------------------------------------------------------
COMPOUND_API = "https://api.compound.finance/api/v2/ctoken"


async def get_secondary_apy_compound(chain: str, symbol: str) -> Optional[float]:
    """Fetch supply rate from Compound API. Returns APY in percent or None."""
    if (chain or "").lower() not in ("ethereum", "mainnet"):
        return None
    symbol_upper = (symbol or "").split("-")[0].strip().upper()
    if not symbol_upper:
        return None
    cache_key = ("compound", chain, symbol_upper)
    if cache_key in _secondary_apy_cache:
        return _secondary_apy_cache[cache_key]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                COMPOUND_API,
                timeout=_REQUEST_TIMEOUT,
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
    except Exception as e:
        logger.debug("Compound APY fetch failed: %s", e)
        return None
    for token in (data.get("cToken") or []):
        underlying = (token.get("underlying_symbol") or "").upper()
        if underlying == symbol_upper:
            try:
                supply_rate = float(token.get("supply_rate", {}).get("value", 0))
                apy_pct = supply_rate * 100
                _secondary_apy_cache[cache_key] = apy_pct
                return apy_pct
            except (TypeError, ValueError, AttributeError):
                pass
    return None


# ---------------------------------------------------------------------------
# Curve Finance  (Curve API — pools endpoint)
# ---------------------------------------------------------------------------
CURVE_API_TEMPLATE = "https://api.curve.fi/api/getPools/{chain}/main"


async def get_secondary_apy_curve(chain: str, symbol: str) -> Optional[float]:
    """Fetch base APY for a Curve pool from the Curve API. Returns APY in percent or None."""
    curve_chain = CURVE_CHAIN_NAMES.get((chain or "").lower())
    if not curve_chain:
        return None
    symbol_upper = (symbol or "").strip().upper()
    if not symbol_upper:
        return None
    cache_key = ("curve", chain, symbol_upper)
    if cache_key in _secondary_apy_cache:
        return _secondary_apy_cache[cache_key]
    url = CURVE_API_TEMPLATE.format(chain=curve_chain)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=_REQUEST_TIMEOUT) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
    except Exception as e:
        logger.debug("Curve APY fetch failed for %s: %s", chain, e)
        return None
    pools: List[dict] = (data.get("data") or {}).get("poolData") or []
    for pool in pools:
        # Match by coin symbols — pool["coins"] is a list of {symbol, ...}
        pool_symbols = [
            (c.get("symbol") or "").upper() for c in (pool.get("coins") or [])
        ]
        pool_name = (pool.get("name") or "").upper()
        # Match if the query symbol appears in the pool's coin list or name
        if symbol_upper in pool_symbols or symbol_upper in pool_name:
            try:
                base_apy = float(pool.get("baseApy") or pool.get("apy") or 0)
                apy_pct = base_apy if base_apy > 0.01 else base_apy * 100
                _secondary_apy_cache[cache_key] = apy_pct
                return apy_pct
            except (TypeError, ValueError):
                pass
    return None


# ---------------------------------------------------------------------------
# Yearn Finance  (yDaemon REST API)
# ---------------------------------------------------------------------------
YEARN_API_TEMPLATE = "https://ydaemon.yearn.fi/{chain_id}/vaults/all"


async def get_secondary_apy_yearn(chain: str, symbol: str) -> Optional[float]:
    """Fetch net APY for a Yearn vault from the yDaemon API. Returns APY in percent or None."""
    chain_id = YEARN_CHAIN_IDS.get((chain or "").lower())
    if not chain_id:
        return None
    symbol_upper = (symbol or "").split("-")[0].strip().upper()
    if not symbol_upper:
        return None
    cache_key = ("yearn", chain, symbol_upper)
    if cache_key in _secondary_apy_cache:
        return _secondary_apy_cache[cache_key]
    url = YEARN_API_TEMPLATE.format(chain_id=chain_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=_REQUEST_TIMEOUT) as resp:
                if resp.status != 200:
                    return None
                vaults = await resp.json()
    except Exception as e:
        logger.debug("Yearn APY fetch failed for %s: %s", chain, e)
        return None
    if not isinstance(vaults, list):
        return None
    for vault in vaults:
        token_symbol = (vault.get("token", {}).get("symbol") or "").upper()
        vault_symbol = (vault.get("symbol") or "").upper()
        if symbol_upper in (token_symbol, vault_symbol):
            try:
                apy_data = vault.get("apy") or {}
                net_apy = apy_data.get("net_apy")
                if net_apy is None:
                    continue
                apy_pct = float(net_apy) * 100
                _secondary_apy_cache[cache_key] = apy_pct
                return apy_pct
            except (TypeError, ValueError):
                pass
    return None


# ---------------------------------------------------------------------------
# Router — dispatches to the correct protocol source
# ---------------------------------------------------------------------------
async def get_secondary_apy(protocol: str, chain: str, symbol: str) -> Optional[float]:
    """
    Return secondary APY (in percent) for a pool from the protocol's own subgraph/API, or None
    if no source is available or fetch fails. Used to cross-check DeFiLlama APY.
    """
    if not protocol or not chain:
        return None
    pl = protocol.lower()
    if "aave" in pl:
        return await get_secondary_apy_aave_v3(chain, symbol)
    if "compound" in pl:
        return await get_secondary_apy_compound(chain, symbol)
    if "curve" in pl:
        return await get_secondary_apy_curve(chain, symbol)
    if "yearn" in pl:
        return await get_secondary_apy_yearn(chain, symbol)
    return None
