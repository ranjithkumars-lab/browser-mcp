"""Provider abstraction."""

from __future__ import annotations

__all__ = ["Provider"]


class Provider:
    """Abstract provider for pluggable services (storage, email, etc.).

    Implemented in later phases; exists to fix the extension point.
    """

    name: str = "unnamed"

    async def initialize(self) -> None:
        """Initialize the provider."""
        raise NotImplementedError

    async def dispose(self) -> None:
        """Release provider resources."""
