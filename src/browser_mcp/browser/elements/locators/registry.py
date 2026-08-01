"""Locator strategy coordinator.

:class:`LocatorRegistry` maps strategy names to their implementations and is
the single seam the element engine uses to build locators. The abstract
:class:`LocatorStrategy` base is defined here so strategy modules stay tiny and
register with one call.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, ClassVar

from browser_mcp.browser.elements.models import LocatorModel, LocatorStrategyName
from browser_mcp.errors import ElementNotFoundError, ElementStateError, InvalidLocatorStrategyError

if TYPE_CHECKING:
    from browser_mcp.browser.elements.provider import LocatorProvider

__all__ = ["LocatorRegistry", "LocatorStrategy"]

Target = Any


class LocatorStrategy(ABC):
    """Base class for a single locator strategy implementation."""

    name: ClassVar[str] = ""

    def __init__(self, provider: LocatorProvider) -> None:
        self._provider = provider

    @abstractmethod
    def create(self, target: Target, value: str) -> Any:
        """Build a locator handle for ``value`` against ``target``."""


class LocatorRegistry:
    """Registers and resolves locator strategies by name."""

    def __init__(self, provider: LocatorProvider, *, register_defaults: bool = True) -> None:
        self._provider = provider
        self._strategies: dict[str, LocatorStrategy] = {}
        if register_defaults:
            self.register_defaults()

    @property
    def provider(self) -> LocatorProvider:
        """Return the underlying locator provider."""
        return self._provider

    def register(self, strategy: LocatorStrategy) -> None:
        """Register ``strategy`` under its strategy name."""
        if not strategy.name:
            raise ValueError("locator strategy must declare a non-empty name")
        self._strategies[strategy.name] = strategy

    def register_all(self, strategies: Iterable[LocatorStrategy]) -> None:
        """Register every strategy in ``strategies``."""
        for strategy in strategies:
            self.register(strategy)

    def get(self, name: str | LocatorStrategyName) -> LocatorStrategy:
        """Return the strategy registered under ``name``."""
        key = str(name)
        strategy = self._strategies.get(key)
        if strategy is None:
            raise InvalidLocatorStrategyError(
                f"unknown locator strategy '{key}' (supported: {', '.join(self.names())})"
            )
        return strategy

    def names(self) -> list[str]:
        """Return the registered strategy names, sorted."""
        return sorted(self._strategies)

    def register_defaults(self) -> None:
        """Register the bundled CSS, XPath, text, ARIA and Playwright strategies."""
        from browser_mcp.browser.elements.locators.aria import AriaStrategy
        from browser_mcp.browser.elements.locators.css import CssStrategy
        from browser_mcp.browser.elements.locators.playwright import PlaywrightStrategy
        from browser_mcp.browser.elements.locators.text import TextStrategy
        from browser_mcp.browser.elements.locators.xpath import XPathStrategy

        self.register_all(
            [
                CssStrategy(self._provider),
                XPathStrategy(self._provider),
                TextStrategy(self._provider),
                AriaStrategy(self._provider),
                PlaywrightStrategy(self._provider),
            ]
        )

    def build(self, target: Target, model: LocatorModel) -> Any:
        """Return the locator handle described by ``model`` without checks."""
        strategy = self.get(model.strategy)
        return strategy.create(target, model.value)

    async def resolve(self, target: Target, model: LocatorModel) -> Any:
        """Build ``model``'s locator and enforce the strict-match contract.

        Raises
        ------
        InvalidLocatorStrategyError:
            When the strategy is not registered.
        ElementStateError:
            When ``strict`` is set and more than one element matches.
        """
        locator = self.build(target, model)
        if model.strict:
            count = await self._provider.count(locator)
            if count > 1:
                raise ElementStateError(
                    f"strict locator '{model.strategy}:{model.value}' matched {count} elements; "
                    "refine the locator or disable strict mode"
                )
            if count == 0 and model.timeout is not None:
                try:
                    await self._provider.wait_for(locator, "attached", model.timeout)
                except Exception as exc:
                    raise ElementNotFoundError(
                        f"element '{model.strategy}:{model.value}' not found within "
                        f"{model.timeout}ms"
                    ) from exc
        return locator
