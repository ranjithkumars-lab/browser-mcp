"""Markdown formatter — serialises typed models to Markdown tables/text."""

from __future__ import annotations

from typing import Any, cast

from browser_mcp.plugins.scraper.formatters.base import BaseFormatter

__all__ = ["MarkdownFormatter"]


class MarkdownFormatter(BaseFormatter):
    """Format output as Markdown."""

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

        simple_rows: list[tuple[str, str]] = []
        nested: list[tuple[str, object]] = []
        for key, value in d.items():
            if isinstance(value, (dict, list)) and value:
                nested.append((str(key), cast(object, value)))
            else:
                simple_rows.append((str(key), _md_value(value)))

        lines: list[str] = []
        if simple_rows:
            lines.append("| Field | Value |")
            lines.append("|-------|-------|")
            for key, value in simple_rows:
                lines.append(f"| {key} | {_escape_table(value)} |")

        for key, value in nested:
            lines.append("")
            lines.append(f"**{key}**")
            if isinstance(value, list):
                lines.append(self._nested_list(cast(list[Any], value)))
            elif isinstance(value, dict):
                sub = MarkdownFormatter()
                lines.extend(sub._format_item(value))

        return lines

    def _nested_list(self, items: list[Any]) -> str:
        lines: list[str] = []
        for item in items:
            if isinstance(item, dict):
                d = cast(dict[str, Any], item)
                first_key = next(iter(d), "")
                first_val: Any = d.get(first_key) if first_key else ""
                lines.append(f"- {first_key}: {_md_value(first_val)}")
            else:
                lines.append(f"- {_md_value(item)}")
        return "\n".join(lines)


def _md_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
