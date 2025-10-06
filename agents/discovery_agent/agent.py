import json
import logging
import os
from typing import Dict, Any, Optional, List
from openai import OpenAI
from uagents import Agent, Context, Model, Protocol
from discovery_logic import DiscoveryLogic
from dotenv import load_dotenv

risk_agent_address = "agent1qfvk3m82xljka6y22447dufg6hnx0zuqejplxmxfvwscsq9qwr2cy0u74hw"
logger = logging.getLogger(__name__)

load_dotenv(override=True)
class PoolListMessage(Model):
    pool_id: str
    metrics: Optional[Dict[str, Any]] = None

class DiscoveryResponse(Model):
    pools: List[PoolListMessage]
    user_intent: Dict[str, Any] = {}

class DiscoveryRequest(Model):
    msg: str

agent = Agent(name="DiscoveryAgent", seed="Discover_pool_seed", port=8007, endpoint=["http://localhost:8007/submit"])

class Message(Model):
    message: str

@agent.on_message(model=Message)
async def handle_discovery(ctx: Context, sender: str, msg: Message):
    try:
        system_prompt = """You are an AI assistant that extracts structured investment criteria "
        "from user input. Given a sentence, return a JSON object with the fields:\n"
        "- action: the user's intent (e.g. 'invest')\n"
        "- amount: numerical amount in USD\n"
        "- min_apy: minimum desired APY (as number, not percentage string)\n"
        "- preference: user's qualitative preferences (e.g. 'safest', 'highest yield')\n\n"
        "If a field is not specified in the input, set its value to None.\n"
        "Return only a valid JSON object. Do not include any explanation or extra text."""
        
        user_prompt = f"Extract criteria from this input {msg.message}"
        message_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        client = OpenAI(
            api_key=os.getenv("ASI_ONE_API_KEY"),  
            base_url="https://api.asi1.ai/v1"
        )
        
        response = client.chat.completions.create(
            model="asi1-mini",
            messages=message_history,
            temperature=0,
            top_p=0.9,
            max_tokens=1000,
            presence_penalty=0,
            frequency_penalty=0,
            stream=False,
            extra_body={"web_search": False},
        )
        
        model_output = response.choices[0].message.content.strip()
        print("Raw model output:", model_output)
        
        start = model_output.find('{')
        end = model_output.rfind('}') + 1
        json_str = model_output[start:end]
        user_intent = json.loads(json_str)
        
        # Ensure required keys are present
        for key in ["action", "amount", "min_apy", "preference"]:
            user_intent.setdefault(key, None)
            
    except (json.JSONDecodeError, IndexError, AttributeError) as e:
        print(":x: Error parsing model response:", e)
        user_intent = {
            "action": None,
            "amount": None,
            "min_apy": None,
            "preference": None
        }
        
    logic = DiscoveryLogic()
    ctx.logger.info(f"Discovery request: {user_intent}")
    pools = await logic.discover_pools_async(user_intent)
    
    # Create list of PoolListMessage objects with full pool data
    pool_objs = [PoolListMessage(pool_id=p["id"], metrics=p) for p in pools]
    
    # Wrap in DiscoveryResponse
    pools_message = DiscoveryResponse(pools=pool_objs, user_intent=user_intent)
    
    ctx.logger.info(f"📤 Forwarding {len(pool_objs)} pools to RiskAgent...")

    await ctx.send(risk_agent_address, pools_message)

if __name__ == "__main__": 
    agent.run()