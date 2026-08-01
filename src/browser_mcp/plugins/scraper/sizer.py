"""Payload size handling — decides inline return vs artifact-file storage.

When a formatted result exceeds ``INLINE_THRESHOLD_BYTES`` it is written to the
scratch (artifact) directory and a metadata envelope (with ``artifact_path``)
is returned instead of the raw string.  This keeps MCP tool responses within
transport-friendly sizes while still making the full data available on disk.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from browser_mcp.plugins.scraper.models import ScrapeMeta, ScrapePayload

__all__ = [
    "DEFAULT_ARTIFACT_DIR",
    "INLINE_THRESHOLD_BYTES",
    "PayloadSizer",
]

INLINE_THRESHOLD_BYTES = 64 * 1024
DEFAULT_ARTIFACT_DIR = Path(tempfile.gettempdir()) / "browser-mcp" / "scraped-artifacts"


class PayloadSizer:
    """Manages the inline-vs-artifact decision for scrape output."""

    def __init__(
        self,
        *,
        inline_threshold: int = INLINE_THRESHOLD_BYTES,
        artifact_dir: Path | str | None = None,
    ) -> None:
        self._threshold = inline_threshold
        self._artifact_dir = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR

    @property
    def threshold(self) -> int:
        return self._threshold

    @property
    def artifact_dir(self) -> Path:
        return self._artifact_dir

    def decide(
        self,
        formatted: str,
        *,
        tool: str,
        meta_dict: dict[str, Any],
        output_format: str = "json",
        item_count: int = 0,
    ) -> ScrapePayload:
        """Return a :class:`ScrapePayload` choosing inline or artifact storage."""
        meta = ScrapeMeta(**meta_dict)
        size_bytes = len(formatted.encode("utf-8"))

        if size_bytes <= self._threshold:
            return ScrapePayload(
                tool=tool,
                meta=meta,
                format=output_format,
                inline_data=formatted,
                item_count=item_count,
            )

        self._artifact_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{tool}_"
            f"{meta_dict.get('page_id', 'unknown')}_"
            f"{tempfile._os.getpid()}_"  # type: ignore[attr-defined]
            f"{id(formatted)}.{output_format}"
        )
        filepath = self._artifact_dir / filename
        filepath.write_text(formatted, encoding="utf-8")

        return ScrapePayload(
            tool=tool,
            meta=meta,
            format=output_format,
            artifact_path=str(filepath),
            artifact_size=size_bytes,
            item_count=item_count,
            inline_data=None,
        )
