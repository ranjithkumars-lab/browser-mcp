"""Metrics backend factory.

Phase 0 ships a no-op provider. Prometheus and OpenTelemetry backends are
added in a later phase behind the same :class:`MetricsProvider` interface.
"""

from __future__ import annotations

from typing import Any

import structlog

from enterprise_mcp.config.models import MetricsSettings
from enterprise_mcp.observability.metrics.base import Metric, MetricsProvider

__all__ = ["NullMetricsProvider", "configure_metrics"]


class NullMetricsProvider(MetricsProvider):
    """No-op provider used when metrics are disabled."""

    def increment(
        self,
        metric: Metric,
        value: float = 1.0,
        labels: dict[str, Any] | None = None,
    ) -> None:
        """No-op increment."""

    def set(
        self,
        metric: Metric,
        value: float,
        labels: dict[str, Any] | None = None,
    ) -> None:
        """No-op set."""

    def observe(
        self,
        metric: Metric,
        value: float,
        labels: dict[str, Any] | None = None,
    ) -> None:
        """No-op observe."""


def configure_metrics(settings: MetricsSettings) -> MetricsProvider:
    """Return a metrics provider based on the given configuration."""
    logger = structlog.get_logger("enterprise_mcp.observability.metrics")
    if settings.enabled and settings.backend != "null":
        logger.warning(
            "metrics_backend_not_implemented",
            backend=settings.backend,
            hint="implemented in a later phase; using null provider",
        )
    return NullMetricsProvider()
