"""Images normaliser — raw dict → ``ImageResult``."""

from __future__ import annotations

from typing import Any

from browser_mcp.plugins.scraper.models import ImageResult, ScrapeMeta

__all__ = ["ImagesNormalizer"]


class ImagesNormalizer:
    """Normalises raw image-collector output into :class:`ImageResult`."""

    def normalize(self, raw: dict[str, Any], meta: ScrapeMeta) -> ImageResult:
        return ImageResult(
            meta=meta,
            src=str(raw.get("src", "")),
            resolved_url=str(raw.get("resolved_url", raw.get("src", ""))),
            alt=raw.get("alt") or None,
            loading=raw.get("loading") or None,
            width=_to_int(raw.get("width")),
            height=_to_int(raw.get("height")),
            natural_width=_to_int(raw.get("natural_width")),
            natural_height=_to_int(raw.get("natural_height")),
            complete=bool(raw.get("complete", True)),
            is_decorative=bool(raw.get("is_decorative", False)),
        )


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
