"""Integration tests for the authentication engine.

Each test wires the real auth manager against a live (headless) Chromium
session, exercising login, state persistence, and header injection end-to-end.
"""

from __future__ import annotations

import asyncio
import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from browser_mcp.auth.manager import AuthManager
from browser_mcp.auth.models import AuthCredentials
from browser_mcp.auth.provider import PlaywrightAuthProvider
from browser_mcp.auth.storage.encryption import AuthEncryptionEngine
from browser_mcp.auth.storage.manager import AuthStorageManager
from browser_mcp.auth.strategies.cookie import CookieAuthStrategy
from browser_mcp.auth.strategies.form import FormAuthStrategy
from browser_mcp.auth.strategies.header import HeaderAuthStrategy
from browser_mcp.auth.strategies.registry import AuthStrategyRegistry
from browser_mcp.browser.context import ContextManager
from browser_mcp.browser.elements.engine import ElementEngine
from browser_mcp.browser.elements.locators.registry import LocatorRegistry
from browser_mcp.browser.elements.provider import PlaywrightLocatorProvider
from browser_mcp.browser.factory import BrowserFactory
from browser_mcp.browser.manager import BrowserManager
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


@pytest.fixture
async def runtime(tmp_path_factory: pytest.TempPathFactory, html_server: str) -> dict[str, Any]:
    settings = BrowserSettings(
        browser={"headless": True},
        timeouts={"navigation_timeout_ms": 15_000, "interaction_timeout_ms": 10_000, "wait_timeout_ms": 10_000},
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

    registry = AuthStrategyRegistry()
    registry.register(FormAuthStrategy())
    registry.register(CookieAuthStrategy())
    registry.register(HeaderAuthStrategy())
    storage_dir = tmp_path_factory.mktemp("auth_states")
    storage = AuthStorageManager(
        directory=storage_dir,
        encryption=AuthEncryptionEngine(allow_plaintext=True),
    )
    provider = PlaywrightAuthProvider()
    auth_manager = AuthManager(registry=registry, storage=storage, provider=provider, event_bus=events)

    created = await sessions.create_session()
    session_id = str(created["session_id"])
    context_created = await sessions.create_context(session_id)
    context_id = str(context_created["context_id"])
    page_created = await sessions.new_page(session_id, context_id)
    page_id = str(page_created["page_id"])

    bundle = {
        "pool": pool,
        "sessions": sessions,
        "session_id": session_id,
        "context_id": context_id,
        "page_id": page_id,
        "base": html_server,
        "settings": settings,
        "auth_manager": auth_manager,
        "events": events,
    }
    try:
        yield bundle
    finally:
        await sessions.close_session(session_id)
        await factory.stop()


async def test_form_login_persists_state(runtime: dict[str, Any]) -> None:
    session_id = runtime["session_id"]
    context_id = runtime["context_id"]
    page_id = runtime["page_id"]
    auth_manager = runtime["auth_manager"]

    result = await auth_manager.login(
        runtime["pool"].get_page(page_id).page,
        AuthCredentials(
            username="user",
            password="pass",
            url=runtime["base"] + "/login.html",
            strategy="form",
            metadata={"session_id": session_id, "context_id": context_id},
        ),
    )
    assert result["success"] is True
    assert result["session"]["session"]["authenticated"] is True

    loaded = await auth_manager.load_state(context_id)
    assert loaded.session.session_id == session_id


async def test_header_injection(runtime: dict[str, Any]) -> None:
    session_id = runtime["session_id"]
    context_id = runtime["context_id"]
    auth_manager = runtime["auth_manager"]
    context = runtime["pool"].get_context(context_id).context

    result = await auth_manager.set_headers(context, {"Authorization": "Bearer token"}, context_id=context_id, session_id=session_id)
    assert result["success"] is True
    assert "Authorization" in result["headers_injected"]


async def test_cookie_injection(runtime: dict[str, Any]) -> None:
    session_id = runtime["session_id"]
    context_id = runtime["context_id"]
    auth_manager = runtime["auth_manager"]
    context = runtime["pool"].get_context(context_id).context

    result = await auth_manager.login(
        context,
        AuthCredentials(
            url=runtime["base"] + "/simple.html",
            strategy="cookie",
            cookies={"test": "abc"},
            metadata={"session_id": session_id, "context_id": context_id},
        ),
    )
    assert result["success"] is True
