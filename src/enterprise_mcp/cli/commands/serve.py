"""``serve`` command: run the MCP server over the configured transport."""

from __future__ import annotations

import asyncio

import structlog
import typer

from enterprise_mcp.config.loader import load_settings
from enterprise_mcp.foundation.app import AppContext

__all__ = ["serve"]


def serve(
    host: str | None = typer.Option(None, help="Bind host (overrides config)."),
    port: int | None = typer.Option(None, help="Bind port (overrides config)."),
    env: str | None = typer.Option(None, help="Environment name."),
    transport: str | None = typer.Option(None, help="Transport: streamable-http, sse, stdio."),
    reload: bool = typer.Option(False, help="Enable auto-reload (development)."),
) -> None:
    """Start the Enterprise MCP server."""
    settings = load_settings(
        env=env,
        overrides=_overrides(host, port, transport),
    )
    context = AppContext(settings)
    logger = structlog.get_logger("enterprise_mcp.cli")

    resolved_transport = transport or settings.server.transports.default
    logger.info(
        "starting_server",
        host=host or settings.server.transports.host,
        port=port or settings.server.transports.port,
        transport=resolved_transport,
        environment=settings.server.environment.value,
    )

    if resolved_transport == "stdio":
        _run_stdio(context)
        return

    _run_http(context, host, port, reload)


def _overrides(
    host: str | None,
    port: int | None,
    transport: str | None,
) -> dict[str, object]:
    overrides: dict[str, object] = {}
    if host:
        overrides["transports"] = {"host": host}
    if port:
        overrides["transports"] = {"port": port}
    if transport:
        overrides["transports"] = {"default": transport}
    return overrides


def _run_http(context: AppContext, host: str | None, port: int | None, reload: bool) -> None:
    import uvicorn

    uvicorn.run(
        "enterprise_mcp.interfaces.rest.app:create_app",
        factory=True,
        host=host or context.settings.server.transports.host,
        port=port or context.settings.server.transports.port,
        reload=reload,
    )


def _run_stdio(context: AppContext) -> None:
    asyncio.run(_stdio_async(context))


async def _stdio_async(context: AppContext) -> None:
    from enterprise_mcp.transport.stdio import StdioTransport

    await context.start()
    transport = StdioTransport()
    await transport.start()
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        await transport.stop()
        await context.stop()
