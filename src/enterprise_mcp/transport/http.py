"""Streamable HTTP transport (default).

Implemented on top of the official MCP Python SDK's ``FastMCP`` server. The
transport is pure infrastructure: it knows nothing about business logic or
Playwright. It builds a FastMCP server from a tool registry and exposes the
resulting ASGI application for mounting into a FastAPI app.
"""

from __future__ import annotations

from typing import Any

from mcp.server.transport_security import TransportSecuritySettings

from enterprise_mcp.tools.registry import ToolRegistry
from enterprise_mcp.transport.base import Transport

__all__ = ["StreamableHTTPTransport"]

DEFAULT_MCP_PATH = "/mcp"


class StreamableHTTPTransport(Transport):
    """Streamable HTTP transport backed by the official MCP SDK."""

    name = "streamable-http"

    def __init__(
        self,
        *,
        tools: ToolRegistry | None = None,
        path: str = DEFAULT_MCP_PATH,
        server_name: str = "enterprise-mcp-server",
        host: str = "127.0.0.1",
        debug: bool = False,
        json_response: bool = False,
    ) -> None:
        self._tools = tools or ToolRegistry()
        self._path = path
        self._server_name = server_name
        self._host = host
        self._debug = debug
        self._json_response = json_response
        self._fastmcp: Any = None
        self._app: Any = None
        self._session_ctx: Any = None
        self._running = False

    @property
    def path(self) -> str:
        """Return the mount path of this transport."""
        return self._path

    def _transport_security(self) -> TransportSecuritySettings | None:
        """Return transport-security settings appropriate for the bind host.

        The MCP SDK's DNS rebinding protection only makes sense for loopback
        binds: it validates the incoming ``Host`` header against a fixed set
        of localhost values. When the server is bound to a non-loopback
        address (e.g. ``0.0.0.0`` in Docker/production) a client may reach
        it through any IP/hostname, so the SDK's validation would reject
        legitimate requests with ``421 Misdirected Request``. In that case
        we disable it and rely on the network edge (reverse proxy, firewall,
        API-key auth) for host verification.

        Returning ``None`` lets the SDK apply its secure loopback defaults.
        """
        if self._is_loopback(self._host):
            return None
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)

    @staticmethod
    def _is_loopback(host: str) -> bool:
        """Return whether the bind ``host`` is a loopback address.

        ``0.0.0.0`` / ``::`` / ``""`` mean "all interfaces" and are treated as
        non-loopback because clients may reach the server through any network
        address, defeating the SDK's localhost-only host validation.
        """
        return host in ("127.0.0.1", "localhost", "::1", "[::1]")

    @property
    def is_running(self) -> bool:
        """Return whether the transport is currently running."""
        return self._running

    def _build_server(self) -> Any:
        """Build (and cache) the FastMCP server from the tool registry."""
        if self._fastmcp is not None:
            return self._fastmcp
        from mcp.server.fastmcp import FastMCP

        server = FastMCP(
            name=self._server_name,
            debug=self._debug,
            json_response=self._json_response,
            streamable_http_path="/",
            transport_security=self._transport_security(),
        )
        for metadata in self._tools.list():
            func = self._tools.get(metadata.name)
            server.add_tool(func, name=metadata.name, description=metadata.description)
        self._fastmcp = server
        return server

    def asgi_app(self) -> Any:
        """Return the Starlette ASGI application for this transport."""
        if self._app is None:
            self._app = self._build_server().streamable_http_app()
        return self._app

    def mount(self, app: Any, path: str | None = None) -> None:
        """Mount this transport into a FastAPI/Starlette ``app``.

        Parameters
        ----------
        app:
            The parent FastAPI application to mount into.
        path:
            Mount path; defaults to the transport's configured path.
        """
        app.mount(path or self._path, self.asgi_app())

    async def start(self) -> None:
        """Start accepting Streamable HTTP traffic (runs the session manager)."""
        self.asgi_app()
        self._session_ctx = self._build_server().session_manager.run()
        await self._session_ctx.__aenter__()
        self._running = True

    async def stop(self) -> None:
        """Stop accepting traffic and shut down the session manager."""
        ctx = self._session_ctx
        self._session_ctx = None
        if ctx is not None:
            await ctx.__aexit__(None, None, None)
        self._running = False

    async def handle(self, request: Any) -> Any:
        """Not used for HTTP; requests are handled by the mounted ASGI app."""
        raise NotImplementedError("Streamable HTTP requests are handled by the mounted ASGI app")
