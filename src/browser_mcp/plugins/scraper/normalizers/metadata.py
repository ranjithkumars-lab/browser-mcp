"""Metadata normaliser — raw dict → ``MetadataResult``."""

from __future__ import annotations

from typing import Any

from browser_mcp.plugins.scraper.models import MetadataResult, ScrapeMeta

__all__ = ["MetadataNormalizer"]


class MetadataNormalizer:
    """Normalises raw metadata-collector output into :class:`MetadataResult`."""

    def normalize(self, raw: dict[str, Any], meta: ScrapeMeta) -> MetadataResult:
        return MetadataResult(
            meta=meta,
            title=str(raw.get("title", "") or ""),
            description=raw.get("description") or None,
            keywords=raw.get("keywords") or None,
            og=dict(raw.get("og", {}) or {}),
            twitter=dict(raw.get("twitter", {}) or {}),
            other=dict(raw.get("other", {}) or {}),
        )
