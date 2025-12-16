"""
LiveKit + Langfuse Integration Example
This demonstrates how to build a voice AI agent with observability using Langfuse
"""

import asyncio
import os
from langfuse import Langfuse, observe
from livekit import agents, rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.plugins import openai
import google.generativeai as genai

# Setup Langfuse
langfuse = Langfuse(
    public_key="pk-lf-a9e6914d-2e63-4658-88d3-6151715b5821",
    secret_key="sk-lf-347475ef-2e06-4a2e-9353-679a8386b57f",
    host="http://localhost:3000"
)

# Configure Gemini
genai.configure(api_key="AIzaSyB2iWVf7NwL_G7D3Pg0C90ED8aLuc6CUow")


class VoiceAgent:
    """Voice AI Agent with Langfuse tracing"""
    
    def __init__(self):
        self.conversation_history = []
    
    @observe(as_type="generation")
    def get_ai_response(self, user_text: str, use_prompt_version: int = None):
        """
        Get AI response with Langfuse prompt management and tracing
        """
        try:
            # Fetch prompt from Langfuse
            if use_prompt_version:
                prompt = langfuse.get_prompt("voice-assistant", version=use_prompt_version)
            else:
                # Try to get the prompt, create if doesn't exist
                try:
                    prompt = langfuse.get_prompt("voice-assistant")
                except Exception:
                    # Create default prompt if not found
                    self._create_default_prompt()
                    prompt = langfuse.get_prompt("voice-assistant")
            
            # Compile prompt with conversation history
            print(f"This is the prompt: {prompt.prompt}")
            rendered_prompt = prompt.compile(
                user_input=user_text,
                history="\n".join(self.conversation_history[-5:])  # Last 5 messages
            )
            print(f"This is the rendered prompt: {rendered_prompt}")
            # Call Gemini LLM
            response = self._call_gemini(rendered_prompt)
            
            # Update conversation history
            self.conversation_history.append(f"User: {user_text}")
            self.conversation_history.append(f"Assistant: {response}")
            
            return response
            
        except Exception as e:
            print(f"Error in get_ai_response: {e}")
            return "I'm sorry, I encountered an error processing your request."
    
    @observe(as_type="generation")
    def _call_gemini(self, prompt: str):
        """Call Gemini API with tracing"""
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    
    def _create_default_prompt(self):
        """Create default voice assistant prompt in Langfuse"""
        print("coming inside default prompt creation")
        prompt_text = """You are a helpful voice assistant. Be concise and conversational.

Previous conversation:
{{history}}

User says: {{user_input}}

Respond naturally and helpfully in 1-2 sentences."""
        
        langfuse.create_prompt(
            name="voice-assistant",
            prompt=prompt_text,
            labels=["production"]
        )
        print("Created default voice-assistant prompt in Langfuse")


@observe(as_type="trace")
async def entrypoint(ctx: JobContext):
    """
    LiveKit room entry point with full Langfuse tracing
    """
    print(f"Connecting to room: {ctx.room.name}")
    
    # Initialize voice agent
    agent = VoiceAgent()
    
    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Wait for participant
    participant = await ctx.wait_for_participant()
    print(f"Participant joined: {participant.identity}")
    
    @observe(as_type="span")
    async def handle_speech(text: str):
        """Handle transcribed speech with tracing"""
        print(f"User said: {text}")
        
        # Get AI response (traced by @observe decorator)
        response = agent.get_ai_response(text)
        print(f"AI response: {response}")
        
        # In a real implementation, you would:
        # 1. Use TTS to convert response to speech
        # 2. Send audio back to the participant
        return response
    
    # Simulate conversation (in real app, this would be triggered by speech-to-text)
    test_messages = [
        "Hello, how are you?",
        "Tell me a joke",
        "What's the weather like?"
    ]
    
    for msg in test_messages:
        await handle_speech(msg)
        await asyncio.sleep(2)
    
    print("Demo completed!")


# Standalone demo function (doesn't require LiveKit server)
@observe(as_type="trace")
def demo_without_livekit():
    """
    Demo function to test Langfuse integration without LiveKit server
    Run this if you don't have LiveKit server set up
    """
    print("=== LiveKit + Langfuse Integration Demo ===\n")
    
    agent = VoiceAgent()
    
    # Simulate a conversation
    conversations = [
        "Hello, I need help with Python programming",
        "How do I create a list?",
        "What about dictionaries?",
        "Thank you!"
    ]
    
    for user_input in conversations:
        print(f"\n👤 User: {user_input}")
        response = agent.get_ai_response(user_input)
        print(f"🤖 Assistant: {response}")
        print("-" * 50)
    
    print("\n✅ Demo completed! Check your Langfuse dashboard for traces.")


if __name__ == "__main__":
    # Check if LiveKit credentials are set
    if os.getenv("LIVEKIT_URL") and os.getenv("LIVEKIT_API_KEY"):
        # Option 1: Run with LiveKit server
        print("Starting LiveKit agent...")
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
    else:
        # Option 2: Run standalone demo (no LiveKit server needed)
        print("LiveKit credentials not found. Running standalone demo...")
        print("To use LiveKit server, set these environment variables:")
        print("  export LIVEKIT_URL=<your-livekit-url>")
        print("  export LIVEKIT_API_KEY=<your-api-key>")
        print("  export LIVEKIT_API_SECRET=<your-api-secret>")
        print()
        demo_without_livekit()
