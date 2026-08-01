from __future__ import annotations

import typer

app = typer.Typer(no_args_is_help=True)


@app.command()
def version() -> None:
    typer.echo("browser-mcp")


@app.command()
def transports() -> None:
    typer.echo("stdio, streamable_http, sse")


@app.command()
def serve() -> None:
    typer.echo("Use browser_mcp.server.mcp.BrowserMCPServer from your host process.")
