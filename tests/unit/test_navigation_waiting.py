"""Tests for WaitingManager: wait_timeout, wait_navigation, wait_url, wait_download, wait_popup."""

from __future__ import annotations

import asyncio

import pytest
from tests.fakes import FakeDownload, FakePage
from tests.helpers import build_runtime

from browser_mcp.browser.navigation.waiting import WaitingManager
from browser_mcp.errors import NavigationTimeoutError

pytestmark = pytest.mark.unit


async def test_wait_timeout_returns_elapsed() -> None:
    runtime = await build_runtime()
    waiting: WaitingManager = runtime["waiting"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await waiting.wait_timeout(session_id, page_id, 5)
    assert result["waited_ms"] == 5


async def test_wait_navigation_success() -> None:
    runtime = await build_runtime()
    waiting: WaitingManager = runtime["waiting"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await waiting.wait_navigation(session_id, page_id, state="networkidle")
    assert result["url"] == page.url
    assert page.last_wait_for_load_state == ("networkidle", 10_000)


async def test_wait_navigation_failure() -> None:
    page = FakePage(url="https://example.com")
    page.wait_for_load_state_error = RuntimeError("boom")
    runtime = await build_runtime(page=page)
    waiting: WaitingManager = runtime["waiting"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    with pytest.raises(NavigationTimeoutError):
        await waiting.wait_navigation(session_id, page_id)


async def test_wait_url_success() -> None:
    runtime = await build_runtime()
    waiting: WaitingManager = runtime["waiting"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await waiting.wait_url(session_id, page_id, "**/example**")
    assert result["url"] == page.url
    assert page.last_wait_for_url == ("**/example**", 10_000)


async def test_wait_url_failure() -> None:
    page = FakePage(url="https://example.com")
    page.wait_for_url_error = RuntimeError("boom")
    runtime = await build_runtime(page=page)
    waiting: WaitingManager = runtime["waiting"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    with pytest.raises(NavigationTimeoutError):
        await waiting.wait_url(session_id, page_id, "**/nope**")


async def test_wait_download_success() -> None:
    runtime = await build_runtime()
    waiting: WaitingManager = runtime["waiting"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    task = asyncio.create_task(waiting.wait_download(session_id, page_id))
    await asyncio.sleep(0)
    page.emit_download(FakeDownload("report.txt", "https://x.example/report.txt"))
    result = await asyncio.wait_for(task, timeout=2)

    assert result["suggested_filename"] == "report.txt"


async def test_wait_download_timeout() -> None:
    runtime = await build_runtime()
    waiting: WaitingManager = runtime["waiting"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    with pytest.raises(NavigationTimeoutError):
        await waiting.wait_download(session_id, page_id, timeout_ms=100)


async def test_wait_popup_returns_popup() -> None:
    runtime = await build_runtime()
    waiting: WaitingManager = runtime["waiting"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id
    context = runtime["page"].context

    task = asyncio.create_task(waiting.wait_popup(session_id, page_id))
    await asyncio.sleep(0)
    context.emit_page(FakePage(url="https://popup.example/"))
    result = await asyncio.wait_for(task, timeout=2)

    assert result["popup_id"]
    assert result["origin_page_id"] == page_id
