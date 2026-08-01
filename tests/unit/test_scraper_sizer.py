"""Unit tests for the scraper PayloadSizer."""

from __future__ import annotations

import pytest

from browser_mcp.plugins.scraper.models import ScrapePayload
from browser_mcp.plugins.scraper.sizer import (
    DEFAULT_ARTIFACT_DIR,
    INLINE_THRESHOLD_BYTES,
    PayloadSizer,
)

pytestmark = pytest.mark.unit


class TestPayloadSizer:
    def test_defaults(self) -> None:
        sizer = PayloadSizer()
        assert sizer.threshold == INLINE_THRESHOLD_BYTES
        assert sizer.artifact_dir == DEFAULT_ARTIFACT_DIR

    def test_custom_threshold(self) -> None:
        sizer = PayloadSizer(inline_threshold=100)
        assert sizer.threshold == 100

    def test_custom_artifact_dir(self, tmp_path: object) -> None:
        sizer = PayloadSizer(artifact_dir=str(tmp_path))
        assert str(sizer.artifact_dir) == str(tmp_path)

    def test_inline_when_small(self) -> None:
        sizer = PayloadSizer(inline_threshold=1000)
        meta = {"session_id": "s1", "page_id": "p1", "url": "https://x.com", "title": "T"}
        payload = sizer.decide("small data", tool="text", meta_dict=meta)
        assert payload.inline_data == "small data"
        assert payload.artifact_path is None
        assert payload.artifact_size is None
        assert payload.item_count == 0
        assert isinstance(payload, ScrapePayload)

    def test_artifact_when_large(self, tmp_path: object) -> None:
        sizer = PayloadSizer(inline_threshold=10, artifact_dir=str(tmp_path))
        meta = {"session_id": "s1", "page_id": "p1", "url": "https://x.com", "title": "T"}
        large = "x" * 100
        payload = sizer.decide(large, tool="scrape.text", meta_dict=meta)
        assert payload.inline_data is None
        assert payload.artifact_path is not None
        assert payload.artifact_size == 100
        assert payload.format == "json"
        assert "scrape.text" in payload.artifact_path

    def test_artifact_file_written(self, tmp_path: object) -> None:
        import os

        sizer = PayloadSizer(inline_threshold=1, artifact_dir=str(tmp_path))
        meta = {"session_id": "s1", "page_id": "p1", "url": None, "title": None}
        payload = sizer.decide("data", tool="text", meta_dict=meta)
        assert payload.artifact_path is not None
        assert os.path.exists(payload.artifact_path)
        with open(payload.artifact_path, encoding="utf-8") as f:
            assert f.read() == "data"

    def test_inline_at_threshold_boundary(self) -> None:
        sizer = PayloadSizer(inline_threshold=5)
        meta = {"session_id": "s1", "page_id": "p1", "url": None, "title": None}
        payload = sizer.decide("abcde", tool="text", meta_dict=meta)
        assert payload.inline_data == "abcde"

    def test_artifact_just_above_threshold(self, tmp_path: object) -> None:
        sizer = PayloadSizer(inline_threshold=5, artifact_dir=str(tmp_path))
        meta = {"session_id": "s1", "page_id": "p1", "url": None, "title": None}
        payload = sizer.decide("abcdef", tool="text", meta_dict=meta)
        assert payload.inline_data is None
        assert payload.artifact_path is not None
