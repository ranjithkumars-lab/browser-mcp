"""JSON-LD collector — extracts and parses ``application/ld+json`` blocks."""

from __future__ import annotations

import json
from typing import Any, cast

from browser_mcp.plugins.scraper.collectors.base import BaseCollector

__all__ = ["JsonLdCollector"]

_JSONLD_JS = """\
() => {
  const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
  return scripts.map(s => s.textContent.trim()).filter(t => t.length > 0);
}
"""


class JsonLdCollector(BaseCollector):
    """Collects ``application/ld+json`` script blocks and parses them."""

    async def collect(self, page: Any, **kwargs: Any) -> list[dict[str, Any]]:
        raw_blocks: list[str] = await page.evaluate(_JSONLD_JS) or []
        results: list[dict[str, Any]] = []
        for raw in raw_blocks:
            try:
                data: Any = json.loads(raw)
            except (json.JSONDecodeError, TypeError) as exc:
                results.append({"raw": raw, "data": {}, "type": None, "_parse_error": str(exc)})
                continue
            ld_type = self._extract_type(data)
            results.append({"raw": raw, "data": data, "type": ld_type})
        return results

    @staticmethod
    def _extract_type(data: Any) -> str | None:
        if not isinstance(data, dict):
            return None
        d = cast(dict[str, Any], data)
        t = d.get("@type")
        if isinstance(t, str):
            return t
        if isinstance(t, list):
            t_list = cast(list[object], t)
            if t_list:
                first = t_list[0]
                if isinstance(first, str):
                    return first
        return None
