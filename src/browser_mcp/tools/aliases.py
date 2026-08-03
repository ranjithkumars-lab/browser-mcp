"""Shared helpers for registering underscore-spaced tool aliases.

LLM clients frequently guess underscore tool names (matching lifecycle tools
like ``browser.list_frames``) instead of the dotted names used by grouped
toolkits (``browser.element.find``, ``browser.scrape.text``). Registering both
spellings keeps the agent loop working either way.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from enterprise_mcp.tools.decorators import get_tool_metadata
from enterprise_mcp.tools.metadata import ToolMetadata

__all__ = ["register_underscore_alias"]


def register_underscore_alias(
    registry: Any,
    method: Callable[..., Any],
    namespace: str,
    name: str,
) -> None:
    """Register an ``{namespace}_{name}`` alias for a dotted tool method."""
    metadata = get_tool_metadata(method)
    if metadata is None:
        return
    alias = ToolMetadata(
        name=f"{namespace}_{name}",
        description=(f"Alias for '{metadata.name}'. {metadata.description}"),
        parameters=metadata.parameters,
        returns=metadata.returns,
        version=metadata.version,
    )
    registry.register(method, metadata=alias)
