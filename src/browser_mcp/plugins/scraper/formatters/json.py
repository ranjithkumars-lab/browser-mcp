"""JSON formatter — serialises typed models to JSON."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from browser_mcp.plugins.scraper.formatters.base import BaseFormatter

__all__ = ["JsonFormatter"]


class JsonFormatter(BaseFormatter):
    """Format output as indented JSON."""

    def format(self, data: list[Any]) -> str:
        return json.dumps(data, default=_default, indent=2, ensure_ascii=False)


def _default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    return str(obj)
