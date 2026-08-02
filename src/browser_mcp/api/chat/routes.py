"""SSE chat routes for the Ollama agent."""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from browser_mcp.api.chat.schemas import ChatConfigResponse, ChatRequest

router = APIRouter(tags=["chat"])


def _get_agent(request: Request) -> Any:
    return request.app.state.chat_agent


AgentDep = Annotated[Any, Depends(_get_agent)]


def _sse(event: str, payload: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.get("/chat/config")
async def chat_config(agent: AgentDep) -> ChatConfigResponse:
    definitions = agent.tool_definitions()
    return ChatConfigResponse(
        host=agent._config.host,
        model=agent._config.model,
        tools=len(definitions),
        tool_names=[d["function"]["name"] for d in definitions],
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, agent: AgentDep) -> StreamingResponse:
    """Run the Ollama agent loop and stream events as Server-Sent Events."""

    async def generate():
        try:
            async for event in agent.stream(request.messages, model=request.model):
                yield _sse(event["type"], {k: v for k, v in event.items() if k != "type"})
        except Exception as exc:
            yield _sse("error", {"detail": str(exc)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
