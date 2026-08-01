"""Integration tests for the element engine against a real Chromium.

Each test launches a disposable headless Chromium session and drives the real
managers (including the Phase 3 :class:`ElementEngine`) against HTML fixtures
served over a local HTTP server, so CSS/XPath/ARIA/text strategies, property
extraction and state checks behave exactly as they would against a real site.
"""

from __future__ import annotations

import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from browser_mcp.browser.context import ContextManager
from browser_mcp.browser.elements.engine import ElementEngine
from browser_mcp.browser.elements.locators.registry import LocatorRegistry
from browser_mcp.browser.elements.provider import PlaywrightLocatorProvider
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
from browser_mcp.errors import ElementNotFoundError, ElementStateError
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
    downloads_dir = tmp_path_factory.mktemp("browser-mcp-element-downloads")
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
    registry = LocatorRegistry(PlaywrightLocatorProvider())
    engine = ElementEngine(state, frames, registry, events, settings)
    interactions = InteractionManager(state, frames, events, settings, engine)
    waiting = WaitingManager(state, windows, events, settings)

    created = await sessions.create_session()
    session_id = str(created["session_id"])
    context_id = str((await sessions.create_context(session_id))["context_id"])
    page_id = str((await sessions.new_page(session_id, context_id))["page_id"])

    bundle = {
        "pool": pool,
        "sessions": sessions,
        "state": state,
        "frames": frames,
        "navigation": navigation,
        "interactions": interactions,
        "engine": engine,
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


async def _goto(runtime: dict[str, Any], fixture: str) -> None:
    await runtime["navigation"].goto(
        runtime["session_id"], runtime["page_id"], fixture_url(runtime["base"], fixture)
    )


async def _find(
    runtime: dict[str, Any], strategy: str, value: str, **kwargs: Any
) -> dict[str, Any]:
    return await runtime["engine"].find(
        runtime["session_id"], runtime["page_id"], strategy, value, **kwargs
    )


async def test_find_and_text_round_trip(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "elements.html")
    found = await _find(runtime, "css", "#heading")
    assert found["element_id"].startswith("element_")
    assert found["strategy"] == "css"

    text = await runtime["engine"].text(
        runtime["session_id"], runtime["page_id"], found["element_id"]
    )
    assert text["text"] == "Elements Fixture"


async def test_find_by_xpath(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "elements.html")
    found = await _find(runtime, "xpath", "//h1[@id='heading']")
    assert found["count"] == 1
    text = await runtime["engine"].text(
        runtime["session_id"], runtime["page_id"], found["element_id"]
    )
    assert text["text"] == "Elements Fixture"


async def test_find_by_text_strategy(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "elements.html")
    found = await _find(runtime, "text", "Static paragraph one.")
    text = await runtime["engine"].text(
        runtime["session_id"], runtime["page_id"], found["element_id"]
    )
    assert text["text"] == "Static paragraph one."


async def test_find_by_aria_role(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "aria.html")
    found = await _find(runtime, "aria", "button:Save")
    assert found["count"] == 1
    text = await runtime["engine"].text(
        runtime["session_id"], runtime["page_id"], found["element_id"]
    )
    assert text["text"] == "Save"


async def test_find_all_returns_indexed_matches(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "elements.html")
    result = await runtime["engine"].find_all(
        runtime["session_id"], runtime["page_id"], "css", ".item"
    )
    assert result["count"] == 3
    texts = [
        (
            await runtime["engine"].text(
                runtime["session_id"], runtime["page_id"], entry["element_id"]
            )
        )["text"]
        for entry in result["elements"]
    ]
    assert texts == ["first item", "second item", "third item"]


async def test_attribute_extraction(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "elements.html")
    found = await _find(runtime, "css", "#items")
    attr = await runtime["engine"].attribute(
        runtime["session_id"], runtime["page_id"], found["element_id"], "data-count"
    )
    assert attr["value"] == "3"


async def test_html_inner_and_outer(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "elements.html")
    found = await _find(runtime, "css", "#items")
    inner = await runtime["engine"].html(
        runtime["session_id"], runtime["page_id"], found["element_id"]
    )
    outer = await runtime["engine"].html(
        runtime["session_id"], runtime["page_id"], found["element_id"], outer=True
    )
    assert "first item" in inner["html"]
    assert "item-3" in inner["html"]
    assert '<ul id="items"' in outer["html"]


async def test_state_snapshot(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "elements.html")
    hidden = await _find(runtime, "css", "#hidden")
    checks = await runtime["engine"].state(
        runtime["session_id"], runtime["page_id"], hidden["element_id"]
    )
    assert checks["exists"] is True
    assert checks["visible"] is False

    disabled = await _find(runtime, "css", "#submit")
    state = await runtime["engine"].state(
        runtime["session_id"], runtime["page_id"], disabled["element_id"]
    )
    assert state["enabled"] is False

    checkbox = await _find(runtime, "css", "#checkbox")
    boxed = await runtime["engine"].state(
        runtime["session_id"], runtime["page_id"], checkbox["element_id"]
    )
    assert boxed["checked"] is True

    text_input = await _find(runtime, "css", "#text-input")
    editable = await runtime["engine"].state(
        runtime["session_id"], runtime["page_id"], text_input["element_id"]
    )
    assert editable["editable"] is True


async def test_shadow_dom_open_supported(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "shadow-dom.html")
    found = await _find(runtime, "css", ".inner")
    text = await runtime["engine"].text(
        runtime["session_id"], runtime["page_id"], found["element_id"]
    )
    assert text["text"] == "shadow text"


async def test_find_inside_frame(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "nested-frames.html")
    frames = await runtime["frames"].list_frames(runtime["session_id"], runtime["page_id"])
    inner = next(f for f in frames if not f["is_main"])

    found = await _find(runtime, "css", "#frame-button", frame_id=inner["frame_id"])
    text = await runtime["engine"].text(
        runtime["session_id"], runtime["page_id"], found["element_id"]
    )
    assert text["text"] == "Frame Button"


async def test_dynamic_element_auto_wait(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "dynamic.html")
    found = await _find(runtime, "css", "#late-button", timeout_ms=5_000)
    text = await runtime["engine"].text(
        runtime["session_id"], runtime["page_id"], found["element_id"]
    )
    assert text["text"] == "Late Button"


async def test_not_found_raises(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "elements.html")
    with pytest.raises(ElementNotFoundError):
        await _find(runtime, "css", "#does-not-exist", timeout_ms=500)


async def test_strict_violation_raises(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "elements.html")
    with pytest.raises(ElementStateError):
        await _find(runtime, "css", "p", timeout_ms=500)


async def test_interaction_by_element_id(runtime: dict[str, Any]) -> None:
    await _goto(runtime, "elements.html")
    found = await _find(runtime, "css", "#save")
    result = await runtime["interactions"].click(
        runtime["session_id"], runtime["page_id"], element_id=found["element_id"]
    )
    assert result["action"] == "click"
    assert result["element_id"] == found["element_id"]

    submitted = (
        await runtime["pool"]
        .get_page(runtime["page_id"])
        .page.evaluate("() => document.body.dataset.saved")
    )
    assert submitted == "true"
