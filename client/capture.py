"""
client/capture.py – 1 FPS screen capture (FR-01).

Uses the *mss* library for minimal CPU overhead.
Returns raw JPEG bytes ready for Gemini Live API transmission.

Configuration:
    MONITOR: Bounding box dict with keys "top", "left", "width", "height".
    Override this to capture only the game window (exclude OBS/chat).
"""

from __future__ import annotations

import io

import mss
from PIL import Image

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default: full primary monitor. Override per-streamer to crop to game window.
MONITOR: dict = {"top": 0, "left": 0, "width": 1920, "height": 1080}

# Target resolution for Gemini Live (720p balances quality vs bandwidth)
TARGET_SIZE: tuple[int, int] = (1280, 720)

# JPEG quality: 85 is "visually lossless" - below 75 you see banding on game UIs
JPEG_QUALITY: int = 85

# ---------------------------------------------------------------------------
# Capture Functions
# ---------------------------------------------------------------------------

def get_screen_frame(monitor: dict | None = None) -> bytes:
    """Capture screen, resize to 720p, JPEG-encode, return raw bytes.

    Args:
        monitor: Bounding box dict with keys "top", "left", "width", "height".
                 Defaults to the global MONITOR config.

    Returns:
        Raw JPEG bytes (not base64-encoded), ready to send via Gemini Live API.
    """
    region = monitor or MONITOR

    with mss.mss() as sct:
        shot = sct.grab(region)
        # Convert BGRA raw bytes to PIL Image (BGRX swaps BGR->RGB in one op)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

    # Resize to 720p using bilinear interpolation (fast + good quality)
    img = img.resize(TARGET_SIZE, Image.BILINEAR)

    # JPEG encode to in-memory buffer
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return buf.getvalue()


def capture_frame() -> Image.Image:
    """Grab a single frame from the screen and return it as a PIL Image.

    This function is kept for backward compatibility. For new code, prefer
    get_screen_frame() which returns raw JPEG bytes.

    Returns:
        PIL Image at native resolution (not resized).
    """
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Primary monitor
        screenshot = sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")