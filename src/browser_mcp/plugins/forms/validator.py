"""Pre-interaction form field validation.

Validates that a resolved element is safe to interact with before
any form action is performed. Checks are ordered by the validation
pipeline: existence → visibility → enabled → editable.
"""

from __future__ import annotations

from typing import Any

from browser_mcp.browser.elements.state import ElementState
from browser_mcp.errors import (
    ElementNotFoundError,
    ElementStateError,
)

__all__ = ["FormValidator"]


class FormValidator:
    """Validates form field state before interaction."""

    def __init__(self, state: ElementState) -> None:
        self._state = state

    async def validate(
        self,
        locator: Any,
        *,
        require_visible: bool = True,
        require_enabled: bool = True,
        require_editable: bool = False,
    ) -> dict[str, bool]:
        """Validate a form field against the required conditions.

        Parameters
        ----------
        locator:
            The resolved Playwright locator for the field.
        require_visible:
            The field must be visible.
        require_enabled:
            The field must be enabled.
        require_editable:
            The field must be editable (e.g. for text inputs).

        Returns
        -------
        A dict of check results.

        Raises
        ------
        ElementNotFoundError
            If the element does not exist in the DOM.
        ElementStateError
            If the element fails a required check.
        """
        snapshot = await self._state.snapshot(locator)

        if not snapshot["exists"]:
            raise ElementNotFoundError("Element does not exist in the DOM")

        if require_visible and not snapshot["visible"]:
            raise ElementStateError("Element is not visible")

        if require_enabled and not snapshot["enabled"]:
            raise ElementStateError("Element is not enabled")

        if require_editable and not snapshot["editable"]:
            raise ElementStateError("Element is not editable")

        return snapshot
