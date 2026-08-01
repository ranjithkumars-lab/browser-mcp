"""Tests for the dependency injection container."""

from __future__ import annotations

import pytest

from enterprise_mcp.foundation.container import Container, DependencyError

pytestmark = pytest.mark.unit


class Engine:
    def __init__(self, name: str = "engine") -> None:
        self.name = name


class Car:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine


def test_register_and_resolve_by_class() -> None:
    container = Container()
    container.register(Engine)
    engine = container.resolve(Engine)
    assert isinstance(engine, Engine)


def test_singleton_returns_same_instance() -> None:
    container = Container()
    container.register(Engine)
    assert container.resolve(Engine) is container.resolve(Engine)


def test_transient_returns_new_instances() -> None:
    container = Container()
    container.register(Engine, singleton=False)
    assert container.resolve(Engine) is not container.resolve(Engine)


def test_register_instance() -> None:
    container = Container()
    instance = Engine("fixed")
    container.register_instance(instance)
    assert container.resolve(Engine) is instance


def test_named_registration_and_resolution() -> None:
    container = Container()
    container.register(name="engine", factory=lambda: Engine("named"))
    assert container.resolve("engine").name == "named"
    assert container.has("engine")
    assert not container.has("missing")


def test_duplicate_registration_raises() -> None:
    container = Container()
    container.register(Engine)
    with pytest.raises(DependencyError):
        container.register(Engine)


def test_resolve_unregistered_raises() -> None:
    container = Container()
    with pytest.raises(DependencyError):
        container.resolve("missing")


async def test_async_factory_resolution() -> None:
    container = Container()

    async def async_engine() -> Engine:
        return Engine("async")

    container.register(name="engine", factory=async_engine)
    resolved = await container.aresolve("engine")
    assert resolved.name == "async"


def test_async_factory_sync_resolve_raises() -> None:
    container = Container()

    async def async_engine() -> Engine:
        return Engine()

    container.register(name="engine", factory=async_engine)
    with pytest.raises(DependencyError):
        container.resolve("engine")


async def test_acreate_wires_constructor_dependencies() -> None:
    container = Container()
    container.register(Engine)
    car = await container.acreate(Car)
    assert isinstance(car, Car)
    assert isinstance(car.engine, Engine)
