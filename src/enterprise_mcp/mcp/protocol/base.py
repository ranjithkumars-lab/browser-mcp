"""MCP protocol interface."""

from __future__ import annotations

from typing import Any

__all__ = ["Protocol"]


class Protocol:
    """Abstract MCP protocol handler.

    The official MCP Python SDK is integrated in a later phase. Business code
    should depend on this abstraction, never on the SDK directly.
    """

    @property
    def name(self) -> str:
        """Return the protocol implementation name."""
        return "abstract"

    def list_tools(self) -> list[dict[str, Any]]:
        """Return the MCP tool descriptors."""
        raise NotImplementedError

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Invoke ``name`` with ``arguments``."""
        raise NotImplementedError

    async def initialize(self) -> None:
        """Negotiate protocol initialization."""
        raise NotImplementedError
