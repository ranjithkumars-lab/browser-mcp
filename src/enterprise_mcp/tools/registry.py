"""Tool runtime registry."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from enterprise_mcp.tools.decorators import get_tool_metadata
from enterprise_mcp.tools.metadata import ToolMetadata
from enterprise_mcp.utils.errors import ToolError

__all__ = ["ToolRegistry"]


class ToolRegistry:
    """Thread-safe registry of named, callable tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}
        self._metadata: dict[str, ToolMetadata] = {}

    def register(self, func: Callable[..., Any], metadata: ToolMetadata | None = None) -> None:
        """Register ``func`` under its tool metadata name.

        Metadata is taken from the ``@tool`` decorator when not provided.
        """
        resolved_metadata = metadata or get_tool_metadata(func)
        if resolved_metadata is None:
            raise ToolError(
                f"cannot register '{func.__name__}': no metadata found "
                "(decorate with @tool or pass metadata explicitly)"
            )
        if resolved_metadata.name in self._tools:
            raise ToolError(f"tool '{resolved_metadata.name}' is already registered")
        self._tools[resolved_metadata.name] = func
        self._metadata[resolved_metadata.name] = resolved_metadata

    def get(self, name: str) -> Callable[..., Any]:
        """Return the callable for ``name``."""
        func = self._tools.get(name)
        if func is None:
            raise ToolError(f"tool '{name}' is not registered")
        return func

    def metadata(self, name: str) -> ToolMetadata:
        """Return metadata for ``name``."""
        meta = self._metadata.get(name)
        if meta is None:
            raise ToolError(f"tool '{name}' is not registered")
        return meta

    def list(self) -> list[ToolMetadata]:
        """Return metadata for all registered tools."""
        return list(self._metadata.values())

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    async def call(self, tool_name: str, **arguments: Any) -> Any:
        """Invoke ``tool_name`` with validated ``arguments``."""
        func = self.get(tool_name)
        result = func(**arguments)
        if inspect.isawaitable(result):
            return await result
        return result
