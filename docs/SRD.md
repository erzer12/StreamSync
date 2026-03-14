# System Requirements Document (SRD) – StreamSync Live

**Version:** 1.0

## Functional Requirements
- FR-01: Capture screen at exactly 1 FPS (mss library + bounding box)
- FR-02: 16 kHz PCM upstream + 24 kHz PCM downstream
- FR-03: Native barge-in via BidiGenerateContentServerContent interruption flag + instant buffer flush
- FR-04: Overwrite `subtitles.txt` with latest output transcription
- FR-05: Route AI audio exclusively to VB-Audio CABLE Input
- FR-06: Mute physical mic in OBS; monitor AI audio in headphones
- FR-07: Handle 10-minute session rollover with context summary
- FR-08: Deploy on Vertex AI Agent Engine with Terraform

## Non-Functional Requirements
- Latency: ≤ 600 ms first token
- CPU impact on game: < 5%
- Subtitle sync: 0 ms drift
- Audio isolation: 100% (no feedback loops)
- Hardware: Consumer PC (i5/Ryzen 5 + 16 GB RAM)

## Software Prerequisites
- Python 3.11+
- OBS Studio 30+
- VB-Audio Virtual Cable
- Gemini Multimodal Live API access
