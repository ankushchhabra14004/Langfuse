"""
Script to manually trigger agent dispatch for a room
This creates an agent dispatch job that tells the agent to join the room
"""

import asyncio
from livekit import api
from dotenv import load_dotenv
import os

load_dotenv()

async def trigger_agent_for_room(room_name="test-room-langfuse"):
    # Initialize LiveKit API
    livekit_api = api.LiveKitAPI(
        url=os.getenv('LIVEKIT_URL'),
        api_key=os.getenv('LIVEKIT_API_KEY'),
        api_secret=os.getenv('LIVEKIT_API_SECRET')
    )
    
    try:
        # Create an agent dispatch job for the room
        dispatch = await livekit_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="voice-assistant",  # Match the agent name in your code
            )
        )
        
        print(f"✓ Agent dispatch created successfully!")
        print(f"  Agent: {dispatch.agent_name or 'any'}")
        print(f"  Room: {room_name}")
        print(f"  Dispatch ID: {dispatch.id}")
        print("\nThe agent should join the room shortly.")
        
    except Exception as e:
        print(f"✗ Failed to create agent dispatch: {e}")
        print("\nMake sure:")
        print("1. The agent is running (python livekit_voice_agent.py dev)")
        print("2. The room exists (someone has joined it)")
        print("3. Your API credentials are correct")
    
    await livekit_api.aclose()

if __name__ == "__main__":
    import sys
    room = sys.argv[1] if len(sys.argv) > 1 else "test-room-langfuse"
    print(f"Triggering agent for room: {room}")
    asyncio.run(trigger_agent_for_room(room))
