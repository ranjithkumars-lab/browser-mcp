"""Tests for Phase 2 configuration models (navigation + timeouts)."""

from __future__ import annotations

import pydantic
import pytest

from browser_mcp.config.models import BrowserSettings, NavigationStrategy

pytestmark = pytest.mark.unit


def test_strategy_wait_until_mapping() -> None:
    assert NavigationStrategy.FAST.wait_until() == "domcontentloaded"
    assert NavigationStrategy.NORMAL.wait_until() == "load"
    assert NavigationStrategy.COMPLETE.wait_until() == "networkidle"


def test_strategy_values() -> None:
    assert [s.value for s in NavigationStrategy] == ["fast", "normal", "complete"]


def test_defaults_include_navigation_and_timeouts() -> None:
    settings = BrowserSettings()
    assert settings.navigation.allow_redirects is True
    assert settings.navigation.max_redirects == 10
    assert settings.navigation.allowed_schemes == ["http", "https", "file"]
    assert settings.navigation.default_strategy is NavigationStrategy.NORMAL
    assert settings.navigation.max_navigation_depth is None
    assert settings.timeouts.default_timeout_ms == 30_000
    assert settings.timeouts.navigation_timeout_ms == 30_000
    assert settings.timeouts.interaction_timeout_ms == 10_000
    assert settings.timeouts.wait_timeout_ms == 10_000


def test_navigation_override() -> None:
    settings = BrowserSettings(
        navigation={
            "allowed_domains": ["example.com"],
            "blocked_domains": ["bad.example"],
            "allow_redirects": False,
            "max_redirects": 2,
            "allowed_schemes": ["https"],
            "default_strategy": "complete",
        }
    )
    assert settings.navigation.allowed_domains == ["example.com"]
    assert settings.navigation.allow_redirects is False
    assert settings.navigation.max_redirects == 2
    assert settings.navigation.allowed_schemes == ["https"]
    assert settings.navigation.default_strategy is NavigationStrategy.COMPLETE


def test_timeout_override() -> None:
    settings = BrowserSettings(
        timeouts={
            "default_timeout_ms": 5_000,
            "navigation_timeout_ms": 15_000,
            "interaction_timeout_ms": 2_000,
        }
    )
    assert settings.timeouts.default_timeout_ms == 5_000
    assert settings.timeouts.navigation_timeout_ms == 15_000
    assert settings.timeouts.interaction_timeout_ms == 2_000


def test_timeout_must_be_positive() -> None:
    with pytest.raises(pydantic.ValidationError):
        BrowserSettings(timeouts={"navigation_timeout_ms": 0})
