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
KNOWLEDGE: You know about general local retail products, typical shop hours, and common shopping inquiries. You do NOT have access to real-time inventory databases, specific pricing, or delivery tracking systems.
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
- ESCALATION SCRIPT: If a customer asks for specifics you don't know, you must say: "I don't have the exact details right now, but I can have the shopkeeper call you back or you can visit the store."
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