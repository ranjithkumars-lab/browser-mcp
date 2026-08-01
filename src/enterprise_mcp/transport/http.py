"""Streamable HTTP transport (default).

Implemented on top of the official MCP Python SDK's ``FastMCP`` server. The
transport is pure infrastructure: it knows nothing about business logic or
Playwright. It builds a FastMCP server from a tool registry and exposes the
resulting ASGI application for mounting into a FastAPI app.
"""

from __future__ import annotations

from typing import Any

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
        debug: bool = False,
        json_response: bool = False,
    ) -> None:
        self._tools = tools or ToolRegistry()
        self._path = path
        self._server_name = server_name
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
