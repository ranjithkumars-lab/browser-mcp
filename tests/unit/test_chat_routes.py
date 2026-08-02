"""Tests for the SSE chat routes."""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from browser_mcp.api.chat.agent import ChatAgent
from browser_mcp.api.v1.router import router as v1_router
from browser_mcp.config.models import OllamaConfig
from enterprise_mcp.tools.decorators import tool
from enterprise_mcp.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit


@tool(description="Echo input.")
def echo(text: str = "") -> str:
    """Echo."""
    return text


def _app_client() -> TestClient:
    from fastapi import FastAPI

    registry = ToolRegistry()
    registry.register(echo)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text='{"message":{"content":"pong","role":"assistant"},"done":true}\n',
        )

    agent = ChatAgent(
        registry,
        OllamaConfig(host="http://ollama.local", model="test-model"),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    app = FastAPI()
    app.state.chat_agent = agent
    app.include_router(v1_router)
    return TestClient(app)


def test_chat_config_reports_tool_count() -> None:
    client = _app_client()
    response = client.get("/api/v1/chat/config")
    assert response.status_code == 200
    payload = response.json()
    assert payload["host"] == "http://ollama.local"
    assert payload["model"] == "test-model"
    assert payload["tools"] == 1


def test_chat_stream_emits_sse_frames() -> None:
    client = _app_client()
    response = client.post(
        "/api/v1/chat/stream",
        json={"messages": [{"role": "user", "content": "ping"}]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: text" in body
    assert "event: done" in body
    assert '"delta": "pong"' in body


def test_chat_stream_accepts_model_override() -> None:
    client = _app_client()
    response = client.post(
        "/api/v1/chat/stream",
        json={"messages": [], "model": "other-model"},
    )
    assert response.status_code == 200
