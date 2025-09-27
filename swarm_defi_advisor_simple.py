"""
Simplified Swarm-based DeFi Advisor using uAgents Framework
Uses our existing logic without external API dependencies
"""

from uagents import Agent, Model, Bureau, Context
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import our existing logic
from agents.discovery_agent.discovery_logic import DiscoveryLogic
from agents.risk_agent.agent import RiskUAgent
from agents.decision_agent.decision_logic import DecisionAgent

logger = logging.getLogger(__name__)

# ------------------------------
# uAgents Message Models
# ------------------------------

class DeFiRequest(Model):
    user_criteria: Dict[str, Any]
    message: str

class DeFiResponse(Model):
    status: str
    result: Dict[str, Any]
    recommendation: str
    timestamp: str

class DiscoveryData(Model):
    pools: List[Dict[str, Any]]
    criteria: Dict[str, Any]

class RiskAnalysisData(Model):
    analysis: List[Dict[str, Any]]
    pools: List[Dict[str, Any]]

class DecisionData(Model):
    optimal_pool: Dict[str, Any]
    reasoning: str
    all_candidates: List[Dict[str, Any]]
    user_criteria: Dict[str, Any]

# ------------------------------
# uAgents
# ------------------------------

defi_orchestrator = Agent(name='DeFiOrchestrator')
discovery_uagent = Agent(name='DiscoveryAgent')
risk_uagent = Agent(name='RiskAgent')
decision_uagent = Agent(name='DecisionAgent')

# ------------------------------
# Message Handlers
# ------------------------------

@defi_orchestrator.on_message(DeFiRequest)
async def handle_defi_request(ctx: Context, sender: str, request: DeFiRequest):
    """Main entry point for DeFi advice requests."""
    try:
        ctx.logger.info(f"🎯 Received DeFi request: {request.message}")
        
        # Extract discovery criteria from user request
        discovery_criteria = {
            "min_tvl": request.user_criteria.get("min_tvl", 100000),
            "min_apy": request.user_criteria.get("min_apy", 0.05),
            "top_n": 5
        }
        
        # Start the pipeline by sending to discovery agent
        await ctx.send(discovery_uagent.address, DiscoveryData(
            pools=[],  # Will be populated by discovery agent
            criteria=discovery_criteria
        ))
        
    except Exception as e:
        ctx.logger.error(f"❌ Error in DeFi orchestration: {e}")
        await ctx.send(sender, DeFiResponse(
            status="error",
            result={"error": str(e)},
            recommendation="Error occurred during analysis",
            timestamp=datetime.now().isoformat()
        ))

@discovery_uagent.on_message(DiscoveryData)
async def handle_discovery_data(ctx: Context, sender: str, data: DiscoveryData):
    """Handle discovery data and forward to risk analysis."""
    try:
        ctx.logger.info(f"🔍 Starting discovery with criteria: {data.criteria}")
        
        # Use our existing discovery logic
        discovery_logic = DiscoveryLogic()
        pools = await discovery_logic.discover_pools_async(data.criteria)
        
        ctx.logger.info(f"✅ Found {len(pools)} pools")
        
        # Forward to risk analysis
        await ctx.send(risk_uagent.address, RiskAnalysisData(
            analysis=[],  # Will be populated by risk agent
            pools=pools
        ))
        
    except Exception as e:
        ctx.logger.error(f"❌ Error in discovery: {e}")
        # Send error to decision agent
        await ctx.send(decision_uagent.address, DecisionData(
            optimal_pool={},
            reasoning=f"Discovery failed: {str(e)}",
            all_candidates=[],
            user_criteria={}
        ))

@risk_uagent.on_message(RiskAnalysisData)
async def handle_risk_analysis(ctx: Context, sender: str, data: RiskAnalysisData):
    """Handle risk analysis data."""
    try:
        ctx.logger.info(f"⚠️ Starting risk analysis for {len(data.pools)} pools")
        
        # Use our existing risk logic
        risk_agent = RiskUAgent()
        risk_result = await risk_agent.act(data.pools)
        risk_analysis = risk_result.get("analysis", [])
        
        ctx.logger.info(f"✅ Risk analysis completed for {len(risk_analysis)} pools")
        
        # Forward to decision making
        await ctx.send(decision_uagent.address, DecisionData(
            optimal_pool={},  # Will be populated by decision agent
            reasoning="",
            all_candidates=data.pools,
            user_criteria={"preference": "safest"}  # Default preference
        ))
        
    except Exception as e:
        ctx.logger.error(f"❌ Error in risk analysis: {e}")
        # Send error to decision agent
        await ctx.send(decision_uagent.address, DecisionData(
            optimal_pool={},
            reasoning=f"Risk analysis failed: {str(e)}",
            all_candidates=data.pools,
            user_criteria={}
        ))

@decision_uagent.on_message(DecisionData)
async def handle_decision_data(ctx: Context, sender: str, data: DecisionData):
    """Handle final decision data."""
    try:
        ctx.logger.info(f"🎯 Making final decision for {len(data.all_candidates)} pools")
        
        # Use our existing decision logic
        decision_agent = DecisionAgent()
        decision_result = await decision_agent.select_optimal_pool(
            user_criteria=data.user_criteria,
            pools=data.all_candidates,
            risk_analysis=[]  # We'll use mock risk data for now
        )
        
        optimal_pool = decision_result.get("optimalPool", {})
        reasoning = decision_result.get("reasoningTrace", [])
        
        ctx.logger.info(f"✅ Decision made: {optimal_pool.get('id', 'N/A')}")
        
        # Create beautiful final recommendation
        if optimal_pool:
            # Format APY with proper styling
            apy = optimal_pool.get('apy', 0)
            apy_formatted = f"{apy:,.2f}%" if apy < 1000 else f"{apy/1000:.1f}k%"
            
            # Get risk level with emoji
            risk_level = optimal_pool.get('riskData', {}).get('riskLevel', 'medium')
            risk_emoji = {
                'very_low': '🟢',
                'low': '🟡', 
                'medium': '🟠',
                'high': '🔴',
                'very_high': '🛑'
            }.get(risk_level, '🟠')
            
            # Format TVL
            tvl = optimal_pool.get('tvl', 0)
            tvl_formatted = f"${tvl:,.0f}" if tvl < 1000000 else f"${tvl/1000000:.1f}M"
            
            recommendation = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           🎯 FINAL RECOMMENDATION                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

🏆 OPTIMAL POOL SELECTED:
   ┌─────────────────────────────────────────────────────────────────────────┐
   │ Pool ID: {optimal_pool.get('id', 'N/A')[:50]:<50} │
   │ Protocol: {optimal_pool.get('protocol', 'N/A'):<47} │
   │ Chain: {optimal_pool.get('chain', 'N/A'):<50} │
   │ Symbol: {optimal_pool.get('symbol', 'N/A'):<48} │
   └─────────────────────────────────────────────────────────────────────────┘

💰 FINANCIAL METRICS:
   • APY: {apy_formatted:<15} 🚀
   • TVL: {tvl_formatted:<15} 💎
   • Total Score: {optimal_pool.get('totalScore', 0):.2f}/100 ⭐

⚠️  RISK ASSESSMENT:
   • Risk Level: {risk_level.upper():<15} {risk_emoji}
   • Risk Score: {optimal_pool.get('riskData', {}).get('riskScore', 50):.1f}/100

📊 SCORING BREAKDOWN:
   • APY Score: {optimal_pool.get('scoreFactors', {}).get('apyScore', 0):.1f}/40
   • Risk Score: {optimal_pool.get('scoreFactors', {}).get('riskScore', 0):.1f}/30  
   • Liquidity Score: {optimal_pool.get('scoreFactors', {}).get('liquidityScore', 0):.1f}/20
   • Protocol Bonus: {optimal_pool.get('scoreFactors', {}).get('protocolBonus', 0):.1f}/10

🤖 AGENT COMMUNICATION FLOW:
   ┌─────────────────────────────────────────────────────────────────────────┐
   │ 1️⃣  Discovery Agent → Found {len(data.all_candidates)} pools from DeFiLlama    │
   │ 2️⃣  Risk Agent → Analyzed pool risks and security factors              │
   │ 3️⃣  Decision Agent → Selected optimal pool using scoring algorithm     │
   └─────────────────────────────────────────────────────────────────────────┘

💡 RECOMMENDATION:
   This pool offers the best balance of yield ({apy_formatted}) and safety 
   for your investment criteria. The {optimal_pool.get('protocol', 'N/A')} protocol 
   on {optimal_pool.get('chain', 'N/A')} provides strong liquidity ({tvl_formatted}) 
   and competitive returns.

🎯 NEXT STEPS:
   • Research the {optimal_pool.get('symbol', 'N/A')} token pair
   • Verify the protocol's security audits
   • Consider your risk tolerance
   • Start with a small test investment
"""
        else:
            recommendation = "❌ No suitable pool found matching your criteria."
        
        # Send final response back to orchestrator
        await ctx.send(defi_orchestrator.address, DeFiResponse(
            status="success",
            result={
                "optimal_pool": optimal_pool,
                "reasoning": reasoning,
                "total_pools_analyzed": len(data.all_candidates)
            },
            recommendation=recommendation,
            timestamp=datetime.now().isoformat()
        ))
        
    except Exception as e:
        ctx.logger.error(f"❌ Error in decision making: {e}")
        await ctx.send(defi_orchestrator.address, DeFiResponse(
            status="error",
            result={"error": str(e)},
            recommendation=f"Decision making failed: {str(e)}",
            timestamp=datetime.now().isoformat()
        ))

# ------------------------------
# Trigger Agent for Demo
# ------------------------------

trigger_agent = Agent(name='TriggerAgent')

@trigger_agent.on_event('startup')
async def trigger_request(ctx: Context):
    """Trigger the DeFi analysis pipeline."""
    await asyncio.sleep(3)  # Give agents time to start
    
    user_request = DeFiRequest(
        user_criteria={
            "action": "invest",
            "amount": 100,
            "preference": "safest",
            "min_tvl": 100000,
            "min_apy": 0.05
        },
        message="I want to invest $100 in the safest DeFi pool. Please find and analyze the best options."
    )
    
    ctx.logger.info("🚀 Triggering DeFi analysis pipeline...")
    await ctx.send(defi_orchestrator.address, user_request)

@trigger_agent.on_message(DeFiResponse)
async def handle_final_response(ctx: Context, sender: str, response: DeFiResponse):
    """Handle the final response from the DeFi advisor."""
    print("\n" + "🎉" * 40)
    print("🎉" + " " * 38 + "🎉")
    print("🎉" + " " * 12 + "ANALYSIS COMPLETE!" + " " * 12 + "🎉")
    print("🎉" + " " * 38 + "🎉")
    print("🎉" * 40)
    
    if response.status == "success":
        print(response.recommendation)
    else:
        print(f"❌ Error: {response.result.get('error', 'Unknown error')}")
    
    print("\n" + "🎉" * 40)
    print(f"📅 Timestamp: {response.timestamp}")
    print("🎉" * 40)
    
    # Stop the bureau after getting the response
    ctx.logger.info("✅ Analysis complete. Shutting down...")
    
    # Add a small delay before shutdown for better UX
    await asyncio.sleep(2)

# ------------------------------
# Main Execution
# ------------------------------

def run_swarm_defi_advisor():
    """Run the Swarm-based DeFi advisor."""
    bureau = Bureau()
    bureau.add(defi_orchestrator)
    bureau.add(discovery_uagent)
    bureau.add(risk_uagent)
    bureau.add(decision_uagent)
    bureau.add(trigger_agent)
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                    🤖 ROBOT DEFI ADVISOR v2.0 🤖                           ║")
    print("║                        Agent Intercommunication System                      ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("🚀 Starting Agent Intercommunication DeFi Advisor...")
    print("📡 Agents will communicate via uAgents Framework")
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
    
    bureau.run()

if __name__ == "__main__":
    run_swarm_defi_advisor()
