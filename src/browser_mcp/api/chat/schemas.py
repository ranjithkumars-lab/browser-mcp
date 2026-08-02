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


class ChatConfigResponse(BaseModel):
    host: str
    model: str
    tools: int
