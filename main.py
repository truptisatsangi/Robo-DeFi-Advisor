import asyncio

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
        
        # Create a beautiful, user-friendly response
        response_text = "🎯 **INVESTMENT RECOMMENDATION** 🎯\n\n"
        
        # Pool ID (shortened for readability)
        pool_id = pool.get('id', 'Unknown')
        short_id = pool_id[:8] + "..." if len(pool_id) > 8 else pool_id
        response_text += f"📊 **Recommended Pool:** `{short_id}`\n\n"
        
        # Risk Assessment
        risk_score = pool.get('riskScore', 0)
        risk_level = pool.get('riskLevel', 'unknown').replace('_', ' ').title()
        
        # Risk emoji based on level
        risk_emoji = {
            'Very Low': '🟢',
            'Low': '🟡', 
            'Medium': '🟠',
            'High': '🔴',
            'Very High': '🚨'
        }.get(risk_level, '❓')
        
        response_text += f"⚠️ **Risk Assessment:** {risk_emoji} {risk_level} (Score: {risk_score}/100)\n\n"
        
        # Recommendations
        recommendations = pool.get('recommendations', [])
        if recommendations:
            response_text += "💡 **Recommendations:**\n"
            for rec in recommendations[:3]:  # Show top 3 recommendations
                response_text += f"• {rec}\n"
            response_text += "\n"
        
        # Investment Details
        user_intent = msg.user_intent or {}
        amount = user_intent.get('amount', 'N/A')
        preference = user_intent.get('preference', 'N/A')
        
        response_text += f"💰 **Investment Amount:** ${amount}\n"
        response_text += f"🎯 **Your Preference:** {preference.title()}\n\n"
        
        # Success message
        if risk_score < 30:
            response_text += "🚨 **Warning:** This pool has high risk. Consider safer alternatives.\n"
        elif risk_score > 70:
            response_text += "✅ **Great Choice:** This pool has low risk and is suitable for conservative investments.\n"
        else:
            response_text += "⚖️ **Balanced:** This pool offers moderate risk with potential for good returns.\n"
            
        response_text += "\n---\n*Powered by DeFi Risk Advisor*"
        
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
