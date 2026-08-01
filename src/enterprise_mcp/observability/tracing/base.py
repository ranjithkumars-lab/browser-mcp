"""Provider-agnostic tracing interface."""

from __future__ import annotations

import structlog

from enterprise_mcp.config.models import TracingSettings

__all__ = ["TracerProvider", "configure_tracing"]


class TracerProvider:
    """Abstract interface for distributed tracing.

    Concrete backends (OpenTelemetry) are added in a later phase.
    """

    @property
    def enabled(self) -> bool:
        """Return whether tracing is active."""
        return False

    def start_span(
        self,
        name: str,
        attributes: dict[str, str] | None = None,
    ) -> object:  # pragma: no cover - implemented by concrete backends
        """Open a new span, returning a context-manager-like handle."""
        raise NotImplementedError


class NullTracerProvider(TracerProvider):
    """No-op tracer used until a real backend is configured."""

    def start_span(self, name: str, attributes: dict[str, str] | None = None) -> object:
        return None


def configure_tracing(settings: TracingSettings) -> TracerProvider:
    """Return a tracer provider based on the given configuration."""
    logger = structlog.get_logger("enterprise_mcp.observability.tracing")
    if settings.enabled and settings.backend != "null":
        logger.warning(
            "tracing_backend_not_implemented",
            backend=settings.backend,
            hint="implemented in a later phase; using null provider",
        )
    return NullTracerProvider()
