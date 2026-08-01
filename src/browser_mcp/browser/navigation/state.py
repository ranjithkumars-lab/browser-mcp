"""Central state management for the browser resource hierarchy.

:class:`StateManager` is the **single source of truth** for the full
hierarchy:

    Session -> Browser -> Context -> Page -> Frame

It composes the :class:`BrowserPool` (authoritative store of live handles)
with the :class:`SessionManager` (session mapping) and additionally tracks
frame-level state and popups, which the pool does not model.

No other manager owns or caches state directly; they delegate all hierarchy
and frame queries to this manager.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

from browser_mcp.browser.models import BrowserHandle, ContextHandle, PageHandle
from browser_mcp.browser.pool import BrowserPool
from browser_mcp.config.models import BrowserSettings
from browser_mcp.errors import FrameError, PopupError, SessionError

if TYPE_CHECKING:
    from playwright.async_api import Frame as PlaywrightFrame

    from browser_mcp.browser.session import SessionManager, SessionRecord

__all__ = ["FrameState", "PopupState", "StateManager", "new_frame_id"]


def new_frame_id() -> str:
    """Return a new unique frame identifier."""
    return f"frame_{uuid4().hex[:12]}"


@dataclass(slots=True)
class FrameState:
    """Read-only snapshot describing a live frame within a page."""

    frame_id: str
    page_id: str
    context_id: str
    browser_id: str
    parent_frame_id: str | None = None
    name: str = ""
    url: str | None = None
    is_main: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: Literal["attached", "detached"] = "attached"


@dataclass(slots=True)
class PopupState:
    """Read-only snapshot describing a popup (new tab/window) page."""

    popup_id: str
    origin_page_id: str
    context_id: str
    browser_id: str
    url: str | None = None
    title: str | None = None
    opened_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: Literal["open", "closed"] = "open"


def frame_guid(frame: PlaywrightFrame) -> str:
    """Return the stable Playwright driver guid for ``frame``.

    The guid is stable for the lifetime of the frame and uniquely identifies
    it even across wrapper object recreation. It is read defensively (both
    ``guid`` and the private ``_guid`` attribute are checked) so the state
    layer degrades gracefully if Playwright changes its internals.
    """
    impl = getattr(frame, "_impl_obj", None)
    guid = getattr(impl, "guid", None)
    if not isinstance(guid, str) or not guid:
        guid = getattr(impl, "_guid", None)
    if not isinstance(guid, str) or not guid:
        raise FrameError("cannot determine stable identity of Playwright frame")
    return guid


class StateManager:
    """Single source of truth for the browser resource hierarchy."""

    def __init__(
        self,
        pool: BrowserPool,
        sessions: SessionManager,
        settings: BrowserSettings,
    ) -> None:
        self._pool = pool
        self._sessions = sessions
        self._settings = settings
        self._lock = asyncio.Lock()
        self._frames: dict[str, FrameState] = {}
        self._guid_to_frame: dict[str, str] = {}
        self._frame_objects: dict[str, PlaywrightFrame] = {}
        self._popups: dict[str, PopupState] = {}

    # -- session/browser/context/page ----------------------------------

    def session(self, session_id: str) -> SessionRecord:
        """Return the session record for ``session_id``."""
        return self._sessions.get_session(session_id)

    def browser(self, browser_id: str) -> BrowserHandle:
        """Return the live handle for ``browser_id``."""
        return self._pool.get_browser(browser_id)

    def context(self, context_id: str) -> ContextHandle:
        """Return the live handle for ``context_id``."""
        return self._pool.get_context(context_id)

    def page(self, page_id: str) -> PageHandle:
        """Return the live handle for ``page_id``."""
        return self._pool.get_page(page_id)

    def page_in_session(self, session_id: str, page_id: str) -> PageHandle:
        """Return the page handle, verifying ownership by ``session_id``."""
        browser_id = self._sessions.session_browser_id(session_id)
        handle = self._pool.get_page(page_id)
        if handle.browser_id != browser_id:
            raise SessionError(f"page '{page_id}' does not belong to session '{session_id}'")
        return handle

    def context_in_session(self, session_id: str, context_id: str) -> ContextHandle:
        """Return the context handle, verifying ownership by ``session_id``."""
        browser_id = self._sessions.session_browser_id(session_id)
        handle = self._pool.get_context(context_id)
        if handle.browser_id != browser_id:
            raise SessionError(f"context '{context_id}' does not belong to session '{session_id}'")
        return handle

    def session_ids(self) -> list[str]:
        """Return all live session identifiers."""
        return self._sessions.session_ids()

    # -- frames --------------------------------------------------------

    def register_frame(self, state: FrameState) -> None:
        """Register or update ``state`` in the frame registry."""
        self._frames[state.frame_id] = state

    def unregister_page_frames(self, page_id: str) -> None:
        """Remove every frame belonging to ``page_id``."""
        for frame_id in [fid for fid, st in self._frames.items() if st.page_id == page_id]:
            self._frames.pop(frame_id, None)
            self._frame_objects.pop(frame_id, None)

    def list_frames(self, page_id: str) -> list[FrameState]:
        """Return all frame snapshots currently tracked for ``page_id``."""
        return [st for st in self._frames.values() if st.page_id == page_id]

    def frame(self, frame_id: str) -> FrameState:
        """Return the frame snapshot for ``frame_id``."""
        state = self._frames.get(frame_id)
        if state is None:
            raise FrameError(f"frame '{frame_id}' not found")
        return state

    def has_frame(self, frame_id: str) -> bool:
        """Return whether ``frame_id`` is currently tracked."""
        return frame_id in self._frames

    def main_frame(self, page_id: str) -> FrameState:
        """Return the main frame snapshot for ``page_id``."""
        for state in self.list_frames(page_id):
            if state.is_main:
                return state
        raise FrameError(f"page '{page_id}' has no main frame tracked")

    def frame_object(self, frame_id: str) -> PlaywrightFrame:
        """Return the live Playwright frame object for ``frame_id``."""
        frame = self._frame_objects.get(frame_id)
        if frame is None:
            raise FrameError(f"frame '{frame_id}' is not a live frame")
        return frame

    def frame_id_for_guid(self, guid: str) -> str | None:
        """Return the tracked frame id for a Playwright driver guid."""
        return self._guid_to_frame.get(guid)

    def bind_frame_object(self, frame_id: str, guid: str, frame: PlaywrightFrame) -> None:
        """Bind ``frame_id`` to a Playwright driver guid and live object."""
        self._guid_to_frame[guid] = frame_id
        self._frame_objects[frame_id] = frame

    def drop_frame(self, frame_id: str) -> None:
        """Remove ``frame_id`` and every reference to it."""
        self._frames.pop(frame_id, None)
        self._frame_objects.pop(frame_id, None)
        for guid, mapped in tuple(self._guid_to_frame.items()):
            if mapped == frame_id:
                self._guid_to_frame.pop(guid, None)

    # -- popups --------------------------------------------------------

    def register_popup(self, state: PopupState) -> None:
        """Register ``state`` in the popup registry."""
        self._popups[state.popup_id] = state

    def popups(self) -> list[PopupState]:
        """Return all tracked open popups."""
        return list(self._popups.values())

    def popup(self, popup_id: str) -> PopupState:
        """Return the popup snapshot for ``popup_id``."""
        state = self._popups.get(popup_id)
        if state is None:
            raise PopupError(f"popup '{popup_id}' not found")
        return state

    def close_popup(self, popup_id: str) -> None:
        """Mark ``popup_id`` as closed and remove it from the registry."""
        state = self._popups.pop(popup_id, None)
        if state is None:
            raise PopupError(f"popup '{popup_id}' not found")

    # -- metrics -------------------------------------------------------

    def metrics(self) -> dict[str, int]:
        """Return runtime metrics for logs and health endpoints."""
        stats = self._pool.stats()
        return {
            "browsers": stats["browsers"],
            "contexts": stats["contexts"],
            "pages": stats["pages"],
            "frames": len(self._frames),
            "popups": len(self._popups),
            "sessions": len(self._sessions.session_ids()),
        }
