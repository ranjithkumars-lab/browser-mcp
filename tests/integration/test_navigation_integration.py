"""Integration tests for the navigation engine against a real Chromium.

Each test launches a disposable headless Chromium session and drives it
through the real managers (NavigationManager, HistoryManager, FrameManager,
WindowManager, InteractionManager, WaitingManager). A local HTTP server
serves the HTML fixtures so navigation, popups, redirects and downloads all
behave exactly as they would against a real site (file:// URLs do not emit
download events, so HTTP is required).
"""

from __future__ import annotations

import asyncio
import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from browser_mcp.browser.context import ContextManager
from browser_mcp.browser.factory import BrowserFactory
from browser_mcp.browser.manager import BrowserManager
from browser_mcp.browser.navigation.frames import FrameManager
from browser_mcp.browser.navigation.history import HistoryManager
from browser_mcp.browser.navigation.interactions import InteractionManager
from browser_mcp.browser.navigation.manager import NavigationManager
from browser_mcp.browser.navigation.policy import NavigationPolicy
from browser_mcp.browser.navigation.state import StateManager
from browser_mcp.browser.navigation.waiting import WaitingManager
from browser_mcp.browser.navigation.windows import WindowManager
from browser_mcp.browser.page import PageManager
from browser_mcp.browser.pool import BrowserPool
from browser_mcp.browser.profile import ProfileManager
from browser_mcp.browser.session import SessionManager
from browser_mcp.config.models import BrowserSettings
from enterprise_mcp.events.bus import EventBus

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "html"


@pytest.fixture(scope="session")
def html_server() -> str:
    """Serve the HTML fixtures over HTTP on an ephemeral port."""
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(FIXTURES))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        yield base
    finally:
        server.shutdown()
        thread.join(timeout=5)


def fixture_url(base: str, name: str) -> str:
    """Return the served URL for ``name`` inside the HTML fixtures."""
    return f"{base}/{name}"


@pytest.fixture
async def runtime(tmp_path_factory: pytest.TempPathFactory, html_server: str) -> dict[str, Any]:
    """Launch a disposable Chromium session wired with the real managers."""
    downloads_dir = tmp_path_factory.mktemp("browser-mcp-downloads")
    settings = BrowserSettings(
        browser={"headless": True, "downloads_dir": str(downloads_dir)},
        timeouts={
            "navigation_timeout_ms": 15_000,
            "interaction_timeout_ms": 10_000,
            "wait_timeout_ms": 10_000,
        },
    )
    pool = BrowserPool(settings)
    factory = BrowserFactory()
    profiles = ProfileManager(settings)
    await factory.start()
    browsers = BrowserManager(settings, pool, factory, profiles)
    contexts = ContextManager(settings, pool, factory, profiles)
    pages = PageManager(pool, factory)
    sessions = SessionManager(pool, browsers, contexts, pages)
    events = EventBus()
    state = StateManager(pool, sessions, settings)
    policy = NavigationPolicy(settings)
    frames = FrameManager(state, events, settings)
    navigation = NavigationManager(state, policy, events, settings)
    history = HistoryManager(state, events, settings)
    windows = WindowManager(pool, state, pages, events, settings)
    interactions = InteractionManager(state, frames, events, settings)
    waiting = WaitingManager(state, windows, events, settings)

    created = await sessions.create_session()
    session_id = str(created["session_id"])
    context_created = await sessions.create_context(session_id)
    context_id = str(context_created["context_id"])
    page_created = await sessions.new_page(session_id, context_id)
    page_id = str(page_created["page_id"])

    bundle = {
        "pool": pool,
        "sessions": sessions,
        "state": state,
        "frames": frames,
        "navigation": navigation,
        "history": history,
        "windows": windows,
        "interactions": interactions,
        "waiting": waiting,
        "session_id": session_id,
        "context_id": context_id,
        "page_id": page_id,
        "base": html_server,
        "settings": settings,
    }
    try:
        yield bundle
    finally:
        await sessions.close_session(session_id)
        await factory.stop()


async def test_goto_round_trip(runtime: dict[str, Any]) -> None:
    result = await runtime["navigation"].goto(
        runtime["session_id"], runtime["page_id"], fixture_url(runtime["base"], "simple.html")
    )
    assert result["status"] == 200
    assert result["title"] == "Simple Page"
    assert result["url"].endswith("simple.html")
    assert result["strategy"] == "normal"


async def test_goto_rejects_disallowed_scheme(runtime: dict[str, Any]) -> None:
    with pytest.raises(Exception) as excinfo:
        await runtime["navigation"].goto(
            runtime["session_id"], runtime["page_id"], "javascript:alert(1)"
        )
    assert "scheme" in str(excinfo.value) or "not allowed" in str(excinfo.value)


async def test_back_and_forward(runtime: dict[str, Any]) -> None:
    navigation = runtime["navigation"]
    history = runtime["history"]
    session_id, page_id = runtime["session_id"], runtime["page_id"]

    await navigation.goto(session_id, page_id, fixture_url(runtime["base"], "simple.html"))
    await navigation.goto(session_id, page_id, fixture_url(runtime["base"], "iframe.html"))

    back = await history.back(session_id, page_id)
    assert back["direction"] == "back"
    assert back["url"].endswith("simple.html")

    forward = await history.forward(session_id, page_id)
    assert forward["direction"] == "forward"
    assert forward["url"].endswith("iframe.html")


async def test_reload(runtime: dict[str, Any]) -> None:
    session_id, page_id = runtime["session_id"], runtime["page_id"]
    await runtime["navigation"].goto(
        session_id, page_id, fixture_url(runtime["base"], "simple.html")
    )
    result = await runtime["navigation"].reload(session_id, page_id)
    assert result["status"] == 200
    assert "navigation_time_ms" in result


async def test_frames_discovered_and_interacted(runtime: dict[str, Any]) -> None:
    session_id, page_id = runtime["session_id"], runtime["page_id"]
    await runtime["navigation"].goto(
        session_id, page_id, fixture_url(runtime["base"], "iframe.html")
    )

    frames = await runtime["frames"].list_frames(session_id, page_id)
    assert len(frames) == 2
    inner = next(f for f in frames if not f["is_main"])
    main = next(f for f in frames if f["is_main"])
    assert inner["url"].endswith("frame.html")
    assert inner["parent_frame_id"] == main["frame_id"]

    result = await runtime["interactions"].click(
        session_id, page_id, "#frame-button", frame_id=inner["frame_id"]
    )
    assert result["action"] == "click"
    assert result["frame_id"] == inner["frame_id"]

    frame = await runtime["frames"].frame_object_for(session_id, page_id, inner["frame_id"])
    output = await frame.evaluate("() => document.getElementById('frame-output').textContent")
    assert output == "frame clicked"


async def test_interactions_on_simple_page(runtime: dict[str, Any]) -> None:
    session_id, page_id = runtime["session_id"], runtime["page_id"]
    await runtime["navigation"].goto(
        session_id, page_id, fixture_url(runtime["base"], "simple.html")
    )
    interactions = runtime["interactions"]
    page_object = runtime["pool"].get_page(page_id).page

    await interactions.click(session_id, page_id, "#click-me")
    assert (
        await page_object.evaluate("() => document.getElementById('click-output').textContent")
        == "clicked"
    )

    await interactions.double_click(session_id, page_id, "#dblclick-me")
    assert (
        await page_object.evaluate("() => document.getElementById('click-output').textContent")
        == "double-clicked"
    )

    await interactions.right_click(session_id, page_id, "#rightclick-me")
    assert (
        await page_object.evaluate("() => document.getElementById('click-output').textContent")
        == "right-clicked"
    )

    await interactions.hover(session_id, page_id, "#hover-target")
    assert (
        await page_object.evaluate("() => document.getElementById('hover-output').textContent")
        == "hovered"
    )

    scroll = await interactions.scroll_to(session_id, page_id, 0, 500)
    assert scroll["action"] == "scroll_to"
    scroll_y = await page_object.evaluate("() => window.scrollY")
    assert scroll_y >= 400


async def test_wait_apis(runtime: dict[str, Any]) -> None:
    session_id, page_id = runtime["session_id"], runtime["page_id"]
    navigation = runtime["navigation"]
    waiting = runtime["waiting"]

    await navigation.goto(session_id, page_id, fixture_url(runtime["base"], "simple.html"))

    waited = await waiting.wait_navigation(session_id, page_id, state="load")
    assert waited["url"].endswith("simple.html")

    matched = await waiting.wait_url(session_id, page_id, "**/simple.html")
    assert matched["url"].endswith("simple.html")

    timed = await waiting.wait_timeout(session_id, page_id, 20)
    assert timed["waited_ms"] == 20


async def test_popup_detection_and_close(runtime: dict[str, Any]) -> None:
    session_id, page_id = runtime["session_id"], runtime["page_id"]
    navigation = runtime["navigation"]
    interactions = runtime["interactions"]
    waiting = runtime["waiting"]
    windows = runtime["windows"]

    await navigation.goto(session_id, page_id, fixture_url(runtime["base"], "popup.html"))
    await interactions.click(session_id, page_id, "#open-popup")

    result = await waiting.wait_popup(session_id, page_id)
    popup_id = result["popup_id"]
    assert result["origin_page_id"] == page_id

    popup_handle = runtime["pool"].get_page(popup_id)
    await popup_handle.page.wait_for_url("**/simple.html", timeout=10_000)
    assert popup_handle.page.url.endswith("simple.html")
    assert runtime["state"].popups()[0].popup_id == popup_id

    listing = await windows.list_windows(session_id, page_id)
    assert len(listing) == 2
    assert {entry["page_id"] for entry in listing} == {page_id, popup_id}

    closed = await windows.close_popup(session_id, popup_id)
    assert closed["closed"] is True
    assert runtime["state"].popups() == []


async def test_download_wait(runtime: dict[str, Any]) -> None:
    session_id, page_id = runtime["session_id"], runtime["page_id"]
    await runtime["navigation"].goto(
        session_id, page_id, fixture_url(runtime["base"], "downloads.html")
    )

    task = asyncio.create_task(
        runtime["waiting"].wait_download(session_id, page_id, timeout_ms=10_000)
    )
    await asyncio.sleep(0.1)
    await runtime["interactions"].click(session_id, page_id, "#download-link")
    result = await asyncio.wait_for(task, timeout=15)

    assert result["suggested_filename"] == "download.txt"
    assert result["url"].endswith("download.txt")


async def test_policy_blocks_blocked_domain(runtime: dict[str, Any]) -> None:
    blocked = BrowserSettings(
        navigation={"blocked_domains": ["example.com"]},
        timeouts={"navigation_timeout_ms": 15_000},
    )
    pool = BrowserPool(blocked)
    factory = BrowserFactory()
    profiles = ProfileManager(blocked)
    await factory.start()
    browsers = BrowserManager(blocked, pool, factory, profiles)
    contexts = ContextManager(blocked, pool, factory, profiles)
    pages = PageManager(pool, factory)
    sessions = SessionManager(pool, browsers, contexts, pages)
    created = await sessions.create_session()
    session_id = str(created["session_id"])
    context_id = str((await sessions.create_context(session_id))["context_id"])
    page_id = str((await sessions.new_page(session_id, context_id))["page_id"])
    policy = NavigationPolicy(blocked)
    navigation = NavigationManager(
        StateManager(pool, sessions, blocked), policy, EventBus(), blocked
    )
    try:
        with pytest.raises(Exception) as excinfo:
            await navigation.goto(session_id, page_id, "https://example.com/")
        assert "blocked" in str(excinfo.value)
    finally:
        await sessions.close_session(session_id)
        await factory.stop()
