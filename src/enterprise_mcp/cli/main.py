"""Typer-based CLI entry point."""

from __future__ import annotations

import typer

from enterprise_mcp.cli.commands import config, doctor, plugins, serve, version

app = typer.Typer(
    name="enterprise-mcp",
    help="Enterprise MCP Server Template - production-ready MCP server foundation.",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)

app.command(name="serve")(serve)
app.command(name="version")(version)
app.command(name="doctor")(doctor)
app.command(name="config")(config)
app.command(name="plugins")(plugins)


def main() -> None:
    """Console script entry point."""
    app()
