# Software Design Document (SDD) – StreamSync Live

**Version:** 1.0

## High-Level Architecture

```
[Streamer Mic] ──► main.py (asyncio.gather)
    ├── send_audio()  (20 ms chunks)
    ├── send_video()  (1 FPS mss → JPEG)
    └── receive()  → pyaudio (CABLE Input) + subtitles.txt

[Game Window] ──► capture.py (mss) → Gemini Live WebSocket

[OBS]
    ├── Game Capture
    ├── Audio Input Capture (CABLE Output) → Monitor & Output
    ├── GDI+ Text Source (subtitles.txt)
    └── Stream (Audience hears only AI)
```

## Key Design Decisions
1. **Vision**: Embrace 1 FPS limit → system prompt forces "color commentator" mode
2. **Barge-in**: Rely 100% on Gemini native VAD + server-side cancellation + client buffer flush
3. **Subtitles**: Flat-file overwrite (bypasses timestamp hallucinations)
4. **Audio Isolation**: Mandatory VB-Audio Virtual Cable matrix
5. **Session**: Stateful WebSocket with graceful 10-min reconnect

## Component Ownership (Hackathon Sprint)
- Person 2 → `capture.py`
- Person 3 → audio + receive loop in `main.py`
- Person 4 → OBS + virtual cable routing
- Person 1 & 5 → Vertex AI + Terraform

## Risks & Mitigations
- Thread blocking → `asyncio.gather()` from day 1
- Timestamp hallucinations → flat-file strategy
- Auth delay → fallback service account key
