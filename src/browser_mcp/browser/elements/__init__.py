"""Element engine: locator strategies, resolution and property/state queries.

Phase 3 introduces a universal locator engine supporting CSS, XPath, ARIA,
text and raw engine selectors, plus ``element_id``-based element queries.
"""

from browser_mcp.browser.elements.engine import ElementEngine, ElementRef, new_element_id
from browser_mcp.browser.elements.models import LocatorModel, LocatorStrategyName
from browser_mcp.browser.elements.properties import ElementProperties
from browser_mcp.browser.elements.provider import LocatorProvider, PlaywrightLocatorProvider
from browser_mcp.browser.elements.resolver import LocatorResolver
from browser_mcp.browser.elements.state import ElementState

__all__ = [
    "ElementEngine",
    "ElementProperties",
    "ElementRef",
    "ElementState",
    "LocatorModel",
    "LocatorProvider",
    "LocatorResolver",
    "LocatorStrategyName",
    "PlaywrightLocatorProvider",
    "new_element_id",
]
