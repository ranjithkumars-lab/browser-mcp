"""Images collector — extracts ``<img>`` tag data with resolved URLs."""

from __future__ import annotations

from typing import Any

from browser_mcp.plugins.scraper.collectors.base import BaseCollector
from browser_mcp.plugins.scraper.urls import normalize_href

__all__ = ["ImagesCollector"]

_IMAGES_JS = """\
(selector) => {
  const imgs = selector ? document.querySelectorAll(selector) : document.querySelectorAll('img');
  return Array.from(imgs).map((img) => {
    const rect = img.getBoundingClientRect();
    return {
      src: img.getAttribute('src') || img.src || '',
      current_src: img.currentSrc || '',
      alt: img.getAttribute('alt') || img.alt || '',
      loading: img.loading || 'lazy',
      width: img.width || 0,
      height: img.height || 0,
      natural_width: img.naturalWidth || 0,
      natural_height: img.naturalHeight || 0,
      complete: img.complete,
      decoded: img.complete,
      is_decorative: (img.getAttribute('alt') || '') === ''
    };
  });
}
"""


class ImagesCollector(BaseCollector):
    """Collects ``<img>`` elements with resolved URLs and dimensions."""

    async def collect(
        self,
        page: Any,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        base_url: str | None = kwargs.get("base_url") or page.url
        selector: str | None = kwargs.get("selector")
        raw_images = await page.evaluate(_IMAGES_JS, selector if selector else None)

        results: list[dict[str, Any]] = []
        raw_images: list[dict[str, Any]] = await page.evaluate(_IMAGES_JS, selector if selector else None)
        for img in raw_images or []:
            src = str(img.get("src", ""))
            current_src = str(img.get("current_src") or "")
            resolved = normalize_href(src or current_src or "", base_url) or ""
            results.append({**img, "resolved_url": resolved})
        return results
