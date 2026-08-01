"""Shared error hierarchy for the Enterprise MCP Server."""

from __future__ import annotations

__all__ = [
    "ConfigError",
    "EnterpriseMCPError",
    "LifecycleError",
    "ToolError",
    "TransportError",
]


class EnterpriseMCPError(Exception):
    """Base class for all enterprise MCP server errors."""


class ConfigError(EnterpriseMCPError):
    """Raised when configuration cannot be loaded or validated."""


class LifecycleError(EnterpriseMCPError):
    """Raised when application startup or shutdown fails."""


class ToolError(EnterpriseMCPError):
    """Raised when a tool cannot be registered, validated, or executed."""


class TransportError(EnterpriseMCPError):
    """Raised when a transport cannot start, stop, or communicate."""
