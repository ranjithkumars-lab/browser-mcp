from __future__ import annotations
from datetime import UTC, datetime, timedelta
from browser_mcp.api.jobs.models import JobModel
def claim(job: JobModel, worker_id: str, lease_seconds: float) -> JobModel:
    now=datetime.now(UTC); job.worker_id=worker_id; job.claimed_at=now; job.heartbeat=now; job.lease_expiration=now+timedelta(seconds=lease_seconds); return job
def abandoned(job: JobModel) -> bool: return bool(job.lease_expiration and job.lease_expiration < datetime.now(UTC))
