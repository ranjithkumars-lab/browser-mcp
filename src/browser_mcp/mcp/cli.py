"""MCP Server (Streamable HTTP) entry points for the Browser MCP platform."""

from __future__ import annotations

from typing import Any

import typer
import uvicorn

app = typer.Typer(
    name="mcp",
    help="MCP Server commands (Streamable HTTP transport).",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host."),
    port: int = typer.Option(8000, help="Bind port."),
    reload: bool = typer.Option(False, help="Enable auto-reload (development)."),
) -> None:
    """Serve the Browser MCP server over Streamable HTTP.

    Builds the full browser context (engine, session manager and every MCP
    tool) and mounts it on the configured port via ``uvicorn --factory``.
    """
    uvicorn.run(
        "browser_mcp.mcp.cli:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        forwarded_allow_ips="*",
        proxy_headers=True,   # Trust proxy headers (including X-Forwarded-Host)
    )


def create_app() -> Any:
    """Factory for uvicorn: return the fully mounted browser MCP application."""
    from browser_mcp.app import create_browser_app

    return create_browser_app()
