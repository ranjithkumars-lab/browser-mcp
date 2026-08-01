"""Table collector — extracts structured ``<table>`` data."""

from __future__ import annotations

from typing import Any

from browser_mcp.plugins.scraper.collectors.base import BaseCollector

__all__ = ["TableCollector"]

_TABLE_JS = """\
() => {
  const tables = Array.from(document.querySelectorAll('table'));
  return tables.map((table, idx) => {
    const captionEl = table.querySelector('caption');
    const caption = captionEl ? captionEl.innerText.trim() : '';
    const rows = Array.from(table.querySelectorAll('tr')).map(tr => {
      const cells = Array.from(tr.querySelectorAll('th, td')).map(cell => {
        const tag = cell.tagName.toLowerCase();
        return {
          value: (cell.innerText || cell.textContent || '').trim(),
          is_header: tag === 'th',
          col_span: parseInt(cell.getAttribute('colspan') || '1', 10) || 1,
          row_span: parseInt(cell.getAttribute('rowspan') || '1', 10) || 1
        };
      });
      return { cells: cells };
    });
    return {
      index: idx,
      caption: caption,
      rows: rows
    };
  });
  return tables;
}
"""

_TABLE_BY_SELECTOR_JS = """\
(sel) => {
  const table = document.querySelector(sel);
  if (!table) return [];
  const captionEl = table.querySelector('caption');
  const caption = captionEl ? captionEl.innerText.trim() : '';
  const rows = Array.from(table.querySelectorAll('tr')).map(tr => {
    const cells = Array.from(tr.querySelectorAll('th, td')).map(cell => {
      const tag = cell.tagName.toLowerCase();
      return {
        value: (cell.innerText || cell.textContent || '').trim(),
        is_header: tag === 'th',
        col_span: parseInt(cell.getAttribute('colspan') || '1', 10) || 1,
        row_span: parseInt(cell.getAttribute('rowspan') || '1', 10) || 1
      };
    });
    return { cells: cells };
  });
  return [{ index: 0, caption: caption, rows: rows }];
}
"""


class TableCollector(BaseCollector):
    """Collects all ``<table>`` elements (or a single table by selector)."""

    async def collect(self, page: Any, **kwargs: Any) -> list[dict[str, Any]]:
        selector: str | None = kwargs.get("selector")
        if selector:
            result = await page.evaluate(_TABLE_BY_SELECTOR_JS, selector)
        else:
            result = await page.evaluate(_TABLE_JS)
        return result
