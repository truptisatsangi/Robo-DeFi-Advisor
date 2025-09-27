# decision_logic.py
"""
DecisionAgent logic for optimal pool selection with transparent reasoning.
This module contains the full decision-making class used by uAgents wrapper.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


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

            # Step 1: Filter pools based on criteria
            filtered_pools = self.filter_pools_by_criteria(pools, user_criteria)
            print(f"📊 Decision Agent: {len(filtered_pools)} pools after filtering")

            # Step 2: Apply risk analysis
            pools_with_risk = self.apply_risk_analysis(filtered_pools, risk_analysis)
            print(f"🔍 Decision Agent: Applied risk analysis to {len(pools_with_risk)} pools")

            # Step 3: Score and rank pools
            scored_pools = self.score_pools(pools_with_risk, user_criteria)
            print(f"📈 Decision Agent: Scored {len(scored_pools)} pools")

            # Step 4: Select optimal pool
            optimal_pool = self.select_optimal_pool_from_scored(scored_pools)
            print(f"🏆 Decision Agent: Selected optimal pool: {optimal_pool['id']}")

            # Step 5: Generate reasoning trace
            reasoning_trace = self.generate_reasoning_trace(user_criteria, scored_pools, optimal_pool)
            print(f"🔍 Decision Agent: Generated reasoning trace: {reasoning_trace}")   
            print({
                "success": True,
                "optimalPool": optimal_pool,
                "allCandidates": scored_pools,
                "reasoningTrace": reasoning_trace,
                "criteria": user_criteria,
                "timestamp": datetime.now().isoformat(),
            })

            return {
                "success": True,
                "optimalPool": optimal_pool,
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
        filtered = []

        for pool in pools:
            pool_dict = pool if isinstance(pool, dict) else pool.__dict__

            # Check TVL if specified
            if criteria.get("min_tvl") and pool_dict.get("tvl", 0) < criteria["min_tvl"]:
                continue
            # Check APY if specified  
            if criteria.get("min_apy") and pool_dict.get("apy", 0) < criteria["min_apy"]:
                continue
            # Check protocol if specified
            if criteria.get("protocol") and pool_dict.get("protocol") != criteria["protocol"]:
                continue
            # Check symbol if specified
            if criteria.get("symbol") and criteria["symbol"] not in pool_dict.get("symbol", ""):
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

    # -------------------------------
    # Scoring
    # -------------------------------
    def score_pools(self, pools: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Score and rank pools based on criteria."""
        scored_pools = []

        for pool in pools:
            score_factors = {}
            total_score = 0.0

            # APY Score (0–40 points)
            apy = pool.get("apy", 0)
            apy_score = min(40.0, apy * 2.0)
            total_score += apy_score
            score_factors["apyScore"] = apy_score

            # Risk Score (0–30 points)
            risk_score_val = pool.get("riskData", {}).get("riskScore", 50)
            risk_score = max(0.0, 30.0 - (risk_score_val * 0.3))
            total_score += risk_score
            score_factors["riskScore"] = risk_score

            # Liquidity Score (0–20 points)
            tvl = pool.get("tvl", 0)
            liquidity_score = min(20.0, (tvl ** 0.1) / 2.0)
            total_score += liquidity_score
            score_factors["liquidityScore"] = liquidity_score

            # Protocol Bonus (0–10 points)
            protocol = pool.get("protocol", "")
            protocol_bonus = 10.0 if protocol == "Uniswap V3" else 5.0
            total_score += protocol_bonus
            score_factors["protocolBonus"] = protocol_bonus

            # Safety Preference Adjustment
            safety_preference = criteria.get("preference", "medium")
            if safety_preference == "safest":
                total_score = total_score * 0.7 + (30.0 if risk_score_val > 70 else 0.0)
            elif safety_preference == "highest_yield":
                total_score = total_score * 1.2 + (20.0 if apy > 15 else 0.0)

            pool["totalScore"] = round(total_score, 2)
            pool["scoreFactors"] = score_factors
            scored_pools.append(pool)

        scored_pools.sort(key=lambda x: x["totalScore"], reverse=True)
        for i, pool in enumerate(scored_pools):
            pool["ranking"] = i + 1

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

        trace.append({
            "step": 2,
            "agent": "DecisionAgent",
            "action": "score_pools",
            "input": {"poolsToScore": len(all_pools)},
            "output": {
                "scoringFactors": list(optimal_pool["scoreFactors"].keys()),
                "topScores": [{"id": p["id"], "score": p["totalScore"]} for p in all_pools[:3]],
            },
            "reasoning": "Scored pools using APY (40%), Risk (30%), Liquidity (20%), and Protocol (10%) weights",
            "timestamp": datetime.now().isoformat(),
        })

        trace.append({
            "step": 3,
            "agent": "DecisionAgent",
            "action": "select_optimal",
            "input": {"candidatePools": len(all_pools)},
            "output": {
                "selectedPool": {
                    "id": optimal_pool["id"],
                    "protocol": optimal_pool["protocol"],
                    "score": optimal_pool["totalScore"],
                    "apy": optimal_pool["apy"],
                    "riskScore": optimal_pool.get("riskData", {}).get("riskScore", 50),
                }
            },
            "reasoning": f"Selected {optimal_pool['id']} with highest composite score ({optimal_pool['totalScore']})",
            "timestamp": datetime.now().isoformat(),
        })

        trace.append({
            "step": 4,
            "agent": "DecisionAgent",
            "action": "justify_selection",
            "input": {"selectedPool": optimal_pool["id"]},
            "output": {
                "justification": {
                    "apyAdvantage": optimal_pool["apy"],
                    "riskAssessment": optimal_pool.get("riskData", {}).get("riskLevel", "medium"),
                    "liquidityStrength": optimal_pool["tvl"],
                    "protocolReliability": optimal_pool["protocol"],
                }
            },
            "reasoning": (
                f"Pool selected due to {optimal_pool['apy']}% APY, "
                f"{optimal_pool.get('riskData', {}).get('riskLevel', 'medium')} risk, and strong liquidity of "
                f"${optimal_pool['tvl']:,.0f}"
            ),
            "timestamp": datetime.now().isoformat(),
        })

        return trace
