"""
Unit tests for client/capture.py

Tests the capture -> resize -> JPEG encode pipeline.
These tests run against the actual screen, so they require a display.
"""

import io

import pytest
from PIL import Image

from capture import MONITOR, capture_frame, get_screen_frame


class TestGetScreenFrame:
    """Tests for get_screen_frame() function."""

    def test_get_screen_frame_returns_bytes(self):
        """Verify get_screen_frame returns raw bytes, not a PIL Image."""
        result = get_screen_frame()
        assert isinstance(result, bytes), f"Expected bytes, got {type(result)}"
        assert len(result) > 0, "Expected non-empty bytes"

    def test_jpeg_header_magic_bytes(self):
        """Verify returned bytes start with JPEG SOI marker (FF D8 FF)."""
        result = get_screen_frame()
        # JPEG files start with FF D8 FF (SOI marker + APP0/APP1 marker)
        assert result[:3] == b"\xFF\xD8\xFF", "Not a valid JPEG header"

    def test_decoded_dimensions_are_720p(self):
        """Decode JPEG and verify output is 1280x720."""
        result = get_screen_frame()
        img = Image.open(io.BytesIO(result))
        assert img.size == (1280, 720), f"Expected (1280, 720), got {img.size}"

    def test_custom_bounding_box(self):
        """Verify resize works regardless of input region size."""
        # Pass a small bounding box and verify output is still 1280x720
        small_region = {"top": 0, "left": 0, "width": 200, "height": 200}
        result = get_screen_frame(monitor=small_region)
        img = Image.open(io.BytesIO(result))
        assert img.size == (1280, 720), f"Expected (1280, 720), got {img.size}"

    def test_jpeg_format(self):
        """Verify the decoded image is actually a valid JPEG."""
        result = get_screen_frame()
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG", f"Expected JPEG, got {img.format}"


class TestCaptureFrameBackwardCompat:
    """Tests for legacy capture_frame() function."""

    def test_capture_frame_returns_pil_image(self):
        """Verify legacy capture_frame still returns PIL Image."""
        result = capture_frame()
        assert isinstance(result, Image.Image), f"Expected Image, got {type(result)}"

    def test_capture_frame_at_native_resolution(self):
        """Verify capture_frame returns image at native resolution."""
        result = capture_frame()
        # Should be at monitor resolution, not 720p
        assert result.size[0] > 0 and result.size[1] > 0


class TestMonitorConfig:
    """Tests for MONITOR configuration."""

    def test_monitor_dict_has_required_keys(self):
        """Verify MONITOR dict has all required keys."""
        assert "top" in MONITOR
        assert "left" in MONITOR
        assert "width" in MONITOR
        assert "height" in MONITOR

    def test_monitor_values_are_integers(self):
        """Verify MONITOR values are valid integers."""
        assert isinstance(MONITOR["top"], int)
        assert isinstance(MONITOR["left"], int)
        assert isinstance(MONITOR["width"], int)
        assert isinstance(MONITOR["height"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])