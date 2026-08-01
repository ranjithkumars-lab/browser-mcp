"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from enterprise_mcp.foundation.app import AppContext
from enterprise_mcp.interfaces.rest.routes import health_router, version_router

__all__ = ["create_app"]


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

    app = FastAPI(
        title=resolved_context.settings.server.name,
        version=resolved_context.settings.server.version,
        description="Enterprise MCP Server Template REST interface.",
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.state.context = resolved_context

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
