"""SSE chat routes for the Ollama agent."""

from __future__ import annotations

import json
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from browser_mcp.api.chat.schemas import ChatConfigResponse, ChatRequest
from browser_mcp.api.screenshots import ScreenshotRecord, ScreenshotStore

router = APIRouter(tags=["chat"])


def _get_agent(request: Request) -> Any:
    return request.app.state.chat_agent


def _get_screenshot_store(request: Request) -> ScreenshotStore:
    return request.app.state.screenshot_store


AgentDep = Annotated[Any, Depends(_get_agent)]
StoreDep = Annotated[ScreenshotStore, Depends(_get_screenshot_store)]


def _sse(event: str, payload: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _record_screenshot(
    store: ScreenshotStore, user_id: str | None, name: str, content: str
) -> None:
    """Register a ``browser.screenshot`` tool result with its owning user."""
    if name != "browser.screenshot":
        return
    try:
        raw: Any = json.loads(content)
    except (TypeError, ValueError):
        return
    if not isinstance(raw, dict):
        return
    payload = cast(dict[str, Any], raw)

    def _field(key: str, default: Any = None) -> Any:
        value: Any = payload.get(key, default)
        return value if isinstance(value, (str, int, bool)) or value is None else default

    path = _field("screenshot_path")
    if not path:
        return
    store.record(
        ScreenshotRecord(
            filename=ScreenshotStore.filename_from_path(str(path)),
            path=str(path),
            user_id=user_id,
            session_id=_field("session_id"),
            page_id=_field("page_id"),
            url=_field("url"),
            title=_field("title"),
            mime_type=_field("mime_type") or "image/png",
            width=_field("width"),
            height=_field("height"),
        )
    )


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
async def chat_stream(request: ChatRequest, agent: AgentDep, store: StoreDep) -> StreamingResponse:
    """Run the Ollama agent loop and stream events as Server-Sent Events."""

    async def generate():
        try:
            async for event in agent.stream(request.messages, model=request.model):
                if event["type"] == "tool_result":
                    _record_screenshot(store, request.user_id, event["name"], event["content"])
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
