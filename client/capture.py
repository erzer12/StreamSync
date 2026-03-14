"""
client/capture.py – 1 FPS screen capture (FR-01).

Uses the *mss* library for minimal CPU overhead.
Returns a PIL Image ready for JPEG encoding.
"""

from __future__ import annotations

import mss
from PIL import Image

# Capture the primary monitor.  Change the index to target a specific display.
MONITOR_INDEX = 1


def capture_frame() -> Image.Image:
    """Grab a single frame from the primary monitor and return it as a PIL Image."""
    with mss.mss() as sct:
        monitor = sct.monitors[MONITOR_INDEX]
        screenshot = sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
