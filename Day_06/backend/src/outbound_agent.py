import logging
import json
import os

from dotenv import load_dotenv
from livekit import rtc, api
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("outbound-agent")
load_dotenv(".env.local")

# Outbound specific prompt
SYSTEM_PROMPT = """IDENTITY: You are "Dukaan Sathi", a friendly and helpful local commerce voice assistant working for local shopkeepers in India.
OBJECTIVES: You are making an OUTBOUND call to a returning customer. Your goal is to give them a friendly restock nudge based on their past order rhythm.
KNOWLEDGE: Last month, this customer ordered "5 bags of Basmati Rice". You are calling to check if they need a refill today.
LANGUAGE & SCRIPT: 
- If the user speaks in English, reply ENTIRELY in English.
- If the user speaks in Hindi, reply ENTIRELY in Hindi.
- Always write every language in its own native script. Hindi -> Devanagari (नमस्ते), never romanized (never "namaste").

GUARDRAILS: 
- Do not make any promises on behalf of the store. Keep the call short and polite. 
- If they say yes, tell them you will have the shopkeeper deliver it by this evening.
STYLE: Keep your sentences short, practical, and conversational. Maintain a moderate, patient pace."""

class Assistant(Agent):
    def __init__(self, instructions: str) -> None:
        super().__init__(instructions=instructions)

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session(agent_name="outbound-agent")
async def outbound_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    await ctx.connect()
    
    # In outbound, we don't necessarily wait for the participant to speak first
    # We just connect and start our pipeline
    
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        tts=murf.TTS(
            voice="Anisha", 
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=Assistant(instructions=SYSTEM_PROMPT),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Speak immediately when connected!
    await session.generate_reply(
        instructions="Introduce yourself warmly as Dukaan Sathi. Say you are calling because they ordered 5 bags of Basmati Rice last month, and ask if they would like to restock today for evening delivery."
    )

if __name__ == "__main__":
    cli.run_app(server)
