"""Basic example: a minimal server exposing a single tool.

Run with:
    uv run enterprise-mcp serve --transport streamable-http
"""

from __future__ import annotations

from enterprise_mcp import __version__
from enterprise_mcp.config.loader import load_settings
from enterprise_mcp.foundation.app import AppContext
from enterprise_mcp.tools.decorators import tool


@tool(description="Say hello to someone.")
async def hello(name: str) -> str:
    """Return a friendly greeting."""
    return f"hello, {name}!"


def main() -> None:
    """Bootstrap the example application."""
    settings = load_settings(env="development")
    context = AppContext(settings=settings)
    context.tools.register(hello)
    print(
        "registered tools:",
        [metadata.name for metadata in context.tools.list()],
    )
    print(f"enterprise-mcp-server v{__version__} ready")


if __name__ == "__main__":
    main()
