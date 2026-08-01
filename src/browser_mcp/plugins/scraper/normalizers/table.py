"""Table normaliser — raw dict → ``TableResult``."""

from __future__ import annotations

from typing import Any, cast

from browser_mcp.plugins.scraper.models import ScrapeMeta, TableCell, TableResult, TableRow

__all__ = ["TableNormalizer"]


class TableNormalizer:
    """Normalises raw table-collector output into :class:`TableResult`."""

    def normalize(self, raw: dict[str, Any], meta: ScrapeMeta) -> TableResult:
        raw_rows: list[dict[str, Any]] = raw.get("rows", []) or []
        rows: list[TableRow] = []
        headers_set: set[str] = set()

        for raw_row in raw_rows:
            cells: list[TableCell] = []
            raw_cells: list[dict[str, Any]] = raw_row.get("cells", []) or []
            for raw_cell in raw_cells:
                cell = TableCell(
                    value=str(raw_cell.get("value", "")),
                    is_header=bool(raw_cell.get("is_header", False)),
                    col_span=int(raw_cell.get("col_span", 1)),
                    row_span=int(raw_cell.get("row_span", 1)),
                )
                if cell.is_header:
                    headers_set.add(cell.value)
                cells.append(cell)
            rows.append(TableRow(cells=cells))

        header_cells: list[dict[str, Any]] = (
            cast(list[dict[str, Any]], raw_rows[0].get("cells", [])) if raw_rows else []
        )
        th_cells = [c for c in header_cells if c.get("is_header")] if header_cells else []
        if not headers_set and th_cells:
            headers = [str(c.get("value", "")) for c in th_cells]
        elif not headers_set and rows:
            headers = [c.value for c in rows[0].cells if c.value]
        else:
            headers = sorted(headers_set)

        body_rows = rows[1:] if raw_rows and th_cells else rows
        non_empty_rows = [r for r in body_rows if any(c.value for c in r.cells)]

        col_count = max((len(r.cells) for r in non_empty_rows), default=0)

        return TableResult(
            meta=meta,
            index=int(raw.get("index", 0)),
            caption=raw.get("caption") or None,
            headers=headers,
            rows=non_empty_rows,
            row_count=len(non_empty_rows),
            col_count=col_count,
        )
