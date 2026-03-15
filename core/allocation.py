"""
Multi-pool allocation engine — distributes capital across top-ranked pools.
Respects max_tvl_per_pool_pct from policy. Computes weighted portfolio APY.
"""

from typing import Any, Dict, List, Optional


DEFAULT_MAX_POOL_PCT = 40.0  # If policy doesn't set max_tvl_per_pool_pct, cap at 40%
MAX_POOLS_IN_ALLOCATION = 5  # Don't spread thinner than 5 pools


def allocate_across_pools(
    scored_pools: List[Dict[str, Any]],
    amount_usd: float,
    max_tvl_per_pool_pct: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Distribute `amount_usd` across top scored pools using score-weighted allocation,
    capped by `max_tvl_per_pool_pct` (% of total amount per pool).

    Returns:
        {
            "allocations": [
                {"pool_id": ..., "protocol": ..., "chain": ..., "apy": ...,
                 "risk_score": ..., "amount_usd": ..., "pct": ..., "score": ...},
                ...
            ],
            "expected_portfolio_apy": float,
            "total_allocated_usd": float,
        }
    """
    if not scored_pools or amount_usd <= 0:
        return {
            "allocations": [],
            "expected_portfolio_apy": 0.0,
            "total_allocated_usd": 0.0,
        }

    cap_pct = max_tvl_per_pool_pct if max_tvl_per_pool_pct and max_tvl_per_pool_pct > 0 else DEFAULT_MAX_POOL_PCT
    cap_frac = cap_pct / 100.0

    candidates = scored_pools[:MAX_POOLS_IN_ALLOCATION]

    total_score = sum(p.get("totalScore", 0) for p in candidates)
    if total_score <= 0:
        total_score = len(candidates)
        for p in candidates:
            p["totalScore"] = 1.0

    raw_fracs = []
    for p in candidates:
        frac = p.get("totalScore", 0) / total_score
        raw_fracs.append(frac)

    # Iteratively cap pools that exceed the limit and redistribute surplus
    final_fracs = list(raw_fracs)
    for _ in range(10):
        surplus = 0.0
        uncapped_total = 0.0
        capped_indices = set()
        for i, frac in enumerate(final_fracs):
            if frac > cap_frac:
                surplus += frac - cap_frac
                final_fracs[i] = cap_frac
                capped_indices.add(i)
        if surplus <= 0:
            break
        uncapped_total = sum(final_fracs[i] for i in range(len(final_fracs)) if i not in capped_indices)
        if uncapped_total <= 0:
            break
        for i in range(len(final_fracs)):
            if i not in capped_indices:
                final_fracs[i] += surplus * (final_fracs[i] / uncapped_total)

    # Drop pools with negligible allocation (< 2%)
    min_alloc_frac = 0.02
    allocations = []
    for i, p in enumerate(candidates):
        if final_fracs[i] < min_alloc_frac:
            continue
        risk_data = p.get("riskData") or {}
        allocations.append({
            "pool_id": p.get("id", ""),
            "protocol": p.get("protocol", "Unknown"),
            "chain": p.get("chain", "Unknown"),
            "apy": p.get("apy", 0),
            "risk_score": risk_data.get("riskScore", 0),
            "risk_level": risk_data.get("riskLevel", "—"),
            "tvl": p.get("tvl", 0),
            "score": p.get("totalScore", 0),
            "pct": round(final_fracs[i] * 100, 1),
            "amount_usd": round(final_fracs[i] * amount_usd, 2),
            "url": p.get("url") or "",
            "explanation": p.get("explanation") or p.get("selection_reason") or "",
        })

    # Re-normalize so percentages sum to ~100 after dropping tiny slices
    alloc_sum = sum(a["pct"] for a in allocations)
    if allocations and alloc_sum > 0 and abs(alloc_sum - 100.0) > 0.5:
        scale = 100.0 / alloc_sum
        for a in allocations:
            a["pct"] = round(a["pct"] * scale, 1)
            a["amount_usd"] = round(a["pct"] / 100.0 * amount_usd, 2)

    total_allocated = sum(a["amount_usd"] for a in allocations)

    # Weighted portfolio APY
    if total_allocated > 0:
        portfolio_apy = sum(a["apy"] * a["amount_usd"] for a in allocations) / total_allocated
    else:
        portfolio_apy = 0.0

    return {
        "allocations": allocations,
        "expected_portfolio_apy": round(portfolio_apy, 2),
        "total_allocated_usd": round(total_allocated, 2),
    }
