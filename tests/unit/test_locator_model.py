"""Tests for the locator model and strategy name enum."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from browser_mcp.browser.elements.models import LocatorModel, LocatorStrategyName

pytestmark = pytest.mark.unit


async def test_locator_model_defaults() -> None:
    model = LocatorModel(strategy="xpath", value="//div")
    assert model.strategy == LocatorStrategyName.XPATH
    assert model.value == "//div"
    assert model.timeout is None
    assert model.strict is True


async def test_locator_model_accepts_enum_strategy() -> None:
    model = LocatorModel(strategy=LocatorStrategyName.CSS, value="#a")
    assert model.strategy == LocatorStrategyName.CSS


async def test_locator_model_rejects_unknown_strategy() -> None:
    with pytest.raises(ValidationError):
        LocatorModel(strategy="bogus", value="#a")


async def test_locator_model_rejects_empty_value() -> None:
    with pytest.raises(ValidationError):
        LocatorModel(strategy="css", value="   ")


async def test_locator_model_rejects_non_positive_timeout() -> None:
    with pytest.raises(ValidationError):
        LocatorModel(strategy="css", value="#a", timeout=0)


async def test_strategy_name_values() -> None:
    assert {name.value for name in LocatorStrategyName} == {
        "css",
        "xpath",
        "aria",
        "text",
        "playwright",
    }
