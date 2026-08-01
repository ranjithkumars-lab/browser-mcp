"""Metadata collector — extracts ``<title>``, ``<meta>``, OpenGraph, Twitter cards."""

from __future__ import annotations

from typing import Any

from browser_mcp.plugins.scraper.collectors.base import BaseCollector

__all__ = ["MetadataCollector"]

_METADATA_JS = """\
() => {
  const meta = {};
  const og = {};
  const twitter = {};
  const other = {};

  const titleEl = document.querySelector('title');
  const title = titleEl ? titleEl.innerText.trim() : '';

  document.querySelectorAll('meta').forEach(m => {
    const name = m.getAttribute('name') || m.getAttribute('property') || '';
    const content = m.getAttribute('content') || '';
    if (!name) return;

    if (name === 'description') {
      meta['description'] = content;
    } else if (name === 'keywords') {
      meta['keywords'] = content;
    } else if (name.startsWith('og:')) {
      og[name] = content;
    } else if (name.startsWith('twitter:')) {
      twitter[name] = content;
    } else {
      other[name] = content;
    }
    meta[name] = content;
  });

  return {
    title: title,
    description: meta['description'] || '',
    keywords: meta['keywords'] || '',
    og: og,
    twitter: twitter,
    other: other
  };
}
"""


class MetadataCollector(BaseCollector):
    """Collects page-level metadata from ``<meta>``, ``<title>``, OG and Twitter tags."""

    async def collect(self, page: Any, **kwargs: Any) -> list[dict[str, Any]]:
        result = await page.evaluate(_METADATA_JS)
        return [result]
