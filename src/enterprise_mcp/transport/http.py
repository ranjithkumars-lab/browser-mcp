"""Streamable HTTP transport (default).

Implemented in a later phase using the official MCP Python SDK over FastAPI.
"""

from __future__ import annotations

from enterprise_mcp.transport.base import Transport

__all__ = ["StreamableHTTPTransport"]


class StreamableHTTPTransport(Transport):
    """Streamable HTTP transport stub."""

    name = "streamable-http"

    async def start(self) -> None:
        raise NotImplementedError("Streamable HTTP transport is implemented in a later phase")

    async def stop(self) -> None:
        raise NotImplementedError("Streamable HTTP transport is implemented in a later phase")
