"""MCP server composition root.

Binds the protocol, tool registry, and transports. Full protocol behaviour
is added in a later phase; this class already exposes a valid surface for
dependency wiring and testing.
"""

from __future__ import annotations

from typing import Any

from enterprise_mcp.tools.registry import ToolRegistry
from enterprise_mcp.transport.base import Transport

__all__ = ["MCPServer"]


class MCPServer:
    """Composes tool registry and transports into an MCP server."""

    def __init__(self, *, tools: ToolRegistry | None = None) -> None:
        self.tools = tools or ToolRegistry()
        self._transports: dict[str, Transport] = {}
        self._running = False

    def add_transport(self, transport: Transport) -> None:
        """Register ``transport`` for this server."""
        if transport.name in self._transports:
            raise ValueError(f"transport '{transport.name}' is already attached")
        self._transports[transport.name] = transport

    @property
    def transports(self) -> dict[str, Transport]:
        """Return attached transports by name."""
        return dict(self._transports)

    async def start(self) -> None:
        """Start all attached transports."""
        for transport in self._transports.values():
            await transport.start()
        self._running = True

    async def stop(self) -> None:
        """Stop all attached transports."""
        for transport in self._transports.values():
            await transport.stop()
        self._running = False

    def list_tools(self) -> list[dict[str, Any]]:
        """Return tool descriptors in MCP-compatible form."""
        descriptors: list[dict[str, Any]] = []
        for metadata in self.tools.list():
            descriptors.append(
                {
                    "name": metadata.name,
                    "description": metadata.description,
                    "parameters": [parameter.model_dump() for parameter in metadata.parameters],
                }
            )
        return descriptors
