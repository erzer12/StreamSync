# Tech Stack – StreamSync Live

| Layer                | Technology                              | Purpose                                      | Reason Chosen |
|----------------------|-----------------------------------------|----------------------------------------------|---------------|
| AI Core              | Gemini Multimodal Live API (gemini-2.0-flash-live-001) | Real-time audio + vision + native VAD | Unified model, <600 ms latency |
| Client Runtime       | Python 3.11 + asyncio                   | Bidirectional WebSocket                      | Native async for barge-in |
| Screen Capture       | mss                                     | 40+ FPS raw capture → 1 FPS JPEG             | Lowest CPU overhead |
| Audio I/O            | pyaudio                                 | Device-specific playback & input             | Full control of virtual cable |
| Audio Isolation      | VB-Audio Virtual Cable                  | CABLE Input / Output                         | Industry standard, zero latency |
| Broadcast            | OBS Studio 30+                          | Game + AI audio + GDI+ Text                  | Native file monitoring |
| Subtitles            | Flat `subtitles.txt` overwrite          | Real-time sync                               | Bypasses Gemini bug |
| Cloud Deployment     | Vertex AI Agent Engine + ADK            | Managed streaming agent                      | Native WebSocket support |
| IaC                  | Terraform                               | Bonus points automation                      | Required for hackathon scoring |
| Image Encoding       | Pillow                                  | mss → JPEG Blob                              | Required MIME type |

**Local Dependencies** – see `client_requirements.txt`  
**Cloud Dependencies** – see `my_agent/requirements.txt`
