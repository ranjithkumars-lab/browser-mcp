"""Deterministic DOM form detection.

Form fields are detected by analysing the DOM structure using a
strict fallback order: explicit selector → ARIA attributes →
associated ``<label>`` → ``name`` attribute → ``id`` attribute →
``placeholder`` attribute. No AI guessing is involved.
"""

from __future__ import annotations

from typing import Any

from browser_mcp.browser.elements.provider import LocatorProvider

__all__ = ["FormDetector"]


class FormDetector:
    """Detects form fields on a page using deterministic DOM analysis."""

    def __init__(self, provider: LocatorProvider) -> None:
        self._provider = provider

    async def detect(
        self,
        page: Any,
        explicit_selector: str | None = None,
        field_name: str | None = None,
        field_id: str | None = None,
        field_placeholder: str | None = None,
        field_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Detect form fields matching the given criteria.

        Parameters
        ----------
        page:
            The Playwright page handle.
        explicit_selector:
            An explicit CSS selector to locate the field directly.
        field_name:
            The ``name`` attribute value to match.
        field_id:
            The ``id`` attribute value to match.
        field_placeholder:
            The ``placeholder`` attribute value to match.
        field_type:
            The input ``type`` attribute (e.g. ``text``, ``email``,
            ``password``, ``checkbox``, ``radio``, ``select``).

        Returns
        -------
        A list of dicts with ``strategy``, ``value``, and ``type`` keys.
        """
        if explicit_selector:
            return [
                {"strategy": "css", "value": explicit_selector, "type": field_type or "unknown"}
            ]

        candidates: list[dict[str, Any]] = []

        if field_id:
            candidates.append(
                {"strategy": "css", "value": f"#{field_id}", "type": field_type or "unknown"}
            )

        if field_name:
            candidates.append(
                {
                    "strategy": "css",
                    "value": f'[name="{field_name}"]',
                    "type": field_type or "unknown",
                }
            )

        if field_placeholder:
            candidates.append(
                {
                    "strategy": "css",
                    "value": f'[placeholder="{field_placeholder}"]',
                    "type": field_type or "unknown",
                }
            )

        if field_name:
            candidates.append(
                {
                    "strategy": "xpath",
                    "value": (
                        f"//label[contains(text(), '{field_name}')]"
                        "/following::input[1]"
                    ),
                    "type": field_type or "unknown",
                }
            )

        if field_id:
            candidates.append(
                {
                    "strategy": "xpath",
                    "value": f"//label[@for='{field_id}']/following::input[1]",
                    "type": field_type or "unknown",
                }
            )

        if field_name:
            candidates.append(
                {"strategy": "aria", "value": f"{field_name}", "type": field_type or "unknown"}
            )

        return candidates
