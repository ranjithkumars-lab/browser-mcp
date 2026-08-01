"""Tests for global timeout resolution."""

from __future__ import annotations

import pytest

from browser_mcp.browser.navigation.timeouts import resolve_timeout
from browser_mcp.config.models import BrowserSettings
from browser_mcp.errors import NavigationTimeoutError

pytestmark = pytest.mark.unit


def test_override_wins() -> None:
    settings = BrowserSettings()
    assert resolve_timeout(settings, "navigation", 123) == 123


def test_global_fallback() -> None:
    settings = BrowserSettings(timeouts={"navigation_timeout_ms": 9_999})
    assert resolve_timeout(settings, "navigation", None) == 9_999
    assert resolve_timeout(settings, "default", None) == 30_000


def test_interaction_fallback() -> None:
    settings = BrowserSettings(timeouts={"interaction_timeout_ms": 1_111})
    assert resolve_timeout(settings, "interaction", None) == 1_111


def test_wait_fallback() -> None:
    settings = BrowserSettings(timeouts={"wait_timeout_ms": 2_222})
    assert resolve_timeout(settings, "wait", None) == 2_222


def test_invalid_override_raises() -> None:
    settings = BrowserSettings()
    with pytest.raises(NavigationTimeoutError):
        resolve_timeout(settings, "default", 0)
