"""Ollama chat agent that drives the browser tool registry.

The agent translates the in-process :class:`ToolRegistry` into Ollama function
definitions, runs the standard tool-calling loop, and exposes the exchange as an
async stream of discrete events (text deltas, tool invocations, tool results).
It is transport-agnostic: the FastAPI SSE route renders these events, while
tests can consume them directly.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any, cast

import httpx
import structlog

from browser_mcp.api.chat.schemas import ChatMessage
from browser_mcp.config.models import OllamaConfig
from enterprise_mcp.tools.metadata import ToolMetadata
from enterprise_mcp.tools.registry import ToolRegistry

__all__ = ["ChatAgent"]

_LOGGER = structlog.get_logger("browser_mcp.api.chat")


def tool_parameters(meta: ToolMetadata) -> dict[str, Any]:
    """Return a JSON schema for a tool's parameters across MCP versions.

    The in-process registry stores structured :class:`ToolParameter` objects;
    this mirrors the ``input_schema``/``inputSchema`` shape exposed by the MCP
    SDK so the same helper can be reused for OpenAPI-derived tools.
    """
    properties: dict[str, Any] = {}
    required: list[str] = []
    for parameter in meta.parameters:
        property_schema: dict[str, Any] = {"type": parameter.type}
        if parameter.description:
            property_schema["description"] = parameter.description
        if parameter.default is not None:
            property_schema["default"] = parameter.default
        properties[parameter.name] = property_schema
        if parameter.required:
            required.append(parameter.name)
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


class ChatAgent:
    """Runs Ollama tool-calling loops against the browser tool registry."""

    def __init__(
        self,
        tools: ToolRegistry,
        config: OllamaConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._tools = tools
        self._config = config
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(self._config.timeout_seconds)
        )

    async def aclose(self) -> None:
        """Release the underlying HTTP client."""
        await self._client.aclose()

    def tool_definitions(self) -> list[dict[str, Any]]:
        """Return Ollama-format function definitions for every registered tool."""
        definitions: list[dict[str, Any]] = []
        for meta in self._tools.list():
            definitions.append(
                {
                    "type": "function",
                    "function": {
                        "name": meta.name,
                        "description": meta.description,
                        "parameters": tool_parameters(meta),
                    },
                }
            )
        return definitions

    async def stream(
        self, messages: list[ChatMessage], model: str | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Run the agent loop and yield chat events.

        Emitted events (``{"type": ...}``):

        - ``text``: ``{"delta": str}`` streamed assistant text.
        - ``tool_call``: ``{"name": str, "arguments": dict}`` before execution.
        - ``tool_result``: ``{"name": str, "content": str, "error": bool}``.
        - ``done``: ``{"content": str, "steps": int}`` terminal event.
        - ``error``: ``{"detail": str}`` fatal failure.
        """
        resolved_model = model or self._config.model
        tools = self.tool_definitions()
        history: list[dict[str, Any]] = [
            {"role": "system", "content": self._config.system_prompt},
            *[message.model_dump(exclude_none=True) for message in messages],
        ]
        steps = 0
        final_text = ""

        while True:
            steps += 1
            tool_calls: list[dict[str, Any]] = []
            step_text = ""
            try:
                async for delta, raw_calls in self._chat_stream(
                    resolved_model, history, tools
                ):
                    if delta:
                        step_text += delta
                        final_text += delta
                        yield {"type": "text", "delta": delta}
                    if raw_calls:
                        tool_calls.extend(raw_calls)
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                _LOGGER.error("chat_agent_request_failed", error=str(exc))
                yield {"type": "error", "detail": str(exc)}
                return

            if not tool_calls:
                break

            history.append(
                {
                    "role": "assistant",
                    "content": step_text,
                    "tool_calls": tool_calls,
                }
            )
            for tool_call in tool_calls:
                function = cast(dict[str, Any], tool_call.get("function") or {})
                name = str(function.get("name", ""))
                raw_arguments: Any = function.get("arguments") or {}
                arguments = cast(dict[str, Any], raw_arguments)
                yield {"type": "tool_call", "name": name, "arguments": arguments}
                try:
                    result = await self._tools.call(name, **arguments)
                    content = self._serialize(result)
                    error = False
                except Exception as exc:
                    content = f"Error: {exc}"
                    error = True
                yield {
                    "type": "tool_result",
                    "name": name,
                    "content": content,
                    "error": error,
                }
                history.append(
                    {"role": "tool", "name": name, "content": content}
                )

            if steps >= self._config.max_tool_steps:
                yield {"type": "done", "content": final_text, "steps": steps}
                return

        yield {"type": "done", "content": final_text, "steps": steps}

    async def _chat_stream(
        self, model: str, history: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AsyncIterator[tuple[str, list[dict[str, Any]]]]:
        """Yield ``(content_delta, tool_calls)`` as Ollama streams them."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": history,
            "tools": tools,
            "stream": True,
            "options": {
                "temperature": self._config.temperature,
                "num_ctx": self._config.context_tokens,
            },
        }
        async with self._client.stream(
            "POST", f"{self._config.host.rstrip('/')}/api/chat", json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                chunk = cast(dict[str, Any], json.loads(line))
                message = cast(dict[str, Any], chunk.get("message") or {})
                content = message.get("content")
                raw_calls: Any = message.get("tool_calls")
                calls = (
                    cast(list[dict[str, Any]], raw_calls)
                    if isinstance(raw_calls, list)
                    else []
                )
                yield (content if isinstance(content, str) else ""), calls

    @staticmethod
    def _serialize(result: Any) -> str:
        if isinstance(result, str):
            return result
        if result is None:
            return ""
        try:
            return json.dumps(result, default=str, indent=None, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(result)
