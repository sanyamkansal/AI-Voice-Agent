import argparse
import asyncio
import os
import uuid
import sys

from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

async def dial(phone_number: str) -> None:
    lk = api.LiveKitAPI()
    
    # Generate a random room name for this call
    room_name = f"outbound-call-{uuid.uuid4().hex[:8]}"
    print(f"Creating room: {room_name}")
    
    # Create the room
    await lk.room.create_room(api.CreateRoomRequest(name=room_name))
    
    # Dispatch our outbound agent to the room
    print("Dispatching outbound-agent to the room...")
    await lk.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name="outbound-agent",
            room=room_name,
            metadata='{"phone_number": "' + phone_number + '"}'
        )
    )
    
    # Get the SIP trunk ID from env
    trunk_id = os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID")
    if not trunk_id:
        print("ERROR: LIVEKIT_SIP_OUTBOUND_TRUNK_ID is not set in .env.local")
        print("Please follow the setup instructions in the walkthrough to create a SIP trunk.")
        await lk.aclose()
        return

    print(f"Dialing {phone_number} via SIP trunk {trunk_id}...")
    
    # Create the SIP participant which rings the destination phone
    await lk.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            sip_trunk_id=trunk_id,
            sip_call_to=phone_number,
            room_name=room_name,
            participant_identity="customer",
            wait_until_answered=True,
        )
    )
    
    print("Call dialed successfully! Check your phone/Linphone.")
    await lk.aclose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dial a phone number or SIP URI.")
    parser.add_argument("--to", required=True, help="The phone number or SIP URI to call (e.g., sip:user@sip.linphone.org)")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(dial(args.to))
    except KeyboardInterrupt:
        pass
