"""Observability subsystem.

Structured logging (structlog) plus metrics and tracing abstractions.
Backends are scaffolded only and implemented in later phases.
"""

from enterprise_mcp.observability.logging.setup import configure_logging
from enterprise_mcp.observability.metrics.base import Metric, MetricsProvider
from enterprise_mcp.observability.metrics.provider import NullMetricsProvider, configure_metrics
from enterprise_mcp.observability.tracing.base import TracerProvider

__all__ = [
    "Metric",
    "MetricsProvider",
    "NullMetricsProvider",
    "TracerProvider",
    "configure_logging",
    "configure_metrics",
]
