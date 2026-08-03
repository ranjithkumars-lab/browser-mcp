"""Tests for the browser MCP application wiring (app.py)."""

from __future__ import annotations

import pytest

from browser_mcp.app import create_browser_context
from browser_mcp.config.models import BrowserSettings
from browser_mcp.tools.navigation import TOOL_NAMESPACE
from enterprise_mcp.config.loader import load_settings
from enterprise_mcp.foundation.app import AppContext

pytestmark = pytest.mark.unit

NAV_TOOL_NAMES = frozenset(
    {
        "goto",
        "back",
        "forward",
        "reload",
        "wait_timeout",
        "wait_navigation",
        "wait_popup",
        "wait_download",
        "wait_url",
        "scroll_to",
        "scroll_by",
        "scroll_element",
        "click",
        "hover",
        "double_click",
        "right_click",
        "list_frames",
        "list_windows",
        "close_popup",
        "activate_window",
    }
)


def _app_context() -> AppContext:
    settings = load_settings(env="test")
    context = AppContext(settings=settings)
    browser_settings = BrowserSettings(
        browser={"headless": True},
        timeouts={"navigation_timeout_ms": 15_000},
    )
    return create_browser_context(browser_settings, context=context)


def test_registers_navigation_and_lifecycle_tools() -> None:
    context = _app_context()
    names = {m.name for m in context.tools.list()}
    assert f"{TOOL_NAMESPACE}.create_session" in names
    assert {f"{TOOL_NAMESPACE}.{name}" for name in NAV_TOOL_NAMES} <= names
    assert {"browser.element.find", "browser.element.text", "browser.element.state"} <= names
    assert "browser.screenshot" in names
    assert len(names) >= 20 + 3 + 6


def test_registers_health_providers() -> None:
    context = _app_context()
    assert {"browser_pool", "navigation", "elements"} <= set(context.health_providers)


def test_registers_container_instances() -> None:
    context = _app_context()
    assert context.container.has("browser_sessions")
    assert context.container.has("navigation_state")
    assert context.container.has("navigation_manager")
    assert context.container.has("element_engine")
    assert context.container.has("screenshot_manager")
    assert context.container.resolve("navigation_state") is not None
    assert context.container.resolve("element_engine") is not None


async def test_start_stop_runs_lifecycle() -> None:
    context = _app_context()
    await context.start()
    await context.stop()


async def test_navigation_health_provider_payload() -> None:
    context = _app_context()
    provider = context.health_providers["navigation"]
    payload = await provider()
    assert set(payload["metrics"]) == {
        "browsers",
        "contexts",
        "pages",
        "frames",
        "popups",
        "sessions",
    }
    assert payload["navigation"]["default_strategy"] == "normal"
    assert payload["navigation"]["allow_redirects"] is True


async def test_elements_health_provider_payload() -> None:
    context = _app_context()
    provider = context.health_providers["elements"]
    payload = await provider()
    assert payload == {"cache": {"cached_elements": 0}}


def test_app_context_accepts_browser_settings_without_enterprise_attributes() -> None:
    """Regression: AppContext must tolerate BrowserSettings whose ServerConfig
    lacks the enterprise-only ``name`` and ``observability`` attributes."""
    browser_settings = BrowserSettings()
    context = AppContext(settings=browser_settings)
    assert context.mcp.name == "browser-mcp-server"
    assert context.settings is browser_settings
