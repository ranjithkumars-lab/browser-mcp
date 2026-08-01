"""YAML formatter (reserved scaffold).

Converts typed model instances to YAML.  Reserved for Phase 5+; currently
raises to signal the feature is not yet implemented.
"""

from __future__ import annotations

from typing import Any

from browser_mcp.errors import FormattingError
from browser_mcp.plugins.scraper.formatters.base import BaseFormatter

__all__ = ["YamlFormatter"]


class YamlFormatter(BaseFormatter):
    """Format output as YAML — reserved scaffold."""

    def format(self, data: list[Any]) -> str:
        raise FormattingError("YAML formatting is not yet implemented")
