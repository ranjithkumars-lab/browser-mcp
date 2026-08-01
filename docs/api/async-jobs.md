# Async Jobs
Browser operations are asynchronous.
1. `POST /api/v1/plugins/run` -> Returns `202 Accepted` + `job_id`.
2. `GET /api/v1/jobs/{job_id}` -> Poll for `Completed`, `Failed`, etc.
Handled by `JobManager` and `JobExecutionProvider`.
