"""Shared test runtime builders for the navigation package."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from browser_mcp.browser.models import (
    BrowserHandle,
    BrowserState,
    ContextHandle,
    ContextState,
    PageHandle,
    PageState,
    new_context_id,
    new_page_id,
)
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
from browser_mcp.browser.session import SessionRecord
from browser_mcp.config.models import BrowserEngine, BrowserProfile, BrowserSettings
from browser_mcp.errors import SessionNotFoundError
from tests.fakes import FakePage


class FakeSessions:
    """Stand-in for :class:`SessionManager` used by the state layer."""

    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = mapping
        self._records = {
            session_id: SessionRecord(session_id=session_id, browser_id=browser_id)
            for session_id, browser_id in mapping.items()
        }

    def get_session(self, session_id: str) -> SessionRecord:
        record = self._records.get(session_id)
        if record is None:
            raise SessionNotFoundError(f"session '{session_id}' not found")
        return record

    def session_browser_id(self, session_id: str) -> str:
        return self.get_session(session_id).browser_id

    def session_ids(self) -> list[str]:
        return list(self._mapping)


class FakePool(BrowserPool):
    """BrowserPool subclass exposing controlled registration helpers."""

    async def register_browser(self, browser_id: str = "b1") -> None:
        state = BrowserState(
            browser_id=browser_id,
            engine=BrowserEngine.CHROMIUM,
            headless=True,
            profile=BrowserProfile.TEMPORARY,
        )
        await self.add_browser(
            BrowserHandle(browser_id=browser_id, browser=SimpleNamespace(), state=state)
        )

    async def register_context(self, browser_id: str = "b1", context_id: str | None = None) -> str:
        resolved = context_id or new_context_id()
        state = ContextState(
            context_id=resolved,
            browser_id=browser_id,
            profile=BrowserProfile.TEMPORARY,
        )
        await self.add_context(
            ContextHandle(
                context_id=resolved,
                browser_id=browser_id,
                context=SimpleNamespace(),
                state=state,
            )
        )
        return resolved

    async def register_page(
        self,
        context_id: str,
        page: FakePage,
        page_id: str | None = None,
    ) -> PageHandle:
        resolved = page_id or new_page_id()
        context = self.get_context(context_id)
        state = PageState(page_id=resolved, context_id=context_id, url=page.url)
        handle = PageHandle(
            page_id=resolved,
            context_id=context_id,
            browser_id=context.browser_id,
            page=page,
            state=state,
        )
        await self.add_page(handle)
        return handle


def default_settings(**overrides: Any) -> BrowserSettings:
    """Return test settings with the given nested overrides."""
    return BrowserSettings(**overrides)


async def _close_page(page: Any) -> None:
    """Test factory hook: closing a fake page is a no-op."""
    return None


async def build_runtime(
    settings: BrowserSettings | None = None,
    *,
    page: FakePage | None = None,
    session_id: str = "s1",
    browser_id: str = "b1",
) -> dict[str, Any]:
    """Build the full Phase 2 runtime around a fake page.

    Returns a mapping with ``pool``, ``state``, ``events``, ``frames``,
    ``navigation``, ``history``, ``windows``, ``interactions``, ``waiting``,
    ``page_handle`` and ``settings``.
    """
    from enterprise_mcp.events.bus import EventBus

    resolved_settings = settings or default_settings()
    pool = FakePool(resolved_settings)
    await pool.register_browser(browser_id)
    context_id = await pool.register_context(browser_id)

    fake_page = page or FakePage(url="about:blank")
    page_handle = await pool.register_page(context_id, fake_page)

    sessions = FakeSessions({session_id: browser_id})
    events = EventBus()
    state = StateManager(pool, sessions, resolved_settings)
    policy = NavigationPolicy(resolved_settings)
    frames = FrameManager(state, events, resolved_settings)
    navigation = NavigationManager(state, policy, events, resolved_settings)
    history = HistoryManager(state, events, resolved_settings)
    pages = PageManager(
        pool,
        SimpleNamespace(
            new_page=lambda context: fake_page,
            close_page=_close_page,
        ),
    )
    windows = WindowManager(pool, state, pages, events, resolved_settings)
    interactions = InteractionManager(state, frames, events, resolved_settings)
    waiting = WaitingManager(state, windows, events, resolved_settings)

    return {
        "pool": pool,
        "state": state,
        "events": events,
        "policy": policy,
        "frames": frames,
        "navigation": navigation,
        "history": history,
        "windows": windows,
        "interactions": interactions,
        "waiting": waiting,
        "page_handle": page_handle,
        "page": fake_page,
        "settings": resolved_settings,
        "session_id": session_id,
        "context_id": context_id,
        "browser_id": browser_id,
    }
