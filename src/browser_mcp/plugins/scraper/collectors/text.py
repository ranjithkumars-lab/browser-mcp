"""Text collector — extracts visible body text."""

from __future__ import annotations

from typing import Any

from browser_mcp.plugins.scraper.collectors.base import BaseCollector

__all__ = ["TextCollector"]

_TEXT_EVAL = """\
() => {
  const text = document.body.innerText || '';
  const words = text.trim().split(/\\s+/).filter(w => w.length > 0);
  return {
    text: text,
    word_count: words.length,
    char_count: text.length
  };
}
"""

_SELECTOR_TEXT_JS = """\
(sel) => {
  const nodes = document.querySelectorAll(sel);
  const texts = Array.from(nodes).map(n => (n.innerText || n.textContent || '').trim());
  return texts.filter(t => t.length > 0);
}
"""


class TextCollector(BaseCollector):
    """Collects visible text content from the page body."""

    async def collect(self, page: Any, **kwargs: Any) -> list[dict[str, Any]]:
        selector: str | None = kwargs.get("selector")
        if selector:
            texts = await page.evaluate(_SELECTOR_TEXT_JS, selector)
            return [{"texts": texts}]
        result = await page.evaluate(_TEXT_EVAL)
        return [result]
