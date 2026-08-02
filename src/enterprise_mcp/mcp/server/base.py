"""MCP server composition root.

Binds the tool registry and transports together and exposes the Streamable
HTTP ASGI application for mounting into the REST interface.
"""

from __future__ import annotations

from typing import Any, cast

from enterprise_mcp.tools.registry import ToolRegistry
from enterprise_mcp.transport.base import Transport
from enterprise_mcp.transport.http import StreamableHTTPTransport

__all__ = ["MCPServer"]


class MCPServer:
    """Composes a tool registry and transports into an MCP server."""

    def __init__(
        self,
        *,
        tools: ToolRegistry | None = None,
        name: str = "enterprise-mcp-server",
        host: str = "127.0.0.1",
    ) -> None:
        self.name = name
        self.host = host
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

    def streamable_http_transport(self) -> StreamableHTTPTransport:
        """Return a Streamable HTTP transport bound to this server's tools.

        The transport is cached on first access so repeated calls share the
        same FastMCP server instance.
        """
        transport = self._transports.get("streamable-http")
        if transport is None:
            transport = StreamableHTTPTransport(
                tools=self.tools,
                server_name=self.name,
                host=self.host,
            )
            self._transports["streamable-http"] = transport
        return cast(StreamableHTTPTransport, transport)

    def asgi_app(self) -> Any:
        """Return the Streamable HTTP ASGI application."""
        return self.streamable_http_transport().asgi_app()

    def mount(self, app: Any, path: str | None = None) -> None:
        """Mount the Streamable HTTP transport into a FastAPI/Starlette app."""
        self.streamable_http_transport().mount(app, path)

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
