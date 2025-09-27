import asyncio

from uagents import Agent, Context, Protocol, Model

from datetime import datetime
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
        timestamp=datetime.utcnow(),
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
        response_text = f"✅ Optimal pool found: {msg.optimalPool.get('id', 'Unknown')}\n"
        response_text += f"Risk Score: {msg.optimalPool.get('riskScore', 'N/A')}\n"
        response_text += f"Risk Level: {msg.optimalPool.get('riskLevel', 'N/A')}\n"
        
        if msg.reasoningTrace:
            response_text += "\nReasoning:\n"
            for reason in msg.reasoningTrace[:3]:  # Show first 3 reasons
                response_text += f"• {reason}\n"
    else:
        response_text = f"❌ Decision failed: {msg.error or 'Unknown error'}"
    
    # Send response back to ASI chat
    if original_chat_sender:
        response_content = [TextContent(type="text", text=response_text)]
        response_msg = ChatMessage(
            timestamp=datetime.utcnow(),
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
