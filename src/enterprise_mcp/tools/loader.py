"""Automatic tool discovery and loading."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from types import ModuleType

import structlog

from enterprise_mcp.tools.decorators import get_tool_metadata
from enterprise_mcp.tools.registry import ToolRegistry

__all__ = ["discover_tools"]

_logger = structlog.get_logger("enterprise_mcp.tools.loader")


def discover_tools(
    package: str | ModuleType,
    registry: ToolRegistry,
    *,
    recursive: bool = True,
) -> int:
    """Discover ``@tool``-decorated callables inside ``package``.

    Returns the number of tools registered.
    """
    module = importlib.import_module(package) if isinstance(package, str) else package
    count = 0
    for module_info in pkgutil.walk_packages(module.__path__, module.__name__ + "."):
        if not recursive:
            break
        try:
            submodule = importlib.import_module(module_info.name)
        except Exception as exc:
            _logger.warning("tool_module_import_failed", module=module_info.name, error=str(exc))
            continue
        count += _scan_module(submodule, registry)
    count += _scan_module(module, registry)
    return count


def _scan_module(module: ModuleType, registry: ToolRegistry) -> int:
    count = 0
    for _, member in inspect.getmembers(module, inspect.isfunction):
        metadata = get_tool_metadata(member)
        if metadata is None:
            continue
        registry.register(member, metadata)
        count += 1
    return count
