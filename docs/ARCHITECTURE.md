# Architecture Diagram & Overview

![StreamSync Live Architecture](../assets/architecture_diagram.png)

## Core Data Flows
1. **Input** → Mic (16 kHz) + Screen (1 FPS JPEG)
2. **Gemini Live Session** → Stateful WebSocket
3. **Output** → 24 kHz audio → CABLE Input → OBS
4. **Subtitles** → Real-time overwrite of `subtitles.txt`

## Critical Constraints Honored
- Exactly 1 FPS vision (color-commentator prompt)
- Native barge-in (no wake word)
- Zero feedback loops (virtual cable matrix)
- No SRT timestamps (flat-file strategy)
