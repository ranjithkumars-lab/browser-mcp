"""Session lifecycle management.

A *session* is the top-level unit of work. It maps a ``session_id`` to a live
browser (and, transitively, its contexts and pages). ``SessionManager`` is the
facade the MCP tools call; it delegates down the strict resource hierarchy:

    Session -> Browser -> Context -> Page
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

import structlog

from browser_mcp.browser.context import ContextManager
from browser_mcp.browser.manager import BrowserManager
from browser_mcp.browser.models import new_session_id
from browser_mcp.browser.page import PageManager
from browser_mcp.browser.pool import BrowserPool
from browser_mcp.config.models import BrowserEngine, BrowserProfile
from browser_mcp.errors import SessionError, SessionNotFoundError

__all__ = ["SessionManager", "SessionRecord"]


@dataclass(slots=True)
class SessionRecord:
    """Tracks the mapping between a session and its browser."""

    session_id: str
    browser_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SessionManager:
    """Top-level facade over the browser resource hierarchy."""

    def __init__(
        self,
        pool: BrowserPool,
        browsers: BrowserManager,
        contexts: ContextManager,
        pages: PageManager,
    ) -> None:
        self._pool = pool
        self._browsers = browsers
        self._contexts = contexts
        self._pages = pages
        self._sessions: dict[str, SessionRecord] = {}
        self._logger = structlog.get_logger("browser_mcp.session")

    @property
    def pool(self) -> BrowserPool:
        """Return the underlying browser pool (for health reporting)."""
        return self._pool

    async def start(self) -> None:
        """Start the session manager (no-op; browsers start lazily)."""

    async def stop(self) -> None:
        """Close every live browser and clear all sessions."""
        for browser_id in tuple(self._pool.browser_ids()):
            try:
                await self._browsers.close(browser_id)
            except Exception:
                self._logger.exception("session_stop_close_failed", browser_id=browser_id)
        self._sessions.clear()

    # -- session lifecycle ---------------------------------------------

    async def create_session(
        self,
        *,
        engine: BrowserEngine | str | None = None,
        headless: bool | None = None,
        profile: BrowserProfile | str | None = None,
        label: str | None = None,
    ) -> dict[str, object]:
        """Create a new session (launches a browser).

        Returns
        -------
        A structured mapping with ``session_id``, ``browser_id`` and the
        applied ``profile``.
        """
        state = await self._browsers.launch(
            engine=engine, headless=headless, profile=profile, label=label
        )
        session_id = new_session_id()
        self._sessions[session_id] = SessionRecord(
            session_id=session_id, browser_id=state.browser_id
        )
        self._logger.info(
            "session_created",
            session_id=session_id,
            browser_id=state.browser_id,
            engine=state.engine.value,
            profile=state.profile.value,
        )
        return {
            "session_id": session_id,
            "browser_id": state.browser_id,
            "profile": state.profile.value,
        }

    async def close_session(self, session_id: str) -> dict[str, object]:
        """Close ``session_id`` and all of its resources."""
        record = self._resolve_session(session_id)
        await self._browsers.close(record.browser_id)
        self._sessions.pop(session_id, None)
        self._logger.info("session_closed", session_id=session_id)
        return {"session_id": session_id, "closed": True}

    def get_session(self, session_id: str) -> SessionRecord:
        """Return the session record for ``session_id``."""
        return self._resolve_session(session_id)

    def session_browser_id(self, session_id: str) -> str:
        """Return the browser id owned by ``session_id``."""
        return self._resolve_session(session_id).browser_id

    def _resolve_session(self, session_id: str) -> SessionRecord:
        record = self._sessions.get(session_id)
        if record is None:
            raise SessionNotFoundError(f"session '{session_id}' not found")
        return record

    # -- context / page lifecycle --------------------------------------

    async def create_context(
        self,
        session_id: str,
        *,
        profile: BrowserProfile | str | None = None,
        label: str | None = None,
    ) -> dict[str, object]:
        """Create a context inside the browser owned by ``session_id``."""
        browser_id = self.session_browser_id(session_id)
        state = await self._contexts.create(browser_id, profile=profile, label=label)
        return {
            "session_id": session_id,
            "browser_id": browser_id,
            "context_id": state.context_id,
            "profile": state.profile.value,
        }

    async def close_context(self, session_id: str, context_id: str) -> dict[str, object]:
        """Close ``context_id``, verifying it belongs to ``session_id``."""
        browser_id = self.session_browser_id(session_id)
        handle = self._pool.get_context(context_id)
        if handle.browser_id != browser_id:
            raise SessionError(
                f"context '{context_id}' does not belong to session '{session_id}'"
            )
        await self._contexts.close(context_id)
        return {"session_id": session_id, "context_id": context_id, "closed": True}

    async def new_page(
        self,
        session_id: str,
        context_id: str,
        *,
        url: str | None = None,
    ) -> dict[str, object]:
        """Open a new page in ``context_id`` within ``session_id``."""
        browser_id = self.session_browser_id(session_id)
        handle = self._pool.get_context(context_id)
        if handle.browser_id != browser_id:
            raise SessionError(
                f"context '{context_id}' does not belong to session '{session_id}'"
            )
        state = await self._pages.create(context_id, url=url)
        return {
            "session_id": session_id,
            "context_id": context_id,
            "page_id": state.page_id,
            "url": state.url,
        }

    async def close_page(self, session_id: str, page_id: str) -> dict[str, object]:
        """Close ``page_id``, verifying it belongs to ``session_id``."""
        browser_id = self.session_browser_id(session_id)
        handle = self._pool.get_page(page_id)
        if handle.browser_id != browser_id:
            raise SessionError(
                f"page '{page_id}' does not belong to session '{session_id}'"
            )
        await self._pages.close(page_id)
        return {"session_id": session_id, "page_id": page_id, "closed": True}

    # -- diagnostics ---------------------------------------------------

    def stats(self) -> dict[str, int]:
        """Return pool statistics for health reporting."""
        return self._pool.stats()

    def session_ids(self) -> list[str]:
        """Return all live session identifiers."""
        return list(self._sessions)
