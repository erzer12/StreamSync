"""
client/audio_routing.py – VB-Audio Virtual Cable helpers (FR-05).

Lists available audio devices and resolves the correct device index for
VB-Audio CABLE Input (AI output) and CABLE Output (OBS source).
"""

from __future__ import annotations

import pyaudio


def list_devices() -> None:
    """Print all available PyAudio devices to stdout."""
    pa = pyaudio.PyAudio()
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        print(f"[{i:>2}] {info['name']}  (in={info['maxInputChannels']}, out={info['maxOutputChannels']})")
    pa.terminate()


def find_device(pa: pyaudio.PyAudio, name_fragment: str, direction: str = "output") -> int:
    """Return the index of the first device whose name contains *name_fragment*.

    Args:
        pa: An open PyAudio instance.
        name_fragment: Case-insensitive substring to match against device names.
        direction: ``"input"`` or ``"output"``.

    Raises:
        RuntimeError: If no matching device is found.
    """
    channel_key = "maxOutputChannels" if direction == "output" else "maxInputChannels"
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if name_fragment.lower() in info["name"].lower() and info[channel_key] > 0:
            return i
    raise RuntimeError(
        f"No {direction} device containing '{name_fragment}' found. "
        "Is VB-Audio Virtual Cable installed?"
    )


def get_cable_input_device_index(pa: pyaudio.PyAudio) -> int:
    return find_device(pa, "CABLE Input", direction="output")


def get_mic_device_index(pa: pyaudio.PyAudio) -> int:
    try:
        return pa.get_default_input_device_info()["index"]
    except Exception:
        return find_device(pa, "Microphone", direction="input")


if __name__ == "__main__":
    list_devices()
