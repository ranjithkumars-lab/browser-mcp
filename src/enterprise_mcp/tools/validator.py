"""Tool input validation."""

from __future__ import annotations

from typing import Any

from enterprise_mcp.tools.metadata import ToolMetadata
from enterprise_mcp.utils.errors import ToolError

__all__ = ["validate_input"]


def validate_input(metadata: ToolMetadata, arguments: dict[str, Any]) -> None:
    """Validate ``arguments`` against ``metadata``.

    Checks that all required parameters are present and no unknown parameters
    are supplied.
    """
    allowed = {parameter.name for parameter in metadata.parameters}
    unknown = set(arguments) - allowed
    if unknown:
        raise ToolError(f"tool '{metadata.name}' received unknown parameter(s): {sorted(unknown)}")

    for parameter in metadata.parameters:
        if parameter.required and parameter.name not in arguments:
            raise ToolError(
                f"tool '{metadata.name}' is missing required parameter '{parameter.name}'"
            )
