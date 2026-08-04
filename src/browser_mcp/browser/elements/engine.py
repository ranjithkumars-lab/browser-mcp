"""Element engine facade.

:class:`ElementEngine` coordinates element finding and property/state queries
while an :class:`LocatorProvider` isolates it from Playwright:

    ElementEngine -> LocatorRegistry -> LocatorStrategy -> LocatorProvider -> Playwright

``find()`` resolves a locator to a cached ``element_id``; later operations
(``text()``, ``html()``, ``attribute()``, ``state()``, and Phase 2
interactions) consume that ``element_id`` instead of re-evaluating the
locator. Cached references are validated against the live page on every use so
stale references are surfaced as :class:`StaleElementReferenceError`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from browser_mcp.browser.elements.locators.registry import LocatorRegistry
from browser_mcp.browser.elements.models import LocatorModel, LocatorStrategyName
from browser_mcp.browser.elements.properties import ElementProperties
from browser_mcp.browser.elements.provider import LocatorHandle
from browser_mcp.browser.elements.state import ElementState
from browser_mcp.browser.navigation.frames import FrameManager, normalize_frame_id
from browser_mcp.browser.navigation.state import StateManager
from browser_mcp.browser.navigation.timeouts import resolve_timeout
from browser_mcp.config.models import BrowserSettings
from browser_mcp.errors import (
    ElementError,
    ElementNotFoundError,
    ElementStateError,
    PageNotFoundError,
    StaleElementReferenceError,
)
from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

if TYPE_CHECKING:
    from browser_mcp.browser.models import PageHandle

__all__ = ["ElementEngine", "ElementRef"]


def new_element_id() -> str:
    """Return a new unique element identifier."""
    return f"element_{uuid4().hex[:12]}"


def _locator_hint(value: str) -> str:
    """Return an actionable suggestion when a locator fails to match.

    Guards against the most common agent failure mode: guessing selector names
    for login/input controls instead of discovering them first. The hint steers
    the agent toward reading the page structure and using the form tools.
    """
    lowered = value.lower()
    if any(tag in lowered for tag in ("input", "button", "login", "password", "email", "form")):
        return (
            "Hint: inspect the page with browser.scrape.text first, then resolve "
            "fields with browser.element.find using their id/type, or use "
            "browser.form.fill (field='...') which matches by name/id/placeholder/label."
        )
    return (
        "Hint: confirm the selector against the live DOM using browser.scrape.text "
        "or browser.element.find_all, and prefix raw selectors with strategy='css'."
    )


@dataclass(slots=True)
class ElementRef:
    """Cached mapping from an ``element_id`` to a resolved locator."""

    element_id: str
    session_id: str
    browser_id: str
    context_id: str
    page_id: str
    frame_id: str | None
    strategy: str
    value: str
    index: int | None
    base: Any
    created_at: float = field(default_factory=time.monotonic)

    def payload(self) -> dict[str, Any]:
        """Return the public element record."""
        payload: dict[str, Any] = {
            "element_id": self.element_id,
            "session_id": self.session_id,
            "browser_id": self.browser_id,
            "context_id": self.context_id,
            "page_id": self.page_id,
            "strategy": self.strategy,
            "value": self.value,
            "frame_id": self.frame_id,
        }
        if self.index is not None:
            payload["index"] = self.index
        return payload


class ElementEngine:
    """Facade coordinating element resolution, caching and queries."""

    def __init__(
        self,
        state: StateManager,
        frames: FrameManager,
        registry: LocatorRegistry,
        events: EventBus,
        settings: BrowserSettings,
    ) -> None:
        self._state = state
        self._frames = frames
        self._registry = registry
        self._events = events
        self._settings = settings
        self._provider = registry.provider
        self._properties = ElementProperties(self._provider)
        self._state_checks = ElementState(self._provider)
        self._refs: dict[str, ElementRef] = {}

    # -- finding --------------------------------------------------------

    async def find(
        self,
        session_id: str,
        page_id: str,
        strategy: str | LocatorStrategyName,
        value: str,
        *,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
        strict: bool = True,
    ) -> dict[str, Any]:
        """Resolve a locator to a cached ``element_id`` and return its record."""
        frame_id = normalize_frame_id(frame_id)
        model = LocatorModel.model_validate(
            {"strategy": strategy, "value": value, "timeout": timeout_ms, "strict": strict}
        )
        timeout = model.timeout or resolve_timeout(self._settings, "interaction", None)
        handle = self._state.page_in_session(session_id, page_id)
        target = await self._target(session_id, page_id, frame_id)
        start = time.monotonic()

        try:
            locator = await self._registry.resolve(target, model)
            await self._provider.wait_for(locator, "attached", timeout)
        except ElementError as exc:
            if isinstance(exc, ElementNotFoundError):
                await self._emit_not_found(session_id, handle, page_id, frame_id, model)
            raise
        except Exception as exc:
            await self._emit_not_found(session_id, handle, page_id, frame_id, model)
            raise ElementNotFoundError(
                f"element '{model.strategy}:{model.value}' not found on page '{page_id}' "
                f"within {timeout}ms. {_locator_hint(model.value)}"
            ) from exc

        ref = self._cache(
            session_id,
            handle,
            page_id,
            frame_id,
            locator,
            model.strategy.value,
            model.value,
            index=None,
        )
        payload = ref.payload()
        payload["count"] = 1
        payload["duration_ms"] = self._duration_ms(start)
        await self._emit_resolved(ref)
        await self._emit_found(ref, payload)
        return payload

    async def find_all(
        self,
        session_id: str,
        page_id: str,
        strategy: str | LocatorStrategyName,
        value: str,
        *,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Resolve every match to a cached ``element_id``."""
        frame_id = normalize_frame_id(frame_id)
        model = LocatorModel.model_validate(
            {"strategy": strategy, "value": value, "timeout": timeout_ms, "strict": False}
        )
        timeout = model.timeout or resolve_timeout(self._settings, "interaction", None)
        handle = self._state.page_in_session(session_id, page_id)
        target = await self._target(session_id, page_id, frame_id)
        start = time.monotonic()

        locator = self._registry.build(target, model)
        try:
            await self._provider.wait_for(locator, "attached", timeout, strict=False)
        except Exception as exc:
            await self._emit_not_found(session_id, handle, page_id, frame_id, model)
            raise ElementNotFoundError(
                f"no element matched '{model.strategy}:{model.value}' on page '{page_id}' "
                f"within {timeout}ms. {_locator_hint(model.value)}"
            ) from exc

        count = await self._provider.count(locator)
        elements: list[dict[str, Any]] = []
        for index in range(count):
            ref = self._cache(
                session_id,
                handle,
                page_id,
                frame_id,
                locator,
                model.strategy.value,
                model.value,
                index=index,
            )
            elements.append({"element_id": ref.element_id, "index": index})

        payload: dict[str, Any] = {
            "session_id": session_id,
            "browser_id": handle.browser_id,
            "context_id": handle.context_id,
            "page_id": page_id,
            "frame_id": frame_id,
            "strategy": model.strategy.value,
            "value": model.value,
            "count": count,
            "elements": elements,
            "duration_ms": self._duration_ms(start),
        }
        await self._emit_found(self._refs[elements[0]["element_id"]], payload)
        return payload

    # -- property / state queries --------------------------------------

    async def text(self, session_id: str, page_id: str, element_id: str) -> dict[str, Any]:
        """Return the rendered text of ``element_id``."""
        ref = self._require_ref(element_id, page_id)
        locator = self._resolve_locator(ref)
        start = time.monotonic()
        try:
            text = await self._properties.text(locator)
        except Exception as exc:
            raise ElementStateError(
                f"failed to read text of element '{element_id}': {exc}"
            ) from exc
        return {
            **ref.payload(),
            "text": text,
            "duration_ms": self._duration_ms(start),
        }

    async def html(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        *,
        outer: bool = False,
    ) -> dict[str, Any]:
        """Return the inner (or outer) HTML of ``element_id``."""
        ref = self._require_ref(element_id, page_id)
        locator = self._resolve_locator(ref)
        start = time.monotonic()
        try:
            markup = await self._properties.html(locator, outer=outer)
        except Exception as exc:
            raise ElementStateError(
                f"failed to read HTML of element '{element_id}': {exc}"
            ) from exc
        return {
            **ref.payload(),
            "html": markup,
            "outer": outer,
            "duration_ms": self._duration_ms(start),
        }

    async def attribute(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        attribute_name: str,
    ) -> dict[str, Any]:
        """Return the value of ``attribute_name`` on ``element_id``."""
        ref = self._require_ref(element_id, page_id)
        locator = self._resolve_locator(ref)
        start = time.monotonic()
        try:
            value = await self._properties.attribute(locator, attribute_name)
        except Exception as exc:
            raise ElementStateError(
                f"failed to read attribute '{attribute_name}' of element '{element_id}': {exc}"
            ) from exc
        return {
            **ref.payload(),
            "attribute_name": attribute_name,
            "value": value,
            "duration_ms": self._duration_ms(start),
        }

    async def state(self, session_id: str, page_id: str, element_id: str) -> dict[str, Any]:
        """Return the boolean state snapshot of ``element_id``."""
        ref = self._require_ref(element_id, page_id)
        locator = self._resolve_locator(ref)
        start = time.monotonic()
        try:
            checks = await self._state_checks.snapshot(locator)
        except Exception as exc:
            raise ElementStateError(
                f"failed to inspect state of element '{element_id}': {exc}"
            ) from exc
        payload = {
            **ref.payload(),
            **checks,
            "duration_ms": self._duration_ms(start),
        }
        await self._events.publish(
            DomainEvent(
                event_name="element.state_changed",
                payload={
                    "element_id": element_id,
                    "session_id": session_id,
                    "page_id": page_id,
                    **checks,
                },
            )
        )
        return payload

    # -- input actions --------------------------------------------------

    async def fill(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        value: str,
        *,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Replace the value of ``element_id`` with ``value``."""
        async def _fill(locator: LocatorHandle, timeout: int | None) -> None:
            await self._provider.fill(locator, value, timeout)
        return await self._act(
            "fill",
            session_id,
            page_id,
            element_id,
            _fill,
            timeout_ms=timeout_ms,
            extra={"value": value},
        )

    async def type_text(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        text: str,
        *,
        delay_ms: int | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Type ``text`` into ``element_id`` one key at a time."""
        timeout = resolve_timeout(self._settings, "interaction", timeout_ms)
        ref = self._require_ref(element_id, page_id)
        locator = self._resolve_locator(ref)
        start = time.monotonic()
        try:
            await self._provider.press_sequentially(locator, text, delay_ms=delay_ms)
        except Exception as exc:
            raise ElementStateError(
                f"failed to type into element '{element_id}': {exc}"
            ) from exc
        return {
            **ref.payload(),
            "action": "type",
            "text": text,
            "delay_ms": delay_ms,
            "timeout_ms": timeout,
            "duration_ms": self._duration_ms(start),
        }

    async def clear(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        *,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Clear the value of ``element_id``."""
        async def _clear(locator: LocatorHandle, timeout: int | None) -> None:
            await self._provider.clear(locator, timeout)
        return await self._act(
            "clear",
            session_id,
            page_id,
            element_id,
            _clear,
            timeout_ms=timeout_ms,
        )

    async def press(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        key: str,
        *,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Press a keyboard ``key`` (e.g. ``Enter``) on ``element_id``."""
        async def _press(locator: LocatorHandle, timeout: int | None) -> None:
            await self._provider.press(locator, key, timeout)
        return await self._act(
            "press",
            session_id,
            page_id,
            element_id,
            _press,
            timeout_ms=timeout_ms,
            extra={"key": key},
        )

    async def select_option(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        value: str,
        *,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Select the option ``value`` in the ``<select>`` ``element_id``."""
        async def _select_option(locator: LocatorHandle, timeout: int | None) -> None:
            await self._provider.select_option(locator, value, timeout)
        return await self._act(
            "select_option",
            session_id,
            page_id,
            element_id,
            _select_option,
            timeout_ms=timeout_ms,
            extra={"value": value},
        )

    async def check(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        *,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Check the checkbox/radio ``element_id``."""
        async def _check(locator: LocatorHandle, timeout: int | None) -> None:
            await self._provider.check(locator, timeout)
        return await self._act(
            "check",
            session_id,
            page_id,
            element_id,
            _check,
            timeout_ms=timeout_ms,
        )

    async def uncheck(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        *,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Uncheck the checkbox/radio ``element_id``."""
        async def _uncheck(locator: LocatorHandle, timeout: int | None) -> None:
            await self._provider.uncheck(locator, timeout)
        return await self._act(
            "uncheck",
            session_id,
            page_id,
            element_id,
            _uncheck,
            timeout_ms=timeout_ms,
        )

    async def input_value(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
    ) -> dict[str, Any]:
        """Return the current value of ``element_id``."""
        ref = self._require_ref(element_id, page_id)
        locator = self._resolve_locator(ref)
        start = time.monotonic()
        try:
            value = await self._provider.input_value(locator)
        except Exception as exc:
            raise ElementStateError(
                f"failed to read input value of element '{element_id}': {exc}"
            ) from exc
        return {
            **ref.payload(),
            "value": value,
            "duration_ms": self._duration_ms(start),
        }

    async def focus(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        *,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Move keyboard focus to ``element_id``."""
        async def _focus(locator: LocatorHandle, timeout: int | None) -> None:
            await self._provider.focus(locator, timeout)
        return await self._act(
            "focus",
            session_id,
            page_id,
            element_id,
            _focus,
            timeout_ms=timeout_ms,
        )

    # -- resolution helpers (used by InteractionManager) ---------------

    async def resolve_locator(
        self,
        session_id: str,
        page_id: str,
        strategy: str | LocatorStrategyName,
        value: str,
        *,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
        strict: bool = True,
    ) -> Any:
        """Return a locator handle for ``strategy``/``value`` (no caching)."""
        frame_id = normalize_frame_id(frame_id)
        model = LocatorModel.model_validate(
            {"strategy": strategy, "value": value, "timeout": timeout_ms, "strict": strict}
        )
        target = await self._target(session_id, page_id, frame_id)
        return await self._registry.resolve(target, model)

    async def locator_for(self, element_id: str, page_id: str) -> Any:
        """Return the resolved locator handle for ``element_id``."""
        ref = self._require_ref(element_id, page_id)
        return self._resolve_locator(ref)

    def ref_for(self, element_id: str, page_id: str | None = None) -> ElementRef:
        """Return the cached :class:`ElementRef`, validating liveness."""
        return self._require_ref(element_id, page_id)

    def release(self, element_id: str) -> None:
        """Drop ``element_id`` from the cache."""
        self._refs.pop(element_id, None)

    def drop_page(self, page_id: str) -> None:
        """Drop every cached element reference that belongs to ``page_id``."""
        for element_id in [eid for eid, ref in self._refs.items() if ref.page_id == page_id]:
            self._refs.pop(element_id, None)

    def cache_stats(self) -> dict[str, int]:
        """Return cache size and per-page element counts for observability."""
        return {"cached_elements": len(self._refs)}

    # -- internals ------------------------------------------------------

    async def _target(self, session_id: str, page_id: str, frame_id: str | None) -> Any:
        frame_id = normalize_frame_id(frame_id)
        if frame_id is not None:
            return await self._frames.frame_object_for(session_id, page_id, frame_id)
        return self._frames.page_object(session_id, page_id)

    async def _act(
        self,
        action: str,
        session_id: str,
        page_id: str,
        element_id: str,
        op: Any,
        *,
        timeout_ms: int | None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        timeout = resolve_timeout(self._settings, "interaction", timeout_ms)
        ref = self._require_ref(element_id, page_id)
        locator = self._resolve_locator(ref)
        start = time.monotonic()
        try:
            await op(locator, timeout)
        except Exception as exc:
            raise ElementStateError(
                f"failed to {action} element '{element_id}': {exc}"
            ) from exc
        payload: dict[str, Any] = {
            **ref.payload(),
            "action": action,
            "timeout_ms": timeout,
            "duration_ms": self._duration_ms(start),
        }
        if extra:
            payload.update(extra)
        await self._events.publish(
            DomainEvent(
                event_name="element.action.completed",
                payload={
                    "action": action,
                    "element_id": element_id,
                    "session_id": session_id,
                    "page_id": page_id,
                },
            )
        )
        return payload

    def _cache(
        self,
        session_id: str,
        handle: PageHandle,
        page_id: str,
        frame_id: str | None,
        base: Any,
        strategy: str,
        value: str,
        *,
        index: int | None,
    ) -> ElementRef:
        ref = ElementRef(
            element_id=new_element_id(),
            session_id=session_id,
            browser_id=handle.browser_id,
            context_id=handle.context_id,
            page_id=page_id,
            frame_id=frame_id,
            strategy=strategy,
            value=value,
            index=index,
            base=base,
        )
        self._refs[ref.element_id] = ref
        return ref

    def _require_ref(self, element_id: str, page_id: str | None) -> ElementRef:
        ref = self._refs.get(element_id)
        if ref is None:
            raise ElementNotFoundError(f"unknown element_id '{element_id}'")
        if page_id is not None and ref.page_id != page_id:
            raise ElementNotFoundError(
                f"element '{element_id}' belongs to page '{ref.page_id}', not '{page_id}'"
            )
        try:
            self._state.page(ref.page_id)
        except PageNotFoundError as exc:
            self._refs.pop(element_id, None)
            raise StaleElementReferenceError(
                f"element '{element_id}' refers to a page that has closed"
            ) from exc
        return ref

    def _resolve_locator(self, ref: ElementRef) -> Any:
        if ref.index is None:
            return ref.base
        return self._provider.nth(ref.base, ref.index)

    async def _emit_resolved(self, ref: ElementRef) -> None:
        await self._events.publish(
            DomainEvent(
                event_name="element.resolved",
                payload=dict(ref.payload()),
            )
        )

    async def _emit_found(self, ref: ElementRef, payload: dict[str, Any]) -> None:
        await self._events.publish(
            DomainEvent(
                event_name="element.found",
                payload={
                    "element_id": ref.element_id,
                    "session_id": ref.session_id,
                    "page_id": ref.page_id,
                    "count": payload.get("count"),
                    "duration_ms": payload.get("duration_ms"),
                },
            )
        )

    async def _emit_not_found(
        self,
        session_id: str,
        handle: PageHandle,
        page_id: str,
        frame_id: str | None,
        model: LocatorModel,
    ) -> None:
        await self._events.publish(
            DomainEvent(
                event_name="element.not_found",
                payload={
                    "session_id": session_id,
                    "browser_id": handle.browser_id,
                    "context_id": handle.context_id,
                    "page_id": page_id,
                    "frame_id": frame_id,
                    "strategy": model.strategy.value,
                    "value": model.value,
                },
            )
        )

    @staticmethod
    def _duration_ms(start: float) -> float:
        return round((time.monotonic() - start) * 1000, 3)
