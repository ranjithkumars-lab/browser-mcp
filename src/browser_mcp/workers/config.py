from pydantic import BaseModel, Field
class WorkerConfig(BaseModel):
    concurrency: int = Field(default=4, ge=1)
    lease_timeout_seconds: float = Field(default=60, gt=0)
    retry_backoff_max: float = Field(default=300, gt=0)
    queue_name: str = "browser_jobs"
