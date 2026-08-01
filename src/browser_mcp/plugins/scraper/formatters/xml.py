"""XML formatter (reserved scaffold).

Converts typed model instances to a minimal XML representation.  Reserved
for Phase 5+; currently raises to signal the feature is not yet implemented.
"""

from __future__ import annotations

from typing import Any

from browser_mcp.errors import FormattingError
from browser_mcp.plugins.scraper.formatters.base import BaseFormatter

__all__ = ["XmlFormatter"]


class XmlFormatter(BaseFormatter):
    """Format output as XML — reserved scaffold."""

    def format(self, data: list[Any]) -> str:
        raise FormattingError("XML formatting is not yet implemented")
