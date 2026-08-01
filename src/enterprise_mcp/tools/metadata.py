"""Tool metadata models."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["ToolMetadata", "ToolParameter"]


class ToolParameter(BaseModel):
    """A single tool input parameter."""

    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: object | None = None


class ToolMetadata(BaseModel):
    """Structured metadata for a registered tool."""

    name: str
    description: str = ""
    parameters: list[ToolParameter] = Field(default_factory=list[ToolParameter])
    returns: str = "json"
    version: str = "1.0.0"
