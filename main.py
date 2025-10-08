from uagents import Agent, Context, Protocol, Model

from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict, Any, List, Optional
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
   ChatAcknowledgement,
   ChatMessage,
   EndSessionContent,
   StartSessionContent,
   TextContent,
   chat_protocol_spec,
)

agent = Agent(
    name="Start",
    seed="Start_agent",
    port=8004,
    mailbox=True
)

print("🚀 Agents initialized.\n")

class Message(Model):
    message : str

class DecisionResponse(Model):
    success: bool
    optimalPool: Optional[Dict[str, Any]]
    alternatives: Optional[List[Dict[str, Any]]]
    reasoningTrace: Optional[List[Dict[str, Any]]]
    allCandidates: Optional[List[Dict[str, Any]]]
    error: Optional[str]
    timestamp: str
    user_intent: Optional[Dict[str, Any]] = {}

@agent.on_event("startup")
async def startup(ctx):
    ctx.logger.info("Agent is ready with mailbox!")


discovery_agent_address = "agent1q0yp3tt90n0v9a8dq6w4q4aknv899phpluue5cpc6dt8adsujv696ndy2cm"

# Store the original chat sender for responses
original_chat_sender = None


# Initialize the chat protocol with the standard chat spec
chat_proto = Protocol(spec=chat_protocol_spec)


# Utility function to wrap plain text into a ChatMessage
def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content,
    )

# Helper function to generate protocol-specific transaction links
def _get_transaction_link(pool: Dict[str, Any]) -> str:
    """Generate direct transaction link for the selected pool."""
    protocol = pool.get("protocol", "").lower()
    pool_id = pool.get("id", "")
    url = pool.get("url", "")
    
    # If pool already has a URL, use it
    if url:
        return url
    
    # Protocol-specific transaction links
    transaction_links = {
        "uniswap": {
            "base_url": "https://app.uniswap.org/explore/pools/ethereum/",
            "fallback_url": "https://app.uniswap.org/explore/pools"
        },
        "uniswap-v2": {
            "base_url": "https://v2.info.uniswap.org/pair/",
            "fallback_url": "https://app.uniswap.org/explore/pools"
        },
        "uniswap v3": {
            "base_url": "https://app.uniswap.org/explore/pools/ethereum/",
            "fallback_url": "https://app.uniswap.org/explore/pools"
        },
        "compound": {
            "base_url": "https://app.compound.finance/",
            "fallback_url": "https://app.compound.finance/"
        },
        "aave": {
            "base_url": "https://app.aave.com/reserve-overview/?underlyingAsset=",
            "fallback_url": "https://app.aave.com/"
        },
        "curve": {
            "base_url": "https://curve.fi/#/ethereum/pools/",
            "fallback_url": "https://curve.fi/"
        },
        "balancer": {
            "base_url": "https://app.balancer.fi/#/ethereum/pool/",
            "fallback_url": "https://app.balancer.fi/"
        },
        "pendle": {
            "base_url": "https://app.pendle.finance/trade/pools/",
            "fallback_url": "https://app.pendle.finance/"
        },
        "lido": {
            "base_url": "https://stake.lido.fi/",
            "fallback_url": "https://stake.lido.fi/"
        },
        "maple": {
            "base_url": "https://app.maple.finance/lend/pool/",
            "fallback_url": "https://app.maple.finance/"
        },
        "sparklend": {
            "base_url": "https://app.spark.fi/reserve-overview/?underlyingAsset=",
            "fallback_url": "https://app.spark.fi/"
        },
        "justlend": {
            "base_url": "https://justlend.org/#/market/",
            "fallback_url": "https://justlend.org/"
        },
        "raydium": {
            "base_url": "https://raydium.io/liquidity/pool/",
            "fallback_url": "https://raydium.io/swap/"
        },
        "hyperion": {
            "base_url": "https://app.hyperion.finance/pool/",
            "fallback_url": "https://app.hyperion.finance/"
        },
        "spectra": {
            "base_url": "https://app.spectra.finance/pool/",
            "fallback_url": "https://app.spectra.finance/"
        },
        "spectra-v2": {
            "base_url": "https://app.spectra.finance/pool/",
            "fallback_url": "https://app.spectra.finance/"
        }
    }
    
    # Get the appropriate link for the protocol
    if protocol in transaction_links:
        link_info = transaction_links[protocol]
        
        # Try to construct specific pool link with pool ID
        if pool_id:
            return f"{link_info['base_url']}{pool_id}"
        else:
            return link_info["fallback_url"]
    
    # Fallback to DeFiLlama for unknown protocols
    if protocol:
        return f"https://defillama.com/protocol/{protocol.replace(' ', '-')}"
    
    return None

# Helper function to format pool information
def format_pool_info(pool: Dict[str, Any], is_alternative: bool = False) -> str:
    """Format pool information with all details and links."""
    prefix = "🔄 **Alternative Pool:**" if is_alternative else "📊 **Recommended Pool:**"
    
    # Pool ID (full address)
    pool_id = pool.get('id', 'Unknown')
    
    # Pool Details
    apy = pool.get('apy', 0)
    tvl = pool.get('tvl', 0)
    protocol = pool.get('protocol', 'Unknown')
    symbol = pool.get('symbol', 'Unknown')
    chain = pool.get('chain', 'ethereum')
    
    # Get proper transaction link
    pool_link = _get_transaction_link(pool)
    
    # Risk Assessment
    risk_data = pool.get('riskData', {})
    risk_score = risk_data.get('riskScore', 0)
    risk_level = risk_data.get('riskLevel', 'unknown').replace('_', ' ').title()
    
    # Risk emoji based on level
    risk_emoji = {
        'Very Low': '🟢',
        'Low': '🟡', 
        'Medium': '🟠',
        'High': '🔴',
        'Very High': '🚨'
    }.get(risk_level, '❓')
    
    # Pool Security Details
    factors = risk_data.get('factors', {})
    
    # Build the formatted string
    formatted = f"{prefix}\n\n"
    formatted += f"📝 **Pool ID:** `{pool_id}`\n"
    formatted += f"💱 **Symbol:** {symbol}\n"
    formatted += f"🏦 **Protocol:** {protocol}\n"
    formatted += f"⛓️ **Chain:** {chain.capitalize()}\n"
    formatted += f"📈 **APY:** {apy:.2f}%\n"
    formatted += f"💧 **Total Value Locked:** ${tvl:,.0f}\n"
    formatted += f"⚠️ **Risk Assessment:** {risk_emoji} {risk_level} (Score: {risk_score}/100)\n\n"
    
    # Security metrics based on available data
    formatted += "🔒 **Security Metrics:**\n"
    
    # TVL as security indicator
    if tvl > 100_000_000:
        formatted += f"• Liquidity Depth: 🟢 Excellent (${tvl:,.0f})\n"
    elif tvl > 10_000_000:
        formatted += f"• Liquidity Depth: 🟡 Good (${tvl:,.0f})\n"
    elif tvl > 1_000_000:
        formatted += f"• Liquidity Depth: 🟠 Moderate (${tvl:,.0f})\n"
    else:
        formatted += f"• Liquidity Depth: 🔴 Low (${tvl:,.0f})\n"
    
    # Protocol reputation
    established_protocols = ["uniswap", "aave", "compound", "curve", "balancer", "lido", "makerdao", "yearn", "convex", "frax"]
    protocol_lower = protocol.lower()
    if any(est in protocol_lower for est in established_protocols):
        formatted += f"• Protocol Reputation: 🟢 Established & Audited\n"
    else:
        formatted += f"• Protocol Reputation: 🟡 Verify independently\n"
    
    # Risk level as security indicator
    if risk_level.lower() in ['very low', 'low']:
        formatted += f"• Risk Level: 🟢 Low Risk\n"
    elif risk_level.lower() == 'medium':
        formatted += f"• Risk Level: 🟡 Medium Risk\n"
    else:
        formatted += f"• Risk Level: 🔴 High Risk\n"
    
    # Add link
    if pool_link:
        formatted += f"\n🔗 **Pool Link:** {pool_link}\n"
        formatted += f"📊 **View on Etherscan:** https://etherscan.io/address/{pool_id}\n"
    else:
        formatted += f"\n🔗 **Pool Link:** Not available\n"
        formatted += f"📊 **View on Etherscan:** https://etherscan.io/address/{pool_id}\n"
    
    # Add recommendations
    recommendations = risk_data.get('recommendations', [])
    if recommendations:
        formatted += "\n💡 **Recommendations:**\n"
        for rec in recommendations[:3]:  # Show top 3 recommendations
            formatted += f"• {rec}\n"
    
    return formatted


# Handle incoming chat messages
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Received message from {sender}")


    # Process each content item inside the chat message
    for item in msg.content:
    # Marks the start of a chat session
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Session started with {sender}")
        
        # Handles plain text messages (from another agent or ASI:One)
        elif isinstance(item, TextContent):
            ctx.logger.info(f"Text message from {sender}: {item.text}")
            # Store the original chat sender for responses
            global original_chat_sender
            original_chat_sender = sender
            data = Message(message=item.text)
            await ctx.send(discovery_agent_address, data)


        # Marks the end of a chat session
        elif isinstance(item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")
        # Catches anything unexpected
        else:
            ctx.logger.info(f"Received unexpected content type from {sender}")


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
   ctx.logger.info(f"Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}")

# Handle decision responses from decision agent
@agent.on_message(model=DecisionResponse)
async def handle_decision_response(ctx: Context, sender: str, msg: DecisionResponse):
    ctx.logger.info(f"Received decision response from {sender}")
    
    if msg.success and msg.optimalPool:
        pool = msg.optimalPool
        alternatives = msg.alternatives or []
        
        # Create a beautiful, user-friendly response
        response_text = "🎯 **INVESTMENT RECOMMENDATION** 🎯\n\n"
        
        # Add recommended pool
        response_text += format_pool_info(pool, is_alternative=False)
        
        # Investment Details
        user_intent = msg.user_intent or {}
        amount = user_intent.get('amount', 'N/A')
        preference = user_intent.get('preference', 'N/A')
        
        response_text += f"💰 **Your Investment:** ${amount}\n"
        response_text += f"🎯 **Your Preference:** {preference.title() if preference else 'Not specified'}\n\n"
        
        # Risk assessment message
        risk_data = pool.get('riskData', {})
        risk_level = risk_data.get('riskLevel', 'unknown').replace('_', ' ').title()
        
        if risk_level.lower() in ['high', 'very high']:
            response_text += "🚨 **Warning:** This pool has high risk. Consider safer alternatives below.\n\n"
        elif risk_level.lower() in ['very low', 'low']:
            response_text += "✅ **Great Choice:** This pool has low risk and is suitable for conservative investments.\n\n"
        else:
            response_text += "⚖️ **Balanced:** This pool offers moderate risk with potential for good returns.\n\n"
        
        # Add alternatives if available
        if alternatives:
            response_text += "🔄 **ALTERNATIVE OPTIONS** 🔄\n\n"
            for i, alt_pool in enumerate(alternatives[:2], 1):  # Show max 2 alternatives
                response_text += f"**Option {i}:**\n"
                response_text += format_pool_info(alt_pool, is_alternative=True)
                response_text += "\n" + "─" * 50 + "\n\n"
        
        response_text += "---\n*Powered by DeFi Risk Advisor*"
        
    else:
        response_text = f"❌ **Investment Analysis Failed**\n\n"
        response_text += f"**Error:** {msg.error or 'Unknown error occurred'}\n\n"
        response_text += "Please try again or contact support if the issue persists."
    
    # Send response back to ASI chat
    if original_chat_sender:
        response_content = [TextContent(type="text", text=response_text)]
        response_msg = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=response_content,
        )
        await ctx.send(original_chat_sender, response_msg)
        ctx.logger.info(f"Sent response back to chat: {response_text}")
    else:
        ctx.logger.info(f"Final response (no chat sender): {response_text}")

# Include the chat protocol and publish the manifest to Agentverse
agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__": 
    agent.run()
