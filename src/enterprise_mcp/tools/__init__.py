"""Tool abstraction layer.

Tools are the unit of capability exposed over MCP. This package provides
metadata models, a decorator-based registration API, a runtime registry,
and an input validator.
"""

from enterprise_mcp.tools.decorators import tool
from enterprise_mcp.tools.metadata import ToolMetadata, ToolParameter
from enterprise_mcp.tools.registry import ToolRegistry
from enterprise_mcp.tools.validator import validate_input

__all__ = [
    "ToolMetadata",
    "ToolParameter",
    "ToolRegistry",
    "tool",
    "validate_input",
]
