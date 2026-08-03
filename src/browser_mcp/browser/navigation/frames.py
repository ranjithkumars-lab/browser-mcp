"""Frame and iframe context management.

:class:`FrameManager` keeps the frame hierarchy of every live page in sync
with the :class:`StateManager`, exposes frame identifiers to tools, and
resolves frame ids back to live Playwright frame objects for interactions.

Playwright does not support "switching" to a frame; instead locators are
created against the desired frame. FrameManager therefore isolates frame
discovery and resolution so interactions can target any frame by id.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from browser_mcp.browser.navigation.state import FrameState, StateManager, frame_guid, new_frame_id
from browser_mcp.config.models import BrowserSettings
from browser_mcp.errors import FrameError
from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

if TYPE_CHECKING:
    from playwright.async_api import Page as PlaywrightPage

__all__ = ["FrameManager", "normalize_frame_id"]


def normalize_frame_id(frame_id: str | None) -> str | None:
    """Return ``None`` for empty or whitespace-only frame ids.

    Tools accept ``frame_id`` as an optional string; LLM clients commonly send
    ``""`` for "no specific frame". Normalizing it to ``None`` makes such calls
    target the page's main frame instead of failing with ``frame '' not found``.
    """
    if frame_id is None:
        return None
    stripped = frame_id.strip()
    return stripped or None


class FrameManager:
    """Discovers, tracks and resolves browser frames."""

    def __init__(
        self,
        state: StateManager,
        events: EventBus,
        settings: BrowserSettings,
    ) -> None:
        self._state = state
        self._events = events
        self._settings = settings

    def page_object(self, session_id: str, page_id: str) -> PlaywrightPage:
        """Return the live Playwright page, verifying session ownership."""
        return self._state.page_in_session(session_id, page_id).page

    async def sync_frames(self, session_id: str, page_id: str) -> list[FrameState]:
        """Reconcile the tracked frame hierarchy with ``page_id``.

        Emits ``frame.changed`` events for frames that attached or detached
        since the last sync and returns the current frame snapshots.
        """
        handle = self._state.page_in_session(session_id, page_id)
        page = handle.page
        before = {st.frame_id for st in self._state.list_frames(page_id)}
        main_guid = frame_guid(page.main_frame)

        current: list[FrameState] = []
        current_ids: set[str] = set()
        for frame in page.frames:
            guid = frame_guid(frame)
            frame_id = self._state.frame_id_for_guid(guid)
            if frame_id is None:
                frame_id = new_frame_id()
            parent = frame.parent_frame
            parent_id = self._state.frame_id_for_guid(frame_guid(parent)) if parent else None
            snapshot = FrameState(
                frame_id=frame_id,
                page_id=page_id,
                context_id=handle.context_id,
                browser_id=handle.browser_id,
                parent_frame_id=parent_id,
                name=frame.name or "",
                url=frame.url or None,
                is_main=guid == main_guid,
            )
            self._state.register_frame(snapshot)
            self._state.bind_frame_object(frame_id, guid, frame)
            current.append(snapshot)
            current_ids.add(frame_id)

        for frame_id in before - current_ids:
            detached = self._state.frame(frame_id)
            self._state.drop_frame(frame_id)
            await self._publish_frame_event("detached", detached)

        for snapshot in current:
            if snapshot.frame_id not in before:
                await self._publish_frame_event("attached", snapshot)

        return current

    async def frame_object_for(self, session_id: str, page_id: str, frame_id: str) -> Any:
        """Return the live Playwright frame for ``frame_id`` within ``page_id``."""
        await self.sync_frames(session_id, page_id)
        snapshot = self._state.frame(frame_id)
        if snapshot.page_id != page_id:
            raise FrameError(f"frame '{frame_id}' does not belong to page '{page_id}'")
        return self._state.frame_object(frame_id)

    async def list_frames(self, session_id: str, page_id: str) -> list[dict[str, Any]]:
        """Return structured frame payloads for tools."""
        snapshots = await self.sync_frames(session_id, page_id)
        return [self._payload(snapshot) for snapshot in snapshots]

    async def main_frame_payload(self, session_id: str, page_id: str) -> dict[str, Any]:
        """Return the structured payload for ``page_id``'s main frame."""
        await self.sync_frames(session_id, page_id)
        return self._payload(self._state.main_frame(page_id))

    @staticmethod
    def _payload(snapshot: FrameState) -> dict[str, Any]:
        return {
            "frame_id": snapshot.frame_id,
            "page_id": snapshot.page_id,
            "parent_frame_id": snapshot.parent_frame_id,
            "name": snapshot.name,
            "url": snapshot.url,
            "is_main": snapshot.is_main,
        }

    async def _publish_frame_event(self, action: str, snapshot: FrameState) -> None:
        await self._events.publish(
            DomainEvent(
                event_name="frame.changed",
                payload={
                    "action": action,
                    "frame_id": snapshot.frame_id,
                    "page_id": snapshot.page_id,
                    "context_id": snapshot.context_id,
                    "browser_id": snapshot.browser_id,
                    "parent_frame_id": snapshot.parent_frame_id,
                    "url": snapshot.url,
                },
            )
        )
