"""``version`` command."""

from __future__ import annotations

import sys

import typer

from enterprise_mcp.utils.version import get_version

__all__ = ["version"]


def version() -> None:
    """Print version information."""
    typer.echo(f"enterprise-mcp-server {get_version()}")
    typer.echo(f"python {sys.version.split()[0]}")
