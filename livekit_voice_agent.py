"""
LiveKit Voice Agent with Real STT/TTS + Langfuse Observability
Uses Deepgram for STT, Google Gemini for LLM, Cartesia for TTS
"""

import logging
import os
from dotenv import load_dotenv
from langfuse import Langfuse, observe

# Load environment variables
load_dotenv()

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

# Initialize Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
)
logger.info("Langfuse initialized")

from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import (
    deepgram,
    silero,
    google,
    cartesia,
)


def ensure_prompt_exists():
    """Create default voice-assistant prompt in Langfuse if it doesn't exist"""
    try:
        langfuse.get_prompt("voice-assistant")
        logger.info("Prompt 'voice-assistant' already exists in Langfuse")
    except Exception:
        logger.info("Creating default 'voice-assistant' prompt in Langfuse...")
        langfuse.create_prompt(
            name="voice-assistant",
            prompt="""You are a helpful assistant communicating via voice.
Be concise and conversational in your responses.
Keep answers brief (1-3 sentences) since this is voice conversation.""",
            labels=["production", "voice"]
        )
        logger.info("Created default prompt in Langfuse")


class Assistant(Agent):
    """Voice Assistant with real STT/TTS and Langfuse observability"""
    
    @observe(as_type="span")
    def __init__(self, instructions: str = None) -> None:
        logger.info("Initializing Assistant components...")
        
        try:
            # Initialize AI components - All FREE services!
            logger.info("Loading Google LLM...")
            llm = google.LLM(model="gemini-2.5-flash")
            
            logger.info("Loading Deepgram STT...")
            stt = deepgram.STT()
            
            logger.info("Loading Cartesia TTS...")
            tts = cartesia.TTS()
            
            logger.info("Loading Silero VAD...")
            silero_vad = silero.VAD.load()
            
            logger.info("All components initialized successfully!")
            
            # Use provided instructions or default
            if instructions is None:
                instructions = """
                    You are a helpful assistant communicating via voice.
                    Be concise and conversational in your responses.
                """
            
            super().__init__(
                instructions=instructions,
                stt=stt,
                llm=llm,
                tts=tts,
                vad=silero_vad,
            )
        except Exception as e:
            logger.error(f"Failed to initialize Assistant: {e}")
            raise


@observe(as_type="trace")
async def entrypoint(ctx: JobContext):
    """Entry point for LiveKit agent with Langfuse tracing"""
    logger.info(f"Agent joining room: {ctx.room.name}")
    
    # Fetch prompt from Langfuse and inject into Assistant
    instructions = None
    try:
        prompt = langfuse.get_prompt("voice-assistant")
        instructions = prompt.prompt  # Get the actual prompt text
        logger.info(f"Loaded prompt 'voice-assistant' version {prompt.version}")
        logger.info(f"Using Langfuse prompt: {instructions[:100]}...")  # Log first 100 chars
    except Exception as e:
        logger.warning(f"Could not fetch prompt from Langfuse: {e}")
        logger.info("Using default instructions")
    
    await ctx.connect()

    session = AgentSession()

    await session.start(
        room=ctx.room,
        agent=Assistant(instructions=instructions)  # Pass Langfuse prompt to Agent
    )
    
    logger.info("Agent session started successfully")


if __name__ == "__main__":
    # Ensure prompt exists in Langfuse before starting agent
    ensure_prompt_exists()
    
    # Run the agent with auto-dispatch for all rooms
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="voice-assistant"  # Named agent for easier identification
        )
    )


# Available ElevenLabs Voice IDs:
# Roger: CwhRBWXzGAHq8TQ4Fs17
# Sarah: EXAVITQu4vr4xnSDxMaL
# Laura: FGY2WhTYpPnrIDTdsKH5
# George: JBFqnCBsd6RMkjVDRZzb
