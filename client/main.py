"""
client/main.py – StreamSync Live entry-point.

Launches three concurrent asyncio tasks:
  • send_audio  – streams 20 ms PCM chunks from the default mic to Gemini Live
  • send_video  – sends 1 FPS JPEG screen captures to Gemini Live
  • receive     – plays AI audio through VB-Audio CABLE Input and writes subtitles
"""

import asyncio
import io
import os
from dotenv import load_dotenv

# Load .env file from the parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import pyaudio
from google import genai
from google.genai import types
from PIL import Image

from audio_routing import get_cable_input_device_index, get_mic_device_index
from capture import get_screen_frame

# ---------------------------------------------------------------------------
# Screen Capture Configuration
# ---------------------------------------------------------------------------

# Screen capture config - adjust per streamer to match game window position
MONITOR_CONFIG: dict = {"top": 0, "left": 0, "width": 1920, "height": 1080}

# Set to a .jpg/.png path to bypass live capture (for API connection testing)
TEST_IMAGE_PATH: str | None = None

# ---------------------------------------------------------------------------
# Gemini Configuration
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-3.1-flash-lite-preview"

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
# Helper Functions
# ---------------------------------------------------------------------------

def _load_test_image() -> bytes:
    """Load a static JPEG for API connection testing.

    Loads TEST_IMAGE_PATH, resizes to 720p, encodes as JPEG at quality=85.

    Returns:
        Raw JPEG bytes ready for Gemini Live API.
    """
    with Image.open(TEST_IMAGE_PATH) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")
        img = img.resize((1280, 720), Image.BILINEAR)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Async Tasks
# ---------------------------------------------------------------------------
async def send_audio(session: genai.live.AsyncSession) -> None:
    """Read from the default mic and stream PCM to Gemini Live."""
    mic_idx = get_mic_device_index(pa)
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE_IN,
        input=True,
        input_device_index=mic_idx,
        frames_per_buffer=CHUNK_FRAMES_IN,
    )
    try:
        while True:
            data = await asyncio.get_running_loop().run_in_executor(
                None, stream.read, CHUNK_FRAMES_IN, False
            )
            # Use send_realtime_input with Blob for proper Gemini Live API
            blob = types.Blob(data=data, mime_type="audio/pcm")
            await session.send_realtime_input(audio=blob)
    finally:
        stream.stop_stream()
        stream.close()


async def send_video(session: genai.live.AsyncSession) -> None:
    """Capture one screen frame per second and send it to Gemini Live.

    Uses monotonic clock timing to maintain exactly 1 FPS without drift.
    If TEST_IMAGE_PATH is set, loads a static image instead of live capture.
    """
    loop = asyncio.get_running_loop()
    next_tick = loop.time()

    while True:
        next_tick += 1.0

        # Get frame: either from static test image or live capture
        if TEST_IMAGE_PATH:
            frame_bytes = await loop.run_in_executor(None, _load_test_image)
        else:
            frame_bytes = await loop.run_in_executor(
                None, get_screen_frame, MONITOR_CONFIG
            )

        # Wrap as Gemini Blob and send via realtime input channel
        blob = types.Blob(data=frame_bytes, mime_type="image/jpeg")
        await session.send_realtime_input(video=blob)

        # Sleep until next tick (compensating for capture/encode time)
        # Added a longer delay to respect API rate limits
        delay = max(0.5, next_tick - loop.time()) # minimum 500ms between frames
        await asyncio.sleep(delay)


async def receive(session: genai.live.AsyncSession) -> None:
    """Play AI audio through VB-Audio CABLE Input and write subtitles to disk."""
    cable_idx = get_cable_input_device_index(pa)
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
                print("Barge-in detected – flushing buffer")
                out_stream.stop_stream()
                out_stream.close()
                out_stream = pa.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=SAMPLE_RATE_OUT,
                    output=True,
                    output_device_index=cable_idx,
                )
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
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1alpha"})
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
