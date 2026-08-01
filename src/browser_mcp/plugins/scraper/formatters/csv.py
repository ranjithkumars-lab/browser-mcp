"""CSV formatter — serialises table-like and link/image data to CSV."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, cast

from browser_mcp.plugins.scraper.formatters.base import BaseFormatter

__all__ = ["CsvFormatter"]


class CsvFormatter(BaseFormatter):
    """Format output as CSV."""

    def format(self, data: list[Any]) -> str:
        rows: list[list[str]] = []
        for item in data:
            if hasattr(item, "model_dump"):
                d = cast(dict[str, Any], item.model_dump(mode="json"))
            elif isinstance(item, dict):
                d = cast(dict[str, Any], item)
            else:
                d = {"value": str(item)}
            rows.append(self._to_row(d))

        if not rows:
            return ""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        for row in rows:
            writer.writerow(row)
        return output.getvalue()

    @staticmethod
    def _to_row(data: dict[str, Any]) -> list[str]:
        return [_stringify(v) for v in data.values()]


def _stringify(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return str(value)
