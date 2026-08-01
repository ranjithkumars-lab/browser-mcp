"""Decorator-based tool registration."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, TypeVar, get_type_hints

from enterprise_mcp.tools.metadata import ToolMetadata, ToolParameter

F = TypeVar("F", bound=Callable[..., Any])

__all__ = ["TOOL_ATTR", "get_tool_metadata", "tool"]

TOOL_ATTR = "_enterprise_mcp_tool_metadata"


def tool(  # noqa: UP047 - PEP 695 syntax deferred for clarity of the dual usage pattern
    _func: F | None = None,
    *,
    name: str | None = None,
    description: str = "",
    returns: str = "json",
    version: str = "1.0.0",
) -> F | Callable[[F], F]:
    """Decorate a callable to register it as a tool.

    Usable with or without parentheses:

        @tool
        def greet(name: str) -> str: ...

        @tool(description="Sum two integers")
        def add(a: int, b: int) -> int: ...
    """

    def decorator(func: F) -> F:
        metadata = _build_metadata(func, name, description, returns, version)
        setattr(func, TOOL_ATTR, metadata)
        return func

    if _func is not None:
        return decorator(_func)
    return decorator


def get_tool_metadata(func: Callable[..., Any]) -> ToolMetadata | None:
    """Return tool metadata attached to ``func``, or ``None``."""
    metadata = getattr(func, TOOL_ATTR, None)
    return metadata if isinstance(metadata, ToolMetadata) else None


def _build_metadata(
    func: Callable[..., Any],
    name: str | None,
    description: str,
    returns: str,
    version: str,
) -> ToolMetadata:
    resolved_name = name or func.__name__
    resolved_description = description or (func.__doc__ or "").strip() or "No description provided."
    parameters = _parameters_from_signature(func)
    return ToolMetadata(
        name=resolved_name,
        description=resolved_description,
        parameters=parameters,
        returns=returns,
        version=version,
    )


def _parameters_from_signature(func: Callable[..., Any]) -> list[ToolParameter]:
    signature = inspect.signature(func)
    hints = get_type_hints(func)
    parameters: list[ToolParameter] = []
    for parameter in signature.parameters.values():
        if parameter.name in ("self", "cls"):
            continue
        annotation = hints.get(parameter.name)
        type_name = _annotation_name(annotation)
        has_default = parameter.default is not inspect.Parameter.empty
        parameters.append(
            ToolParameter(
                name=parameter.name,
                type=type_name,
                required=not has_default,
                default=None if not has_default else parameter.default,
            )
        )
    return parameters


def _annotation_name(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty or annotation is None:
        return "any"
    origin = getattr(annotation, "__origin__", None)
    if origin is not None:
        return getattr(origin, "__name__", str(origin))
    name = getattr(annotation, "__name__", None)
    return name if isinstance(name, str) else str(annotation)
