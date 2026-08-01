"""Links normaliser — raw dict → ``LinkResult``."""

from __future__ import annotations

from typing import Any

from browser_mcp.plugins.scraper.models import LinkResult, ScrapeMeta

__all__ = ["LinksNormalizer"]

_VALID_LINK_TYPES = frozenset({"internal", "external", "anchor", "other"})


class LinksNormalizer:
    """Normalises raw links-collector output into :class:`LinkResult`."""

    def normalize(self, raw: dict[str, Any], meta: ScrapeMeta) -> LinkResult:
        resolved = raw.get("resolved_url") or raw.get("href", "")
        link_type = raw.get("link_type", "other")
        return LinkResult(
            meta=meta,
            href=str(raw.get("href", "")),
            resolved_url=str(resolved),
            text=str(raw.get("text", "")),
            rel=raw.get("rel") or None,
            is_internal=raw.get("is_internal"),
            is_anchor=raw.get("is_anchor"),
            link_type=link_type if link_type in _VALID_LINK_TYPES else "other",  # type: ignore[arg-type]
        )
