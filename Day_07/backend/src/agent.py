import logging

from dotenv import load_dotenv
from livekit import rtc
import json
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
    llm,
    function_tool,
    RunContext,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel
import db

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """IDENTITY: You are "Dukaan Sathi", a friendly and helpful local commerce voice assistant working for local shopkeepers and small businesses in India.
OBJECTIVES: Your goal is to help customers find products, check availability, and understand store policies while maintaining a welcoming persona. A successful interaction ends with the customer feeling confident about their potential purchase and knowing the next steps.
KNOWLEDGE: You know about general local retail products, typical shop hours, and common shopping inquiries. You DO have access to real-time inventory and pricing via the check_product_stock_and_price tool. Always use this tool when asked about prices or availability. When quoting stock and prices, you MUST mention the timestamp the data is from (provided by the tool).
LANGUAGE & SCRIPT: 
Listen carefully to the language the user is speaking. 
- If the user speaks in English, reply ENTIRELY in English.
- If the user speaks in Hindi, reply ENTIRELY in Hindi.
- Always write every language in its own native script. Hindi -> Devanagari (नमस्ते), never romanized (never "namaste").
Do not mix languages unnecessarily. Maintain a polite, respectful, and informal register like a friendly shopkeeper.

MEMORY & CONSENT:
You have a memory database. When speaking with a new customer, you must ask for their explicit consent before saving their details. Tell the caller you are going to remember this, and if they say no, do NOT save it.
If they say yes, use the save_caller_facts tool to save their name and any important details (past orders, delivery preferences, etc).
GUARDRAILS: 
- HARD REFUSAL: NEVER confirm an order, price, or delivery date that the seller hasn't explicitly set.
- HARD REFUSAL: NEVER disclose store profits, financial details, or owner secrets. 
- Do not make any promises on behalf of the store. 
ESCALATION / HUMAN HANDOFF: 
You must ask for human help using the create_escalation tool if:
1. The caller has a payment, refund, or order dispute.
2. The caller requests a bulk order or custom discount that you cannot authorize.
CRITICAL RULE: Before calling the create_escalation tool, you MUST summarize the issue to the caller and explicitly ask for their permission to forward the details to the shopkeeper. If they say no, do NOT escalate.
STYLE: Keep your sentences short, practical, and conversational. Maintain a moderate, patient pace. Do not use special formatting like bolding or asterisks since you are a voice assistant. If there is silence, gently ask if they need help with anything else."""


class Assistant(Agent):
    def __init__(self, instructions: str) -> None:
        super().__init__(instructions=instructions)

    @function_tool
    async def save_caller_facts(self, user_id: str, name: str, language_preference: str, facts_json: str, context: RunContext):
        """Use this tool to save or update the caller's memory facts in the database.
        
        Args:
            user_id: The unique ID of the caller (provided in your system prompt).
            name: The caller's name.
            language_preference: The caller's preferred language.
            facts_json: A JSON string containing key-value pairs of facts to save (e.g. '{"past_orders": "cotton", "preferred_delivery": "evening"}').
        """
        logger.info(f"Saving facts for {name} ({user_id})")
        facts_dict = json.loads(facts_json)
        db.save_caller(user_id, name, language_preference, facts_dict)
        return "Facts saved successfully."

    @function_tool
    async def check_product_stock_and_price(self, product_name: str, context: RunContext):
        """Use this tool to look up the current price and stock availability of a product in the store's catalog.
        
        Args:
            product_name: The name of the product to search for (e.g. "Rice", "Atta").
        """
        import os
        from datetime import datetime
        
        logger.info(f"Looking up stock for {product_name}")
        
        catalog_path = "catalog.json"
        if not os.path.exists(catalog_path):
            return "Error: The catalog database is currently unreachable. Apologize to the user and tell them you cannot check prices right now."
            
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            for item in data.get("items", []):
                if product_name.lower() in item["name"].lower() or item["name"].lower() in product_name.lower():
                    # Format timestamp
                    try:
                        dt = datetime.fromisoformat(item["last_updated"].replace("Z", "+00:00"))
                        formatted_time = dt.strftime("%B %d, %Y at %I:%M %p")
                    except:
                        formatted_time = item["last_updated"]
                        
                    return f"Found '{item['name']}'. Price: ₹{item['price_inr']} per {item['unit']}. Stock available: {item['stock']}. This data is current as of {formatted_time}."
                    
            return "Product '{product_name}' not found in our catalog. Apologize and offer alternatives."
        except Exception as e:
            logger.error(f"Catalog error: {e}")
            return "Error: Failed to read from the catalog. Apologize to the user."

    @function_tool
    async def create_escalation(self, caller_name: str, issue_summary: str, agent_actions: str, urgency_level: str, preferred_language: str, context: RunContext):
        """Use this tool to escalate an issue to a human shopkeeper.
        
        Args:
            caller_name: The name of the caller needing help.
            issue_summary: A short summary of what happened and why they need help. Do NOT include passwords or private info.
            agent_actions: What you (the agent) already checked or told the caller.
            urgency_level: 'High', 'Medium', or 'Low' depending on the situation.
            preferred_language: The caller's preferred language.
        """
        import os
        from datetime import datetime
        
        logger.info(f"Escalating issue for {caller_name}")
        
        escalation_data = {
            "caller_name": caller_name,
            "issue_summary": issue_summary,
            "agent_actions": agent_actions,
            "urgency": urgency_level,
            "language": preferred_language,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            filepath = "escalations.json"
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"escalations": []}
                
            data["escalations"].append(escalation_data)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                
            return "Escalation created successfully. Tell the user the shopkeeper will follow up with them."
        except Exception as e:
            logger.error(f"Failed to save escalation: {e}")
            return "Error: Failed to create escalation. Tell the user to call back later."

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    db.init_db()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    await ctx.connect()
    participant = await ctx.wait_for_participant()
    user_id = participant.identity

    caller_data = db.get_caller(user_id)
    
    dynamic_instructions = SYSTEM_PROMPT + f"\n\nCURRENT CALLER USER ID: {user_id}\n"
    if caller_data:
        dynamic_instructions += f"STATUS: RETURNING CUSTOMER\nNAME: {caller_data['name']}\nFACTS: {json.dumps(caller_data['facts'])}\n\nINSTRUCTION: Welcome them back warmly by name and reference one of their past facts."
    else:
        dynamic_instructions += "STATUS: NEW CUSTOMER\n\nINSTRUCTION: Greet them and ask how you can help. Remember to ask for consent before saving any of their details."

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="Anisha", 
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(instructions=dynamic_instructions),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )


if __name__ == "__main__":
    cli.run_app(server)