# Worker and Job Lifecycle

## Worker state machine

    Stopped → Starting → Ready → Busy → Ready
                        │       │
                        └──────→ Failed
    Ready/Busy → Stopping → Stopped

WorkerManager owns start, stop, and status operations. WorkerEngine performs
one claimed payload at a time; concurrency orchestration can run multiple
engines or tasks up to the configured limit.

## Job ownership

When claimed, a job records worker_id, claimed_at, heartbeat, and
lease_expiration. The owner should renew heartbeats for long-running work. On
lease expiry another worker may safely treat it as abandoned.

## Cancellation

CancellationToken is passed to the executor and should be checked before
executing a tool and at safe checkpoints in long-running workflows.
Cancellation is cooperative, avoiding corruption from force-killing browser
operations mid-step.
