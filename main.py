"""
Beautiful DeFi Advisor with Agent Intercommunication
Clean, formatted output with proper agent communication flow
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

# Import our existing logic
from agents.discovery_agent.discovery_logic import DiscoveryLogic
from agents.risk_agent.agent import RiskUAgent
from agents.decision_agent.decision_logic import DecisionAgent
# Intent extraction is handled by the existing logic


# Configure logging to be less verbose
logging.basicConfig(level=logging.WARNING)

def print_banner():
    """Print beautiful startup banner."""
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                    🤖 ROBOT DEFI ADVISOR v2.0 🤖                           ║")
    print("║                        Agent Intercommunication System                      ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("🚀 Starting Agent Intercommunication DeFi Advisor...")
    print("📡 Agents will communicate via direct function calls")
    print("🔄 Flow: Discovery → Risk → Decision")
    print()
    print("🤖 AGENT TEAM:")
    print("   • 🔍 Discovery Agent  → Finding DeFi pools")
    print("   • ⚠️  Risk Agent      → Analyzing pool risks") 
    print("   • 🎯 Decision Agent  → Selecting optimal pool")
    print("   • 🎮 Orchestrator    → Coordinating workflow")
    print()
    print("⏳ Initializing agents... Please wait for analysis...")
    print("━" * 80)

def print_agent_step(step_num: int, agent_name: str, action: str, result: str):
    """Print formatted agent step."""
    print(f"┌─ Step {step_num}: {agent_name}")
    print(f"├─ Action: {action}")
    print(f"└─ Result: {result}")
    print()

def format_apy(apy: float) -> str:
    """Format APY with proper units."""
    if apy < 1000:
        return f"{apy:,.2f}%"
    elif apy < 1000000:
        return f"{apy/1000:.1f}k%"
    else:
        return f"{apy/1000000:.1f}M%"

def format_tvl(tvl: float) -> str:
    """Format TVL with proper units."""
    if tvl < 1000000:
        return f"${tvl:,.0f}"
    else:
        return f"${tvl/1000000:.1f}M"

def get_risk_emoji(risk_level: str) -> str:
    """Get emoji for risk level."""
    risk_emojis = {
        'very_low': '🟢',
        'low': '🟡', 
        'medium': '🟠',
        'high': '🔴',
        'very_high': '🛑'
    }
    return risk_emojis.get(risk_level, '🟠')

def print_final_recommendation(optimal_pool: Dict[str, Any], total_pools: int):
    """Print beautiful final recommendation."""
    
    # Format values
    apy_formatted = format_apy(optimal_pool.get('apy', 0))
    tvl_formatted = format_tvl(optimal_pool.get('tvl', 0))
    risk_level = optimal_pool.get('riskData', {}).get('riskLevel', 'medium')
    risk_emoji = get_risk_emoji(risk_level)
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                           🎯 FINAL RECOMMENDATION                           ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    print("🏆 OPTIMAL POOL SELECTED:")
    print("   ┌─────────────────────────────────────────────────────────────────────────┐")
    print(f"   │ Pool ID: {optimal_pool.get('id', 'N/A')[:50]:<50} │")
    print(f"   │ Protocol: {optimal_pool.get('protocol', 'N/A'):<47} │")
    print(f"   │ Chain: {optimal_pool.get('chain', 'N/A'):<50} │")
    print(f"   │ Symbol: {optimal_pool.get('symbol', 'N/A'):<48} │")
    print("   └─────────────────────────────────────────────────────────────────────────┘")
    print()
    
    print("💰 FINANCIAL METRICS:")
    print(f"   • APY: {apy_formatted:<15} 🚀")
    print(f"   • TVL: {tvl_formatted:<15} 💎")
    print(f"   • Total Score: {optimal_pool.get('totalScore', 0):.2f}/100 ⭐")
    print()
    
    print("⚠️  RISK ASSESSMENT:")
    print(f"   • Risk Level: {risk_level.upper():<15} {risk_emoji}")
    print(f"   • Risk Score: {optimal_pool.get('riskData', {}).get('riskScore', 50):.1f}/100")
    print()
    
    print("📊 SCORING BREAKDOWN:")
    score_factors = optimal_pool.get('scoreFactors', {})
    print(f"   • APY Score: {score_factors.get('apyScore', 0):.1f}/40")
    print(f"   • Risk Score: {score_factors.get('riskScore', 0):.1f}/30")  
    print(f"   • Liquidity Score: {score_factors.get('liquidityScore', 0):.1f}/20")
    print(f"   • Protocol Bonus: {score_factors.get('protocolBonus', 0):.1f}/10")
    print()
    
    print("🤖 AGENT COMMUNICATION FLOW:")
    print("   ┌─────────────────────────────────────────────────────────────────────────┐")
    print(f"   │ 1️⃣  Discovery Agent → Found {total_pools} pools from DeFiLlama    │")
    print("   │ 2️⃣  Risk Agent → Analyzed pool risks and security factors              │")
    print("   │ 3️⃣  Decision Agent → Selected optimal pool using scoring algorithm     │")
    print("   └─────────────────────────────────────────────────────────────────────────┘")
    print()
    
    print("💡 RECOMMENDATION:")
    print(f"   This pool offers the best balance of yield ({apy_formatted}) and safety")
    print(f"   for your investment criteria. The {optimal_pool.get('protocol', 'N/A')} protocol")
    print(f"   on {optimal_pool.get('chain', 'N/A')} provides strong liquidity ({tvl_formatted})")
    print("   and competitive returns.")
    print()
    
    print("🎯 NEXT STEPS:")
    print(f"   • Research the {optimal_pool.get('symbol', 'N/A')} token pair")
    print("   • Verify the protocol's security audits")
    print("   • Consider your risk tolerance")
    print("   • Start with a small test investment")

def print_completion():
    """Print completion banner."""
    print()
    print("🎉" * 40)
    print("🎉" + " " * 38 + "🎉")
    print("🎉" + " " * 12 + "ANALYSIS COMPLETE!" + " " * 12 + "🎉")
    print("🎉" + " " * 38 + "🎉")
    print("🎉" * 40)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉" * 40)


# ASI Chat integration removed - using built-in intent extraction

# Intent extraction function removed - using built-in logic

async def run_defi_advisor():
    """Run the complete DeFi advisor workflow."""
    
    # Print startup banner
    print_banner()
    
    try:
        # Step 1: Discovery Agent
        print_agent_step(1, "🔍 Discovery Agent", "Finding DeFi pools", "Initializing...")
        
        
        discovery_logic = DiscoveryLogic()
        discovery_criteria = {
            "min_tvl": 100000,
            "min_apy": 0.05,
            "top_n": 5
        }
        
        pools = await discovery_logic.discover_pools_async(discovery_criteria)
        print_agent_step(1, "🔍 Discovery Agent", "Finding DeFi pools", f"Found {len(pools)} pools")
        
        # Step 2: Risk Agent
        print_agent_step(2, "⚠️  Risk Agent", "Analyzing pool risks", "Initializing...")
        
        risk_agent = RiskUAgent()
        risk_result = await risk_agent.act(pools)
        risk_analysis = risk_result.get("analysis", [])
        
        print_agent_step(2, "⚠️  Risk Agent", "Analyzing pool risks", f"Analyzed {len(risk_analysis)} pools")
        
        # Step 3: Decision Agent
        print_agent_step(3, "🎯 Decision Agent", "Selecting optimal pool", "Initializing...")
        
        decision_agent = DecisionAgent()
        decision_result = await decision_agent.select_optimal_pool(
            user_criteria={"preference": "safest"},
            pools=pools,
            risk_analysis=risk_analysis
        )
        
        optimal_pool = decision_result.get("optimalPool", {})
        print_agent_step(3, "🎯 Decision Agent", "Selecting optimal pool", f"Selected pool: {optimal_pool.get('id', 'N/A')[:20]}...")
        
        # Print final recommendation
        if optimal_pool:
            print_final_recommendation(optimal_pool, len(pools))
        else:
            print("❌ No suitable pool found matching your criteria.")
        
        # Print completion
        print_completion()
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        print_completion()

def main():
    """Main entry point."""
    asyncio.run(run_defi_advisor())

if __name__ == "__main__":
    main()
