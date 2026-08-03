"""Chat request/response schemas for the Ollama agent endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str | None = None


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list[ChatMessage])
    model: str | None = None
    user_id: str | None = Field(
        default=None,
        description="Optional identifier of the chat user requesting the run.",
    )


class ChatConfigResponse(BaseModel):
    host: str
    model: str
    tools: int
    tool_names: list[str] = Field(default_factory=list[str])
