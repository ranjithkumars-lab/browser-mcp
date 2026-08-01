"""Unit tests for scraper URL utilities."""

from __future__ import annotations

import pytest

from browser_mcp.plugins.scraper.urls import (
    BLOCKED_SCHEMES,
    is_anchor_link,
    is_internal,
    normalize_href,
)

pytestmark = pytest.mark.unit


class TestNormalizeHref:
    def test_relative_url_resolved(self) -> None:
        result = normalize_href("/about", "https://example.com")
        assert result == "https://example.com/about"

    def test_absolute_url_preserved(self) -> None:
        result = normalize_href("https://other.com/page", "https://example.com")
        assert result == "https://other.com/page"

    def test_protocol_relative(self) -> None:
        result = normalize_href("//cdn.example.com/lib.js", "https://example.com")
        assert result == "https://cdn.example.com/lib.js"

    def test_anchor_only(self) -> None:
        assert normalize_href("#section", "https://example.com") is None

    def test_empty_href(self) -> None:
        assert normalize_href("", "https://example.com") is None

    def test_whitespace_only_href(self) -> None:
        assert normalize_href("   ", "https://example.com") is None

    def test_mailto_blocked(self) -> None:
        assert normalize_href("mailto:test@example.com", "https://example.com") is None

    def test_tel_blocked(self) -> None:
        assert normalize_href("tel:+18005551234", "https://example.com") is None

    def test_javascript_blocked(self) -> None:
        assert normalize_href("javascript:void(0)", "https://example.com") is None

    def test_data_blocked(self) -> None:
        assert normalize_href("data:text/html,<b>x</b>", "https://example.com") is None

    def test_ftp_blocked(self) -> None:
        assert normalize_href("ftp://example.com/file", "https://example.com") is None

    def test_blob_blocked(self) -> None:
        assert normalize_href("blob:https://example.com/uuid", "https://example.com") is None

    def test_file_blocked(self) -> None:
        assert normalize_href("file:///etc/passwd", "https://example.com") is None

    def test_no_base_url_no_scheme(self) -> None:
        assert normalize_href("/page", None) is None

    def test_no_base_url_with_scheme(self) -> None:
        result = normalize_href("https://example.com/page", None)
        assert result == "https://example.com/page"

    def test_trailing_slash_stripped(self) -> None:
        result = normalize_href("https://example.com/page/", None)
        assert result == "https://example.com/page"

    def test_relative_without_base(self) -> None:
        assert normalize_href("relative/path", None) is None

    def test_blocked_after_resolution(self) -> None:
        result = normalize_href("mailto:test@example.com", "https://example.com")
        assert result is None


class TestIsInternal:
    def test_same_host(self) -> None:
        assert is_internal("https://example.com/page", "https://example.com/other") is True

    def test_different_host(self) -> None:
        assert is_internal("https://other.com/page", "https://example.com") is False

    def test_no_base_url(self) -> None:
        assert is_internal("https://example.com/page", None) is None

    def test_empty_base_host(self) -> None:
        assert is_internal("https://example.com/page", "about:blank") is None

    def test_no_base_host(self) -> None:
        assert is_internal("https://example.com/page", "") is None


class TestIsAnchorLink:
    def test_same_page_anchor(self) -> None:
        assert (
            is_anchor_link("https://example.com/page#section", "https://example.com/page") is True
        )

    def test_fragment_only(self) -> None:
        assert is_anchor_link("#section", None) is True

    def test_full_url_not_anchor(self) -> None:
        assert is_anchor_link("https://example.com/page2", "https://example.com/page") is False

    def test_empty_resolved(self) -> None:
        assert is_anchor_link("", "https://example.com") is None

    def test_no_base_fragment_with_base(self) -> None:
        assert is_anchor_link("#section", "https://example.com") is False

    def test_fragment_with_trailing_slash_base(self) -> None:
        assert is_anchor_link("https://example.com/#section", "https://example.com") is True


class TestBlockedSchemes:
    def test_blocked_schemes_set(self) -> None:
        assert "mailto" in BLOCKED_SCHEMES
        assert "tel" in BLOCKED_SCHEMES
        assert "javascript" in BLOCKED_SCHEMES
        assert "data" in BLOCKED_SCHEMES
        assert "http" not in BLOCKED_SCHEMES
        assert "https" not in BLOCKED_SCHEMES
