"""Tests for the Ollama chat agent (agent.py)."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from browser_mcp.api.chat.agent import ChatAgent, tool_parameters
from browser_mcp.api.chat.schemas import ChatMessage
from browser_mcp.config.models import OllamaConfig
from enterprise_mcp.tools.decorators import tool
from enterprise_mcp.tools.metadata import ToolMetadata, ToolParameter
from enterprise_mcp.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit


@tool(description="Add two integers.")
def add(a: int, b: int) -> int:
    """Sum two integers."""
    return a + b


def _registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(add)
    return registry


def _agent(
    registry: ToolRegistry,
    handler: object,
    config: OllamaConfig | None = None,
) -> ChatAgent:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    return ChatAgent(registry, config or OllamaConfig(), client=client)


def test_tool_parameters_builds_json_schema() -> None:
    meta = ToolMetadata(
        name="demo",
        parameters=[
            ToolParameter(name="url", type="string", description="The URL", required=True),
            ToolParameter(name="count", type="integer", required=False, default=1),
        ],
    )
    schema = tool_parameters(meta)
    assert schema["type"] == "object"
    assert schema["properties"]["url"]["description"] == "The URL"
    assert schema["required"] == ["url"]
    assert "count" not in schema["required"]


def test_tool_definitions_flatten_registry() -> None:
    agent = _agent(_registry(), lambda request: httpx.Response(200, text=""))
    definitions = agent.tool_definitions()
    assert [d["function"]["name"] for d in definitions] == ["add"]
    assert definitions[0]["function"]["parameters"]["required"] == ["a", "b"]


async def test_stream_simple_text_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/api/chat" in request.url.path
        return httpx.Response(
            200,
            text=(
                '{"message":{"content":"Hel","role":"assistant"}}\n'
                '{"message":{"content":"lo","role":"assistant"},'
                '"done":true}\n'
            ),
        )

    agent = _agent(_registry(), handler)
    events = [event async for event in agent.stream([ChatMessage(role="user", content="hi")])]
    assert events == [
        {"type": "text", "delta": "Hel"},
        {"type": "text", "delta": "lo"},
        {"type": "done", "content": "Hello", "steps": 1},
    ]


async def test_stream_executes_tool_and_continues() -> None:
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if len(calls) == 1:
            return httpx.Response(
                200,
                text=(
                    '{"message":{"content":"","role":"assistant","tool_calls":'
                    '[{"function":{"name":"add","arguments":{"a":2,"b":3}}}]},'
                    '"done":true}\n'
                ),
            )
        return httpx.Response(
            200,
            text='{"message":{"content":"5","role":"assistant"},"done":true}\n',
        )

    agent = _agent(_registry(), handler)
    events = [
        event
        async for event in agent.stream([ChatMessage(role="user", content="sum")])
    ]
    assert events[0] == {
        "type": "tool_call",
        "name": "add",
        "arguments": {"a": 2, "b": 3},
    }
    assert events[1]["type"] == "tool_result"
    assert events[1]["content"] == "5"
    assert events[2] == {"type": "text", "delta": "5"}
    assert events[3]["type"] == "done"


async def test_stream_surfaces_tool_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=(
                '{"message":{"content":"","role":"assistant","tool_calls":'
                '[{"function":{"name":"missing","arguments":{}}}]},"done":true}\n'
            ),
        )

    agent = _agent(_registry(), handler)
    events = [
        event
        async for event in agent.stream([ChatMessage(role="user", content="x")])
    ]
    assert events[1]["type"] == "tool_result"
    assert events[1]["error"] is True
    assert "Error" in events[1]["content"]


async def test_stream_handles_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    agent = _agent(_registry(), handler)
    events = [
        event
        async for event in agent.stream([ChatMessage(role="user", content="x")])
    ]
    assert events[0]["type"] == "error"
    assert events[0]["detail"]


async def test_stream_forces_summary_when_tool_calls_have_no_text() -> None:
    calls: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body)
        if "tools" not in body:
            return httpx.Response(
                200,
                text='{"message":{"content":"The sum is 5.","role":"assistant"},"done":true}\n',
            )
        return httpx.Response(
            200,
            text=(
                '{"message":{"content":"","role":"assistant","tool_calls":'
                '[{"function":{"name":"add","arguments":{"a":2,"b":3}}}]},'
                '"done":true}\n'
            ),
        )

    config = OllamaConfig(max_tool_steps=2)
    agent = _agent(_registry(), handler, config)
    events = [
        event
        async for event in agent.stream([ChatMessage(role="user", content="sum")])
    ]
    assert [e["type"] for e in events] == [
        "tool_call",
        "tool_result",
        "tool_call",
        "tool_result",
        "text",
        "done",
    ]
    assert events[4]["delta"] == "The sum is 5."
    assert events[5]["content"] == "The sum is 5."
    assert events[5]["steps"] == 2
    assert len(calls) == 3
    assert "tools" not in calls[2]


async def test_stream_does_not_force_summary_when_text_present() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=(
                '{"message":{"content":"Partial answer:","role":"assistant","tool_calls":'
                '[{"function":{"name":"add","arguments":{"a":1,"b":1}}}]},'
                '"done":true}\n'
            ),
        )

    config = OllamaConfig(max_tool_steps=1)
    agent = _agent(_registry(), handler, config)
    events = [
        event
        async for event in agent.stream([ChatMessage(role="user", content="sum")])
    ]
    assert events[0]["type"] == "text"
    assert events[0]["delta"] == "Partial answer:"
    assert events[1]["type"] == "tool_call"
    assert events[2]["type"] == "tool_result"
    assert events[-1]["type"] == "done"
    assert events[-1]["content"] == "Partial answer:"
