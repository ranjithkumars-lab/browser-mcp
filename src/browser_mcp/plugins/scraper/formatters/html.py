"""HTML formatter — serialises typed models to a basic HTML table/structure."""

from __future__ import annotations

from typing import Any, cast
from xml.sax.saxutils import escape

from browser_mcp.plugins.scraper.formatters.base import BaseFormatter

__all__ = ["HtmlFormatter"]


class HtmlFormatter(BaseFormatter):
    """Format output as minimal HTML."""

    def format(self, data: list[Any]) -> str:
        style = (
            "table{border-collapse:collapse;margin:1em 0}"
            "td,th{border:1px solid #999;padding:4px 8px}"
        )
        parts: list[str] = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            '<head><meta charset="utf-8">',
            f"<style>{style}</style>",
            "</head>",
            "<body>",
        ]
        for item in data:
            parts.extend(self._format_item(item))
        parts.append("</body></html>")
        return "\n".join(parts)

    def _format_item(self, item: Any) -> list[str]:
        if hasattr(item, "model_dump"):
            d = cast(dict[str, Any], item.model_dump(mode="json"))
        elif isinstance(item, dict):
            d = cast(dict[str, Any], item)
        else:
            return [f"<p>{escape(str(item))}</p>"]

        rows: list[str] = []
        for key, value in d.items():
            if isinstance(value, (dict, list)) and value:
                rows.append(
                    f"<tr><th>{escape(str(key))}</th><td>{self._nested(value)}</td></tr>"
                )
            else:
                rows.append(
                    f"<tr><th>{escape(str(key))}</th><td>"
                    f"{escape(_html_value(value))}</td></tr>"
                )

        return ["<table>", *rows, "</table>"]

    def _nested(self, value: Any) -> str:
        if isinstance(value, list):
            inner: list[str] = []
            for sub in cast(list[object], value):
                inner.extend(self._format_item(sub))
            return "<div>" + "".join(inner) + "</div>"
        if isinstance(value, dict):
            d = cast(dict[str, Any], value)
            inner: list[str] = []
            for key, val in d.items():
                if isinstance(val, (dict, list)) and val:
                    inner.append(
                        f"<p><strong>{escape(str(key))}</strong>: "
                        f"{self._nested(val)}</p>"
                    )
                else:
                    inner.append(
                        f"<p><strong>{escape(str(key))}</strong>: "
                        f"{escape(_html_value(val))}</p>"
                    )
            return "".join(inner)
        return escape(str(value))


def _html_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
