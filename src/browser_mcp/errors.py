"""Browser domain error hierarchy.

All browser-specific failures derive from :class:`BrowserError`. Errors are
kept specific so callers (tools, HTTP handlers, tests) can react precisely.
"""

from __future__ import annotations

__all__ = [
    "BrowserError",
    "BrowserNotFoundError",
    "BrowserNotReadyError",
    "BrowserPoolLimitError",
    "ContextError",
    "ContextNotFoundError",
    "DownloadError",
    "ElementError",
    "ElementNotFoundError",
    "ElementStateError",
    "ExtractionError",
    "FieldNotEditableError",
    "FieldNotFoundError",
    "FormError",
    "FormattingError",
    "FrameError",
    "InteractionError",
    "InvalidLocatorStrategyError",
    "NavigationError",
    "NavigationTimeoutError",
    "PageError",
    "PageNotFoundError",
    "PaginationError",
    "PolicyViolationError",
    "PopupError",
    "ProductExtractionError",
    "ProfileError",
    "ScraperError",
    "SessionError",
    "SessionNotFoundError",
    "StaleElementReferenceError",
    "SubmitError",
    "ValidationError",
]


class BrowserError(Exception):
    """Base class for all browser automation errors."""


class BrowserNotReadyError(BrowserError):
    """Raised when a browser operation runs before the engine is started."""


class BrowserNotFoundError(BrowserError):
    """Raised when a browser_id does not map to a live browser."""


class BrowserPoolLimitError(BrowserError):
    """Raised when the browser pool capacity is exhausted."""


class ContextError(BrowserError):
    """Base class for browser context failures."""


class ContextNotFoundError(ContextError):
    """Raised when a context_id does not map to a live context."""


class PageError(BrowserError):
    """Base class for page failures."""


class PageNotFoundError(PageError):
    """Raised when a page_id does not map to a live page."""


class NavigationError(PageError):
    """Raised when a navigation (goto/reload/back/forward) fails."""


class NavigationTimeoutError(NavigationError):
    """Raised when a navigation or wait operation exceeds its timeout."""


class FrameError(NavigationError):
    """Raised when a frame or iframe operation fails."""


class PopupError(NavigationError):
    """Raised when a popup (new window/tab) cannot be resolved."""


class InteractionError(NavigationError):
    """Raised when a user interaction (click/hover/scroll) fails."""


class PolicyViolationError(NavigationError):
    """Raised when navigation violates a configured navigation policy."""


class DownloadError(NavigationError):
    """Raised when a download cannot be awaited or resolved."""


class ElementError(PageError):
    """Base class for element finding and property extraction failures."""


class ElementNotFoundError(ElementError):
    """Raised when a locator resolves to no element."""


class InvalidLocatorStrategyError(ElementError):
    """Raised when an unknown locator strategy name is requested."""


class ElementStateError(ElementError):
    """Raised when an element property or state query fails."""


class StaleElementReferenceError(ElementError):
    """Raised when a cached ``element_id`` no longer refers to a live page."""


class SessionError(BrowserError):
    """Base class for session lifecycle failures."""


class SessionNotFoundError(SessionError):
    """Raised when a session_id does not map to a live session."""


class ProfileError(BrowserError):
    """Raised when a profile cannot be resolved or materialized."""


class FormError(BrowserError):
    """Base class for form automation errors."""


class ValidationError(FormError):
    """Raised when form field validation fails."""


class FieldNotFoundError(FormError):
    """Raised when a form field cannot be located in the DOM."""


class FieldNotEditableError(FormError):
    """Raised when a form field is not editable."""


class SubmitError(FormError):
    """Raised when a form submission fails."""


class ScraperError(BrowserError):
    """Base class for all web scraping failures."""


class ExtractionError(ScraperError):
    """Raised when DOM extraction fails (e.g. page evaluation error)."""


class FormattingError(ScraperError):
    """Raised when a result cannot be serialised to the requested format."""


class PaginationError(ScraperError):
    """Raised when pagination beyond the supported limit is requested."""


class ProductExtractionError(ScraperError):
    """Raised when the composite product collector cannot extract any data."""
