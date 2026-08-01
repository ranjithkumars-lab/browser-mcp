"""JSON-LD normaliser — raw dict → ``JsonLdResult``."""

from __future__ import annotations

from typing import Any

from browser_mcp.plugins.scraper.models import JsonLdResult, ScrapeMeta

__all__ = ["JsonLdNormalizer"]


class JsonLdNormalizer:
    """Normalises raw JSON-LD-collector output into :class:`JsonLdResult`."""

    def normalize(self, raw: dict[str, Any], meta: ScrapeMeta) -> JsonLdResult:
        return JsonLdResult(
            meta=meta,
            raw=str(raw.get("raw", "")),
            data=dict(raw.get("data", {}) or {}),
            type=raw.get("type"),
        )
