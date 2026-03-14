# StreamSync Live – Gemini Live Agent Challenge

**Winner-ready AI co-commentator for non-native streamers**

## Documentation
- [Product Requirements (PRD)](docs/PRD.md)
- [System Requirements (SRD)](docs/SRD.md)
- [Software Design (SDD)](docs/DESIGN.md)
- [Tech Stack](docs/TECHSTACK.md)
- [Architecture](docs/ARCHITECTURE.md)

## Quick Start
1. `pip install -r client_requirements.txt`
2. Install **VB-Audio Virtual Cable** + **OBS Studio**
3. `export GEMINI_API_KEY=AIza...`
4. `cd client && python main.py`
5. Configure OBS (see [PRD](docs/PRD.md) for routing)

## Cloud Deployment (Bonus Points)
```bash
cd my_agent/deployment
python deploy.py
```