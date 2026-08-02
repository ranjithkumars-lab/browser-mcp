import typer

from browser_mcp.api.cli import app as api_app
from browser_mcp.mcp.cli import app as mcp_app
from browser_mcp.workers.cli import app as workers_app

app = typer.Typer(
    name="browser-mcp",
    help="Browser MCP Automation Platform",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)

app.add_typer(api_app, name="api", help="REST API Engine & UI Server commands.")
app.add_typer(mcp_app, name="mcp", help="MCP Server (Streamable HTTP) commands.")
app.add_typer(workers_app, name="worker", help="Distributed Worker Engine commands.")


def main() -> None:
    """Console script entry point."""
    app()
