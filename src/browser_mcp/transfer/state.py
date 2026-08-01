"""Transfer state management and lifecycle engine.

:class:`TransferStateManager` provides thread-safe (async-safe) tracking of
in-flight and historical transfers.  It implements a finite-state machine with
the following lifecycle:

    Queued -> Running -> Completed
                     -> Failed
                     -> Cancelled
             -> Paused  (reserved)
    Paused  -> Running  (reserved)
    Paused  -> Cancelled

Progress metrics (speed, ETA, percentage) are computed from byte counters and
elapsed time.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from browser_mcp.transfer.models import TransferProgress, TransferStatus, new_transfer_id

__all__ = [
    "TransferRecord",
    "TransferState",
    "TransferStateManager",
]


@dataclass(slots=True)
class TransferState:
    """Mutable runtime state for a single transfer."""

    transfer_id: str
    tool_name: str
    status: TransferStatus = TransferStatus.QUEUED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    transferred_bytes: int = 0
    total_bytes: int | None = None
    last_update: float = field(default_factory=time.monotonic)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    def to_progress(self) -> TransferProgress:
        """Compute a :class:`TransferProgress` snapshot from current counters."""
        now = time.monotonic()
        # ``monotonic`` and ``datetime.timestamp`` have unrelated epochs.
        # Keep a monotonic start marker in ``last_update`` until a progress
        # update arrives; wall-clock datetimes remain only for reporting.
        elapsed = max(now - self.last_update, 0.001)
        elapsed = max(elapsed, 0.001)
        transferred = self.transferred_bytes
        total = self.total_bytes
        percentage = 0.0
        if total is not None and total > 0:
            percentage = min((transferred / total) * 100.0, 100.0)
        elif transferred > 0:
            percentage = 0.0
        speed_bps = transferred / elapsed if elapsed > 0 else 0.0
        eta: float | None = None
        if total is not None and total > 0 and speed_bps > 0:
            remaining = total - transferred
            eta = remaining / speed_bps if remaining > 0 else 0.0
        return TransferProgress(
            transferred_bytes=transferred,
            total_bytes=total,
            percentage=round(percentage, 2),
            speed_bps=round(speed_bps, 2),
            eta_seconds=round(eta, 2) if eta is not None else None,
        )

    def duration_ms(self) -> float | None:
        """Return elapsed milliseconds from start to completion (or now)."""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.now(UTC)
        return (end - self.started_at).total_seconds() * 1000.0


@dataclass(slots=True)
class TransferRecord:
    """Immutable-ish record combining state and result metadata."""

    transfer_id: str
    tool_name: str
    status: TransferStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    transferred_bytes: int
    total_bytes: int | None
    error: str | None
    metadata: dict[str, Any]


# Valid state transitions: current -> set of allowed next states
_TRANSITIONS: dict[TransferStatus, frozenset[TransferStatus]] = {
    TransferStatus.QUEUED: frozenset(
        {TransferStatus.RUNNING, TransferStatus.CANCELLED, TransferStatus.FAILED}
    ),
    TransferStatus.RUNNING: frozenset(
        {
            TransferStatus.PAUSED,
            TransferStatus.COMPLETED,
            TransferStatus.FAILED,
            TransferStatus.CANCELLED,
        }
    ),
    TransferStatus.PAUSED: frozenset({TransferStatus.RUNNING, TransferStatus.CANCELLED}),
    TransferStatus.COMPLETED: frozenset(),
    TransferStatus.FAILED: frozenset(),
    TransferStatus.CANCELLED: frozenset(),
}


class TransferStateManager:
    """Thread-safe (async-safe) state tracking for transfers."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._transfers: dict[str, TransferState] = {}
        self._cancellations: dict[str, asyncio.Event] = {}

    async def register(
        self,
        tool_name: str,
        *,
        total_bytes: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Register a new transfer and return its ``transfer_id``."""
        transfer_id = new_transfer_id()
        state = TransferState(
            transfer_id=transfer_id,
            tool_name=tool_name,
            total_bytes=total_bytes,
            metadata=metadata or {},
        )
        async with self._lock:
            self._transfers[transfer_id] = state
        return transfer_id

    async def transition(
        self,
        transfer_id: str,
        to_status: TransferStatus,
        *,
        error: str | None = None,
    ) -> TransferState:
        """Move ``transfer_id`` to ``to_status``, validating the transition.

        Raises
        ------
        KeyError
            When ``transfer_id`` is unknown.
        ValueError
            When the transition is not allowed by the state machine.
        """
        async with self._lock:
            state = self._transfers.get(transfer_id)
            if state is None:
                raise KeyError(f"transfer '{transfer_id}' not found")
            allowed = _TRANSITIONS.get(state.status, frozenset())
            if to_status not in allowed:
                raise ValueError(
                    f"invalid transition: '{state.status.value}' -> '{to_status.value}'"
                )
            state.status = to_status
            if to_status in (
                TransferStatus.COMPLETED,
                TransferStatus.FAILED,
                TransferStatus.CANCELLED,
            ):
                state.completed_at = datetime.now(UTC)
            if to_status == TransferStatus.RUNNING and state.started_at is None:
                state.started_at = datetime.now(UTC)
            if error is not None:
                state.error = error
            state.last_update = time.monotonic()
            return state

    async def update_progress(
        self,
        transfer_id: str,
        *,
        transferred_bytes: int,
        total_bytes: int | None = None,
    ) -> TransferProgress:
        """Update byte counters and return a fresh progress snapshot."""
        async with self._lock:
            state = self._transfers.get(transfer_id)
            if state is None:
                raise KeyError(f"transfer '{transfer_id}' not found")
            state.transferred_bytes = transferred_bytes
            if total_bytes is not None:
                state.total_bytes = total_bytes
            state.last_update = time.monotonic()
            return state.to_progress()

    async def get(self, transfer_id: str) -> TransferState:
        """Return the live state for ``transfer_id``."""
        async with self._lock:
            state = self._transfers.get(transfer_id)
            if state is None:
                raise KeyError(f"transfer '{transfer_id}' not found")
            return state

    async def get_record(self, transfer_id: str) -> TransferRecord:
        """Return an immutable :class:`TransferRecord` snapshot."""
        state = await self.get(transfer_id)
        return TransferRecord(
            transfer_id=state.transfer_id,
            tool_name=state.tool_name,
            status=state.status,
            created_at=state.created_at,
            started_at=state.started_at,
            completed_at=state.completed_at,
            transferred_bytes=state.transferred_bytes,
            total_bytes=state.total_bytes,
            error=state.error,
            metadata=dict(state.metadata),
        )

    async def cancel(self, transfer_id: str) -> bool:
        """Request cancellation of ``transfer_id``.

        Returns ``True`` if the transfer was running (and a cancellation
        event was signalled), ``False`` if it was already terminal.
        """
        async with self._lock:
            state = self._transfers.get(transfer_id)
            if state is None:
                raise KeyError(f"transfer '{transfer_id}' not found")
            if state.status in (
                TransferStatus.COMPLETED,
                TransferStatus.FAILED,
                TransferStatus.CANCELLED,
            ):
                return False
            event = self._cancellations.get(transfer_id)
            if event is None:
                event = asyncio.Event()
                self._cancellations[transfer_id] = event
            event.set()
            allowed = _TRANSITIONS.get(state.status, frozenset())
            if TransferStatus.CANCELLED in allowed:
                state.status = TransferStatus.CANCELLED
                state.completed_at = datetime.now(UTC)
                state.error = "cancelled by caller"
                state.last_update = time.monotonic()
            return True

    def cancellation_event(self, transfer_id: str) -> asyncio.Event:
        """Return (creating if necessary) the cancellation event for ``transfer_id``."""
        event = self._cancellations.get(transfer_id)
        if event is None:
            event = asyncio.Event()
            self._cancellations[transfer_id] = event
        return event

    async def list_transfers(self) -> list[TransferRecord]:
        """Return records for all known transfers (in-flight and historical)."""
        async with self._lock:
            return [
                TransferRecord(
                    transfer_id=s.transfer_id,
                    tool_name=s.tool_name,
                    status=s.status,
                    created_at=s.created_at,
                    started_at=s.started_at,
                    completed_at=s.completed_at,
                    transferred_bytes=s.transferred_bytes,
                    total_bytes=s.total_bytes,
                    error=s.error,
                    metadata=dict(s.metadata),
                )
                for s in self._transfers.values()
            ]

    async def cleanup(self, max_history: int = 1000) -> int:
        """Remove completed/failed/cancelled transfers beyond ``max_history``.

        Returns the number of records removed.
        """
        async with self._lock:
            terminal = [
                tid
                for tid, s in self._transfers.items()
                if s.status
                in (TransferStatus.COMPLETED, TransferStatus.FAILED, TransferStatus.CANCELLED)
            ]
            if len(terminal) <= max_history:
                return 0
            to_remove = terminal[: len(terminal) - max_history]
            for tid in to_remove:
                self._transfers.pop(tid, None)
                self._cancellations.pop(tid, None)
            return len(to_remove)
