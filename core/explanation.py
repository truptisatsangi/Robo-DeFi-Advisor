"""
Recommendation explanation layer — produces a short "why this pool was selected" for each recommended pool.
Rule-based (no LLM). Attach to each pool in the final output for governance transparency.
"""

from typing import Any, Dict, List, Union


def explain_pool_selection(pool: Dict[str, Any], policy: Dict[str, Any]) -> List[str]:
    """
    Given one pool and the TreasuryPolicy (or criteria dict), return a list of reasons
    why this pool was selected. Used to attach as explanation/selection_reason on each recommended pool.
    """
    reasons: List[str] = []

    min_apy = (policy.get("min_apy") or 0)
    apy = pool.get("apy") or 0
    if min_apy and apy >= min_apy:
        reasons.append("APY above policy threshold")

    risk_cfg = policy.get("risk") or {}
    if isinstance(risk_cfg, str):
        risk_cfg = {"max_level": risk_cfg, "min_score": None}
    min_score = risk_cfg.get("min_score")
    max_level = risk_cfg.get("max_level")
    risk_data = pool.get("riskData") or {}
    risk_score = risk_data.get("riskScore", 0)
    risk_level = (risk_data.get("riskLevel") or "medium").lower().replace(" ", "_")
    level_ok = True
    if max_level:
        order = ["very_low", "low", "medium", "high", "very_high"]
        try:
            pool_rank = order.index(risk_level)
            max_rank = order.index(str(max_level).lower().replace(" ", "_"))
            level_ok = pool_rank <= max_rank
        except ValueError:
            pass
    score_ok = min_score is None or (risk_score >= min_score)
    if level_ok and score_ok and (min_score is not None or max_level is not None):
        reasons.append("Risk score within mandate limits")

    allowed = policy.get("allowed_protocols") or []
    protocol = (pool.get("protocol") or "").lower()
    if not allowed or any(p in protocol for p in [a.lower() for a in allowed]):
        reasons.append("Protocol whitelisted in policy")

    min_tvl = policy.get("min_pool_tvl_usd") or policy.get("min_tvl") or 0
    tvl = pool.get("tvl") or 0
    if min_tvl and tvl >= min_tvl:
        reasons.append("Pool TVL above minimum threshold")

    if not reasons:
        reasons.append("Pool met all policy filters and ranking criteria")

    return reasons


def explain_pool_selection_str(pool: Dict[str, Any], policy: Dict[str, Any]) -> str:
    """Single string summary: 'Why this pool was selected: ...'"""
    reasons = explain_pool_selection(pool, policy)
    return "Why this pool was selected: " + ". ".join(reasons)
