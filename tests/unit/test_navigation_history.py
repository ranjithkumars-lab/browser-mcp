"""Tests for HistoryManager (back / forward)."""

from __future__ import annotations

import pytest
from tests.fakes import FakePage
from tests.helpers import build_runtime

from browser_mcp.browser.navigation.history import HistoryManager

pytestmark = pytest.mark.unit


async def test_back_success() -> None:
    runtime = await build_runtime()
    history: HistoryManager = runtime["history"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await history.back(session_id, page_id)
    assert result["direction"] == "back"
    assert "navigation_time_ms" in result
    assert page.navigations[-1] == "__back__"


async def test_forward_success() -> None:
    runtime = await build_runtime()
    history: HistoryManager = runtime["history"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await history.forward(session_id, page_id)
    assert result["direction"] == "forward"
    assert page.navigations[-1] == "__forward__"


async def test_back_uses_timeout() -> None:
    runtime = await build_runtime()
    history: HistoryManager = runtime["history"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await history.back(session_id, page_id, timeout_ms=5_000)
    assert result["direction"] == "back"


async def test_back_emits_events() -> None:
    runtime = await build_runtime()
    history: HistoryManager = runtime["history"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id
    received: list[str] = []

    async def handler(event: object) -> None:
        received.append(event.event_name)

    runtime["events"].subscribe(None, handler)
    await history.back(session_id, page_id)
    assert "navigation.started" in received
    assert "navigation.completed" in received
