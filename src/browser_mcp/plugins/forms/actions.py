"""Form action implementations.

Provides ``fill``, ``check``, ``uncheck``, ``select``, and ``submit``
logic backed by Playwright locators and the shared :class:`RetryPolicy`.
"""

from __future__ import annotations

import time
from typing import Any

from browser_mcp.browser.elements.state import ElementState
from browser_mcp.foundation.retry import RetryConfig, RetryPolicy
from browser_mcp.plugins.forms.detector import FormDetector
from browser_mcp.plugins.forms.validator import FormValidator
from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

__all__ = ["FormActions"]


def _form_event(name: str, **payload: Any) -> DomainEvent:
    return DomainEvent(event_name=name, payload=payload)


def _make_result(
    success: bool,
    session_id: str,
    browser_id: str,
    context_id: str,
    page_id: str,
    duration_ms: int,
    message: str,
    error: str | None = None,
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "success": success,
        "session_id": session_id,
        "browser_id": browser_id,
        "context_id": context_id,
        "page_id": page_id,
        "duration_ms": duration_ms,
        "message": message,
    }
    if error is not None:
        base["error"] = error
    return base


class FormActions:
    """Executes form interactions with retry and validation."""

    def __init__(
        self,
        detector: FormDetector,
        validator: FormValidator,
        state: ElementState,
        event_bus: EventBus,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self._detector = detector
        self._validator = validator
        self._state = state
        self._event_bus = event_bus
        self._retry = RetryPolicy(retry_config or RetryConfig(max_attempts=3))

    async def fill(
        self,
        page: Any,
        session_id: str,
        browser_id: str,
        context_id: str,
        page_id: str,
        field: str,
        value: str,
        *,
        selector: str | None = None,
    ) -> dict[str, Any]:
        """Fill a text field with ``value``."""
        start = time.monotonic()
        await self._event_bus.publish(_form_event("form.started", action="fill", field=field))

        try:
            locator = await self._resolve(page, field, selector)
            await self._validator.validate(
                locator,
                require_visible=True,
                require_enabled=True,
                require_editable=True,
            )
            await locator.fill(value)
            await self._event_bus.publish(
                _form_event("form.field.filled", field=field, value=value, session_id=session_id)
            )
            return _make_result(
                success=True,
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                duration_ms=_duration(start),
                message=f"Field '{field}' filled successfully",
            )
        except Exception as exc:
            await self._event_bus.publish(
                _form_event("form.field.failed", field=field, error=str(exc), session_id=session_id)
            )
            return _make_result(
                success=False,
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                duration_ms=_duration(start),
                error=str(exc),
                message=f"Failed to fill field '{field}': {exc}",
            )

    async def check(
        self,
        page: Any,
        session_id: str,
        browser_id: str,
        context_id: str,
        page_id: str,
        field: str,
        *,
        selector: str | None = None,
    ) -> dict[str, Any]:
        """Check a checkbox or radio button."""
        start = time.monotonic()
        await self._event_bus.publish(_form_event("form.started", action="check", field=field))

        try:
            locator = await self._resolve(page, field, selector)
            await self._validator.validate(locator, require_visible=True, require_enabled=True)
            await locator.check()
            await self._event_bus.publish(
                _form_event("form.field.filled", field=field, value=True, session_id=session_id)
            )
            return _make_result(
                success=True,
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                duration_ms=_duration(start),
                message=f"Field '{field}' checked successfully",
            )
        except Exception as exc:
            await self._event_bus.publish(
                _form_event("form.field.failed", field=field, error=str(exc), session_id=session_id)
            )
            return _make_result(
                success=False,
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                duration_ms=_duration(start),
                error=str(exc),
                message=f"Failed to check field '{field}': {exc}",
            )

    async def uncheck(
        self,
        page: Any,
        session_id: str,
        browser_id: str,
        context_id: str,
        page_id: str,
        field: str,
        *,
        selector: str | None = None,
    ) -> dict[str, Any]:
        """Uncheck a checkbox or radio button."""
        start = time.monotonic()
        await self._event_bus.publish(_form_event("form.started", action="uncheck", field=field))

        try:
            locator = await self._resolve(page, field, selector)
            await self._validator.validate(locator, require_visible=True, require_enabled=True)
            await locator.uncheck()
            await self._event_bus.publish(
                _form_event("form.field.filled", field=field, value=False, session_id=session_id)
            )
            return _make_result(
                success=True,
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                duration_ms=_duration(start),
                message=f"Field '{field}' unchecked successfully",
            )
        except Exception as exc:
            await self._event_bus.publish(
                _form_event("form.field.failed", field=field, error=str(exc), session_id=session_id)
            )
            return _make_result(
                success=False,
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                duration_ms=_duration(start),
                error=str(exc),
                message=f"Failed to uncheck field '{field}': {exc}",
            )

    async def select(
        self,
        page: Any,
        session_id: str,
        browser_id: str,
        context_id: str,
        page_id: str,
        field: str,
        value: str,
        *,
        selector: str | None = None,
    ) -> dict[str, Any]:
        """Select an option in a <select> element."""
        start = time.monotonic()
        await self._event_bus.publish(_form_event("form.started", action="select", field=field))

        try:
            locator = await self._resolve(page, field, selector)
            await self._validator.validate(locator, require_visible=True, require_enabled=True)
            await locator.select_option(value)
            await self._event_bus.publish(
                _form_event("form.field.filled", field=field, value=value, session_id=session_id)
            )
            return _make_result(
                success=True,
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                duration_ms=_duration(start),
                message=f"Field '{field}' selected '{value}' successfully",
            )
        except Exception as exc:
            await self._event_bus.publish(
                _form_event("form.field.failed", field=field, error=str(exc), session_id=session_id)
            )
            return _make_result(
                success=False,
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                duration_ms=_duration(start),
                error=str(exc),
                message=f"Failed to select field '{field}': {exc}",
            )

    async def submit(
        self,
        page: Any,
        session_id: str,
        browser_id: str,
        context_id: str,
        page_id: str,
        field: str | None = None,
        *,
        selector: str | None = None,
    ) -> dict[str, Any]:
        """Submit a form."""
        start = time.monotonic()
        await self._event_bus.publish(
            _form_event("form.started", action="submit", field=field or "N/A")
        )

        try:
            if field:
                locator = await self._resolve(page, field, selector)
                await self._validator.validate(locator, require_visible=True, require_enabled=True)
                await locator.click()
            else:
                await page.locator("form").first.click()

            await self._event_bus.publish(
                _form_event("form.submitted", field=field, session_id=session_id)
            )
            return _make_result(
                success=True,
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                duration_ms=_duration(start),
                message="Form submitted successfully",
            )
        except Exception as exc:
            await self._event_bus.publish(
                _form_event(
                    "form.field.failed",
                    field=field or "N/A",
                    error=str(exc),
                    session_id=session_id,
                )
            )
            return _make_result(
                success=False,
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                duration_ms=_duration(start),
                error=str(exc),
                message=f"Failed to submit form: {exc}",
            )

    async def _resolve(
        self,
        page: Any,
        field: str,
        selector: str | None = None,
    ) -> Any:
        candidates = await self._detector.detect(
            page,
            explicit_selector=selector,
            field_name=field,
            field_id=field,
            field_placeholder=field,
        )
        for candidate in candidates:
            try:
                return page.locator(candidate["value"])
            except Exception as exc:
                _log_resolve_failure(exc)
                continue
        raise ValueError(f"Could not resolve form field '{field}'")


def _log_resolve_failure(exc: Exception) -> None:
    import structlog

    logger = structlog.get_logger("browser_mcp.plugins.forms.actions")
    logger.debug("resolve_failed", error=str(exc))


def _duration(start: float) -> int:
    return int((time.monotonic() - start) * 1000)
