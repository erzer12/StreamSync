"""
my_agent/core/agent.py – Vertex AI Agent Engine core definition.

Defines the StreamSync Live ADK agent that wraps Gemini Multimodal Live
and exposes it as a managed streaming agent on Vertex AI Agent Engine.
"""

from __future__ import annotations

import os

from google.adk.agents import LiveRequestQueue, agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL = "gemini-2.0-flash-live-001"

SYSTEM_PROMPT = (
    "You are an energetic, hype English co-commentator for a live gaming stream. "
    "The streamer speaks in Indian-accented English with fillers and stutters. "
    "Deliver polished, grammatically perfect, entertaining English commentary. "
    "Keep responses under 15 words unless describing a key moment."
)


@agent(
    model=MODEL,
    system_instruction=SYSTEM_PROMPT,
    response_modalities=["AUDIO", "TEXT"],
)
class StreamSyncAgent:
    """Real-time AI co-commentator agent for StreamSync Live."""

    async def on_audio(self, audio_bytes: bytes) -> None:
        """Forward raw PCM audio to the Gemini Live session."""
        await self.session.send({"mime_type": "audio/pcm", "data": audio_bytes})

    async def on_image(self, jpeg_bytes: bytes) -> None:
        """Forward a JPEG screen frame to the Gemini Live session."""
        import base64

        await self.session.send(
            {"mime_type": "image/jpeg", "data": base64.b64encode(jpeg_bytes).decode()}
        )


def create_runner() -> Runner:
    """Build and return an ADK Runner backed by an in-memory session service."""
    session_service = InMemorySessionService()
    return Runner(
        agent=StreamSyncAgent(),
        app_name="streamsync-live",
        session_service=session_service,
    )
