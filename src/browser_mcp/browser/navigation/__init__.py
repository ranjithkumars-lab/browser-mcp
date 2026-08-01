"""Navigation & Basic Interaction Engine (Phase 2).

This package implements navigation and interaction primitives on top of the
existing browser resource hierarchy:

- :mod:`manager`: core navigation (``goto``, ``reload``)
- :mod:`history`: back/forward history management
- :mod:`frames`: frame and iframe context switching
- :mod:`windows`: tabs and popup management
- :mod:`interactions`: clicks, hovers and scrolling
- :mod:`waiting`: wait tools (navigation, popup, download, url)
- :mod:`state`: central ``StateManager`` (hierarchy + frame tracking)
- :mod:`policy`: navigation boundaries (domains, redirects, schemes)
- :mod:`timeouts`: global timeout resolution

Phase 2 does **not** implement locator strategies; interactions consume the
``LocatorResolver`` abstraction, which defers element-finding to Phase 3.
"""

from browser_mcp.browser.navigation.frames import FrameManager
from browser_mcp.browser.navigation.history import HistoryManager
from browser_mcp.browser.navigation.interactions import InteractionManager, LocatorResolver
from browser_mcp.browser.navigation.manager import NavigationManager
from browser_mcp.browser.navigation.policy import NavigationPolicy, PolicyResult
from browser_mcp.browser.navigation.state import (
    FrameState,
    PopupState,
    StateManager,
)
from browser_mcp.browser.navigation.waiting import WaitingManager
from browser_mcp.browser.navigation.windows import WindowManager

__all__ = [
    "FrameManager",
    "FrameState",
    "HistoryManager",
    "InteractionManager",
    "LocatorResolver",
    "NavigationManager",
    "NavigationPolicy",
    "PolicyResult",
    "PopupState",
    "StateManager",
    "WaitingManager",
    "WindowManager",
]
