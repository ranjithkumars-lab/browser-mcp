"""User interactions: clicks, hovers and scrolling.

:class:`InteractionManager` routes every interaction through
:class:`LocatorResolver`, isolating element-finding from interaction logic:

    InteractionManager -> LocatorResolver -> ElementEngine -> LocatorProvider -> action()

Actions accept either a plain CSS ``selector`` (legacy Phase 2 style) or a
previously resolved ``element_id`` produced by the Phase 3 element engine, so
agents can find an element once and reuse it across many interactions.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Literal

from browser_mcp.browser.navigation.frames import FrameManager, normalize_frame_id
from browser_mcp.browser.navigation.state import StateManager
from browser_mcp.browser.navigation.timeouts import resolve_timeout
from browser_mcp.config.models import BrowserSettings
from browser_mcp.errors import InteractionError
from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

if TYPE_CHECKING:
    from browser_mcp.browser.elements.engine import ElementEngine
    from browser_mcp.browser.elements.resolver import LocatorResolver

__all__ = ["InteractionManager", "LocatorResolver"]

Button = Literal["left", "right", "middle"]
ScrollAlign = Literal["start", "center", "end", "nearest"]


def __getattr__(name: str) -> Any:
    if name == "LocatorResolver":
        from browser_mcp.browser.elements.resolver import LocatorResolver

        return LocatorResolver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class InteractionManager:
    """Executes clicks, hovers and scrolls on a page."""

    def __init__(
        self,
        state: StateManager,
        frames: FrameManager,
        events: EventBus,
        settings: BrowserSettings,
        engine: ElementEngine,
    ) -> None:
        from browser_mcp.browser.elements.resolver import LocatorResolver

        self._state = state
        self._frames = frames
        self._events = events
        self._settings = settings
        self._engine = engine
        self._resolver = LocatorResolver(frames, engine)

    # -- pointer interactions ------------------------------------------

    async def click(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        *,
        element_id: str | None = None,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
        button: Button = "left",
        click_count: int = 1,
        delay_ms: int | None = None,
    ) -> dict[str, Any]:
        """Click the element matching ``selector`` (or ``element_id``)."""
        frame_id = normalize_frame_id(frame_id)
        locator = await self._resolve_locator(session_id, page_id, selector, element_id, frame_id)
        timeout = resolve_timeout(self._settings, "interaction", timeout_ms)
        start = time.monotonic()
        try:
            await locator.click(
                timeout=timeout,
                button=button,
                click_count=click_count,
                delay=delay_ms or 0,
            )
        except Exception as exc:
            raise InteractionError(
                f"failed to click '{self._describe(selector, element_id)}' "
                f"on page '{page_id}': {exc}"
            ) from exc
        return await self._pointer_payload(
            "click", session_id, page_id, selector, element_id, frame_id, start, timeout
        )

    async def double_click(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        *,
        element_id: str | None = None,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
        delay_ms: int | None = None,
    ) -> dict[str, Any]:
        """Double-click the element matching ``selector`` (or ``element_id``)."""
        frame_id = normalize_frame_id(frame_id)
        locator = await self._resolve_locator(session_id, page_id, selector, element_id, frame_id)
        timeout = resolve_timeout(self._settings, "interaction", timeout_ms)
        start = time.monotonic()
        try:
            await locator.dblclick(timeout=timeout, delay=delay_ms or 0)
        except Exception as exc:
            raise InteractionError(
                f"failed to double-click '{self._describe(selector, element_id)}' "
                f"on page '{page_id}': {exc}"
            ) from exc
        return await self._pointer_payload(
            "double_click", session_id, page_id, selector, element_id, frame_id, start, timeout
        )

    async def right_click(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        *,
        element_id: str | None = None,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Right-click (context menu) the element matching ``selector``."""
        frame_id = normalize_frame_id(frame_id)
        locator = await self._resolve_locator(session_id, page_id, selector, element_id, frame_id)
        timeout = resolve_timeout(self._settings, "interaction", timeout_ms)
        start = time.monotonic()
        try:
            await locator.click(timeout=timeout, button="right")
        except Exception as exc:
            raise InteractionError(
                f"failed to right-click '{self._describe(selector, element_id)}' "
                f"on page '{page_id}': {exc}"
            ) from exc
        return await self._pointer_payload(
            "right_click", session_id, page_id, selector, element_id, frame_id, start, timeout
        )

    async def hover(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        *,
        element_id: str | None = None,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Hover the element matching ``selector`` (or ``element_id``)."""
        frame_id = normalize_frame_id(frame_id)
        locator = await self._resolve_locator(session_id, page_id, selector, element_id, frame_id)
        timeout = resolve_timeout(self._settings, "interaction", timeout_ms)
        start = time.monotonic()
        try:
            await locator.hover(timeout=timeout)
        except Exception as exc:
            raise InteractionError(
                f"failed to hover '{self._describe(selector, element_id)}' "
                f"on page '{page_id}': {exc}"
            ) from exc
        return await self._pointer_payload(
            "hover", session_id, page_id, selector, element_id, frame_id, start, timeout
        )

    # -- scrolling -----------------------------------------------------

    async def scroll_to(
        self,
        session_id: str,
        page_id: str,
        x: int,
        y: int,
        *,
        frame_id: str | None = None,
    ) -> dict[str, Any]:
        """Scroll the viewport of ``page_id`` to the absolute position (``x``, ``y``)."""
        frame_id = normalize_frame_id(frame_id)
        target = await self._scroll_target(session_id, page_id, frame_id)
        start = time.monotonic()
        try:
            await target.evaluate(
                "(args) => window.scrollTo(args.x, args.y)",
                {"x": x, "y": y},
            )
        except Exception as exc:
            raise InteractionError(
                f"failed to scroll to ({x}, {y}) on page '{page_id}': {exc}"
            ) from exc
        return {
            "action": "scroll_to",
            "page_id": page_id,
            "x": x,
            "y": y,
            "frame_id": frame_id,
            "duration_ms": round((time.monotonic() - start) * 1000, 3),
        }

    async def scroll_by(
        self,
        session_id: str,
        page_id: str,
        delta_x: int,
        delta_y: int,
        *,
        frame_id: str | None = None,
    ) -> dict[str, Any]:
        """Scroll the viewport of ``page_id`` by (``delta_x``, ``delta_y``)."""
        frame_id = normalize_frame_id(frame_id)
        target = await self._scroll_target(session_id, page_id, frame_id)
        start = time.monotonic()
        try:
            await target.evaluate(
                "(args) => window.scrollBy(args.x, args.y)",
                {"x": delta_x, "y": delta_y},
            )
        except Exception as exc:
            raise InteractionError(
                f"failed to scroll by ({delta_x}, {delta_y}) on page '{page_id}': {exc}"
            ) from exc
        return {
            "action": "scroll_by",
            "page_id": page_id,
            "delta_x": delta_x,
            "delta_y": delta_y,
            "frame_id": frame_id,
            "duration_ms": round((time.monotonic() - start) * 1000, 3),
        }

    async def scroll_element(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        *,
        element_id: str | None = None,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
        align: ScrollAlign = "center",
    ) -> dict[str, Any]:
        """Scroll the element matching ``selector`` into the viewport."""
        frame_id = normalize_frame_id(frame_id)
        locator = await self._resolve_locator(session_id, page_id, selector, element_id, frame_id)
        timeout = resolve_timeout(self._settings, "interaction", timeout_ms)
        start = time.monotonic()
        try:
            await locator.scroll_into_view_if_needed(timeout=timeout)
        except Exception as exc:
            raise InteractionError(
                f"failed to scroll element '{self._describe(selector, element_id)}' "
                f"on page '{page_id}': {exc}"
            ) from exc
        return {
            "action": "scroll_element",
            "page_id": page_id,
            "selector": selector,
            "element_id": element_id,
            "frame_id": frame_id,
            "align": align,
            "duration_ms": round((time.monotonic() - start) * 1000, 3),
        }

    # -- internals -----------------------------------------------------

    async def _resolve_locator(
        self,
        session_id: str,
        page_id: str,
        selector: str | None,
        element_id: str | None,
        frame_id: str | None,
    ) -> Any:
        if element_id is not None:
            return await self._engine.locator_for(element_id, page_id)
        if not selector or not selector.strip():
            raise InteractionError("interaction selector must not be empty")
        return await self._resolver.resolve(
            session_id, page_id, selector, frame_id=frame_id, strict=False
        )

    @staticmethod
    def _describe(selector: str | None, element_id: str | None) -> str:
        if element_id is not None:
            return f"element '{element_id}'"
        return f"selector '{selector}'"

    async def _scroll_target(self, session_id: str, page_id: str, frame_id: str | None) -> Any:
        frame_id = normalize_frame_id(frame_id)
        if frame_id is not None:
            return await self._frames.frame_object_for(session_id, page_id, frame_id)
        return self._frames.page_object(session_id, page_id)

    async def _pointer_payload(
        self,
        action: str,
        session_id: str,
        page_id: str,
        selector: str | None,
        element_id: str | None,
        frame_id: str | None,
        start: float,
        timeout: int,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "action": action,
            "session_id": session_id,
            "page_id": page_id,
            "frame_id": frame_id,
            "timeout_ms": timeout,
            "duration_ms": round((time.monotonic() - start) * 1000, 3),
        }
        if element_id is not None:
            payload["element_id"] = element_id
        else:
            payload["selector"] = selector
        await self._events.publish(
            DomainEvent(
                event_name="interaction.completed",
                payload=dict(payload),
            )
        )
        return payload
