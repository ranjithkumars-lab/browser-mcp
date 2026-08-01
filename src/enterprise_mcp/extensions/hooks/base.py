"""Hook point abstraction."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

__all__ = ["Hook", "HookDispatcher"]

Hook = Callable[..., Awaitable[None] | None]


class HookDispatcher:
    """Dispatches registered hooks for a named hook point."""

    def __init__(self) -> None:
        self._hooks: dict[str, list[Hook]] = {}

    def register(self, name: str, hook: Hook) -> None:
        """Register ``hook`` for hook point ``name``."""
        self._hooks.setdefault(name, []).append(hook)

    def registered(self, name: str) -> list[Hook]:
        """Return hooks registered for ``name``."""
        return list(self._hooks.get(name, []))

    async def dispatch(self, name: str, **kwargs: Any) -> None:
        """Await all hooks registered for ``name``."""
        for hook in self.registered(name):
            result = hook(**kwargs)
            if hasattr(result, "__await__"):
                await result  # type: ignore[misc]
