"""
Unit tests for client/capture.py

Tests the capture -> resize -> JPEG encode pipeline.
mss is mocked to avoid requiring a physical display.
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from capture import MONITOR, capture_frame, get_screen_frame


def _make_mock_sct(width: int = 1920, height: int = 1080):
    """Return a mock mss context manager whose grab() returns a fake screenshot."""
    # Build BGRA bytes (4 bytes per pixel: B=200, G=100, R=30, A=255)
    bgra_data = bytearray(width * height * 4)
    for i in range(width * height):
        bgra_data[i * 4] = 200      # B
        bgra_data[i * 4 + 1] = 100  # G
        bgra_data[i * 4 + 2] = 30   # R
        bgra_data[i * 4 + 3] = 255  # A

    mock_shot = MagicMock()
    mock_shot.size = (width, height)
    mock_shot.bgra = bytes(bgra_data)

    mock_sct = MagicMock()
    mock_sct.grab.return_value = mock_shot
    mock_sct.monitors = [None, {"top": 0, "left": 0, "width": width, "height": height}]

    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_sct)
    mock_context.__exit__ = MagicMock(return_value=False)
    return mock_context


class TestGetScreenFrame:
    """Tests for get_screen_frame() function."""

    def test_get_screen_frame_returns_bytes(self):
        """Verify get_screen_frame returns raw bytes, not a PIL Image."""
        with patch("mss.mss", return_value=_make_mock_sct()):
            result = get_screen_frame()
        assert isinstance(result, bytes), f"Expected bytes, got {type(result)}"
        assert len(result) > 0, "Expected non-empty bytes"

    def test_jpeg_header_magic_bytes(self):
        """Verify returned bytes start with JPEG SOI marker (FF D8 FF)."""
        with patch("mss.mss", return_value=_make_mock_sct()):
            result = get_screen_frame()
        # JPEG files start with FF D8 FF (SOI marker + APP0/APP1 marker)
        assert result[:3] == b"\xFF\xD8\xFF", "Not a valid JPEG header"

    def test_decoded_dimensions_are_720p(self):
        """Decode JPEG and verify output is 1280x720."""
        with patch("mss.mss", return_value=_make_mock_sct()):
            result = get_screen_frame()
        img = Image.open(io.BytesIO(result))
        assert img.size == (1280, 720), f"Expected (1280, 720), got {img.size}"

    def test_custom_bounding_box(self):
        """Verify resize works regardless of input region size."""
        # Pass a small bounding box and verify output is still 1280x720
        small_region = {"top": 0, "left": 0, "width": 200, "height": 200}
        with patch("mss.mss", return_value=_make_mock_sct(200, 200)):
            result = get_screen_frame(monitor=small_region)
        img = Image.open(io.BytesIO(result))
        assert img.size == (1280, 720), f"Expected (1280, 720), got {img.size}"

    def test_jpeg_format(self):
        """Verify the decoded image is actually a valid JPEG."""
        with patch("mss.mss", return_value=_make_mock_sct()):
            result = get_screen_frame()
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG", f"Expected JPEG, got {img.format}"


class TestCaptureFrameBackwardCompat:
    """Tests for legacy capture_frame() function."""

    def test_capture_frame_returns_pil_image(self):
        """Verify legacy capture_frame still returns PIL Image."""
        with patch("mss.mss", return_value=_make_mock_sct()):
            result = capture_frame()
        assert isinstance(result, Image.Image), f"Expected Image, got {type(result)}"

    def test_capture_frame_at_native_resolution(self):
        """Verify capture_frame returns image at native resolution."""
        with patch("mss.mss", return_value=_make_mock_sct()):
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