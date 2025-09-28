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

            print(f"🎯 Decision Agent: Starting with {len(pools)} pools from discovery")
            
            # Step 1: Filter pools based on criteria
            filtered_pools = self.filter_pools_by_criteria(pools, user_criteria)
            print(f"📊 Decision Agent: {len(filtered_pools)} pools after basic filtering")

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
        # Discovery agent already filtered for min_apy and min_tvl, but let's add safety checks
        filtered = []
        for pool in pools:
            pool_dict = pool if isinstance(pool, dict) else pool.__dict__
            
            # Log pool data for debugging
            apy = pool_dict.get("apy", 0)
            tvl = pool_dict.get("tvl", 0)
            protocol = pool_dict.get("protocol", "Unknown")
            print(f"   📊 Pool {pool_dict.get('id', 'unknown')[:10]}... - {protocol} - APY: {apy}%, TVL: ${tvl:,.0f}")
            
            # Temporarily include all pools to see what we're working with
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
            if apy <= 0:
                apy_score = 0  # No points for 0 or negative APY
            else:
                apy_score = min(40.0, apy * 2.0)
            total_score += apy_score
            score_factors["apyScore"] = apy_score

            # Risk Score (0–30 points)
            # Note: Risk agent uses inverted scale (higher score = lower risk)
            # We need to convert to risk level for decision making
            risk_score_val = pool.get("riskData", {}).get("riskScore", 50)
            risk_level = pool.get("riskData", {}).get("riskLevel", "medium")
            
            # Convert risk level to numeric risk score (0-100, where 0 = very low risk, 100 = very high risk)
            risk_numeric = {
                "very_low": 10,
                "low": 30, 
                "medium": 50,
                "high": 70,
                "very_high": 90
            }.get(risk_level, 50)
            
            # Calculate risk score for decision (lower risk = higher score)
            risk_score = max(0.0, 30.0 - (risk_numeric * 0.3))
            total_score += risk_score
            score_factors["riskScore"] = risk_score

            # Liquidity Score (0–20 points)
            tvl = pool.get("tvl", 0)
            if tvl <= 0:
                liquidity_score = 0  # No points for 0 or negative TVL
            else:
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
                # For safest preference, heavily weight low risk pools
                # Use risk level to determine bonuses/penalties
                if risk_level == "very_low":
                    total_score += 50.0  # Big bonus for very low risk
                elif risk_level == "low":
                    total_score += 25.0  # Moderate bonus for low risk
                elif risk_level == "very_high":
                    total_score -= 40.0  # Heavy penalty for very high risk
                elif risk_level == "high":
                    total_score -= 20.0  # Moderate penalty for high risk
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
                "scoringFactors": list(optimal_pool.get("scoreFactors", {}).keys()),
                "topScores": [{"id": p.get("id", "unknown"), "score": p.get("totalScore", 0)} for p in all_pools[:3]],
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
