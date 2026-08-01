"""``plugins`` command: plugin management (scaffold).

The plugin framework is implemented in a later phase; this command currently
reports the registry state.
"""

from __future__ import annotations

import typer

from enterprise_mcp.extensions.registry import ExtensionRegistry

__all__ = ["plugins"]


def plugins() -> None:
    """List installed extensions and plugins (scaffold)."""
    registry = ExtensionRegistry()
    typer.echo(f"extensions registered: {len(registry.list())}")
    typer.echo("note: plugin framework implemented in a later phase")
