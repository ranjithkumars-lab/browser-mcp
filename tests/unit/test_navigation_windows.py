"""Tests for WindowManager (popups, windows, tabs)."""

from __future__ import annotations

import asyncio

import pytest
from tests.fakes import FakePage
from tests.helpers import build_runtime

from browser_mcp.browser.navigation.windows import WindowManager
from browser_mcp.errors import NavigationTimeoutError

pytestmark = pytest.mark.unit


async def test_wait_for_popup_adopts_already_open_page() -> None:
    runtime = await build_runtime()
    windows: WindowManager = runtime["windows"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id
    context = runtime["page"].context

    popup = FakePage(url="https://popup.example/")
    context.emit_page(popup)

    received: list[str] = []

    async def handler(event: object) -> None:
        received.append(event.event_name)

    runtime["events"].subscribe("popup.opened", handler)

    result = await windows.wait_for_popup(session_id, page_id)
    popup_id = result["popup_id"]
    assert result["origin_page_id"] == page_id
    assert result["url"] == "https://popup.example/"
    assert runtime["pool"].has_page(popup_id)
    assert [p.popup_id for p in runtime["state"].popups()] == [popup_id]
    assert received == ["popup.opened"]


async def test_wait_for_popup_awaits_new_page_event() -> None:
    runtime = await build_runtime()
    windows: WindowManager = runtime["windows"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id
    context = runtime["page"].context

    popup = FakePage(url="https://popup.example/")
    task = asyncio.create_task(windows.wait_for_popup(session_id, page_id))
    await asyncio.sleep(0)
    context.emit_page(popup)
    result = await asyncio.wait_for(task, timeout=2)

    assert result["popup_id"]
    assert result["url"] == "https://popup.example/"


async def test_wait_for_popup_timeout() -> None:
    runtime = await build_runtime()
    windows: WindowManager = runtime["windows"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    with pytest.raises(NavigationTimeoutError):
        await windows.wait_for_popup(session_id, page_id, timeout_ms=100)


async def test_close_popup() -> None:
    runtime = await build_runtime()
    windows: WindowManager = runtime["windows"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id
    context = runtime["page"].context

    popup = FakePage(url="https://popup.example/")
    context.emit_page(popup)
    result = await windows.wait_for_popup(session_id, page_id)
    popup_id = result["popup_id"]

    closed = await windows.close_popup(session_id, popup_id)
    assert closed["closed"] is True
    assert runtime["state"].popups() == []
    assert not runtime["pool"].has_page(popup_id)


async def test_list_windows_returns_context_pages() -> None:
    runtime = await build_runtime()
    windows: WindowManager = runtime["windows"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id
    context = runtime["page"].context

    popup = FakePage(url="https://popup.example/")
    context.emit_page(popup)
    await windows.wait_for_popup(session_id, page_id)

    listing = await windows.list_windows(session_id, page_id)
    assert len(listing) == 2
    by_id = {entry["page_id"]: entry for entry in listing}
    assert by_id[page_id]["is_popup"] is False
    assert by_id[runtime["state"].popups()[0].popup_id]["is_popup"] is True


async def test_activate_brings_page_to_front() -> None:
    runtime = await build_runtime()
    windows: WindowManager = runtime["windows"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await windows.activate(session_id, page_id)
    assert result["activated"] is True
