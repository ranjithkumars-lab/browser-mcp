"""Formatter package — converts typed models to serialised output.

Each formatter consumes a list of normalised model instances and returns a
string in the requested format.  ``json`` is the default and always available;
``csv``, ``markdown`` and ``html`` are also implemented. ``xml`` and ``yaml``
are reserved scaffolds.
"""

from __future__ import annotations

from browser_mcp.plugins.scraper.formatters.base import BaseFormatter
from browser_mcp.plugins.scraper.formatters.csv import CsvFormatter
from browser_mcp.plugins.scraper.formatters.html import HtmlFormatter
from browser_mcp.plugins.scraper.formatters.json import JsonFormatter
from browser_mcp.plugins.scraper.formatters.markdown import MarkdownFormatter

__all__ = [
    "BaseFormatter",
    "CsvFormatter",
    "HtmlFormatter",
    "JsonFormatter",
    "MarkdownFormatter",
]

FORMATTERS: dict[str, type[BaseFormatter]] = {
    "json": JsonFormatter,
    "csv": CsvFormatter,
    "markdown": MarkdownFormatter,
    "html": HtmlFormatter,
}


def get_formatter(output_format: str) -> BaseFormatter:
    """Return a formatter instance for ``output_format``."""
    cls = FORMATTERS.get(output_format.lower())
    if cls is None:
        from browser_mcp.errors import FormattingError

        raise FormattingError(f"unsupported output format: '{output_format}' (not yet implemented)")
    return cls()
