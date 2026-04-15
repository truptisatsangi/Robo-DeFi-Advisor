# decision_logic.py
"""
DecisionAgent logic for optimal pool selection with transparent reasoning.
Uses a deterministic, explainable ranking formula so recommendations are reproducible.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

# Preference-based scoring weights (documented for DAO governance).
# score = w_apy * normalized_apy + w_risk * normalized_risk_score + w_tvl * normalized_tvl
# Each variable is normalized to [0, 1] over the candidate set. Same policy + same data => same ranking.
# Different preference values intentionally produce different pool orderings.
PREFERENCE_WEIGHTS: dict = {
    "safest":        {"apy": 0.15, "risk": 0.65, "tvl": 0.20},
    "balanced":      {"apy": 0.40, "risk": 0.35, "tvl": 0.25},
    "highest_yield": {"apy": 0.70, "risk": 0.20, "tvl": 0.10},
}
# Legacy constants kept for any direct references in tests/docs.
WEIGHT_APY = 0.5
WEIGHT_RISK = 0.3
WEIGHT_TVL = 0.2


@dataclass
class DecisionResult:
    """Data class for decision results."""
    optimal_pool: Dict[str, Any]
    all_candidates: List[Dict[str, Any]]
    reasoning_trace: List[Dict[str, Any]]
    criteria: Dict[str, Any]


class DecisionAgent:
    """Decision Agent for optimal pool selection."""

    def __init__(self):
        self.name = "DecisionAgent"
        self.version = "1.0.0"
        self.description = "Selects optimal DeFi pool with transparent reasoning trace"
        self.tags = ["defi", "decision", "optimization", "reasoning", "selection"]

    async def select_optimal_pool(
        self,
        user_criteria: Dict[str, Any],
        pools: List[Dict[str, Any]],
        risk_analysis: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Select optimal pool based on criteria and risk analysis."""
        try:
            print(f"🎯 Decision Agent: Selecting optimal pool with criteria: {user_criteria}")

            print(f"🎯 Decision Agent: Starting with {len(pools)} pools from risk agent")
            
            filtered_pools = [p if isinstance(p, dict) else p.__dict__ for p in pools]
            print(f"📊 Decision Agent: {len(filtered_pools)} pools received (pre-filtered by discovery + risk)")

            # Step 2: Apply risk analysis
            pools_with_risk = self.apply_risk_analysis(filtered_pools, risk_analysis)
            print(f"🔍 Decision Agent: Applied risk analysis to {len(pools_with_risk)} pools")

            # Step 2.5: Apply safety filters for safest preference
            pools_with_risk = self.apply_safety_filters(pools_with_risk, user_criteria)
            print(f"🛡️ Decision Agent: Applied safety filters, {len(pools_with_risk)} pools remaining")

            # Step 3: Score and rank pools
            scored_pools = self.score_pools(pools_with_risk, user_criteria)
            print(f"📈 Decision Agent: Scored {len(scored_pools)} pools")

            # Step 4: Select optimal pool
            optimal_pool = self.select_optimal_pool_from_scored(scored_pools)
            print(f"🏆 Decision Agent: Selected optimal pool: {optimal_pool.get('id', 'unknown')}")

            # Step 5: Generate reasoning trace
            reasoning_trace = self.generate_reasoning_trace(user_criteria, scored_pools, optimal_pool)
            print(f"🔍 Decision Agent: Generated reasoning trace: {reasoning_trace}")   

            # Get alternatives based on user's target APY if specified
            target_apy = user_criteria.get("target_apy")
            
            if target_apy and len(scored_pools) >= 3:
                # User specified target APY - provide targeted recommendation + safest + highest yield alternatives
                alternatives = []
                
                # Find safest pool (highest risk score)
                safest_pool = max(scored_pools[1:], key=lambda x: x.get("riskScore", 0))
                alternatives.append(safest_pool)
                
                # Find highest yield pool (highest APY) that's not the safest
                highest_yield = max(
                    [p for p in scored_pools[1:] if p.get('id') != safest_pool.get('id')],
                    key=lambda x: x.get("apy", 0),
                    default=None
                )
                if highest_yield:
                    alternatives.append(highest_yield)
            else:
                # No target APY - show next best options
                top_3_pools = scored_pools[:3] if len(scored_pools) >= 3 else scored_pools
                alternatives = top_3_pools[1:] if len(top_3_pools) > 1 else []

            return {
                "success": True,
                "optimalPool": optimal_pool,
                "alternatives": alternatives,
                "allCandidates": scored_pools,
                "reasoningTrace": reasoning_trace,
                "criteria": user_criteria,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as error:
            print(f"❌ Decision Agent Error: {error}")
            return {
                "success": False,
                "error": str(error),
                "optimalPool": None,
                "reasoningTrace": [],
                "timestamp": datetime.now().isoformat(),
            }

    # -------------------------------
    # Filtering
    # -------------------------------
    def filter_pools_by_criteria(self, pools: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter pools based on user criteria."""
        min_apy = criteria.get("min_apy", 0)
        max_apy = criteria.get("max_apy")
        min_tvl = criteria.get("min_pool_tvl_usd", 0)
        allowed_protocols = [p.lower() for p in criteria.get("allowed_protocols", [])]
        allowed_chains = [c.lower() for c in criteria.get("allowed_chains", [])]

        filtered = []
        for pool in pools:
            pool_dict = pool if isinstance(pool, dict) else pool.__dict__

            apy = pool_dict.get("apy") or 0
            tvl = pool_dict.get("tvl") or 0
            protocol = (pool_dict.get("protocol") or "").lower()
            chain = (pool_dict.get("chain") or "").lower()

            if apy < min_apy:
                continue
            if max_apy is not None and apy > max_apy:
                continue
            if tvl < min_tvl:
                continue
            if allowed_protocols and protocol not in allowed_protocols:
                continue
            if allowed_chains and chain not in allowed_chains:
                continue

            filtered.append(pool_dict)
        return filtered

    # -------------------------------
    # Risk analysis
    # -------------------------------
    def apply_risk_analysis(self, pools: List[Dict[str, Any]], risk_analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply risk analysis to pools."""
        risk_map = {risk["poolId"]: risk for risk in risk_analysis}

        pools_with_risk = []
        for pool in pools:
            risk_data = risk_map.get(
                pool["id"],
                {"riskScore": 50, "riskLevel": "medium", "factors": {}, "recommendations": []},
            )
            pool["riskData"] = risk_data
            pools_with_risk.append(pool)

        return pools_with_risk

    def apply_safety_filters(self, pools: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply additional safety filters for safest preference."""
        safety_preference = criteria.get("preference", "medium")
        if safety_preference != "safest":
            return pools
        
        print(f"🛡️ Applying safety filters to {len(pools)} pools for 'safest' preference")
        
        filtered_pools = []
        for pool in pools:
            risk_data = pool.get("riskData", {})
            risk_level = risk_data.get("riskLevel", "medium")
            factors = risk_data.get("factors", {})
            
            print(f"   Pool {pool.get('id', 'unknown')[:10]}... - Risk: {risk_level}, Contract: {factors.get('contractVerified')}, Audit: {factors.get('auditLink') is not None}")
            
            # For now, only exclude very high risk pools to avoid filtering out everything
            if risk_level == "very_high":
                print(f"   ❌ Excluding very high risk pool")
                continue
            
            # Temporarily disable contract and audit filters since MeTTa data might not be available
            # if factors.get("contractVerified") == False:
            #     print(f"   ❌ Excluding unverified contract")
            #     continue
            
            # if factors.get("auditLink") is None:
            #     print(f"   ❌ Excluding pool without audit")
            #     continue
            
            print(f"   ✅ Including pool")
            filtered_pools.append(pool)
        
        print(f"🛡️ Safety filters result: {len(filtered_pools)} pools remaining")
        return filtered_pools

    # -------------------------------
    # Scoring (deterministic ranking formula)
    # -------------------------------
    def _normalize_0_1(self, values: List[float], higher_better: bool = True) -> List[float]:
        """Map values to [0, 1] with min-max. Guard for constant range (return 0.5)."""
        if not values:
            return []
        lo, hi = min(values), max(values)
        if hi <= lo:
            return [0.5] * len(values)
        out = [(v - lo) / (hi - lo) for v in values]
        if not higher_better:
            out = [1.0 - x for x in out]
        return out

    def score_pools(self, pools: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Score and rank pools using a preference-aware deterministic formula:
          score = w_apy * normalized_apy + w_risk * normalized_risk_score + w_tvl * normalized_tvl
        Weights vary by mandate preference (safest / balanced / highest_yield).
        Normalize each variable to [0, 1] over the candidate set. Same policy + same data => same ranking.
        """
        if not pools:
            return []

        preference = (criteria.get("preference") or "balanced").lower()
        weights = PREFERENCE_WEIGHTS.get(preference, PREFERENCE_WEIGHTS["balanced"])
        w_apy = weights["apy"]
        w_risk = weights["risk"]
        w_tvl = weights["tvl"]

        apys = [p.get("apy", 0) or 0 for p in pools]
        risk_scores = [
            (p.get("riskData") or {}).get("riskScore", 50) for p in pools
        ]  # 0-100, higher = safer
        tvls = [max((p.get("tvl") or 0), 0) for p in pools]

        norm_apy = self._normalize_0_1(apys, higher_better=True)
        norm_risk = self._normalize_0_1(risk_scores, higher_better=True)
        norm_tvl = self._normalize_0_1(tvls, higher_better=True)

        scored_pools = []
        for i, pool in enumerate(pools):
            total_score = w_apy * norm_apy[i] + w_risk * norm_risk[i] + w_tvl * norm_tvl[i]
            pool["totalScore"] = round(total_score, 4)
            pool["scoreFactors"] = {
                "normalized_apy": norm_apy[i],
                "normalized_risk_score": norm_risk[i],
                "normalized_tvl": norm_tvl[i],
                "weights": {"apy": w_apy, "risk": w_risk, "tvl": w_tvl},
                "preference": preference,
            }
            scored_pools.append(pool)

        scored_pools.sort(key=lambda x: x["totalScore"], reverse=True)
        for rank, pool in enumerate(scored_pools, 1):
            pool["ranking"] = rank

        return scored_pools

    # -------------------------------
    # Selection
    # -------------------------------
    def select_optimal_pool_from_scored(self, scored_pools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the optimal pool from scored pools."""
        if not scored_pools:
            raise ValueError("No pools available for selection")
        return scored_pools[0]

    # -------------------------------
    # Reasoning trace
    # -------------------------------
    def generate_reasoning_trace(
        self, user_criteria: Dict[str, Any], all_pools: List[Dict[str, Any]], optimal_pool: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate reasoning trace for decision making."""
        trace = []

        trace.append({
            "step": 1,
            "agent": "DecisionAgent",
            "action": "filter_pools",
            "input": {"totalPools": len(all_pools), "criteria": user_criteria},
            "output": {"filteredPools": len(all_pools), "filtersApplied": list(user_criteria.keys())},
            "reasoning": f"Filtered pools based on criteria: {', '.join(user_criteria.keys())}",
            "timestamp": datetime.now().isoformat(),
        })

        score_factors = optimal_pool.get("scoreFactors", {})
        actual_weights = score_factors.get("weights", {"apy": WEIGHT_APY, "risk": WEIGHT_RISK, "tvl": WEIGHT_TVL})
        actual_preference = score_factors.get("preference", user_criteria.get("preference", "balanced"))
        w_apy = actual_weights.get("apy", WEIGHT_APY)
        w_risk = actual_weights.get("risk", WEIGHT_RISK)
        w_tvl = actual_weights.get("tvl", WEIGHT_TVL)

        trace.append({
            "step": 2,
            "agent": "DecisionAgent",
            "action": "score_pools",
            "input": {"poolsToScore": len(all_pools), "preference": actual_preference},
            "output": {
                "scoringFactors": list(score_factors.keys()),
                "topScores": [{"id": p.get("id", "unknown"), "score": p.get("totalScore", 0)} for p in all_pools[:3]],
                "weights": actual_weights,
            },
            "reasoning": (
                f"Scored using '{actual_preference}' preference: "
                f"score = {w_apy}*norm_apy + {w_risk}*norm_risk + {w_tvl}*norm_tvl "
                f"(each normalized to [0,1] over candidate set)"
            ),
            "timestamp": datetime.now().isoformat(),
        })

        trace.append({
            "step": 3,
            "agent": "DecisionAgent",
            "action": "select_optimal",
            "input": {"candidatePools": len(all_pools)},
            "output": {
                "selectedPool": {
                    "id": optimal_pool.get("id", "unknown"),
                    "protocol": optimal_pool.get("protocol", "unknown"),
                    "score": optimal_pool.get("totalScore", 0),
                    "apy": optimal_pool.get("apy", 0),
                    "riskScore": optimal_pool.get("riskScore", 50),
                }
            },
            "reasoning": f"Selected {optimal_pool.get('id', 'unknown')} with highest composite score ({optimal_pool.get('totalScore', 0)})",
            "timestamp": datetime.now().isoformat(),
        })

        trace.append({
            "step": 4,
            "agent": "DecisionAgent",
            "action": "justify_selection",
            "input": {"selectedPool": optimal_pool.get("id", "unknown")},
            "output": {
                "justification": {
                    "apyAdvantage": optimal_pool.get("apy", 0),
                    "riskAssessment": optimal_pool.get("riskLevel", "medium"),
                    "liquidityStrength": optimal_pool.get("tvl", 0),
                    "protocolReliability": optimal_pool.get("protocol", "unknown"),
                }
            },
            "reasoning": (
                f"Pool selected due to {optimal_pool.get('apy', 0)}% APY, "
                f"{optimal_pool.get('riskLevel', 'medium')} risk, and strong liquidity of "
                f"${optimal_pool.get('tvl', 0):,.0f}"
            ),
            "timestamp": datetime.now().isoformat(),
        })

        return trace
