"""Links collector — extracts ``<a>`` tags with strict URL normalisation."""

from __future__ import annotations

from typing import Any

from browser_mcp.plugins.scraper.collectors.base import BaseCollector
from browser_mcp.plugins.scraper.urls import is_anchor_link, is_internal, normalize_href

__all__ = ["LinksCollector"]

_LINKS_JS = """\
(selector) => {
  const sel = selector || 'a[href]';
  const links = document.querySelectorAll(sel);
  return Array.from(links).map(a => {
    return {
      href: a.href || a.getAttribute('href') || '',
      text: (a.innerText || a.textContent || '').trim(),
      rel: a.getAttribute('rel') || ''
    };
  });
}
"""


class LinksCollector(BaseCollector):
    """Collects ``<a>`` elements with normalised, de-duplicated URLs."""

    async def collect(
        self,
        page: Any,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        base_url: str | None = kwargs.get("base_url") or page.url
        selector: str | None = kwargs.get("selector")
        raw_links: list[dict[str, Any]] = await page.evaluate(
            _LINKS_JS, selector if selector else None
        )

        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for link in raw_links or []:
            raw_href = link["href"]
            is_pure_anchor = raw_href.strip().startswith("#")
            resolved = normalize_href(raw_href, base_url)
            if resolved is None and is_pure_anchor and base_url:
                resolved = base_url.rstrip("/") + raw_href.strip()
            if resolved is None:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            internal = is_internal(resolved, base_url)
            anchor = is_anchor_link(resolved, base_url) or is_pure_anchor
            results.append(
                {
                    **link,
                    "resolved_url": resolved,
                    "is_internal": internal,
                    "is_anchor": anchor,
                    "link_type": self._classify(resolved, internal, anchor),
                }
            )
        return results

    @staticmethod
    def _classify(resolved: str, internal: bool | None, anchor: bool | None) -> str:
        if anchor:
            return "anchor"
        if internal:
            return "internal"
        from urllib.parse import urlparse

        if urlparse(resolved).scheme in ("http", "https"):
            return "external"
        return "other"
