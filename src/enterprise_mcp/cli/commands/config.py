"""``config`` command: inspect effective configuration."""

from __future__ import annotations

import typer

from enterprise_mcp.config.loader import load_settings

__all__ = ["config"]


def config(
    env: str | None = typer.Option(None, help="Environment name."),
) -> None:
    """Show the effective configuration as JSON."""
    settings = load_settings(env=env)
    typer.echo(settings.model_dump_json(indent=2))
