"""State value objects and unique identifiers for the browser hierarchy."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page

    from browser_mcp.config.models import BrowserEngine, BrowserProfile

__all__ = [
    "BrowserState",
    "ContextState",
    "PageState",
    "new_browser_id",
    "new_context_id",
    "new_page_id",
    "new_session_id",
]


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def new_session_id() -> str:
    """Return a new unique session identifier."""
    return _new_id("session")


def new_browser_id() -> str:
    """Return a new unique browser identifier."""
    return _new_id("browser")


def new_context_id() -> str:
    """Return a new unique context identifier."""
    return _new_id("context")


def new_page_id() -> str:
    """Return a new unique page identifier."""
    return _new_id("page")


@dataclass(slots=True)
class PageState:
    """Read-only snapshot describing a live page."""

    page_id: str
    context_id: str
    url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: Literal["open", "closed"] = "open"


@dataclass(slots=True)
class ContextState:
    """Read-only snapshot describing a live context."""

    context_id: str
    browser_id: str
    profile: BrowserProfile
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: Literal["open", "closed"] = "open"
    pages: list[PageState] = field(default_factory=list[PageState])


@dataclass(slots=True)
class BrowserState:
    """Read-only snapshot describing a live browser instance."""

    browser_id: str
    engine: BrowserEngine
    headless: bool
    profile: BrowserProfile
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: Literal["open", "closed"] = "open"
    contexts: list[ContextState] = field(default_factory=list[ContextState])


@dataclass(slots=True)
class BrowserHandle:
    """A live Playwright ``Browser`` (or persistent ``BrowserContext``) + its stable identifier."""

    browser_id: str
    browser: Browser | BrowserContext
    state: BrowserState


@dataclass(slots=True)
class ContextHandle:
    """A live Playwright ``BrowserContext`` plus its stable identifier."""

    context_id: str
    browser_id: str
    context: BrowserContext
    state: ContextState


@dataclass(slots=True)
class PageHandle:
    """A live Playwright ``Page`` plus its stable identifier."""

    page_id: str
    context_id: str
    browser_id: str
    page: Page
    state: PageState
