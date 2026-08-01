"""Browser engine package.

Implements the strict resource hierarchy:

    Pool -> Browser -> Context -> Page

Each level carries a stable unique identifier (``browser_id``,
``context_id``, ``page_id``) and is managed by a dedicated manager class.
"""

from browser_mcp.browser.context import ContextManager
from browser_mcp.browser.factory import BrowserFactory
from browser_mcp.browser.manager import BrowserManager
from browser_mcp.browser.page import PageManager
from browser_mcp.browser.pool import BrowserPool
from browser_mcp.browser.profile import ProfileManager
from browser_mcp.browser.session import SessionManager

__all__ = [
    "BrowserFactory",
    "BrowserManager",
    "BrowserPool",
    "ContextManager",
    "PageManager",
    "ProfileManager",
    "SessionManager",
]
