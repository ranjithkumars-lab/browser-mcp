"""Tests for NavigationManager (goto / reload)."""

from __future__ import annotations

import pytest
from tests.fakes import FakePage, redirect_chain
from tests.helpers import build_runtime, default_settings

from browser_mcp.browser.navigation.manager import NavigationManager
from browser_mcp.errors import NavigationError, PolicyViolationError

pytestmark = pytest.mark.unit


async def test_goto_success() -> None:
    runtime = await build_runtime()
    navigation: NavigationManager = runtime["navigation"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await navigation.goto(session_id, page_id, "https://example.com")
    assert "success" not in result
    assert result["url"] == "https://example.com"
    assert result["title"] == ""
    assert result["status"] == 200
    assert "navigation_time_ms" in result
    assert result["session_id"] == "s1"
    assert result["page_id"] == page_id
    assert result["redirect_count"] == 0
    assert page.last_goto == (
        "https://example.com",
        {"wait_until": "load", "timeout": 30_000},
    )
    assert runtime["page_handle"].state.url == "https://example.com"


async def test_goto_strategy_maps_wait_until() -> None:
    runtime = await build_runtime()
    navigation: NavigationManager = runtime["navigation"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    await navigation.goto(session_id, page_id, "https://example.com", strategy="complete")
    assert page.last_goto is not None
    assert page.last_goto[1]["wait_until"] == "networkidle"


async def test_goto_uses_configured_navigation_timeout() -> None:
    runtime = await build_runtime(
        settings=default_settings(timeouts={"navigation_timeout_ms": 7_000})
    )
    navigation: NavigationManager = runtime["navigation"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    await navigation.goto(session_id, page_id, "https://example.com")
    assert page.last_goto is not None
    assert page.last_goto[1]["timeout"] == 7_000


async def test_goto_override_timeout_wins() -> None:
    runtime = await build_runtime()
    navigation: NavigationManager = runtime["navigation"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    await navigation.goto(session_id, page_id, "https://example.com", timeout_ms=999)
    assert page.last_goto is not None
    assert page.last_goto[1]["timeout"] == 999


async def test_goto_policy_violation_blocks_before_navigation() -> None:
    runtime = await build_runtime(
        settings=default_settings(navigation={"blocked_domains": ["example.com"]})
    )
    navigation: NavigationManager = runtime["navigation"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    with pytest.raises(PolicyViolationError):
        await navigation.goto(session_id, page_id, "https://example.com")
    assert page.navigations == []


async def test_goto_failure_raises_navigation_error_and_emits() -> None:
    page = FakePage(url="about:blank")
    page.goto_error = RuntimeError("boom")
    runtime = await build_runtime(page=page)
    navigation: NavigationManager = runtime["navigation"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id
    received: list[str] = []

    async def handler(event: object) -> None:
        received.append(event.event_name)

    runtime["events"].subscribe(None, handler)

    with pytest.raises(NavigationError):
        await navigation.goto(session_id, page_id, "https://example.com")
    assert "navigation.started" in received
    assert "navigation.failed" in received


async def test_goto_emits_completed_event() -> None:
    runtime = await build_runtime()
    navigation: NavigationManager = runtime["navigation"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id
    received: list[str] = []

    async def handler(event: object) -> None:
        received.append(event.event_name)

    runtime["events"].subscribe(None, handler)

    await navigation.goto(session_id, page_id, "https://example.com")
    assert received.count("navigation.started") == 1
    assert received.count("navigation.completed") == 1


async def test_goto_rejects_redirects_when_disabled() -> None:
    page = FakePage(url="about:blank")
    page.goto_response = redirect_chain(1)
    runtime = await build_runtime(
        page=page, settings=default_settings(navigation={"allow_redirects": False})
    )
    navigation: NavigationManager = runtime["navigation"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    with pytest.raises(PolicyViolationError):
        await navigation.goto(session_id, page_id, "https://example.com")


async def test_goto_rejects_excessive_redirects() -> None:
    page = FakePage(url="about:blank")
    page.goto_response = redirect_chain(5)
    runtime = await build_runtime(
        page=page, settings=default_settings(navigation={"max_redirects": 3})
    )
    navigation: NavigationManager = runtime["navigation"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    with pytest.raises(PolicyViolationError):
        await navigation.goto(session_id, page_id, "https://example.com")


async def test_goto_reports_redirect_count() -> None:
    page = FakePage(url="about:blank")
    page.goto_response = redirect_chain(2)
    runtime = await build_runtime(page=page)
    navigation: NavigationManager = runtime["navigation"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await navigation.goto(session_id, page_id, "https://example.com")
    assert result["redirect_count"] == 2


async def test_reload_success() -> None:
    runtime = await build_runtime()
    navigation: NavigationManager = runtime["navigation"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await navigation.reload(session_id, page_id)
    assert result["url"] == page.url
    assert result["status"] == 200
    assert page.last_reload == {"wait_until": "load", "timeout": 30_000}


async def test_reload_failure() -> None:
    page = FakePage(url="https://example.com")
    page.reload_error = RuntimeError("boom")
    runtime = await build_runtime(page=page)
    navigation: NavigationManager = runtime["navigation"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    with pytest.raises(NavigationError):
        await navigation.reload(session_id, page_id)
