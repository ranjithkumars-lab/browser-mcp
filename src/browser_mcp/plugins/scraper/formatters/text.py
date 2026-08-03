"""Plain-text formatter — serialises typed models to readable key/value rows."""

from __future__ import annotations

import json
from typing import Any, cast

from browser_mcp.plugins.scraper.formatters.base import BaseFormatter

__all__ = ["TextFormatter"]


class TextFormatter(BaseFormatter):
    """Format output as plain text (key: value lines)."""

    def format(self, data: list[Any]) -> str:
        lines: list[str] = []
        for index, item in enumerate(data):
            if index > 0:
                lines.append("")
            lines.extend(self._format_item(item))
        return "\n".join(lines)

    def _format_item(self, item: Any) -> list[str]:
        if hasattr(item, "model_dump"):
            d = cast(dict[str, Any], item.model_dump(mode="json"))
        elif isinstance(item, dict):
            d = cast(dict[str, Any], item)
        else:
            return [str(item)]

        lines: list[str] = []
        for key, value in d.items():
            lines.append(f"{key}: {_text_value(value)}")
        return lines


def _text_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
