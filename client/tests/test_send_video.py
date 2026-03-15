"""Integration tests for client/main.py send_video function.

Tests the video pipeline integration with mocked Gemini Live session.
"""

import asyncio
import io
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image


# Set fake API key before importing main.py
os.environ.setdefault("GEMINI_API_KEY", "fake_key_for_testing")

from google.genai import types

# Import main after setting env var
import main


# =============================================================================
# Test Classes
# =============================================================================


class MockSession:
    """Mock Gemini Live session for testing."""

    def __init__(self):
        self.video_calls = []
        self.audio_calls = []

    async def send_realtime_input(self, video=None, audio=None):
        """Mock send_realtime_input method."""
        if video is not None:
            self.video_calls.append(video)
        if audio is not None:
            self.audio_calls.append(audio)


@pytest.mark.asyncio
class TestSendVideoWithTestImage:
    """Tests for send_video with TEST_IMAGE_PATH set."""

    @pytest.fixture
    def temp_test_image(self):
        """Create a temporary test image file."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img = Image.new("RGB", (640, 480), color="red")
            img.save(f.name, format="JPEG")
            yield f.name
        # Cleanup after test
        if os.path.exists(f.name):
            os.unlink(f.name)

    async def test_static_image_sends_blob(self, temp_test_image):
        """Verify send_video sends a Blob with mime_type='image/jpeg'."""
        main.TEST_IMAGE_PATH = temp_test_image

        mock_session = MockSession()

        task = asyncio.create_task(main.send_video(mock_session))
        await asyncio.sleep(2.5)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert mock_session.video_calls, "send_realtime_input not called with video"

        video_blob = mock_session.video_calls[0]
        assert isinstance(video_blob, types.Blob), f"Expected Blob, got {type(video_blob)}"
        assert video_blob.mime_type == "image/jpeg", f"Expected image/jpeg, got {video_blob.mime_type}"
        assert video_blob.data, "Expected non-empty data in blob"

    async def test_timing_interval(self, temp_test_image):
        """Verify frames are sent at approximately 1 second intervals."""
        main.TEST_IMAGE_PATH = temp_test_image

        mock_session = MockSession()
        call_times = []

        original_send = mock_session.send_realtime_input

        async def mock_send(video=None, audio=None):
            if video is not None:
                call_times.append(asyncio.get_running_loop().time())
            await original_send(video=video, audio=audio)

        mock_session.send_realtime_input = mock_send

        task = asyncio.create_task(main.send_video(mock_session))
        await asyncio.sleep(3.5)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        assert len(call_times) >= 2, f"Expected >=2 frames, got {len(call_times)}"

        for i in range(1, len(call_times)):
            interval = call_times[i] - call_times[i - 1]
            assert 0.5 <= interval <= 1.5, f"Interval {interval}s not within 0.5-1.5s range"


@pytest.mark.asyncio
class TestSendVideoLiveCapture:
    """Tests for send_video with live capture (TEST_IMAGE_PATH=None)."""

    async def test_uses_live_capture_when_no_test_image(self):
        """Verify live capture is used when TEST_IMAGE_PATH is None."""
        main.TEST_IMAGE_PATH = None

        mock_session = MockSession()
        mock_session.send_realtime_input = AsyncMock()

        with patch("main.get_screen_frame") as mock_capture:
            mock_capture.return_value = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"

            task = asyncio.create_task(main.send_video(mock_session))
            await asyncio.sleep(2.5)
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            assert mock_capture.called, "get_screen_frame not called"


class TestLoadTestImage:
    """Tests for _load_test_image helper function."""

    @pytest.fixture
    def temp_test_image(self):
        """Create a temporary test image file."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img = Image.new("RGB", (800, 600), color="blue")
            img.save(f.name, format="JPEG")
            yield f.name
        # Cleanup after test
        if os.path.exists(f.name):
            os.unlink(f.name)

    @pytest.fixture
    def temp_rgba_image(self):
        """Create a temporary RGBA test image file."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img = Image.new("RGBA", (800, 600), color=(255, 0, 0, 128))
            img.save(f.name, format="PNG")
            yield f.name
        # Cleanup after test
        if os.path.exists(f.name):
            os.unlink(f.name)

    def test_load_test_image_returns_bytes(self, temp_test_image):
        """Verify _load_test_image returns JPEG bytes."""
        main.TEST_IMAGE_PATH = temp_test_image
        result = main._load_test_image()

        assert isinstance(result, bytes)
        assert result[:3] == b"\xFF\xD8\xFF"

    def test_load_test_image_resizes_to_720p(self, temp_test_image):
        """Verify output is resized to 1280x720."""
        main.TEST_IMAGE_PATH = temp_test_image
        result = main._load_test_image()

        img = Image.open(io.BytesIO(result))
        assert img.size == (1280, 720)

    def test_load_test_image_converts_rgba_to_rgb(self, temp_rgba_image):
        """Verify RGBA images are converted to RGB before JPEG encoding."""
        main.TEST_IMAGE_PATH = temp_rgba_image
        result = main._load_test_image()

        # Should succeed without error and produce valid JPEG
        img = Image.open(io.BytesIO(result))
        assert img.size == (1280, 720)
        assert img.mode == "RGB", f"Expected RGB mode, got {img.mode}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])