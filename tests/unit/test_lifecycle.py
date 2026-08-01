"""Tests for the lifecycle manager."""

from __future__ import annotations

import pytest

from enterprise_mcp.foundation.lifecycle import LifecycleEvent, LifecycleManager
from enterprise_mcp.utils.errors import LifecycleError

pytestmark = pytest.mark.unit


async def test_hooks_run_in_registration_order() -> None:
    manager = LifecycleManager()
    order: list[str] = []

    async def first() -> None:
        order.append("first")

    async def second() -> None:
        order.append("second")

    manager.register(LifecycleEvent.STARTUP, first)
    manager.register(LifecycleEvent.STARTUP, second)
    await manager.run_startup()
    assert order == ["first", "second"]


async def test_shutdown_hooks_run() -> None:
    manager = LifecycleManager()
    called = False

    async def hook() -> None:
        nonlocal called
        called = True

    manager.register(LifecycleEvent.SHUTDOWN, hook)
    await manager.run_shutdown()
    assert called


async def test_decorator_registration() -> None:
    manager = LifecycleManager()

    @manager.on(LifecycleEvent.STARTUP)
    async def hook() -> None:
        pass

    assert hook in manager.hooks_for(LifecycleEvent.STARTUP)


async def test_sync_hook_supported() -> None:
    manager = LifecycleManager()
    called = False

    def hook() -> None:
        nonlocal called
        called = True

    manager.register(LifecycleEvent.STARTUP, hook)
    await manager.run_startup()
    assert called


async def test_failing_hook_raises_lifecycle_error() -> None:
    manager = LifecycleManager()

    async def failing() -> None:
        raise RuntimeError("boom")

    manager.register(LifecycleEvent.STARTUP, failing)
    with pytest.raises(LifecycleError):
        await manager.run_startup()
