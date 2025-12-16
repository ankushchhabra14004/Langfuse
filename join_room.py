"""
Join the LiveKit room as a participant to trigger the agent
"""

import asyncio
from livekit import rtc, api

# Your LiveKit credentials
LIVEKIT_URL = "wss://capstone-gk1fgf3g.livekit.cloud"
LIVEKIT_API_KEY = "APIThxTpPfQDkGL"
LIVEKIT_API_SECRET = "e3JIQxl65eF0CTj9acOKNQKZn9DhE6f6tJOQzEwG0WdB"
ROOM_NAME = "test-room-langfuse"

async def join_room_as_participant():
    """Join the room and stay connected to trigger the agent"""
    
    # Generate access token
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.with_identity("participant-1")
    token.with_name("Participant 1")
    token.with_grants(api.VideoGrants(
        room_join=True,
        room=ROOM_NAME,
    ))
    
    jwt_token = token.to_jwt()
    
    print(f"🚀 Joining room: {ROOM_NAME}")
    print(f"📍 URL: {LIVEKIT_URL}")
    print()
    
    # Create room instance
    room = rtc.Room()
    
    # Set up event handlers
    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        print(f"👤 Participant connected: {participant.identity}")
    
    @room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, *_):
        print(f"🎵 Track subscribed: {track.kind}")
    
    try:
        # Connect to room
        await room.connect(LIVEKIT_URL, jwt_token)
        print(f"✅ Connected to room!")
        print(f"👥 Remote participants: {len(room.remote_participants)}")
        print()
        print("⏳ Staying in room for 60 seconds...")
        print("   (Check your agent terminal for activity)")
        print("   (Check Langfuse dashboard for traces)")
        print()
        
        # Stay connected for 60 seconds
        for i in range(60):
            await asyncio.sleep(1)
            if i % 10 == 0:
                print(f"   Still connected... ({60-i}s remaining)")
        
        print("\n✅ Test complete! Disconnecting...")
        await room.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("LiveKit Room Joiner")
    print("=" * 60)
    print()
    asyncio.run(join_room_as_participant())
