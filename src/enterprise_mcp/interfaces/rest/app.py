"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from enterprise_mcp.foundation.app import AppContext
from enterprise_mcp.interfaces.rest.routes import health_router, version_router

__all__ = ["create_app"]


class HostHeaderMiddleware:
    """Middleware to handle Host header validation for proxied requests.
    
    This middleware ensures that requests with non-standard Host headers
    (e.g., from reverse proxies, Docker, or direct IP access) are accepted
    by setting the Host header to match the server's bound address.
    """
    
    def __init__(self, app, host: str = "0.0.0.0", port: int = 8000):
        self.app = app
        self.host = host
        self.port = port
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Set the Host header to match what the server is bound to
            scope["headers"] = [
                (name, value) for name, value in scope.get("headers", [])
                if name.lower() != b"host"
            ] + [(b"host", f"{self.host}:{self.port}".encode())]
        
        await self.app(scope, receive, send)


def create_app(context: AppContext | None = None) -> FastAPI:
    """Build the FastAPI application bound to ``context``.

    When ``context`` is omitted a default context is constructed from the
    standard configuration sources, enabling ``uvicorn --factory`` style
    launches.

    The lifespan runs the application's startup and shutdown hooks so the
    configured services (event bus, tool registry, MCP server, etc.) are
    available while the API is serving traffic.
    """
    resolved_context = context if context is not None else AppContext()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        logger = structlog.get_logger("enterprise_mcp.interfaces.rest")
        await resolved_context.start()
        logger.info("http_lifespan_started")
        try:
            yield
        finally:
            await resolved_context.stop()
            logger.info("http_lifespan_stopped")

    host = resolved_context.settings.server.transports.host
    port = resolved_context.settings.server.transports.port
    
    app = FastAPI(
        title=resolved_context.settings.server.name,
        version=resolved_context.settings.server.version,
        description="Enterprise MCP Server Template REST interface.",
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.state.context = resolved_context
    
    # Add Host header middleware to handle proxied requests
    app.add_middleware(HostHeaderMiddleware, host=host, port=port)

    app.include_router(health_router)
    app.include_router(version_router)
    _mount_mcp_transport(app, resolved_context)
    return app


def _mount_mcp_transport(app: FastAPI, context: AppContext) -> None:
    """Mount the Streamable HTTP MCP transport when it is enabled."""
    transports = context.settings.server.transports
    if not transports.streamable_http_enabled:
        return
    try:
        context.mcp.mount(app)
    except Exception as exc:
        structlog.get_logger("enterprise_mcp.interfaces.rest").warning(
            "mcp_mount_failed", error=str(exc)
        )
