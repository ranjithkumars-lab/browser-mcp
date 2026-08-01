"""Locator value models for the element engine.

Phase 3 introduces a structured, future-proofed locator model that keeps the
engine vendor-neutral: callers describe *what* to find (strategy + value) and
the provider turns it into a concrete browser locator.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

__all__ = ["LocatorModel", "LocatorStrategyName"]


class LocatorStrategyName(StrEnum):
    """Supported vendor-neutral locator strategy names."""

    CSS = "css"
    XPATH = "xpath"
    ARIA = "aria"
    TEXT = "text"
    PLAYWRIGHT = "playwright"


class LocatorModel(BaseModel):
    """A structured description of how to find an element on a page.

    Attributes
    ----------
    strategy:
        The locator strategy to use (``css``, ``xpath``, ``aria``, ``text`` or
        ``playwright``).
    value:
        The strategy-specific value, e.g. a CSS selector for ``css`` or an
        XPath expression for ``xpath``. For ``aria`` the value uses the
        ``role`` or ``role:accessible name`` syntax.
    timeout:
        Optional per-call timeout in milliseconds. Falls back to the globally
        configured interaction timeout when omitted.
    strict:
        When true (default), a locator must resolve to exactly one element;
        multiple matches raise :class:`ElementStateError`.
    """

    strategy: LocatorStrategyName
    value: str = Field(min_length=1)
    timeout: int | None = Field(default=None, ge=1, description="Timeout in milliseconds.")
    strict: bool = Field(default=True, description="Require exactly one match.")

    @field_validator("value")
    @classmethod
    def value_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value
