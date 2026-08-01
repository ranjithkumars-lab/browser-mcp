"""A small, testable dependency injection container.

Supports:

- registration by class/type or explicit name
- singleton and transient (factory) lifecycles
- synchronous and asynchronous factories
- automatic parameter wiring by name or type annotation

The container is intentionally minimal. It is not a framework replacement;
it exists to keep service composition explicit and testable.
"""

from __future__ import annotations

import inspect
import threading
from collections.abc import Callable
from typing import Any, TypeVar, get_type_hints, overload

from enterprise_mcp.utils.errors import EnterpriseMCPError

T = TypeVar("T")

Factory = Callable[..., Any]

__all__ = ["Container", "DependencyError"]


class DependencyError(EnterpriseMCPError):
    """Raised when a dependency cannot be registered or resolved."""


def _service_key(cls: type[Any] | None, name: str | None) -> str:
    if name is not None:
        return name
    if cls is not None:
        return cls.__name__
    raise DependencyError("either a class or an explicit name must be provided")


def _is_async(factory: Factory) -> bool:
    return inspect.iscoroutinefunction(factory) or inspect.isasyncgenfunction(factory)


class _Service:
    __slots__ = ("factory", "instance", "lock", "singleton")

    def __init__(self, factory: Factory, *, singleton: bool) -> None:
        self.factory = factory
        self.singleton = singleton
        self.lock = threading.Lock()
        self.instance: Any = None

    def has_instance(self) -> bool:
        return self.instance is not None


class Container:
    """Thread-safe, async-capable dependency injection container."""

    def __init__(self) -> None:
        self._services: dict[str, _Service] = {}

    def register(
        self,
        cls: type[Any] | None = None,
        *,
        name: str | None = None,
        factory: Factory | None = None,
        singleton: bool = True,
    ) -> None:
        """Register a service.

        If ``factory`` is omitted, the class itself is used as the factory
        (constructor injection). ``singleton=True`` caches the first resolved
        instance and reuses it for every subsequent resolution.
        """
        key = _service_key(cls, name)
        if key in self._services:
            raise DependencyError(f"service '{key}' is already registered")
        resolved_factory = factory if factory is not None else cls
        if resolved_factory is None:
            raise DependencyError(
                "a factory or class must be provided when registering without a name"
            )
        self._services[key] = _Service(resolved_factory, singleton=singleton)

    def register_instance(self, instance: Any, *, name: str | None = None) -> None:
        """Register an already-constructed instance."""
        key = name if name is not None else type(instance).__name__
        if key in self._services:
            raise DependencyError(f"service '{key}' is already registered")
        service = _Service(lambda: instance, singleton=True)
        service.instance = instance
        self._services[key] = service

    def has(self, name: str) -> bool:
        """Return whether a service is registered under ``name``."""
        return name in self._services

    @overload
    def resolve(self, key: str) -> Any: ...

    @overload
    def resolve(self, key: type[T]) -> T: ...

    def resolve(self, key: str | type[T]) -> Any:
        """Resolve a service synchronously.

        Raises ``DependencyError`` if the factory is asynchronous; use
        :meth:`aresolve` in async contexts.
        """
        name = key if isinstance(key, str) else key.__name__
        service = self._services.get(name)
        if service is None:
            raise DependencyError(f"service '{name}' is not registered")
        if service.singleton and service.has_instance():
            return service.instance
        if _is_async(service.factory):
            raise DependencyError(
                f"service '{name}' has an async factory; use await container.aresolve()"
            )
        instance = service.factory()
        if service.singleton:
            with service.lock:
                if service.instance is None:
                    service.instance = instance
            return service.instance
        return instance

    @overload
    async def aresolve(self, key: str) -> Any: ...

    @overload
    async def aresolve(self, key: type[T]) -> T: ...

    async def aresolve(self, key: str | type[T]) -> Any:
        """Resolve a service asynchronously, awaiting async factories."""
        name = key if isinstance(key, str) else key.__name__
        service = self._services.get(name)
        if service is None:
            raise DependencyError(f"service '{name}' is not registered")
        if service.singleton and service.has_instance():
            return service.instance
        if _is_async(service.factory):
            instance = await service.factory()
        else:
            instance = service.factory()
        if service.singleton:
            with service.lock:
                if service.instance is None:
                    service.instance = instance
            return service.instance
        return instance

    async def acreate(self, cls: type[T]) -> T:
        """Construct ``cls`` once, wiring dependencies from the container."""
        signature = inspect.signature(cls.__init__)
        hints = get_type_hints(cls.__init__)
        kwargs: dict[str, Any] = {}
        for parameter in signature.parameters.values():
            if parameter.name in ("self", "args", "kwargs"):
                continue
            annotation = hints.get(parameter.name, inspect.Parameter.empty)
            if annotation is inspect.Parameter.empty:
                raise DependencyError(
                    f"constructor parameter '{parameter.name}' of {cls.__name__} must be annotated"
                )
            service_key: str | None = None
            if parameter.name in self._services:
                service_key = parameter.name
            elif isinstance(annotation, type) and annotation.__name__ in self._services:
                service_key = annotation.__name__
            if service_key is None:
                if parameter.default is not inspect.Parameter.empty:
                    continue
                raise DependencyError(
                    f"cannot resolve dependency '{parameter.name}' of {cls.__name__}"
                )
            kwargs[parameter.name] = await self.aresolve(service_key)
        return cls(**kwargs)
