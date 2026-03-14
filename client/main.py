"""
client/main.py – StreamSync Live entry-point.

Launches three concurrent asyncio tasks:
  • send_audio  – streams 20 ms PCM chunks from the default mic to Gemini Live
  • send_video  – sends 1 FPS JPEG screen captures to Gemini Live
  • receive     – plays AI audio through VB-Audio CABLE Input and writes subtitles
"""

import asyncio
import base64
import io
import os

import pyaudio
from google import genai
from google.genai import types
from PIL import Image

from audio_routing import find_device
from capture import capture_frame

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-2.5-flash-live-001"

SAMPLE_RATE_IN = 16_000    # mic → Gemini
SAMPLE_RATE_OUT = 24_000   # Gemini → speaker
CHUNK_MS = 20
CHUNK_FRAMES_IN = SAMPLE_RATE_IN * CHUNK_MS // 1000
CHUNK_FRAMES_OUT = SAMPLE_RATE_OUT * CHUNK_MS // 1000

SYSTEM_PROMPT = (
    "You are an energetic, hype English co-commentator for a live gaming stream. "
    "The streamer speaks in Indian-accented English with fillers and stutters. "
    "Deliver polished, grammatically perfect, entertaining English commentary. "
    "Keep responses under 15 words unless describing a key moment."
)

SUBTITLE_PATH = "subtitles.txt"

# ---------------------------------------------------------------------------
# Shared PyAudio instance
# ---------------------------------------------------------------------------
pa = pyaudio.PyAudio()


# ---------------------------------------------------------------------------
# Async tasks
# ---------------------------------------------------------------------------
async def send_audio(session: genai.live.AsyncSession) -> None:
    """Read from the default mic and stream PCM to Gemini Live."""
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE_IN,
        input=True,
        frames_per_buffer=CHUNK_FRAMES_IN,
    )
    try:
        while True:
            data = await asyncio.get_event_loop().run_in_executor(
                None, stream.read, CHUNK_FRAMES_IN, False
            )
            await session.send({"mime_type": "audio/pcm", "data": data})
    finally:
        stream.stop_stream()
        stream.close()


async def send_video(session: genai.live.AsyncSession) -> None:
    """Capture one screen frame per second and send it to Gemini Live."""
    while True:
        frame: Image.Image = await asyncio.get_event_loop().run_in_executor(None, capture_frame)
        buf = io.BytesIO()
        frame.save(buf, format="JPEG", quality=70)
        await session.send(
            {"mime_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}
        )
        await asyncio.sleep(1)


async def receive(session: genai.live.AsyncSession) -> None:
    """Play AI audio through VB-Audio CABLE Input and write subtitles to disk."""
    cable_idx = find_device(pa, "CABLE Input", direction="output")
    out_stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE_OUT,
        output=True,
        output_device_index=cable_idx,
    )
    try:
        async for response in session.receive():
            # Barge-in: flush output buffer on server interruption
            if getattr(response, "server_content", None) and response.server_content.interrupted:
                out_stream.write(b"\x00" * CHUNK_FRAMES_OUT * 2)
                continue

            if response.data:
                out_stream.write(response.data)

            if response.text:
                with open(SUBTITLE_PATH, "w", encoding="utf-8") as f:
                    f.write(response.text)
    finally:
        out_stream.stop_stream()
        out_stream.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main() -> None:
    client = genai.Client(api_key=GEMINI_API_KEY)
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO", "TEXT"],
        system_instruction=SYSTEM_PROMPT,
    )
    async with client.aio.live.connect(model=MODEL, config=config) as session:
        await asyncio.gather(
            send_audio(session),
            send_video(session),
            receive(session),
        )


if __name__ == "__main__":
    asyncio.run(main())
