"""Configuration and bootstrap for structured logging."""

from __future__ import annotations

import logging
import sys

import structlog

from enterprise_mcp.config.models import LoggingSettings

__all__ = ["configure_logging"]


def configure_logging(settings: LoggingSettings) -> None:
    """Configure structlog and the standard library logging bridge."""
    level = getattr(logging, settings.level.upper(), logging.INFO)

    logging.basicConfig(level=level, format="%(message)s", stream=sys.stdout)

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
    ]

    if settings.format == "json":
        renderer: structlog.typing.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )
