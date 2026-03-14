"""
my_agent/deployment/agent_app.py – ADK FastAPI application.

Wraps the StreamSync Live ADK runner in a FastAPI app so that
Vertex AI Agent Engine can serve it over HTTP/WebSocket.
"""

from __future__ import annotations

from google.adk.cli.fast_api import get_fast_api_app

from my_agent.core.agent import create_runner

runner = create_runner()
app = get_fast_api_app(runner=runner)
