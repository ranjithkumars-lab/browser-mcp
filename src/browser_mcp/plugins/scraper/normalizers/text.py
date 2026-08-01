"""Text normaliser — raw dict → ``TextResult``."""

from __future__ import annotations

from typing import Any, cast

from browser_mcp.plugins.scraper.models import ScrapeMeta, TextResult

__all__ = ["TextNormalizer"]


class TextNormalizer:
    """Normalises raw text-collector output into :class:`TextResult`."""

    def normalize(self, raw: dict[str, Any], meta: ScrapeMeta) -> TextResult:
        """``raw`` is the dict returned by :class:`TextCollector`."""
        if "texts" in raw:
            raw_texts: object = raw.get("texts")
            texts: list[str] = (
                [str(x) for x in cast(list[object], raw_texts)]
                if isinstance(raw_texts, list)
                else []
            )
            joined = " ".join(texts).strip()
            words = joined.split() if joined else []
            raw_sel: object = raw.get("selectors_only")
            selectors_only: list[str] = (
                [str(x) for x in cast(list[object], raw_sel)] if isinstance(raw_sel, list) else []
            )
            return TextResult(
                meta=meta,
                text=joined,
                word_count=len(words),
                char_count=len(joined),
                selectors_only=selectors_only,
            )

        text = str(raw.get("text", ""))
        normalized = " ".join(text.split()) if text else ""
        return TextResult(
            meta=meta,
            text=normalized,
            word_count=len(normalized.split()) if normalized else 0,
            char_count=int(raw.get("char_count", len(normalized))),
        )
