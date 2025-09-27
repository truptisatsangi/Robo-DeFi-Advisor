import asyncio
from agents.discovery_agent.agent import DiscoveryUAgent
from agents.risk_agent.agent import RiskUAgent
from agents.decision_agent.agent import DecisionUAgent


async def main():
    # Step 0: Initialize agents
    discovery_agent = DiscoveryUAgent()
    risk_agent = RiskUAgent()
    decision_agent = DecisionUAgent()

    # Step 1: User input
    user_input = "I want to invest $100 in the safest pool"

    print(f"User Input: {user_input}\n")

    # Step 2: Intent extraction (for demo, we mock it)
    context = {
        "user_intent": {
            "action": "invest",
            "amount": 100,
            "preference": "safest"
        }
    }

    # Step 3: Discover pools
    discovery_criteria = {
        "min_tvl": 100000,  # Minimum TVL of $100k
        "min_apy": 0.05,    # Minimum 5% APY
        "top_n": 5          # Get top 5 pools
    }
    discovery_result = await discovery_agent.act(discovery_criteria)
    discovered_pools = discovery_result.get("pools", [])

    print(f"Discovered Pools: {len(discovered_pools)} pools found\n")

    # Step 4: Risk analysis
    risk_result = await risk_agent.act(discovered_pools)
    risk_analyses = risk_result.get("analysis", [])

    print(f"Risk Analysis Completed for {len(risk_analyses)} pools\n")

    # Step 5: Decision agent
    decision_result = await decision_agent.act(
        criteria=context["user_intent"],
        pools=discovered_pools,
        risk_analysis=risk_analyses
    )
    # Extract recommendation from decision result
    if decision_result.get("status") == "success":
        decision_data = decision_result.get("data", {})
        optimal_pool = decision_data.get("optimalPool", {})
        if optimal_pool:
            recommendation = f"""
RECOMMENDED POOL:
   • ID: {optimal_pool.get('id', 'N/A')}
   • Protocol: {optimal_pool.get('protocol', 'N/A')}
   • APY: {optimal_pool.get('apy', 0):.2f}%
   • TVL: ${optimal_pool.get('tvl', 0):,.0f}
   • Risk Score: {optimal_pool.get('riskData', {}).get('riskScore', 50):.1f}
   • Risk Level: {optimal_pool.get('riskData', {}).get('riskLevel', 'medium')}
   
REASONING:
   • Total Score: {optimal_pool.get('totalScore', 0):.2f}/100
   • This pool offers the best balance of yield and safety for your investment criteria.
   • Consider this pool for your $100 investment.
"""
        else:
            recommendation = "No suitable pool found matching your criteria."
    else:
        recommendation = f"Error in decision making: {decision_result.get('error', 'Unknown error')}"

    # Step 6: Print final recommendation in English
    print("✅ Final Recommendation:")
    print(recommendation)

if __name__ == "__main__":
    asyncio.run(main())
