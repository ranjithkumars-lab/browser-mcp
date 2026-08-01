"""Application lifecycle management.

Provides a registry of startup and shutdown hooks that are executed in a
deterministic order during application bootstrap and teardown.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from enum import StrEnum

from enterprise_mcp.utils.errors import LifecycleError

Hook = Callable[[], Awaitable[None] | None]

__all__ = ["LifecycleEvent", "LifecycleManager"]


class LifecycleEvent(StrEnum):
    """Lifecycle events that can be subscribed to."""

    STARTUP = "startup"
    SHUTDOWN = "shutdown"


class LifecycleManager:
    """Registers and runs application startup/shutdown hooks."""

    def __init__(self) -> None:
        self._hooks: dict[LifecycleEvent, list[Hook]] = {
            LifecycleEvent.STARTUP: [],
            LifecycleEvent.SHUTDOWN: [],
        }

    def on(self, event: LifecycleEvent) -> Callable[[Hook], Hook]:
        """Decorator registering ``func`` for the given lifecycle event."""

        def decorator(func: Hook) -> Hook:
            self.register(event, func)
            return func

        return decorator

    def register(self, event: LifecycleEvent, hook: Hook) -> None:
        """Register ``hook`` to run on ``event``."""
        self._hooks[event].append(hook)

    def hooks_for(self, event: LifecycleEvent) -> list[Hook]:
        """Return the hooks registered for ``event``."""
        return list(self._hooks[event])

    async def run_startup(self) -> None:
        """Execute all startup hooks in registration order."""
        await self._run(LifecycleEvent.STARTUP)

    async def run_shutdown(self) -> None:
        """Execute all shutdown hooks in registration order."""
        await self._run(LifecycleEvent.SHUTDOWN)

    async def _run(self, event: LifecycleEvent) -> None:
        for hook in self._hooks[event]:
            try:
                result = hook()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:
                raise LifecycleError(f"{event.value} hook failed: {exc}") from exc
