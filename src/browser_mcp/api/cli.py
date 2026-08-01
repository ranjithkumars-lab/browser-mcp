from __future__ import annotations

import typer
import uvicorn
from typing import Any

app = typer.Typer(
    help="REST API Engine commands",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)

@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind host."),
    port: int = typer.Option(8080, help="Bind port."),
    reload: bool = typer.Option(False, help="Enable auto-reload (development)."),
) -> None:
    """Start the Browser MCP REST API and Control Center UI."""
    uvicorn.run(
        "browser_mcp.api.cli:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )

def create_app() -> Any:
    """Factory for uvicorn to run the API."""
    from browser_mcp.api.app import create_api_app
    from enterprise_mcp.foundation.app import AppContext
    
    # We use AppContext to inject dependencies just like the main enterprise server.
    context = AppContext()
    # The API configuration is handled within create_api_app
    return create_api_app(context, None)
