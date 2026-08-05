"""Chat request/response schemas for the Ollama agent endpoint."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class BaseMessage(BaseModel):
    """Base class for all messages in the unified message model."""
    role: str
    id: str | None = None
    timestamp: str | None = None


class UserMessage(BaseMessage):
    role: Literal["user"] = "user"
    content: str


class AssistantMessage(BaseMessage):
    role: Literal["assistant"] = "assistant"
    content: str


class ToolMessage(BaseMessage):
    role: Literal["tool"] = "tool"
    name: str
    content: str
    tool_call_id: str | None = None


class ArtifactMessage(BaseMessage):
    role: Literal["artifact"] = "artifact"
    artifact_id: str
    artifact_type: str
    url: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SystemMessage(BaseMessage):
    role: Literal["system"] = "system"
    content: str


class ProgressMessage(BaseMessage):
    role: Literal["progress"] = "progress"
    step: str
    status: Literal["pending", "running", "success", "failed"]
    details: str | None = None


class PlanningMessage(BaseMessage):
    role: Literal["planning"] = "planning"
    plan: list[str]


class StatusMessage(BaseMessage):
    role: Literal["status"] = "status"
    content: str


class WorkflowMessage(BaseMessage):
    role: Literal["workflow"] = "workflow"
    workflow_type: str
    status: Literal["running", "success", "failed"]
    details: str | None = None


class SummaryMessage(BaseMessage):
    role: Literal["summary"] = "summary"
    content: str


class TypedError(BaseModel):
    type: Literal[
        "ToolError",
        "BrowserError",
        "TimeoutError",
        "ValidationError",
        "AuthenticationError",
        "RetryableError"
    ]
    message: str
    details: dict[str, Any] | None = None


class ErrorMessage(BaseMessage):
    role: Literal["error"] = "error"
    error: TypedError


ChatMessage = Annotated[
    UserMessage |
    AssistantMessage |
    ToolMessage |
    ArtifactMessage |
    SystemMessage |
    ProgressMessage |
    PlanningMessage |
    StatusMessage |
    WorkflowMessage |
    SummaryMessage |
    ErrorMessage,
    Field(discriminator="role")
]


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
