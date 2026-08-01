"""Audit logging scaffolding."""

from __future__ import annotations

import structlog

__all__ = ["AuditLogger"]


class AuditLogger:
    """Writes audit events to a dedicated structured logger."""

    def __init__(self) -> None:
        self._logger = structlog.get_logger("enterprise_mcp.audit")

    def record(
        self,
        action: str,
        *,
        subject: str | None = None,
        resource: str | None = None,
        outcome: str = "success",
        details: dict[str, object] | None = None,
    ) -> None:
        """Emit an audit event."""
        self._logger.info(
            "audit",
            action=action,
            subject=subject,
            resource=resource,
            outcome=outcome,
            details=details or {},
        )
