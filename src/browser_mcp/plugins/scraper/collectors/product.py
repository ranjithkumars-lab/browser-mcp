"""Composite product collector.

Implements the priority chain described in the architecture document:

    JSON-LD -> Open Graph -> Microdata -> DOM heuristics -> Meta tags

The first signal that yields a non-empty product candidate wins.  The collector
returns a *single* raw dict (not a list) representing the best product found.
"""

from __future__ import annotations

from typing import Any

from browser_mcp.plugins.scraper.collectors.base import BaseCollector

__all__ = ["ProductCollector"]

_JSONLD_PRODUCT_JS = """\
(selector) => {
  const scripts = document.querySelectorAll('script[type="application/ld+json"]');
  for (const s of scripts) {
    try {
      const data = JSON.parse(s.textContent.trim());
      const candidates = (data['@graph'] || [data]).map(d => d).flat();
      for (const item of candidates) {
        if (!item || typeof item !== 'object') continue;
        const t = item['@type'] || '';
        const types = Array.isArray(t) ? t : [t];
        if (types.some(ty => String(ty).toLowerCase().includes('product'))) {
          return item;
        }
      }
    } catch (e) { /* skip malformed */ }
  }
  return null;
}
"""

_OG_PRODUCT_JS = """\
() => {
  const og = {};
  document.querySelectorAll('meta[property^="og:"], meta[name^="og:"]').forEach(m => {
    const prop = m.getAttribute('property') || m.getAttribute('name') || '';
    og[prop] = m.getAttribute('content') || '';
  });
  if (!og['og:type'] || og['og:type'].toLowerCase() !== 'product') return null;
  return og;
}
"""

_MICRODATA_PRODUCT_JS = """\
() => {
  const items = document.querySelectorAll('[itemtype*="product" i]');
  if (items.length === 0) return null;
  const el = items[0];
  const result = {};
  el.querySelectorAll('[itemprop]').forEach(prop => {
    const attr = prop.getAttribute('itemprop');
    const val = (prop.innerText || prop.textContent ||
      prop.getAttribute('content') || '').trim();
    result[attr] = val;
  });
  return Object.keys(result).length > 0 ? result : null;
}
"""

_DOM_PRODUCT_JS = """\
() => {
  const selectors = [
    '.product-title, .product_name, [data-testid="product-title"]',
    '.price, .product-price, [data-testid="price"]',
    '[data-testid="product"]',
    '.product-item'
  ];
  const found = selectors.some(sel => document.querySelector(sel));
  if (!found) return null;

  const titleSel = '.product-title, .product_name, h1[itemprop="name"], h1';
  const priceSel = '.price, .product-price, [data-testid="price"], [itemprop="price"]';
  const descSel = '.description, .product-description, [itemprop="description"]';
  const imgSel = '.product-image img, [data-testid="product-image"] img, img[itemprop="image"]';
  const titleEl = document.querySelector(titleSel);
  const priceEl = document.querySelector(priceSel);
  const descEl = document.querySelector(descSel);
  const imageEl = document.querySelector(imgSel);

  const result = {};
  if (titleEl) result.name = (titleEl.innerText || '').trim();
  if (priceEl) {
    const priceText = (priceEl.innerText || priceEl.getAttribute('content') || '').trim();
    const numeric = parseFloat(priceText.replace(/[^0-9.]/g, ''));
    if (!isNaN(numeric)) result.price = numeric;
    result.price_text = priceText;
  }
  if (descEl) result.description = (descEl.innerText || '').trim();
  if (imageEl) {
    const imgSrc = imageEl.getAttribute('src') || imageEl.getAttribute('data-src') || '';
    result.image = imgSrc;
  }
  return Object.keys(result).length > 0 ? result : null;
}
"""

_META_PRODUCT_JS = """\
() => {
  const result = {};
  const keywords = ['product', 'price', 'currency', 'description'];
  document.querySelectorAll('meta[name], meta[property]').forEach(m => {
    const key = m.getAttribute('name') || m.getAttribute('property') || '';
    const val = m.getAttribute('content') || '';
    if (!val) return;
    const lc = key.toLowerCase();
    if (keywords.some(kw => lc.includes(kw))) {
      result[lc] = val;
    }
  });
  return Object.keys(result).length > 0 ? result : null;
}
"""


class ProductCollector(BaseCollector):
    """Composite collector extracting product data from multiple DOM signals."""

    PRIORITY: tuple[str, ...] = ("jsonld", "opengraph", "microdata", "dom", "meta")

    def __init__(self) -> None:
        self._js_map: dict[str, str] = {
            "jsonld": _JSONLD_PRODUCT_JS,
            "opengraph": _OG_PRODUCT_JS,
            "microdata": _MICRODATA_PRODUCT_JS,
            "dom": _DOM_PRODUCT_JS,
            "meta": _META_PRODUCT_JS,
        }

    async def collect(self, page: Any, **kwargs: Any) -> list[dict[str, Any]]:
        base_url: str | None = kwargs.get("base_url") or page.url
        source_used: str | None = None
        raw_product: dict[str, Any] | None = None

        for name in self.PRIORITY:
            js = self._js_map[name]
            try:
                result = await page.evaluate(js)
            except Exception:  # noqa: S112
                continue
            if result:
                raw_product = result
                source_used = name
                break

        if raw_product is None:
            return []

        return [self._normalize_raw(raw_product, source_used or "unknown", base_url)]

    def _normalize_raw(
        self,
        raw: dict[str, Any],
        source: str,
        base_url: str | None,
    ) -> dict[str, Any]:
        return {
            "raw": raw,
            "source": source,
            "base_url": base_url,
        }
