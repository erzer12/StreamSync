"""Unit tests for client/capture.py

Tests the capture -> resize -> JPEG encode pipeline.
Uses mocks instead of actual screen capture for headless CI compatibility.
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from capture import MONITOR, capture_frame, get_screen_frame


def _make_mock_sct():
    """Create a mock mss.ScreenShot for testing without a display."""
    # Create RGBA image and convert to BGRA bytes (mss returns BGRA)
    # For 640x480: 640 * 480 * 4 bytes = 1,228,800 bytes
    mock_img = Image.new("RGBA", (640, 480), color="red")
    bgra_bytes = mock_img.tobytes("raw", "BGRA")

    # Create mock ScreenShot object
    mock_shot = MagicMock()
    mock_shot.size = (640, 480)
    mock_shot.bgra = bgra_bytes

    # Create mock sct with grab method
    mock_sct = MagicMock()
    mock_sct.grab.return_value = mock_shot

    return mock_sct


class TestGetScreenFrame:
    """Tests for get_screen_frame() function."""

    @patch("capture.mss.mss")
    def test_get_screen_frame_returns_bytes(self, mock_mss):
        """Verify get_screen_frame returns raw bytes, not a PIL Image."""
        mock_mss.return_value.__enter__ = MagicMock(return_value=_make_mock_sct())
        mock_mss.return_value.__exit__ = MagicMock(return_value=False)

        result = get_screen_frame()
        assert isinstance(result, bytes), f"Expected bytes, got {type(result)}"
        assert len(result) > 0, "Expected non-empty bytes"

    @patch("capture.mss.mss")
    def test_jpeg_header_magic_bytes(self, mock_mss):
        """Verify returned bytes start with JPEG SOI marker (FF D8 FF)."""
        mock_mss.return_value.__enter__ = MagicMock(return_value=_make_mock_sct())
        mock_mss.return_value.__exit__ = MagicMock(return_value=False)

        result = get_screen_frame()
        assert result[:3] == b"\xFF\xD8\xFF", "Not a valid JPEG header"

    @patch("capture.mss.mss")
    def test_decoded_dimensions_are_720p(self, mock_mss):
        """Decode JPEG and verify output is 1280x720."""
        mock_mss.return_value.__enter__ = MagicMock(return_value=_make_mock_sct())
        mock_mss.return_value.__exit__ = MagicMock(return_value=False)

        result = get_screen_frame()
        img = Image.open(io.BytesIO(result))
        assert img.size == (1280, 720), f"Expected (1280, 720), got {img.size}"

    @patch("capture.mss.mss")
    def test_custom_bounding_box(self, mock_mss):
        """Verify resize works regardless of input region size."""
        mock_mss.return_value.__enter__ = MagicMock(return_value=_make_mock_sct())
        mock_mss.return_value.__exit__ = MagicMock(return_value=False)

        small_region = {"top": 0, "left": 0, "width": 200, "height": 200}
        result = get_screen_frame(monitor=small_region)
        img = Image.open(io.BytesIO(result))
        assert img.size == (1280, 720), f"Expected (1280, 720), got {img.size}"

    @patch("capture.mss.mss")
    def test_jpeg_format(self, mock_mss):
        """Verify the decoded image is actually a valid JPEG."""
        mock_mss.return_value.__enter__ = MagicMock(return_value=_make_mock_sct())
        mock_mss.return_value.__exit__ = MagicMock(return_value=False)

        result = get_screen_frame()
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG", f"Expected JPEG, got {img.format}"


class TestCaptureFrameBackwardCompat:
    """Tests for legacy capture_frame() function."""

    @patch("capture.mss.mss")
    def test_capture_frame_returns_pil_image(self, mock_mss):
        """Verify legacy capture_frame still returns PIL Image."""
        mock_mss.return_value.__enter__ = MagicMock(return_value=_make_mock_sct())
        mock_mss.return_value.__exit__ = MagicMock(return_value=False)

        result = capture_frame()
        assert isinstance(result, Image.Image), f"Expected Image, got {type(result)}"

    @patch("capture.mss.mss")
    def test_capture_frame_at_native_resolution(self, mock_mss):
        """Verify capture_frame returns image at native resolution."""
        mock_mss.return_value.__enter__ = MagicMock(return_value=_make_mock_sct())
        mock_mss.return_value.__exit__ = MagicMock(return_value=False)

        result = capture_frame()
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