from __future__ import annotations
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4
from pydantic import BaseModel, Field
class JobState(StrEnum):
    QUEUED="queued"; PENDING="pending"; RUNNING="running"; COMPLETED="completed"; FAILED="failed"; CANCELLED="cancelled"; EXPIRED="expired"
class JobModel(BaseModel):
    job_id: str = Field(default_factory=lambda: f"job_{uuid4().hex}")
    type: str
    state: JobState = JobState.QUEUED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None
    progress: float = Field(default=0, ge=0, le=100)
    result: object | None = None
    error: str | None = None
    worker_id: str | None = None
    claimed_at: datetime | None = None
    heartbeat: datetime | None = None
    lease_expiration: datetime | None = None
