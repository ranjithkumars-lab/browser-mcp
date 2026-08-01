# Worker Configuration

Worker settings belong under config.workers.

    workers:
      concurrency: 4
      lease_timeout_seconds: 60
      retry_backoff_max: 300
      queue_name: browser_jobs

| Setting | Default | Meaning |
| --- | ---: | --- |
| concurrency | 4 | Maximum simultaneous worker tasks. |
| lease_timeout_seconds | 60 | Time a claimed job remains owned without heartbeat renewal. |
| retry_backoff_max | 300 | Upper limit for future retry backoff policies. |
| queue_name | browser_jobs | Logical queue namespace. |

The broker polls high, then default, then low. Use high only for
latency-sensitive work; sustained high-priority traffic can starve lower
queues.

A job is abandoned when lease_expiration is earlier than the current UTC time.
Recovery workers should reclaim only abandoned jobs and preserve the original
job id for traceability.
