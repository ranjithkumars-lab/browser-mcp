"""Metrics abstractions. Backends (Prometheus, OpenTelemetry) land in a later phase."""

from enterprise_mcp.observability.metrics.base import Metric, MetricsProvider
from enterprise_mcp.observability.metrics.provider import NullMetricsProvider, configure_metrics

__all__ = ["Metric", "MetricsProvider", "NullMetricsProvider", "configure_metrics"]
