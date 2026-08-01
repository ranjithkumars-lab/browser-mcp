"""Provider-agnostic metrics interface."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

__all__ = ["Metric", "MetricType", "MetricsProvider"]


class MetricType(StrEnum):
    """Supported metric primitives."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class Metric:
    """A metric descriptor with a fixed set of labels."""

    def __init__(self, name: str, metric_type: MetricType, description: str = "") -> None:
        self.name = name
        self.metric_type = metric_type
        self.description = description


class MetricsProvider:
    """Abstract interface implemented by concrete metrics backends."""

    def counter(self, name: str, description: str = "", unit: str = "") -> Metric:
        """Return a counter metric descriptor."""
        return Metric(name, MetricType.COUNTER, description)

    def gauge(self, name: str, description: str = "", unit: str = "") -> Metric:
        """Return a gauge metric descriptor."""
        return Metric(name, MetricType.GAUGE, description)

    def histogram(self, name: str, description: str = "", unit: str = "") -> Metric:
        """Return a histogram metric descriptor."""
        return Metric(name, MetricType.HISTOGRAM, description)

    def increment(  # pragma: no cover - implemented by concrete backends
        self,
        metric: Metric,
        value: float = 1.0,
        labels: dict[str, Any] | None = None,
    ) -> None:
        """Increment a counter."""
        raise NotImplementedError

    def set(  # pragma: no cover - implemented by concrete backends
        self,
        metric: Metric,
        value: float,
        labels: dict[str, Any] | None = None,
    ) -> None:
        """Set a gauge value."""
        raise NotImplementedError

    def observe(  # pragma: no cover - implemented by concrete backends
        self,
        metric: Metric,
        value: float,
        labels: dict[str, Any] | None = None,
    ) -> None:
        """Record a histogram observation."""
        raise NotImplementedError
